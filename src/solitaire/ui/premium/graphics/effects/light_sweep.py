"""A very restrained ambient light sweep across the felt.

One soft diagonal sheen band glides across the table roughly every 19
seconds, at a peak alpha of ~12/255 — felt breathing under the dealer's
lamp, never a distraction. The band is a cached gradient pixmap that only
*translates*; steps are driven by a scene-owned QTimer at ~24 fps, so the
cost is one small clipped blit per step and the timer cannot outlive the
scene. Disabled by Reduce Motion or the user setting; it never animates
game data.
"""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QGraphicsItem

SWEEP_PERIOD_MS = 19_000
BAND_WIDTH = 260.0
PEAK_ALPHA = 12
START_PHASE = -0.35
END_PHASE = 1.35


@lru_cache(maxsize=2)
def _band_pixmap(height: int) -> QPixmap:
    """The cached vertical gradient band (white core, feathered edges)."""
    width = int(BAND_WIDTH)
    pixmap = QPixmap(width, max(1, height))
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    gradient = QLinearGradient(0.0, 0.0, float(width), 0.0)
    gradient.setColorAt(0.0, QColor(255, 252, 235, 0))
    gradient.setColorAt(0.5, QColor(255, 252, 235, PEAK_ALPHA))
    gradient.setColorAt(1.0, QColor(255, 252, 235, 0))
    painter.fillRect(QRectF(0, 0, width, height), gradient)
    painter.end()
    return pixmap


class LightSweepItem(QGraphicsItem):
    """Slow ambient sheen travelling across the tabletop (z above felt)."""

    def __init__(self, width: float, height: float, parent=None) -> None:
        super().__init__(parent)
        self._rect = QRectF(0, 0, width, height)
        self._phase = START_PHASE  # start off-table so the first sweep arrives naturally
        self._enabled = False
        self._last_bucket = None
        self.setZValue(-90.0)  # above the felt (-100), below slots and cards

    def set_size(self, width: float, height: float) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, width, height)
        self.update()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Arm or disarm the sweep (the scene owns the driving timer)."""
        self._enabled = bool(enabled)
        if not enabled:
            self._phase = START_PHASE
            self.update()

    def step(self, dt_ms: int) -> None:
        """Advance the phase; called by the scene's timer (~24 fps)."""
        if not self._enabled:
            return
        self._phase += dt_ms / float(SWEEP_PERIOD_MS) * (END_PHASE - START_PHASE)
        if self._phase > END_PHASE:
            self._phase = START_PHASE
        # Throttle repaints to a 1/240 phase bucket (~24 steps per sweep
        # segment is visually indistinguishable and cheap).
        bucket = int(self._phase * 240)
        if bucket == self._last_bucket:
            return
        self._last_bucket = bucket
        self.update()

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if not self._enabled or self._phase <= START_PHASE + 0.001:
            return
        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(self._rect.adjusted(6, 6, -6, -6), 9, 9)
        painter.setClipPath(clip)
        band = _band_pixmap(int(self._rect.height()))
        x = (self._rect.width() + BAND_WIDTH) * self._phase - BAND_WIDTH
        painter.drawPixmap(int(x), 0, band)
        painter.restore()
