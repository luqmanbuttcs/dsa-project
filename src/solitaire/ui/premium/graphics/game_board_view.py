"""QGraphicsView hosting the casino board with responsive scaling."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsView

from solitaire.ui.premium.graphics.game_board_scene import CONTENT_H, CONTENT_W


class GameBoardView(QGraphicsView):
    """Scales the logical board to the available viewport, no scrollbars."""

    def __init__(self, scene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        from PyQt6.QtGui import QPainter

        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setAcceptDrops(True)
        self.setSceneRect(0, 0, float(CONTENT_W), float(CONTENT_H))
        self.setStyleSheet("background: transparent; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def fit_to_viewport(self) -> None:
        viewport_size = self.viewport().size()
        available_w = max(1, viewport_size.width() - 8)
        available_h = max(1, viewport_size.height() - 8)
        scale = min(available_w / float(CONTENT_W), available_h / float(CONTENT_H))
        scale = max(0.45, min(scale, 1.18))
        self.resetTransform()
        self.scale(scale, scale)
        self.centerOn(float(CONTENT_W) / 2.0, float(CONTENT_H) / 2.0)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.fit_to_viewport()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.fit_to_viewport()
