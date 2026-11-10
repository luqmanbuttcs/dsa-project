"""Central design tokens for the premium casino UI.

Single source of truth for the palette, typography, card metrics and the
application-wide stylesheet. The palette follows the approved visual
reference: deep navy chrome, emerald casino felt, warm ivory cards and
refined gold accents.
"""

from __future__ import annotations

# --- Palette ---------------------------------------------------------------
NAVY_DEEP = "#081220"
NAVY = "#0E1B2E"
NAVY_LIGHT = "#152842"
NAVY_BORDER = "#24395A"
NAVY_CHIP = "#13253D"

GOLD = "#D4AF37"
GOLD_BRIGHT = "#F0C75E"
GOLD_DIM = "#8C7326"
GOLD_DEEP = "#8C6D1D"
GOLD_TEXT = "#E8C766"

IVORY = "#FBF6E9"
IVORY_SHADE = "#EDE3C8"
CARD_BORDER = "#C4B58E"

FELT_DEEP = "#08341A"
FELT = "#0E5226"
FELT_LIGHT = "#16622F"

RED_SUIT = "#C62828"
BLACK_SUIT = "#1B1E26"

OK_GREEN = "#37B96E"
OK_GREEN_DEEP = "#0F3D22"
WARN_RED = "#E05555"
WARN_RED_DEEP = "#3D1414"

# Electric mint / controlled cyan — the arcade half of the identity. Same
# values the card graphics use for selection glow (SELECT_MINT), so the 2D
# board and the widget chrome share one accent system.
MINT = "#40E0B2"
CYAN = "#56C8EA"
EMERALD_SOFT = "#7FB5A3"

TEXT_PRIMARY = "#F2EEE2"
TEXT_MUTED = "#9FB0C6"
TEXT_GOLD = "#E8C766"

# --- Typography ------------------------------------------------------------
FONT_DISPLAY = "Georgia, 'DejaVu Serif', serif"
FONT_UI = "'DejaVu Sans', 'Segoe UI', Arial, sans-serif"

# --- Metrics ---------------------------------------------------------------
CARD_W = 116
CARD_H = 160
CARD_RADIUS = 10

HEADER_HEIGHT = 84
# 410 / 1600 design width = 25.6% — inside the approved 25–27% dashboard band.
DASHBOARD_WIDTH = 410
SPACING = 8
MIN_WINDOW_W = 1280
MIN_WINDOW_H = 800
DESIGN_W = 1600
DESIGN_H = 900

TABLEAU_GAP = 24
FAN_FACE_DOWN = 14
FAN_FACE_UP = 30
WASTE_FAN = 22

ANIMATION_MS = {
    "move": 220,
    "multi_move": 260,
    "flip": 200,
    "stock_draw": 210,
    "foundation": 240,
    "trail": 300,
    "invalid": 150,
    "victory": 1200,
}


def qss() -> str:
    """Application-wide premium stylesheet."""
    return f"""
QMainWindow, QWidget#appShell {{ background: {NAVY_DEEP}; }}

QWidget#headerBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1A314F, stop:0.5 {NAVY}, stop:1 #0A1626);
    border-bottom: 2px solid {GOLD_DIM};
}}

QLabel#headerRule {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(212,175,55,0), stop:0.5 rgba(212,175,55,0.85),
                stop:1 rgba(212,175,55,0));
    border: none;
}}

QLabel#appTitle {{
    font-family: {FONT_DISPLAY};
    font-size: 25px;
    font-weight: bold;
    color: {TEXT_GOLD};
    background: transparent;
}}

QWidget#headerBar[compact="true"] QLabel#appTitle {{
    font-size: 19px;
}}

QLabel#appBadge {{
    font-size: 12px;
    font-weight: bold;
    color: {GOLD_BRIGHT};
    border: 1.6px solid {GOLD_DIM};
    border-radius: 11px;
    padding: 3px 12px;
    background: rgba(212, 175, 55, 0.10);
}}

QWidget#headerBar[compact="true"] QLabel#appBadge {{
    font-size: 11px;
    padding: 2px 8px;
}}

QFrame#metricChip {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1B3050, stop:1 {NAVY_CHIP});
    border: 1px solid {NAVY_BORDER};
    border-radius: 12px;
}}

QLabel#metricValue {{
    color: #F2EEE2;
    font-size: 17px;
    font-weight: bold;
    background: transparent;
}}

QLabel#metricLabel {{
    color: #9FB0C6;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
    background: transparent;
}}

QFrame#metricChip QLabel#metricLabel {{
    color: {TEXT_MUTED};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
    background: transparent;
}}

QFrame#metricChip QLabel#metricValue {{
    color: {TEXT_PRIMARY};
    font-size: 19px;
    font-weight: bold;
    background: transparent;
}}

QWidget#headerBar[compact="true"] QFrame#metricChip QLabel#metricValue {{
    font-size: 15px;
}}

QWidget#headerBar[compact="true"] QFrame#metricChip QLabel#metricLabel {{
    font-size: 9px;
    letter-spacing: 1px;
}}

QWidget#headerBar[compact="true"] QPushButton#goldButton,
QWidget#headerBar[compact="true"] QPushButton#darkButton {{
    font-size: 12px;
    padding: 6px 12px;
}}

QPushButton#goldButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {GOLD_BRIGHT}, stop:1 {GOLD});
    color: #241A02;
    font-weight: bold;
    font-size: 14px;
    border: 1px solid {GOLD_DIM};
    border-radius: 18px;
    padding: 8px 20px;
}}
QPushButton#goldButton:hover {{ background: {GOLD_BRIGHT}; }}
QPushButton#goldButton:pressed {{ background: {GOLD_DIM}; }}
QPushButton#goldButton:disabled {{ background: #6E6033; color: #3A3416; }}

/* Container chrome set via objectName (never widget-level stylesheets, which
   would cascade onto styled children and wash out the gold buttons). */
QWidget#labTopBar {{
    background: {NAVY};
    border-bottom: 2px solid {GOLD_DIM};
}}
QWidget#labTabRow {{
    background: {NAVY_DEEP};
}}
QWidget#dashboardContent {{
    background: {NAVY_DEEP};
    border-left: 1px solid {NAVY_BORDER};
}}

QLabel#countBadge {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {GOLD_BRIGHT}, stop:1 {GOLD});
    color: #241A02;
    font-size: 12px;
    font-weight: bold;
    border: 1px solid {GOLD_DEEP};
    border-radius: 11px;
}}

QPushButton#structureRow {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    text-align: left;
}}
QPushButton#structureRow:hover {{
    background: rgba(212, 175, 55, 0.08);
    border: 1px solid rgba(212, 175, 55, 0.35);
}}
QPushButton#structureRow:pressed {{
    background: rgba(212, 175, 55, 0.16);
}}

QLabel#structureIconChip {{
    background: rgba(212, 175, 55, 0.10);
    border: 1px solid rgba(212, 175, 55, 0.35);
    border-radius: 9px;
}}

QPushButton#darkButton {{
    background: {NAVY_CHIP};
    color: {TEXT_PRIMARY};
    font-weight: bold;
    font-size: 14px;
    border: 1px solid {NAVY_BORDER};
    border-radius: 18px;
    padding: 8px 18px;
}}
QPushButton#darkButton:hover {{ background: {NAVY_LIGHT}; border-color: {GOLD_DIM}; }}
QPushButton#darkButton:pressed {{ background: {NAVY_BORDER}; }}
QPushButton#darkButton:disabled {{ color: {TEXT_MUTED}; background: {NAVY}; }}

QFrame#boardFrame {{
    border: 2.4px solid {GOLD_DIM};
    border-radius: 14px;
    background: {FELT_DEEP};
}}

QFrame#panelCard {{
    background: {NAVY};
    border: 1px solid {NAVY_BORDER};
    border-radius: 12px;
}}

QLabel#panelTitle {{
    color: {GOLD_TEXT};
    font-size: 14px;
    font-weight: bold;
    background: transparent;
}}

QWidget#dashboardFooter {{
    background: {NAVY_DEEP};
    border-top: 1px solid {NAVY_BORDER};
}}

QLabel#panelBody {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    background: transparent;
}}

QLabel#mutedText {{ color: {TEXT_MUTED}; font-size: 12px; background: transparent; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

QScrollBar:vertical {{
    background: {NAVY_DEEP}; width: 10px; border-radius: 5px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {NAVY_BORDER}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {GOLD_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {NAVY_DEEP}; height: 10px; border-radius: 5px; margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {NAVY_BORDER}; border-radius: 5px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {GOLD_DIM}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QListWidget#moveLog, QListWidget#historyList {{
    background: {NAVY};
    border: none;
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QListWidget::item {{ padding: 3px 6px; }}
QListWidget::item:selected {{ background: {NAVY_LIGHT}; }}

QTableWidget {{
    background: {NAVY};
    alternate-background-color: {NAVY_LIGHT};
    color: {TEXT_PRIMARY};
    gridline-color: {NAVY_BORDER};
    border: 1px solid {NAVY_BORDER};
    border-radius: 8px;
    font-size: 12px;
}}
QHeaderView::section {{
    background: {NAVY_CHIP};
    color: {GOLD_TEXT};
    font-weight: bold;
    border: none;
    border-bottom: 1px solid {GOLD_DIM};
    padding: 6px 8px;
}}

QLineEdit, QComboBox, QSpinBox {{
    background: {NAVY_CHIP};
    color: {TEXT_PRIMARY};
    border: 1px solid {NAVY_BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {NAVY_LIGHT};
    color: {TEXT_PRIMARY};
    selection-background-color: {GOLD_DIM};
}}

/* DSA Lab navigation tabs — inactive tabs sit on dark navy with a
   restrained mint/cyan accent; the active tab carries the same premium
   gold gradient as the header's gold buttons so the two workspaces read
   as one application. */
QPushButton#labTab {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {NAVY_LIGHT}, stop:1 {NAVY_CHIP});
    color: {TEXT_MUTED};
    font-weight: bold;
    font-size: 13px;
    border: 1px solid {NAVY_BORDER};
    border-radius: 10px;
    padding: 7px 16px;
}}
QPushButton#labTab:hover {{
    color: {CYAN};
    border: 1px solid rgba(64, 224, 178, 0.45);
}}
QPushButton#labTab:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {GOLD_BRIGHT}, stop:1 {GOLD});
    color: #241A02;
    border: 1.4px solid {GOLD_BRIGHT};
}}
QPushButton#labTab:checked:hover {{ color: #241A02; }}

/* Shared filter-row labels (DSA Lab tables, Game Mode). */
QLabel#filterLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
    font-weight: bold;
    background: transparent;
}}

/* Inline key/value stat text used across the DSA Lab. */
QLabel#statChip {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    background: transparent;
}}

QLabel#sectionTitle {{
    color: {GOLD_TEXT};
    font-size: 15px;
    font-weight: bold;
    background: transparent;
}}

/* The pinned sidebar footer button: same gold language, slightly larger
   so the Open DSA Lab action reads as the sidebar's primary affordance. */
QPushButton#openLabButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {GOLD_BRIGHT}, stop:1 {GOLD});
    color: #241A02;
    font-weight: bold;
    font-size: 14px;
    border: 1px solid {GOLD_DEEP};
    border-radius: 19px;
    padding: 9px 20px;
}}
QPushButton#openLabButton:hover {{ background: {GOLD_BRIGHT}; }}
QPushButton#openLabButton:pressed {{ background: {GOLD_DIM}; }}

QProgressBar#gameProgress {{
    background: {NAVY_CHIP};
    border: 1px solid {NAVY_BORDER};
    border-radius: 9px;
    height: 18px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-weight: bold;
}}
QProgressBar#gameProgress::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {GOLD_BRIGHT}, stop:0.5 {GOLD}, stop:1 {GOLD_DIM});
    border-radius: 8px;
}}

QDialog {{ background: {NAVY}; }}
QLabel#dialogTitle {{
    font-family: {FONT_DISPLAY};
    font-size: 20px;
    font-weight: bold;
    color: {TEXT_GOLD};
}}
QRadioButton, QCheckBox {{ color: {TEXT_PRIMARY}; font-size: 13px; spacing: 8px; }}


/* Move log rows */
QListWidget#moveLog {{
    background: {NAVY_DEEP};
    border: 1px solid {NAVY_BORDER};
    border-radius: 8px;
    padding: 2px;
}}
QListWidget#moveLog::item {{
    border-bottom: 1px solid rgba(36, 57, 90, 0.6);
    padding: 3px 6px;
    color: {TEXT_PRIMARY};
}}
QListWidget#moveLog::item:selected {{ background: rgba(212, 175, 55, 0.12); }}
QLabel#moveLogRow {{ font-size: 12.5px; }}

QPushButton#modeCard {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #16294A, stop:1 #0F1E3C);
    border: 2px solid #24395A;
    border-radius: 14px;
    text-align: left;
}}
QPushButton#modeCard:hover {{ border-color: #8C7326; }}
QPushButton#modeCard:checked {{
    border: 2px solid #F0C75E;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1D3559, stop:1 #14274A);
}}
"""