"""Reusable premium animation manager.

Animations are cosmetic: the engine commits state first, then the manager
animates items from their previous position to the projected target. Any
interrupt snaps items to the authoritative layout so the board can never
diverge from GameState.
"""

from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QPointF,
    QTimer,
    QVariantAnimation,
)
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium.theme import ANIMATION_MS


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

    # --- movement ------------------------------------------------------------
    def animate_move(self, item: QGraphicsObject, from_pos, to_pos, z_value: float,
                     *, base_ms: int = ANIMATION_MS["move"]) -> QPropertyAnimation | None:
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
        animation.destroyed.connect(lambda: self._forget(animation))
        animation.start()
        return animation

    def animate_run(self, items_with_targets, z_value: float,
                    *, base_ms: int = ANIMATION_MS["multi_move"]) -> QParallelAnimationGroup | None:
        """Coordinated multi-card movement (tableau sequence transfer)."""
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
                lambda checked=False, item=item, target=target: item.setZValue(
                    max(item.zValue() - 100.0, 5.0)
                )
            )
            group.addAnimation(animation)
        self._groups.append(group)
        group.destroyed.connect(lambda: self._forget_group(group))
        group.finished.connect(lambda: self._forget_group(group))
        group.start()
        return group

    def _on_move_finished(self, item: QGraphicsObject, to_pos, z_value: float) -> None:
        item.setPos(to_pos)
        item.setZValue(z_value)

    def snap(self, item: QGraphicsObject, to_pos, z_value: float) -> None:
        self.interrupt_for(item)
        item.setPos(to_pos)
        item.setZValue(z_value)

    # --- flips ------------------------------------------------------------------
    def animate_flip(self, item: QGraphicsObject) -> None:
        duration = self._duration(ANIMATION_MS["flip"])
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
        animation.destroyed.connect(lambda: self._forget(animation))
        animation.start()

    # --- pulses / glows ----------------------------------------------------------
    def animate_property(self, item: QGraphicsObject, name: str, target: float, base_ms: int) -> None:
        duration = self._duration(base_ms)
        setter = getattr(item, f"set_{name}")
        if duration <= 0:
            setter(target)
            return
        animation = QPropertyAnimation(item, name.encode(), self._parent)
        animation.setDuration(duration)
        animation.setStartValue(getattr(item, f"get_{name}")())
        animation.setEndValue(target)
        self._active.append(animation)
        animation.destroyed.connect(lambda: self._forget(animation))
        animation.start()

    def pulse_hint(self, item: QGraphicsObject) -> None:
        duration = self._duration(ANIMATION_MS["invalid"])
        if duration <= 0:
            item.set_hint(1.0)
            QTimer.singleShot(900, lambda: item.set_hint(0.0))
            return
        animation = QPropertyAnimation(item, b"hint", self._parent)
        animation.setDuration(max(160, duration) * 2)
        animation.setKeyValueAt(0.0, 0.0)
        animation.setKeyValueAt(0.5, 1.0)
        animation.setKeyValueAt(1.0, 0.0)
        self._active.append(animation)
        animation.destroyed.connect(lambda: self._forget(animation))
        animation.start()

    def pulse_property(self, item: QGraphicsObject, name: str) -> None:
        duration = max(200, self._duration(ANIMATION_MS["invalid"]))
        animation = QPropertyAnimation(item, name.encode(), self._parent)
        animation.setDuration(duration * 2)
        animation.setKeyValueAt(0.0, getattr(item, f"get_{name}")())
        animation.setKeyValueAt(0.5, 1.0)
        animation.setKeyValueAt(1.0, 0.0)
        self._active.append(animation)
        animation.destroyed.connect(lambda: self._forget(animation))
        animation.start()

    def invalid_shake(self, item: QGraphicsObject) -> None:
        """Brief left-right emphasis on an invalid move; state never changes."""
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
        animation.destroyed.connect(lambda: self._forget(animation))
        animation.start()

    # --- lifecycle -----------------------------------------------------------------
    def interrupt_for(self, item: QGraphicsObject) -> None:
        for animation in list(self._active):
            if animation.targetObject() is item:
                animation.stop()
                if animation in self._active:
                    self._active.remove(animation)

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
