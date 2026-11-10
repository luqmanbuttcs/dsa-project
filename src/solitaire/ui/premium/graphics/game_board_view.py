"""QGraphicsView hosting the casino board with responsive relayout.

The scene geometry is recomputed for the actual viewport on every resize, so
the emerald felt fills the whole game area edge to edge (no letterbox bands).
A mild uniform scale is applied only when the viewport is narrower than the
minimum full-size footprint, keeping every card readable and uncropped.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView

from solitaire.ui.premium.graphics.game_board_scene import MIN_CONTENT_W


class GameBoardView(QGraphicsView):
    """Fills the available viewport with the felt table; no scrollbars."""

    def __init__(self, scene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setAcceptDrops(True)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")

    def fit_to_viewport(self) -> None:
        viewport_size = self.viewport().size()
        available_w = max(1, viewport_size.width() - 8)
        available_h = max(1, viewport_size.height() - 8)

        # Scale only below the minimum full-size footprint; above it the
        # scene stretches 1:1 and the felt occupies the entire viewport.
        scale = min(1.0, available_w / float(MIN_CONTENT_W))
        scale = max(scale, 0.62)

        scene_w = available_w / scale
        scene_h = available_h / scale
        self.scene().relayout(scene_w, scene_h)

        self.resetTransform()
        self.scale(scale, scale)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.fit_to_viewport()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.fit_to_viewport()
