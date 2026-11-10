"""Bundled resource loading for the premium UI.

All artwork ships inside the package (SVG + PNG). Nothing is fetched from
the network at runtime. Renderers and pixmaps are cached process-wide so
painting stays cheap.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPixmap, QRadialGradient
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

RESOURCES_DIR = Path(__file__).resolve().parent
ART_DIR = RESOURCES_DIR / "art"
TEXTURE_DIR = RESOURCES_DIR / "textures"
AUDIO_DIR = RESOURCES_DIR / "audio"

_SUIT_FILES = {
    "hearts": "suit-hearts.svg",
    "diamonds": "suit-diamonds.svg",
    "clubs": "suit-clubs.svg",
    "spades": "suit-spades.svg",
}
_COURT_FILES = {
    ("jack", "hearts"): "court-jack-hearts.svg",
    ("jack", "diamonds"): "court-jack-diamonds.svg",
    ("jack", "clubs"): "court-jack-clubs.svg",
    ("jack", "spades"): "court-jack-spades.svg",
    ("queen", "hearts"): "court-queen-hearts.svg",
    ("queen", "diamonds"): "court-queen-diamonds.svg",
    ("queen", "clubs"): "court-queen-clubs.svg",
    ("queen", "spades"): "court-queen-spades.svg",
    ("king", "hearts"): "court-king-hearts.svg",
    ("king", "diamonds"): "court-king-diamonds.svg",
    ("king", "clubs"): "court-king-clubs.svg",
    ("king", "spades"): "court-king-spades.svg",
}


def get_art_path(name: str) -> Path:
    """Return the absolute path of a bundled art asset."""
    candidate = ART_DIR / name
    if not candidate.exists():
        raise FileNotFoundError(f"bundled art asset is missing: {name}")
    return candidate


def get_texture_path(name: str) -> Path:
    candidate = TEXTURE_DIR / name
    if not candidate.exists():
        raise FileNotFoundError(f"bundled texture asset is missing: {name}")
    return candidate


def get_audio_path(name: str) -> Path:
    candidate = AUDIO_DIR / name
    if not candidate.exists():
        raise FileNotFoundError(f"bundled audio asset is missing: {name}")
    return candidate


def suit_renderer(suit: str) -> QSvgRenderer:
    key = _SUIT_FILES.get(suit.lower())
    if key is None:
        raise ValueError(f"unknown suit: {suit}")
    return _cached_renderer(key)


def court_renderer(rank: str, suit: str) -> QSvgRenderer:
    key = _COURT_FILES.get((rank.lower(), suit.lower()))
    if key is None:
        raise ValueError(f"unknown court card: {rank} of {suit}")
    return _cached_renderer(key)


def back_renderer() -> QSvgRenderer:
    return _cached_renderer("card-back.svg")


# Renderers live for the whole process: a plain module-level dict keeps
# strong references forever (unlike lru_cache, which participates in cyclic
# GC timing), and they are parented to the QApplication when one exists so
# Qt owns their lifetime too.
_RENDERERS: dict[str, QSvgRenderer] = {}


def _cached_renderer(file_name: str) -> QSvgRenderer:
    renderer = _RENDERERS.get(file_name)
    if renderer is not None:
        return renderer
    renderer = QSvgRenderer(str(get_art_path(file_name)))
    if not renderer.isValid():
        raise ValueError(f"invalid SVG asset: {file_name}")
    application = QApplication.instance()
    if application is not None:
        renderer.setParent(application)
    _RENDERERS[file_name] = renderer
    return renderer


@lru_cache(maxsize=1)
def felt_tile() -> QPixmap:
    """The bundled woven felt texture as a tiled pixmap."""
    return QPixmap(str(get_texture_path("felt-weave.png")))


@lru_cache(maxsize=4)
def vignette_pixmap(width: int, height: int) -> QPixmap:
    """Cached edge-darkening overlay used to light the casino table."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    gradient = QRadialGradient(width / 2, height / 2, max(width, height) * 0.75)
    gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
    gradient.setColorAt(0.62, QColor(0, 0, 0, 26))
    gradient.setColorAt(0.85, QColor(0, 0, 0, 74))
    gradient.setColorAt(1.0, QColor(0, 0, 0, 120))
    painter.fillRect(QRectF(0, 0, width, height), gradient)
    painter.end()
    return pixmap


def rounded_pixmap(width: int, height: int, radius: int, source: QPainter.Path | None = None,
                   fill: QColor | None = None) -> QPixmap:
    """Utility: rounded transparent pixmap, used by effects."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0.0, 0.0, float(width), float(height), radius, radius)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(fill or QColor(255, 255, 255, 255))
    painter.drawPath(path)
    painter.end()
    return pixmap
