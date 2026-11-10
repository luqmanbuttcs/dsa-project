"""Reusable premium animation manager.

Animations are cosmetic: the engine commits state first, then the manager
animates items from their previous position to the projected target. Any
interrupt snaps items to the authoritative layout so the board can never
diverge from GameState.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QPointF, QTimer, QVariantAnimation
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium.theme import ANIMATION_MS


def _safe_set_z(item: QGraphicsObject, _target) -> None:
    """Restore a post-animation z-order, tolerating a destroyed item."""
    try:
        item.setZValue(max(item.zValue() - 100.0, 5.0))
    except RuntimeError:
        pass


class CardAnimationManager:
    """Owns all card movement, flip, trail and pulse animations."""

    _instance: CardAnimationManager | None = None

    def __init__(self, parent=None) -> None:
        self._parent = parent
        self.reduce_motion = False
        self.speed_multiplier = 1.0
        self._active: list[QPropertyAnimation] = []
        self._groups: list[QParallelAnimationGroup] = []
        self._pending: set[QPropertyAnimation] = set()

    @classmethod
    def instance(cls) -> CardAnimationManager:
        if cls._instance is None:
            cls._instance = CardAnimationManager()
        return cls._instance

    # --- helpers -----------------------------------------------------------
    def duration_for(self, base_ms: int) -> int:
        """Scaled duration for *base_ms* at the user's animation speed.

        The multiplier is a **speed** multiplier, matching the Settings
        label ("Animation speed 2.0x"): 2.0x means the same motion plays
        twice as fast, i.e. the duration is *divided* by the multiplier.
        The historical implementation multiplied instead, so raising the
        slider made the game feel progressively slower — the exact opposite
        of what the control promises.
        """
        if self.reduce_motion:
            return 0
        multiplier = max(float(self.speed_multiplier), 0.1)
        return max(1, int(round(base_ms / multiplier)))

    def _duration(self, base_ms: int) -> int:
        return self.duration_for(base_ms)

    def _prune(self) -> None:
        """Drop animations that finished naturally or lost their target.

        Called before starting new work. Pruning eagerly releases the
        animation<->manager reference cycles while every closure cell is
        still intact, so cyclic GC can never invoke a destroyed-signal
        handler with cleared cells (the CI exit-134 / NameError family).
        Retired timelines are deleteLater()'d: they are QObject children of
        the shared parent, so dropping only the Python reference would let
        the C++ objects accumulate for the whole session.
        """
        from PyQt6.QtCore import QAbstractAnimation

        keep: list[QPropertyAnimation] = []
        for animation in self._active:
            if (
                animation.state() == QAbstractAnimation.State.Running
                or animation in self._pending
            ):
                keep.append(animation)
            else:
                animation.deleteLater()
        self._active = keep
        still: list[QParallelAnimationGroup] = []
        for group in self._groups:
            if group.state() == QAbstractAnimation.State.Running:
                still.append(group)
            else:
                group.deleteLater()
        self._groups = still

    def _track(self, animation) -> None:
        """Register a one-shot animation and retire it when it finishes.

        Retiring on ``finished`` (instead of only at the next ``_prune()``)
        means completed timelines never accumulate — neither as Python
        references nor as C++ children of the shared parent — while gameplay
        keeps starting new animations at full speed.
        """
        self._active.append(animation)
        animation.finished.connect(lambda anim=animation: self._retire(anim))

    def _retire(self, animation) -> None:
        """Forget a finished/stopped animation and release its C++ object."""
        self._pending.discard(animation)
        if animation in self._active:
            self._active.remove(animation)
        animation.deleteLater()

    # --- movement ------------------------------------------------------------
    def animate_move(
        self,
        item: QGraphicsObject,
        from_pos,
        to_pos,
        z_value: float,
        *,
        base_ms: int = ANIMATION_MS["move"],
        bounce: bool = False,
        delay_ms: int = 0,
    ) -> QPropertyAnimation | None:
        self._prune()
        duration = self._duration(base_ms)
        if duration <= 0:
            self.snap(item, to_pos, z_value)
            return None
        # A new movement always supersedes any in-flight animation of the
        # same item (rapid user actions must never fight over `pos`).
        self.interrupt_for(item)
        item.setZValue(z_value + 100.0)
        animation = QPropertyAnimation(item, b"pos", self._parent)
        animation.setDuration(duration)
        animation.setStartValue(from_pos)
        animation.setEndValue(to_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(
            lambda: self._on_move_finished(item, to_pos, z_value, bounce)
        )
        self._track(animation)
        self._watch_item(item)
        if delay_ms > 0:
            self._start_later(animation, delay_ms)
        else:
            animation.start()
        return animation

    def _start_later(self, animation: QPropertyAnimation, delay_ms: int) -> None:
        """Start `animation` after `delay_ms` (staggered deals/draws).

        The pending set keeps _prune() from dropping not-yet-started
        animations; interrupt_all() clears it so an interrupted sequence
        never starts late.
        """
        self._pending.add(animation)

        def _fire() -> None:
            self._pending.discard(animation)
            if animation in self._active:
                try:
                    animation.start()
                except RuntimeError:
                    pass  # retired before its delay elapsed; nothing to start

        QTimer.singleShot(delay_ms, _fire)

    def animate_run(self, items_with_targets, z_value: float,
                    *, base_ms: int = ANIMATION_MS["multi_move"]) -> QParallelAnimationGroup | None:
        """Coordinated multi-card movement (tableau sequence transfer)."""
        self._prune()
        duration = self._duration(base_ms)
        if duration <= 0 or not items_with_targets:
            for item, target in items_with_targets:
                self.snap(item, target, z_value)
            return None
        for item, _target in items_with_targets:
            self.interrupt_for(item)
        group = QParallelAnimationGroup(self._parent)
        stagger_step = self.duration_for(12)
        for index, (item, target) in enumerate(items_with_targets):
            item.setZValue(z_value + 100.0 + index)
            animation = QPropertyAnimation(item, b"pos", group)
            animation.setDuration(duration + index * stagger_step)
            animation.setStartValue(item.pos())
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.finished.connect(
                lambda checked=False, item=item, target=target: _safe_set_z(item, target)
            )
            group.addAnimation(animation)
        self._groups.append(group)
        group.finished.connect(lambda: self._retire_group(group))
        for item, _target in items_with_targets:
            self._watch_item(item)
        group.start()
        return group

    def _on_move_finished(
        self, item: QGraphicsObject, to_pos, z_value: float, bounce: bool = False
    ) -> None:
        try:
            item.setPos(to_pos)
            item.setZValue(z_value)
        except RuntimeError:
            # The item's C++ object was destroyed while the animation ran.
            return
        if bounce:
            self.settle_pop(item)

    def snap(self, item: QGraphicsObject, to_pos, z_value: float) -> None:
        self.interrupt_for(item)
        item.setPos(to_pos)
        item.setZValue(z_value)

    # --- settle pop -----------------------------------------------------------
    def settle_pop(self, item: QGraphicsObject, base_ms: int = 130) -> None:
        """Tiny spring scale when a card lands — the 'placed' feel."""
        if self.reduce_motion:
            return
        duration = self._duration(base_ms)
        if duration <= 0:
            return
        try:
            item.set_pop_scale(0.0)
            animation = QPropertyAnimation(item, b"pop_scale", self._parent)
            animation.setDuration(duration)
            animation.setKeyValueAt(0.0, 0.0)
            animation.setKeyValueAt(0.45, 1.0)
            animation.setKeyValueAt(1.0, 0.0)
            animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self._track(animation)
            self._watch_item(item)
            animation.start()
        except RuntimeError:
            pass

    # --- flips ------------------------------------------------------------------
    def animate_flip(self, item: QGraphicsObject) -> None:
        self._prune()
        duration = self._duration(ANIMATION_MS["flip"])
        self._watch_item(item)
        if duration <= 0:
            item.set_flip(0.0 if item.card.face_up else 1.0)
            return
        target = 0.0 if item.card.face_up else 1.0
        animation = QPropertyAnimation(item, b"flip", self._parent)
        animation.setDuration(duration)
        animation.setStartValue(item.get_flip())
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._track(animation)
        animation.start()

    # --- pulses / glows ----------------------------------------------------------
    def animate_property(self, item: QGraphicsObject, name: str, target: float, base_ms: int) -> None:
        self._prune()
        duration = self._duration(base_ms)
        setter = getattr(item, f"set_{name}")
        self._watch_item(item)
        if duration <= 0:
            setter(target)
            return
        animation = QPropertyAnimation(item, name.encode(), self._parent)
        animation.setDuration(duration)
        animation.setStartValue(getattr(item, f"get_{name}")())
        animation.setEndValue(target)
        self._track(animation)
        animation.start()

    def pulse_hint(self, item: QGraphicsObject) -> None:
        self._prune()
        duration = self._duration(ANIMATION_MS["invalid"])
        if duration <= 0:
            item.set_hint(1.0)

            def _fade_back(target=item) -> None:
                try:
                    target.set_hint(0.0)
                except RuntimeError:
                    pass

            QTimer.singleShot(900, _fade_back)
            return
        animation = QPropertyAnimation(item, b"hint", self._parent)
        animation.setDuration(max(120, duration) * 2)
        animation.setKeyValueAt(0.0, 0.0)
        animation.setKeyValueAt(0.5, 1.0)
        animation.setKeyValueAt(1.0, 0.0)
        self._track(animation)
        animation.start()

    def pulse_property(self, item: QGraphicsObject, name: str) -> None:
        self._prune()
        duration = max(140, self._duration(ANIMATION_MS["invalid"]))
        animation = QPropertyAnimation(item, name.encode(), self._parent)
        animation.setDuration(duration * 2)
        animation.setKeyValueAt(0.0, getattr(item, f"get_{name}")())
        animation.setKeyValueAt(0.5, 1.0)
        animation.setKeyValueAt(1.0, 0.0)
        self._track(animation)
        animation.start()

    def invalid_shake(self, item: QGraphicsObject) -> QPropertyAnimation | None:
        """Brief left-right emphasis on an invalid move; state never changes.

        Returns the running animation so callers can chain follow-up work
        (e.g. the fly-home movement) to its ``finished`` signal, or ``None``
        when the shake is disabled (Reduce Motion). A new shake supersedes an
        in-flight one on the same item, mirroring the movement doctrine.
        """
        self._prune()
        self.interrupt_for(item)
        duration = self._duration(ANIMATION_MS["invalid"])
        if duration <= 0:
            return None
        origin = item.pos()
        animation = QPropertyAnimation(item, b"pos", self._parent)
        animation.setDuration(duration * 2)
        animation.setKeyValueAt(0.0, origin)
        animation.setKeyValueAt(0.25, origin + QPointF(-7, 0))
        animation.setKeyValueAt(0.5, origin + QPointF(7, 0))
        animation.setKeyValueAt(0.75, origin)
        animation.setKeyValueAt(1.0, origin)
        animation.finished.connect(lambda: item.setPos(origin))
        self._track(animation)
        animation.start()
        return animation

    # --- lifecycle -----------------------------------------------------------------
    def _watch_item(self, item: QObject) -> None:
        """Drop tracked animations when their target item is destroyed.

        QGraphicsItems are owned by the scene; when a window is torn down the
        C++ objects can die while an animation still holds them. We must NOT
        call stop()/setPos() during destruction (the item is already dying);
        we only release our references so nothing writes into the dead target
        later. This was observed as an abort (exit code 134) in CI garbage
        collection.
        """
        destroyed_signal = getattr(item, "destroyed", None)
        if destroyed_signal is None:
            return
        destroyed_signal.connect(lambda *_args: self._release_orphans())

    def _release_orphans(self) -> None:
        """Forget animations whose C++ target object no longer exists."""
        still_alive: list = []
        for animation in list(self._active):
            try:
                target = animation.targetObject()
            except RuntimeError:  # Python wrapper already gone
                target = None
            if target is None:
                continue  # orphaned: drop the reference, never call stop()
            still_alive.append(animation)
        self._active = still_alive

        still_alive_groups: list = []
        for group in list(self._groups):
            dead_child = False
            for index in range(group.animationCount()):
                child = group.animationAt(index)
                try:
                    if child.targetObject() is None:
                        dead_child = True
                        break
                except RuntimeError:
                    dead_child = True
                    break
            if not dead_child:
                still_alive_groups.append(group)
            else:
                group.deleteLater()
        self._groups = still_alive_groups

    def interrupt_for(self, item: QGraphicsObject) -> None:
        for animation in list(self._active):
            if animation.targetObject() is item:
                animation.stop()
                self._retire(animation)
        for group in list(self._groups):
            for index in range(group.animationCount()):
                child = group.animationAt(index)
                if child.targetObject() is item:
                    group.stop()
                    self._retire_group(group)
                    break

    def interrupt_all(self) -> None:
        for animation in list(self._active):
            animation.stop()
            self._retire(animation)
        for group in list(self._groups):
            group.stop()
            self._retire_group(group)
        self._active.clear()
        self._groups.clear()
        self._pending.clear()

    def _retire_group(self, group) -> None:
        """Forget a finished/stopped group and release its C++ object."""
        if group in self._groups:
            self._groups.remove(group)
        group.deleteLater()

    def _forget(self, animation) -> None:
        if animation in self._active:
            self._active.remove(animation)

    def _forget_group(self, group) -> None:
        if group in self._groups:
            self._groups.remove(group)
