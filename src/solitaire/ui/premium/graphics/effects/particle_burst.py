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

PARTICLE_COUNT = 14
BURST_MS = 560
MAX_RADIUS = 96.0
START_DELAY_MS = 110  # bloom after the landed card settles


def _scaled(ms: int) -> int:
    """Follow the user's animation speed (2.0x = twice the speed)."""
    from solitaire.ui.premium.animations.card_animation_manager import (
        CardAnimationManager,
    )

    return CardAnimationManager.instance().duration_for(ms)

GOLD = QColor(240, 199, 94)
GOLD_BRIGHT = QColor(255, 236, 170)
MINT = QColor(64, 224, 178)
SHADOW = QColor(6, 20, 12, 150)


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
        self._animation.setDuration(_scaled(BURST_MS))
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.valueChanged.connect(self._on_progress)
        self._animation.finished.connect(self._on_finished)

    def start(self) -> None:
        from PyQt6.QtCore import QTimer

        # A short beat after landing: the burst blooms around the settled
        # card where gold-on-felt reads clearly (never buried on ivory).
        QTimer.singleShot(_scaled(START_DELAY_MS), self._begin)

    def _begin(self) -> None:
        try:
            self._animation.start()
        except RuntimeError:
            pass

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
        # Dark halo pass first so motes read on any surface (felt or ivory).
        for angle, speed, size, color in self._particles:
            distance = radius * speed
            x = self._center.x() + math.cos(angle) * distance
            y = self._center.y() + math.sin(angle) * distance * 0.82
            halo = QColor(SHADOW)
            halo.setAlpha(int(140 * fade))
            painter.setPen(QPen(halo, size + 2.2))
            painter.drawPoint(QPointF(x, y))
        for angle, speed, size, color in self._particles:
            distance = radius * speed
            x = self._center.x() + math.cos(angle) * distance
            y = self._center.y() + math.sin(angle) * distance * 0.82  # slight ellipse
            core = QColor(GOLD_BRIGHT if color is GOLD else color)
            core.setAlpha(int(240 * fade))
            painter.setPen(QPen(core, size))
            painter.drawPoint(QPointF(x, y))
        # Expanding halo ring at low alpha for the "placed" chime feel.
        ring = QColor(GOLD_BRIGHT)
        ring.setAlpha(int(110 * fade))
        painter.setPen(QPen(ring, 2.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self._center, radius * 0.72, radius * 0.72)
        painter.restore()
