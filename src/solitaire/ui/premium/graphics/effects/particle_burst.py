"""Gold particle burst: the Foundation placement celebration.

A short-lived QGraphicsObject holding 12-14 light motes that fly radially
from the slot centre, fading over ~620ms, then remove themselves. Purely
cosmetic: it reads no game state and survives interruption trivially.
"""

from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QRectF, QVariantAnimation, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsObject

PARTICLE_COUNT = 13
BURST_MS = 620
MAX_RADIUS = 58.0

GOLD = QColor(240, 199, 94)
MINT = QColor(64, 224, 178)


class ParticleBurstItem(QGraphicsObject):
    """One radial golden burst; self-removes from the scene when done."""

    def __init__(self, center: QPointF, *, rich: bool = True, seed: int | None = None, parent=None):
        super().__init__(parent)
        rng = random.Random(seed)
        self._center = QPointF(center)
        self._progress = 0.0
        self._particles: list[tuple[float, float, float, QColor]] = []
        for index in range(PARTICLE_COUNT):
            angle = (2.0 * math.pi * index) / PARTICLE_COUNT + rng.uniform(-0.18, 0.18)
            speed = rng.uniform(0.55, 1.0)
            color = GOLD if (not rich or index % 3) else MINT
            self._particles.append((angle, speed, rng.uniform(1.6, 3.1), color))
        self.setZValue(500.0)
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(BURST_MS)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.valueChanged.connect(self._on_progress)
        self._animation.finished.connect(self._on_finished)

    def start(self) -> None:
        self._animation.start()

    def boundingRect(self) -> QRectF:
        radius = MAX_RADIUS + 10.0
        return QRectF(
            self._center.x() - radius,
            self._center.y() - radius,
            radius * 2.0,
            radius * 2.0,
        )

    def _on_progress(self, value) -> None:
        self._progress = float(value)
        self.update()

    def _on_finished(self) -> None:
        scene = self.scene()
        if scene is not None:
            scene.removeItem(self)
        self.deleteLater()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        progress = self._progress
        if progress <= 0.0 or progress >= 1.0:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ease_out = 1.0 - (1.0 - progress) ** 2
        radius = MAX_RADIUS * ease_out
        fade = max(0.0, 1.0 - progress)
        for angle, speed, size, color in self._particles:
            distance = radius * speed
            x = self._center.x() + math.cos(angle) * distance
            y = self._center.y() + math.sin(angle) * distance * 0.82  # slight ellipse
            mote = QColor(color)
            mote.setAlpha(int(230 * fade))
            painter.setPen(QPen(mote, size))
            painter.drawPoint(QPointF(x, y))
        # Expanding halo ring at low alpha for the "placed" chime feel.
        ring = QColor(GOLD)
        ring.setAlpha(int(80 * fade))
        painter.setPen(QPen(ring, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self._center, radius * 0.7, radius * 0.7)
        painter.restore()
