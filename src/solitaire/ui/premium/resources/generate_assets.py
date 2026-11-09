"""Generate the bundled premium card artwork as local SVG assets plus a
cached felt texture PNG.

Everything is deterministic and requires no network access. Re-run with:

    python -m solitaire.ui.premium.resources.generate_assets

Artwork style: premium casino deck — warm ivory faces with layered borders,
royal-blue baroque card backs with a central spade crest, suit palettes with
soft gradients and highlights, and twelve individualised court illustrations
(one per rank × suit combination).
"""

from __future__ import annotations

import random
from pathlib import Path

from PyQt6.QtGui import QColor, QImage, QPainter, QPen

RES_DIR = Path(__file__).resolve().parent
ART_DIR = RES_DIR / "art"
TEXTURE_DIR = RES_DIR / "textures"

RED_LIGHT = "#D24A4A"
RED_DEEP = "#8E1B1B"
INK_LIGHT = "#3D4350"
INK_DEEP = "#14161C"
GOLD = "#C9A227"
GOLD_LIGHT = "#E7C55C"
GOLD_DEEP = "#8C6D1D"

SUITS = ("hearts", "diamonds", "clubs", "spades")
RED_SUITS = ("hearts", "diamonds")
COURTS = ("jack", "queen", "king")

SUIT_GLYPHS = {
    "hearts": "♥",
    "diamonds": "♦",
    "clubs": "♣",
    "spades": "♠",
}

# Per-suit court palette: (robe light, robe deep, accent, metal)
SUIT_COURT_STYLE = {
    "hearts": ("#8E2432", "#4A0F16", "#E0505E", GOLD),
    "diamonds": ("#B45418", "#5C2408", "#E8823A", GOLD_LIGHT),
    "clubs": ("#2E5E33", "#12301A", "#5FA46A", "#A8902F"),
    "spades": ("#2C3E66", "#121A30", "#5E7FB8", "#C0C7D4"),
}


def suit_gradient(suit: str, stop_a: str, stop_b: str, grad_id: str) -> str:
    return (
        f'<linearGradient id="{grad_id}" x1="0" y1="0" x2="0.9" y2="1">'
        f'<stop offset="0" stop-color="{stop_a}"/>'
        f'<stop offset="1" stop-color="{stop_b}"/>'
        f"</linearGradient>"
    )


def suit_body(suit: str, fill: str) -> str:
    """Return the classic suit silhouette centred in a 100x100 viewbox."""
    if suit == "hearts":
        return (
            '<path d="M50 90 C22 68 8 50 8 32 C8 16 19 7 32 7 '
            "C41 7 48 12 50 20 C52 12 59 7 68 7 C81 7 92 16 92 32 "
            'C92 50 78 68 50 90 Z" fill="{fill}"/>'
        ).format(fill=fill)
    if suit == "diamonds":
        return (
            '<path d="M50 4 C57 21 70 37 88 50 C70 63 57 79 50 96 '
            "C43 79 30 63 12 50 C30 37 43 21 50 4 Z\" "
            'fill="{fill}"/>'
        ).format(fill=fill)
    if suit == "clubs":
        return (
            '<circle cx="50" cy="27" r="17" fill="{f}"/>'
            '<circle cx="29" cy="53" r="17" fill="{f}"/>'
            '<circle cx="71" cy="53" r="17" fill="{f}"/>'
            '<path d="M46 52 C48 68 44 80 36 90 L64 90 C56 80 52 68 54 52 Z" fill="{f}"/>'
        ).format(f=fill)
    return (
        '<path d="M50 5 C62 24 84 39 84 58 C84 70 75 79 64 79 '
        "C58 79 52 76 50 71 C48 76 42 79 36 79 C25 79 16 70 16 58 "
        'C16 39 38 24 50 5 Z" fill="{f}"/>'
        '<path d="M46 72 C48 82 44 90 37 96 L63 96 C56 90 52 82 54 72 Z" fill="{f}"/>'
    ).format(f=fill)


def make_suit_svg(suit: str) -> str:
    """Detailed suit illustration: gradient body, inner shading, gloss."""
    light, dark = (RED_LIGHT, RED_DEEP) if suit in RED_SUITS else (INK_LIGHT, INK_DEEP)
    body = suit_body(suit, "url(#suitFill)")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    {suit_gradient(suit, light, dark, "suitFill")}
    <radialGradient id="gloss" cx="0.35" cy="0.28" r="0.75">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.42"/>
      <stop offset="0.55" stop-color="#FFFFFF" stop-opacity="0.10"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
  </defs>
  {body}
  {body.replace('fill="url(#suitFill)"', 'fill="none" stroke="#000000" stroke-opacity="0.35" stroke-width="2.4"')}
  <g clip-path="none" opacity="0.9">
    <ellipse cx="37" cy="27" rx="15" ry="8" fill="#FFFFFF" opacity="0.20" transform="rotate(-24 37 27)"/>
  </g>
  <rect x="0" y="0" width="100" height="100" fill="url(#gloss)"/>
</svg>
"""


# ---------------------------------------------------------------------------
# Court cards: twelve individualised baroque illustrations (see court_art)
# ---------------------------------------------------------------------------
from solitaire.ui.premium.resources.court_art import make_court_svg  # noqa: E402


# ---------------------------------------------------------------------------
# Card back: royal-blue baroque ornament with central spade crest
# ---------------------------------------------------------------------------


def make_back_svg() -> str:
    lattice = []
    for i in range(-8, 17):
        offset = i * 14
        lattice.append(
            f'<line x1="{offset}" y1="-10" x2="{offset + 180}" y2="170" '
            'stroke="#3D5FA3" stroke-width="1" opacity="0.5"/>'
        )
        lattice.append(
            f'<line x1="{offset + 180}" y1="-10" x2="{offset}" y2="170" '
            'stroke="#3D5FA3" stroke-width="1" opacity="0.5"/>'
        )
    # Diamond dots on the lattice crossings
    dots = []
    for gy in range(4):
        for gx in range(4):
            x, y = 26 + gx * 22, 30 + gy * 26
            dots.append(
                f'<path d="M{x} {y - 2.4} L{x + 2.4} {y} L{x} {y + 2.4} L{x - 2.4} {y} Z" '
                'fill="#8FA9DA" opacity="0.5"/>'
            )

    corners = ""
    for cx, cy, rot in ((16, 16, 0), (100, 16, 90), (100, 144, 180), (16, 144, 270)):
        corners += f"""<g transform="translate({cx} {cy}) rotate({rot})">
          <path d="M0 10 C0 3 3 0 10 0 C7 3 4 6 3 12 Z" fill="{GOLD_LIGHT}" opacity="0.95"/>
          <path d="M2 15 C5 8 9 4 16 2 C10 7 7 12 6 18 Z" fill="#E8DFC8" opacity="0.8"/>
          <circle cx="2.5" cy="2.5" r="1.8" fill="{GOLD}"/>
        </g>"""

    petals = ""
    for index in range(12):
        angle = index * 30
        petals += (
            f'<g transform="rotate({angle} 58 80)">'
            '<ellipse cx="58" cy="58" rx="4.6" ry="10" fill="#24488A" '
            'stroke="#C9BC97" stroke-width="0.9" opacity="0.95"/></g>'
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 116 160">
  <defs>
    <linearGradient id="backBase" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#28509B"/>
      <stop offset="0.5" stop-color="#1A3568"/>
      <stop offset="1" stop-color="#102040"/>
    </linearGradient>
    <radialGradient id="backSheen" cx="0.32" cy="0.2" r="1.05">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.16"/>
      <stop offset="0.45" stop-color="#FFFFFF" stop-opacity="0.04"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.22"/>
    </radialGradient>
    <clipPath id="innerClip">
      <rect x="8" y="8" width="100" height="144" rx="7"/>
    </clipPath>
  </defs>

  <rect x="1" y="1" width="114" height="158" rx="10" fill="url(#backBase)"
        stroke="#0C1B38" stroke-width="2"/>
  <rect x="4" y="4" width="108" height="152" rx="8" fill="none"
        stroke="{GOLD_LIGHT}" stroke-width="1.5"/>
  <rect x="6.5" y="6.5" width="103" height="147" rx="7.5" fill="none"
        stroke="#8C6D1D" stroke-width="0.9" opacity="0.9"/>
  <g clip-path="url(#innerClip)">
    <rect x="8" y="8" width="100" height="144" fill="#16294F"/>
    <g>{''.join(lattice)}</g>
    <g>{''.join(dots)}</g>

    {corners}

    <!-- central medallion -->
    <circle cx="58" cy="80" r="33" fill="#E9E2CC" opacity="0.97"/>
    <circle cx="58" cy="80" r="33" fill="none" stroke="{GOLD}" stroke-width="2.2"/>
    <circle cx="58" cy="80" r="28.5" fill="none" stroke="#1A3568" stroke-width="1.2"/>
    <circle cx="58" cy="80" r="26" fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="0.8"/>
    <g>{petals}</g>
    <circle cx="58" cy="80" r="19" fill="#1A3568"/>
    <circle cx="58" cy="80" r="19" fill="none" stroke="{GOLD_LIGHT}" stroke-width="1.4"/>
    <g transform="translate(38.6 61) scale(0.39)">
      {suit_body("spades", "#E9E2CC")}
    </g>
  </g>
  <rect x="1" y="1" width="114" height="158" rx="10" fill="url(#backSheen)"/>
</svg>
"""


# ---------------------------------------------------------------------------
# Felt texture
# ---------------------------------------------------------------------------


def make_felt_tile(path: Path, size: int = 512, seed: int = 200) -> None:
    """Render a tileable woven casino felt with diamond quilting and faint
    suit watermarks, echoing the approved poker-table reference."""
    rng = random.Random(seed)
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor("#0F5C2B"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # Weave: alternating horizontal / vertical bands.
    band = 4
    for y in range(0, size, band):
        light = (y // band) % 2 == 0
        painter.fillRect(0, y, size, band, QColor(255, 255, 255, 14 if light else 0))
        painter.fillRect(0, y, size, band, QColor(0, 0, 0, 13 if not light else 0))
    for x in range(0, size, band):
        painter.fillRect(x, 0, 1, size, QColor(0, 0, 0, 12))
        painter.fillRect(x, 0, 1, size, QColor(255, 255, 255, 7))

    # Fibre noise.
    for _ in range(size * 30):
        x = rng.randrange(size)
        y = rng.randrange(size)
        alpha = rng.randrange(6, 26)
        if rng.random() < 0.5:
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
        else:
            painter.setPen(QPen(QColor(0, 0, 0, alpha), 1))
        painter.drawPoint(x, y)

    # Short directional fibres for the brushed felt look.
    painter.setPen(QPen(QColor(255, 255, 255, 12), 1))
    for _ in range(1500):
        x = rng.randrange(size)
        y = rng.randrange(size)
        length = rng.randrange(4, 12)
        painter.drawLine(x, y, min(size - 1, x + length), y)

    # Diamond quilting with faint suit watermarks at the crossings
    # (matches the suit-printed lattice of the approved reference table).
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor(255, 255, 255, 17), 1))
    step = 96
    for start in range(-size, size * 2, step):
        painter.drawLine(start, 0, start + size, size)
        painter.drawLine(start + size, 0, start, size)

    glyphs = ("♥", "♦", "♣", "♠")
    painter.setPen(QPen(QColor(255, 255, 255, 24), 1))
    font = painter.font()
    font.setPixelSize(26)
    painter.setFont(font)
    index = 0
    for gy in range(0, size, step):
        for gx in range(0, size, step):
            glyph = glyphs[index % 4]
            index += 1
            painter.save()
            painter.translate(gx + step // 2, gy + step // 2)
            painter.rotate(45)
            painter.drawText(
                -painter.fontMetrics().horizontalAdvance(glyph) // 2,
                painter.fontMetrics().ascent() // 2 - 2,
                glyph,
            )
            painter.restore()

    painter.end()
    image.save(str(path), "PNG")


def main() -> None:
    import sys

    from PyQt6.QtGui import QGuiApplication

    # The felt tile renders text (suit watermarks) which needs a QGuiApplication.
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(["generate-assets"])
    app.setApplicationName("premium-asset-generator")

    ART_DIR.mkdir(parents=True, exist_ok=True)
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)

    for suit in SUITS:
        (ART_DIR / f"suit-{suit}.svg").write_text(make_suit_svg(suit), encoding="utf-8")
    for rank in COURTS:
        for suit in SUITS:
            (ART_DIR / f"court-{rank}-{suit}.svg").write_text(
                make_court_svg(rank, suit), encoding="utf-8"
            )
    (ART_DIR / "card-back.svg").write_text(make_back_svg(), encoding="utf-8")
    make_felt_tile(TEXTURE_DIR / "felt-weave.png")

    total = len(list(ART_DIR.glob("*.svg"))) + len(list(TEXTURE_DIR.glob("*.png")))
    print(f"generated {total} asset files under {RES_DIR}")


if __name__ == "__main__":
    main()
