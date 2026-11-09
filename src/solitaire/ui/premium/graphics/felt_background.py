"""The emerald casino tabletop background item.

The woven felt texture is a bundled PNG resource tiled by QPainter; the
lighting variation and edge vignette are cached pixmaps, so paintEvent only
performs cheap blits. A refined gold/green border is painted on top.
"""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PyQt6.QtWidgets import QGraphicsItem

from solitaire.ui.premium import resources
from solitaire.ui.premium.theme import FELT, FELT_DEEP, GOLD_DIM


@lru_cache(maxsize=8)
def _lighting_layer(width: int, height: int) -> QPixmap:
    """Cached natural-lighting overlay: warm centre, dark edges."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)

    # Warm table-light pool from above centre.
    light = QRadialGradient(width * 0.5, height * 0.28, max(width, height) * 0.85)
    light.setColorAt(0.0, QColor(255, 246, 214, 26))
    light.setColorAt(0.45, QColor(255, 246, 214, 8))
    light.setColorAt(1.0, QColor(255, 246, 214, 0))
    painter.fillRect(QRectF(0, 0, width, height), light)

    # Dark vignette around the edges.
    vignette = QRadialGradient(width / 2, height / 2, max(width, height) * 0.72)
    vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
    vignette.setColorAt(0.68, QColor(0, 0, 0, 30))
    vignette.setColorAt(1.0, QColor(0, 0, 0, 108))
    painter.fillRect(QRectF(0, 0, width, height), vignette)
    painter.end()
    return pixmap


class FeltBackgroundItem(QGraphicsItem):
    """Paints the felt table, lighting and border for the whole scene."""

    def __init__(self, width: float, height: float) -> None:
        super().__init__()
        self._rect = QRectF(0, 0, width, height)
        self.setZValue(-100.0)

    def set_size(self, width: float, height: float) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, width, height)
        self.update()

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        rect = self._rect

        # Deep base, then the bundled woven felt tile.
        painter.fillPath(_rounded(rect, 12), QColor(FELT_DEEP))
        tile = resources.felt_tile()
        painter.setClipPath(_rounded(rect, 12))
        painter.drawTiledPixmap(rect, tile)

        # Cached lighting + vignette layer.
        key_w, key_h = int(rect.width()), int(rect.height())
        painter.drawPixmap(0, 0, _lighting_layer(key_w, key_h))

        # Refined gold/green double border.
        painter.setClipping(False)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        border_path = _rounded(rect.adjusted(3, 3, -3, -3), 10)
        painter.setPen(QPen(QColor(GOLD_DIM), 2.0))
        painter.drawPath(border_path)
        painter.setPen(QPen(QColor(16, 84, 44, 220), 5.0))
        inner = _rounded(rect.adjusted(8, 8, -8, -8), 8)
        painter.drawPath(inner)
        painter.restore()


def _rounded(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path
