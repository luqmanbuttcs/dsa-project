"""Emerald felt and premium blue card-back painting helpers."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QFrame

NAVY = "#071D32"
NAVY_RAISED = "#0B2B46"
PANEL = "#0B243A"
PANEL_BORDER = "#28516D"
EMERALD = "#006B35"
EMERALD_DARK = "#004B2A"
GOLD = "#FFD15C"
IVORY = "#FFFDF7"
TEXT = "#F7FAFF"
TEXT_MUTED = "#B9CAD9"
RED = "#D51E35"
INK = "#142332"


APP_STYLESHEET = f"""
QMainWindow, QWidget#central-widget {{ background: {NAVY}; color: {TEXT}; }}
QWidget {{ font-family: "Segoe UI", Arial, sans-serif; color: {TEXT}; }}
QToolTip {{ background: {PANEL}; color: {TEXT}; border: 1px solid {GOLD}; padding: 5px 8px; }}
QPushButton {{ background: #10334E; color: {TEXT}; border: 1px solid #2E5874;
    border-radius: 10px; padding: 8px 13px; font-weight: 700; }}
QPushButton:hover {{ background: #174767; border-color: #67B5E5; }}
QPushButton:focus {{ border: 2px solid {GOLD}; }}
QPushButton:disabled {{ color: #8498A8; border-color: #29465C; }}
QComboBox {{ background: #0B2B46; color: {TEXT}; border: 1px solid #2C5875;
    border-radius: 8px; padding: 7px 11px; min-width: 86px; }}
QComboBox QAbstractItemView {{ background: #0B2B46; color: {TEXT}; selection-background-color: #17669A; }}
QCheckBox {{ color: #DCEAF5; spacing: 8px; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border: 1px solid #5E819C; border-radius: 3px; background: #0B2B46; }}
QCheckBox::indicator:checked {{ background: #7BE36A; border-color: #B5FF9E; }}
QMenu {{ background: #09253C; color: #EDF6FF; border: 1px solid #315D79; padding: 5px; }}
QMenu::item {{ padding: 7px 22px; border-radius: 5px; }}
QMenu::item:selected {{ background: #14527A; }}
QListWidget {{ background: #071F33; color: #EAF4FC; border: 1px solid #28516D; border-radius: 9px; padding: 6px; }}
QListWidget::item {{ padding: 4px 5px; }}
QDockWidget {{ color: {TEXT}; background: #081E32; }}
QDockWidget::title {{ background: #06182A; color: {TEXT}; padding: 10px 12px; text-align: left; border-bottom: 1px solid #28516D; font-weight: 800; }}
QTabWidget::pane {{ border: 1px solid #28516D; border-radius: 9px; background: #081F34; top: -1px; }}
QTabBar::tab {{ background: #0A2942; color: #AFC4D7; padding: 9px 12px; border: 1px solid #244B67; }}
QTabBar::tab:selected {{ background: #075AA0; color: white; border-color: #2D9CF1; font-weight: 800; }}
QTabBar::tab:hover {{ background: #124366; color: white; }}
QTableWidget {{ background: #081F34; color: #EAF4FC; gridline-color: #234761; border: 1px solid #254D69; selection-background-color: #174B70; }}
QTableWidget::item {{ padding: 6px 7px; }}
QHeaderView::section {{ background: #0B2B46; color: #BFD1DF; border: none; border-bottom: 1px solid #315D79; padding: 7px 5px; font-weight: 800; }}
QTextEdit, QPlainTextEdit {{ background: #071F33; color: #EAF4FC; border: 1px solid #28516D; border-radius: 8px; padding: 6px; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #315C78; border-radius: 4px; min-height: 26px; }}
QScrollBar::handle:vertical:hover {{ background: #4D83A6; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #315C78; border-radius: 4px; min-width: 26px; }}
"""


def paint_card_back(
    painter: QPainter,
    rect: QRectF,
    *,
    selected: bool = False,
    radius: float = 8.0,
) -> None:
    """Paint a symmetrical, ornamental royal-blue card back."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    bounds = QRectF(rect).adjusted(1.5, 1.5, -1.5, -1.5)
    clip = QPainterPath()
    clip.addRoundedRect(bounds, radius, radius)
    painter.setClipPath(clip)

    gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
    gradient.setColorAt(0.0, QColor("#1679C5"))
    gradient.setColorAt(0.45, QColor("#07539A"))
    gradient.setColorAt(1.0, QColor("#032C59"))
    painter.fillPath(clip, gradient)

    # Fine woven lines create depth without a raster asset.
    painter.save()
    painter.setClipPath(clip)
    painter.setPen(QPen(QColor(215, 239, 255, 18), 0.7))
    for offset in range(-int(bounds.height()), int(bounds.width()), 9):
        painter.drawLine(
            QPointF(bounds.left() + offset, bounds.top()),
            QPointF(bounds.left() + offset + bounds.height(), bounds.bottom()),
        )
        painter.drawLine(
            QPointF(bounds.left() + offset, bounds.bottom()),
            QPointF(bounds.left() + offset + bounds.height(), bounds.top()),
        )
    painter.restore()

    inset = bounds.adjusted(5, 5, -5, -5)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor("#E2F2FF"), 1.15))
    painter.drawRoundedRect(inset, radius - 2, radius - 2)
    inset2 = inset.adjusted(4, 4, -4, -4)
    painter.setPen(QPen(QColor("#86BDEB"), 0.8))
    painter.drawRoundedRect(inset2, radius - 3, radius - 3)

    cx, cy = bounds.center().x(), bounds.center().y()
    w, h = bounds.width(), bounds.height()
    # Mirrored filigree medallions and corner diamonds.
    painter.setPen(QPen(QColor("#A9D3F5"), 0.9))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for x in (bounds.left() + 18, bounds.right() - 18):
        for y in (bounds.top() + 18, bounds.bottom() - 18):
            painter.drawEllipse(QPointF(x, y), 7, 7)
            painter.drawEllipse(QPointF(x, y), 3, 3)
    for y in (bounds.top() + 34, bounds.bottom() - 34):
        painter.drawArc(QRectF(cx - 22, y - 11, 44, 22), 0, 180 * 16)
        painter.drawArc(QRectF(cx - 22, y - 11, 44, 22), 180 * 16, 180 * 16)

    # Interlaced central medallion.
    medallion = QRectF(cx - min(w, h) * 0.27, cy - min(w, h) * 0.27,
                       min(w, h) * 0.54, min(w, h) * 0.54)
    painter.setPen(QPen(QColor("#D7ECFF"), 1.2))
    painter.drawEllipse(medallion)
    painter.setPen(QPen(QColor("#86BDEB"), 0.8))
    painter.drawEllipse(medallion.adjusted(5, 5, -5, -5))
    diamond = QPolygonF([
        QPointF(cx, medallion.top() + 5),
        QPointF(medallion.right() - 5, cy),
        QPointF(cx, medallion.bottom() - 5),
        QPointF(medallion.left() + 5, cy),
    ])
    painter.drawPolygon(diamond)
    painter.setPen(QPen(QColor("#F5FBFF"), 1.0))
    font = QFont("Segoe UI Symbol", max(18, int(min(w, h) * 0.24)), QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(cx - 25, cy - 28, 50, 56), Qt.AlignmentFlag.AlignCenter, "♠")

    if selected:
        painter.setPen(QPen(QColor("#FFD65A"), 3.0))
        painter.drawRoundedRect(bounds.adjusted(1, 1, -1, -1), radius, radius)
    painter.restore()


class FeltBoard(QFrame):
    """Paints a textured emerald felt table with restrained suit watermarking."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(bounds, 16, 16)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#087E48"))
        gradient.setColorAt(0.32, QColor("#00713B"))
        gradient.setColorAt(0.72, QColor("#006333"))
        gradient.setColorAt(1.0, QColor("#004827"))
        painter.fillPath(path, gradient)
        painter.save()
        painter.setClipPath(path)

        # Fine diagonal felt weave.
        painter.setPen(QPen(QColor(235, 255, 238, 13), 0.65))
        for y in range(-self.width(), self.height() + self.width(), 10):
            painter.drawLine(0, y, self.width(), y + self.width() // 3)
        painter.setPen(QPen(QColor(0, 34, 19, 16), 0.6))
        for y in range(-self.width(), self.height() + self.width(), 14):
            painter.drawLine(0, y, self.width(), y - self.width() // 4)

        # Low-opacity suit emblems add the fabric pattern visible in the reference.
        painter.setPen(QColor(220, 255, 225, 12))
        painter.setFont(QFont("Segoe UI Symbol", 92, QFont.Weight.Bold))
        painter.drawText(QRectF(8, self.height() - 118, 150, 110),
                         Qt.AlignmentFlag.AlignCenter, "♠")
        painter.drawText(QRectF(self.width() - 150, self.height() - 115, 142, 108),
                         Qt.AlignmentFlag.AlignCenter, "♣")
        painter.setFont(QFont("Segoe UI Symbol", 44, QFont.Weight.Bold))
        painter.drawText(QRectF(self.width() * 0.52, self.height() * 0.66, 80, 70),
                         Qt.AlignmentFlag.AlignCenter, "♦")
        painter.restore()

        # Vignette and polished table edge.
        edge = QLinearGradient(0, 0, self.width(), self.height())
        edge.setColorAt(0.0, QColor(150, 255, 185, 16))
        edge.setColorAt(0.55, QColor(0, 0, 0, 0))
        edge.setColorAt(1.0, QColor(0, 24, 12, 44))
        painter.fillPath(path, edge)
        painter.setPen(QPen(QColor("#32A56A"), 1.25))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bounds, 16, 16)
        painter.end()
