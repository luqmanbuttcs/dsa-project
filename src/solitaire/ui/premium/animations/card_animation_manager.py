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

    @classmethod
    def instance(cls) -> CardAnimationManager:
        if cls._instance is None:
            cls._instance = CardAnimationManager()
        return cls._instance

    # --- helpers -----------------------------------------------------------
    def _duration(self, base_ms: int) -> int:
        if self.reduce_motion:
            return 0
        return int(base_ms * self.speed_multiplier)

    def _prune(self) -> None:
        """Drop animations that finished naturally or lost their target.

        Called before starting new work. Pruning eagerly releases the
        animation<->manager reference cycles while every closure cell is
        still intact, so cyclic GC can never invoke a destroyed-signal
        handler with cleared cells (the CI exit-134 / NameError family).
        """
        from PyQt6.QtCore import QAbstractAnimation

        self._active = [
            animation
            for animation in self._active
            if animation.state() == QAbstractAnimation.State.Running
        ]
        self._groups = [
            group
            for group in self._groups
            if group.state() == QAbstractAnimation.State.Running
        ]

    # --- movement ------------------------------------------------------------
    def animate_move(self, item: QGraphicsObject, from_pos, to_pos, z_value: float,
                     *, base_ms: int = ANIMATION_MS["move"]) -> QPropertyAnimation | None:
        self._prune()
        duration = self._duration(base_ms)
        if duration <= 0:
            self.snap(item, to_pos, z_value)
            return None
        item.setZValue(z_value + 100.0)
        animation = QPropertyAnimation(item, b"pos", self._parent)
        animation.setDuration(duration)
        animation.setStartValue(from_pos)
        animation.setEndValue(to_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: self._on_move_finished(item, to_pos, z_value))
        self._active.append(animation)
        self._watch_item(item)
        animation.start()
        return animation

    def animate_run(self, items_with_targets, z_value: float,
                    *, base_ms: int = ANIMATION_MS["multi_move"]) -> QParallelAnimationGroup | None:
        """Coordinated multi-card movement (tableau sequence transfer)."""
        self._prune()
        duration = self._duration(base_ms)
        if duration <= 0 or not items_with_targets:
            for item, target in items_with_targets:
                self.snap(item, target, z_value)
            return None
        group = QParallelAnimationGroup(self._parent)
        for index, (item, target) in enumerate(items_with_targets):
            item.setZValue(z_value + 100.0 + index)
            animation = QPropertyAnimation(item, b"pos", group)
            animation.setDuration(duration + index * 12)
            animation.setStartValue(item.pos())
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.finished.connect(
                lambda checked=False, item=item, target=target: _safe_set_z(item, target)
            )
            group.addAnimation(animation)
        self._groups.append(group)
        group.finished.connect(lambda: self._forget_group(group))
        for item, _target in items_with_targets:
            self._watch_item(item)
        group.start()
        return group

    def _on_move_finished(self, item: QGraphicsObject, to_pos, z_value: float) -> None:
        try:
            item.setPos(to_pos)
            item.setZValue(z_value)
        except RuntimeError:
            # The item's C++ object was destroyed while the animation ran.
            pass

    def snap(self, item: QGraphicsObject, to_pos, z_value: float) -> None:
        self.interrupt_for(item)
        item.setPos(to_pos)
        item.setZValue(z_value)

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
        self._active.append(animation)
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
        self._active.append(animation)
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
        animation.setDuration(max(160, duration) * 2)
        animation.setKeyValueAt(0.0, 0.0)
        animation.setKeyValueAt(0.5, 1.0)
        animation.setKeyValueAt(1.0, 0.0)
        self._active.append(animation)
        animation.start()

    def pulse_property(self, item: QGraphicsObject, name: str) -> None:
        self._prune()
        duration = max(200, self._duration(ANIMATION_MS["invalid"]))
        animation = QPropertyAnimation(item, name.encode(), self._parent)
        animation.setDuration(duration * 2)
        animation.setKeyValueAt(0.0, getattr(item, f"get_{name}")())
        animation.setKeyValueAt(0.5, 1.0)
        animation.setKeyValueAt(1.0, 0.0)
        self._active.append(animation)
        animation.start()

    def invalid_shake(self, item: QGraphicsObject) -> None:
        """Brief left-right emphasis on an invalid move; state never changes."""
        self._prune()
        duration = self._duration(ANIMATION_MS["invalid"])
        if duration <= 0:
            return
        origin = item.pos()
        animation = QPropertyAnimation(item, b"pos", self._parent)
        animation.setDuration(duration * 2)
        animation.setKeyValueAt(0.0, origin)
        animation.setKeyValueAt(0.25, origin + QPointF(-7, 0))
        animation.setKeyValueAt(0.5, origin + QPointF(7, 0))
        animation.setKeyValueAt(0.75, origin)
        animation.setKeyValueAt(1.0, origin)
        animation.finished.connect(lambda: item.setPos(origin))
        self._active.append(animation)
        animation.start()

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
        self._groups = still_alive_groups

    def interrupt_for(self, item: QGraphicsObject) -> None:
        for animation in list(self._active):
            if animation.targetObject() is item:
                animation.stop()
                if animation in self._active:
                    self._active.remove(animation)
        for group in list(self._groups):
            for index in range(group.animationCount()):
                child = group.animationAt(index)
                if child.targetObject() is item:
                    group.stop()
                    if group in self._groups:
                        self._groups.remove(group)
                    break

    def interrupt_all(self) -> None:
        for animation in list(self._active):
            animation.stop()
        for group in list(self._groups):
            group.stop()
        self._active.clear()
        self._groups.clear()

    def _forget(self, animation) -> None:
        if animation in self._active:
            self._active.remove(animation)

    def _forget_group(self, group) -> None:
        if group in self._groups:
            self._groups.remove(group)
