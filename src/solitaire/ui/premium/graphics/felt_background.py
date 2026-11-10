"""The emerald casino tabletop background item.

The woven felt texture is a bundled PNG resource tiled by QPainter; the
lighting layers (overhead table lamp, edge illumination, vignette) are
cached pixmaps, so paintEvent only performs cheap blits. A refined
gold/brass border with an inner bevel is painted on top.
"""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QLinearGradient,
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import QGraphicsItem

from solitaire.ui.premium import resources
from solitaire.ui.premium.theme import FELT, FELT_DEEP, GOLD_DIM


@lru_cache(maxsize=8)
def _lighting_layer(width: int, height: int) -> QPixmap:
    """Cached natural-lighting overlay: warm centre, dark edges."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)

    # Warm table-light pool from above centre — the dealer's spotlight.
    light = QRadialGradient(width * 0.5, height * 0.24, max(width, height) * 0.9)
    light.setColorAt(0.0, QColor(255, 246, 214, 44))
    light.setColorAt(0.45, QColor(255, 246, 214, 13))
    light.setColorAt(1.0, QColor(255, 246, 214, 0))
    painter.fillRect(QRectF(0, 0, width, height), light)

    # Secondary cool pool near the tableau row keeps deep columns readable.
    cool = QRadialGradient(width * 0.5, height * 0.72, max(width, height) * 0.7)
    cool.setColorAt(0.0, QColor(140, 255, 214, 16))
    cool.setColorAt(0.55, QColor(140, 255, 214, 5))
    cool.setColorAt(1.0, QColor(140, 255, 214, 0))
    painter.fillRect(QRectF(0, 0, width, height), cool)

    # Dark vignette around the edges.
    vignette = QRadialGradient(width / 2, height / 2, max(width, height) * 0.72)
    vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
    vignette.setColorAt(0.66, QColor(0, 0, 0, 26))
    vignette.setColorAt(1.0, QColor(0, 0, 0, 96))
    painter.fillRect(QRectF(0, 0, width, height), vignette)
    painter.end()
    return pixmap


@lru_cache(maxsize=8)
def _edge_illumination_layer(width: int, height: int) -> QPixmap:
    """Cached inner rim light: a soft catchlight hugging the brass frame."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    rect = QRectF(0, 0, width, height)
    path = QPainterPath()
    path.addRoundedRect(rect.adjusted(6, 6, -6, -6), 9, 9)
    painter.setClipPath(path)

    # Gentle mint-gold wash along the top edge (light falls from above).
    top_wash = QLinearGradient(0.0, rect.top(), 0.0, rect.top() + 90.0)
    top_wash.setColorAt(0.0, QColor(190, 255, 214, 26))
    top_wash.setColorAt(1.0, QColor(190, 255, 214, 0))
    painter.fillRect(rect.adjusted(0, 4, 0, 0), top_wash)

    # Faint warm return along the bottom edge (felt bounce light).
    bottom_wash = QLinearGradient(0.0, rect.bottom(), 0.0, rect.bottom() - 60.0)
    bottom_wash.setColorAt(0.0, QColor(255, 236, 170, 18))
    bottom_wash.setColorAt(1.0, QColor(255, 236, 170, 0))
    painter.fillRect(rect, bottom_wash)
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

        # Cached lighting + vignette layer, then the edge illumination.
        key_w, key_h = int(rect.width()), int(rect.height())
        painter.drawPixmap(0, 0, _lighting_layer(key_w, key_h))
        painter.drawPixmap(0, 0, _edge_illumination_layer(key_w, key_h))

        # --- multi-layer gold/brass frame with inner bevel -------------------
        painter.setClipping(False)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Outer hairline (deep bronze).
        painter.setPen(QPen(QColor(96, 72, 20, 230), 1.4))
        painter.drawPath(_rounded(rect.adjusted(1.5, 1.5, -1.5, -1.5), 11))

        # Brass band with a vertical metallic sheen.
        band = _rounded(rect.adjusted(3, 3, -3, -3), 10)
        band_gradient = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.bottom()))
        band_gradient.setColorAt(0.0, QColor("#8C6D1D"))
        band_gradient.setColorAt(0.22, QColor("#E7C55C"))
        band_gradient.setColorAt(0.5, QColor("#A98420"))
        band_gradient.setColorAt(0.78, QColor("#E2BC50"))
        band_gradient.setColorAt(1.0, QColor("#7A5D14"))
        painter.setPen(QPen(band_gradient, 3.4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(band)

        # Bevel: light top-left edge and dark bottom-right edge just inside
        # the brass band, giving the tabletop physical depth.
        bevel_rect = rect.adjusted(6, 6, -6, -6)
        painter.setPen(QPen(QColor(255, 244, 200, 70), 1.2))
        painter.drawPath(_rounded(bevel_rect.adjusted(0.6, 0.6, -0.6, -0.6), 9))
        painter.setPen(QPen(QColor(0, 0, 0, 110), 1.6))
        painter.drawPath(_rounded(bevel_rect, 9))

        # Inner gold filigree hairline.
        painter.setPen(QPen(QColor(212, 175, 55, 150), 1.0))
        painter.drawPath(_rounded(rect.adjusted(11, 11, -11, -11), 8))

        # Soft inner shadow where the felt meets the frame.
        inner_glow = QRadialGradient(
            rect.center().x(), rect.center().y(), max(rect.width(), rect.height()) * 0.62
        )
        inner_glow.setColorAt(0.0, QColor(0, 0, 0, 0))
        inner_glow.setColorAt(0.82, QColor(0, 0, 0, 0))
        inner_glow.setColorAt(1.0, QColor(0, 0, 0, 70))
        painter.setClipping(True)
        painter.setClipPath(_rounded(rect.adjusted(6, 6, -6, -6), 9))
        painter.fillRect(rect, inner_glow)
        painter.restore()


def _rounded(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path
