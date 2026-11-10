"""Fading gold movement trail used by the animation system."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QVariantAnimation
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen


class GoldTrailItem:
    """Composition helper: a QGraphicsItem-like trail managed by the scene.

    Implemented as a plain object holding a QVariantAnimation and a drawable
    path; the scene registers it in `effects_layer` and repaints the trail
    while the fade animation runs.
    """

    def __init__(self, path: QPainterPath, duration: int = 300, width: float = 4.0) -> None:
        self.path = path
        self.width = width
        self.opacity = 0.85
        self._animation = QVariantAnimation()
        self._animation.setStartValue(0.85)
        self._animation.setEndValue(0.0)
        self._animation.setDuration(duration)
        self._animation.valueChanged.connect(self._on_value)
        self._animation.finished.connect(self._on_finished)
        self.on_finished = None

    def start(self) -> None:
        self._animation.start()

    def stop(self) -> None:
        self._animation.stop()

    @property
    def running(self) -> bool:
        return self._animation.state() == QVariantAnimation.State.Running

    def _on_value(self, value: float) -> None:
        self.opacity = float(value)

    def _on_finished(self) -> None:
        if self.on_finished is not None:
            self.on_finished(self)

    def paint(self, painter: QPainter) -> None:
        if self.opacity <= 0.01:
            return
        painter.save()
        color = QColor(240, 199, 94, int(220 * self.opacity))
        painter.setPen(QPen(color, self.width))
        painter.setBrush(QColor(212, 175, 55, int(46 * self.opacity)))
        painter.drawPath(self.path)
        painter.restore()
