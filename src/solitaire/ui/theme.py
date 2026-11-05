"""Centralized premium emerald and navy Qt theme."""

from __future__ import annotations

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


from PyQt6.QtWidgets import QFrame


class FeltBoard(QFrame):
    """Emerald tabletop frame styled with native Qt stylesheets."""
