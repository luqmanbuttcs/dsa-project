"""Generate the bundled premium card artwork as local SVG assets plus a
cached felt texture PNG.

Everything is deterministic and requires no network access. Re-run with:

    python -m solitaire.ui.premium.resources.generate_assets

Artwork style: premium casino deck — warm ivory faces, royal blue ornate
card backs, red/black suit palette with soft gradients and highlights.
"""

from __future__ import annotations

import random
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPen

RES_DIR = Path(__file__).resolve().parent
ART_DIR = RES_DIR / "art"
TEXTURE_DIR = RES_DIR / "textures"

RED_LIGHT = "#D24343"
RED_DARK = "#8E1B1B"
INK_LIGHT = "#3A3F4B"
INK_DARK = "#14161C"
GOLD = "#C9A227"
GOLD_LIGHT = "#E7C55C"

SUITS = ("hearts", "diamonds", "clubs", "spades")
RED_SUITS = ("hearts", "diamonds")
COURTS = ("jack", "queen", "king")

SUIT_GLYPHS = {
    "hearts": "♥",
    "diamonds": "♦",
    "clubs": "♣",
    "spades": "♠",
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
    light, dark = (
        (RED_LIGHT, RED_DARK) if suit in RED_SUITS else (INK_LIGHT, INK_DARK)
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    {suit_gradient(suit, light, dark, "suitFill")}
  </defs>
  {suit_body(suit, "url(#suitFill)")}
  <ellipse cx="36" cy="26" rx="14" ry="8" fill="#FFFFFF" opacity="0.22"
           transform="rotate(-24 36 26)"/>
</svg>
"""


def crown(rank: str) -> str:
    """Crown artwork per court rank, centred near the top of the figure."""
    if rank == "king":
        return (
            '<path d="M62 52 L62 34 L74 46 L84 26 L94 46 L106 34 L106 52 Z" '
            f'fill="{GOLD}" stroke="#8C6D1D" stroke-width="2"/>'
            '<circle cx="84" cy="26" r="4" fill="#C0392B"/>'
            '<circle cx="62" cy="38" r="3" fill="#2E6DB4"/>'
            '<circle cx="106" cy="38" r="3" fill="#2E6DB4"/>'
            '<rect x="60" y="50" width="48" height="9" rx="3" '
            f'fill="{GOLD_LIGHT}" stroke="#8C6D1D" stroke-width="2"/>'
        )
    if rank == "queen":
        return (
            '<path d="M64 50 L60 30 L74 42 L84 24 L94 42 L108 30 L104 50 Z" '
            f'fill="{GOLD}" stroke="#8C6D1D" stroke-width="2"/>'
            '<circle cx="84" cy="22" r="4" fill="#2E86C1"/>'
            '<circle cx="62" cy="32" r="3" fill="#2E86C1"/>'
            '<circle cx="106" cy="32" r="3" fill="#2E86C1"/>'
            '<rect x="62" y="48" width="44" height="8" rx="3" '
            f'fill="{GOLD_LIGHT}" stroke="#8C6D1D" stroke-width="2"/>'
        )
    return (
        '<path d="M66 50 L64 36 L84 40 L104 36 L102 50 Z" '
        f'fill="{GOLD}" stroke="#8C6D1D" stroke-width="2"/>'
        '<path d="M104 38 C114 34 120 40 118 50 C112 46 108 44 102 44 Z" '
        f'fill="{GOLD_LIGHT}" stroke="#8C6D1D" stroke-width="1.6"/>'
        '<circle cx="84" cy="36" r="3" fill="#C0392B"/>'
        '<rect x="63" y="48" width="40" height="8" rx="3" '
        f'fill="{GOLD_LIGHT}" stroke="#8C6D1D" stroke-width="2"/>'
    )


def make_court_svg(rank: str, suit: str) -> str:
    red = suit in RED_SUITS
    robe_a, robe_b = ("#A93226", "#6E1F16") if red else ("#2E3446", "#191D28")
    trim = "#F6EFD8"
    skin = "#E9BD92"

    head_cy = {"jack": 74, "queen": 78, "king": 78}[rank]
    extras = ""
    if rank == "king":
        extras = (
            '<path d="M74 92 C76 104 74 112 68 118 L100 118 C94 112 92 104 94 92 Z" '
            'fill="#EFE7CE"/>'
        )
    elif rank == "queen":
        extras = (
            '<path d="M62 80 C54 96 52 114 58 130 L70 126 C64 112 66 96 70 86 Z" '
            'fill="#7A4A21"/>'
            '<path d="M106 80 C114 96 116 114 110 130 L98 126 C104 112 102 96 98 86 Z" '
            'fill="#7A4A21"/>'
        )

    if rank == "king":
        accessory = (
            '<g transform="rotate(18 140 120)">'
            '<rect x="136" y="86" width="7" height="78" rx="3" fill="#8C6D1D"/>'
            f'<circle cx="139.5" cy="82" r="9" fill="{GOLD}" stroke="#8C6D1D" stroke-width="2"/>'
            "</g>"
        )
    elif rank == "queen":
        accessory = (
            '<g transform="rotate(-14 62 130)">'
            '<rect x="59" y="102" width="6" height="62" rx="3" fill="#8C6D1D"/>'
            '<circle cx="62" cy="96" r="10" fill="#D96C6C" stroke="#8C6D1D" stroke-width="2"/>'
            '<circle cx="62" cy="96" r="4" fill="#F4D8D8"/>'
            "</g>"
        )
    else:
        accessory = (
            '<g transform="rotate(16 142 120)">'
            '<rect x="138" y="88" width="6" height="74" rx="3" fill="#7C7F8A"/>'
            '<path d="M141 88 C133 78 141 66 149 62 C151 72 149 82 141 88 Z" '
            f'fill="{GOLD_LIGHT}" stroke="#8C6D1D" stroke-width="1.6"/>'
            "</g>"
        )

    glyph = SUIT_GLYPHS[suit]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 280">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FBF6E7"/>
      <stop offset="1" stop-color="#EFE5C9"/>
    </linearGradient>
    <linearGradient id="robe" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{robe_a}"/>
      <stop offset="1" stop-color="{robe_b}"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="192" height="272" rx="12" fill="url(#bg)"
        stroke="#C9BC97" stroke-width="2"/>
  <rect x="14" y="14" width="172" height="252" rx="9" fill="none"
        stroke="{GOLD}" stroke-width="1.6" opacity="0.85"/>
  <g opacity="0.9">
    <text x="100" y="42" font-size="20" text-anchor="middle"
          fill="{RED_LIGHT if red else INK_DARK}" font-family="Georgia, serif">{glyph}</text>
    <text x="100" y="256" font-size="20" text-anchor="middle"
          fill="{RED_LIGHT if red else INK_DARK}" font-family="Georgia, serif">{glyph}</text>
  </g>
  <g>
    <path d="M100 132 C60 132 42 158 40 200 L38 244 L162 244 L160 200 C158 158 140 132 100 132 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.35" stroke-width="2"/>
    <path d="M100 136 C88 148 76 152 66 152 L74 132 C82 138 92 140 100 140 C108 140 118 138 126 132 L134 152 C124 152 112 148 100 136 Z"
          fill="{trim}" opacity="0.95"/>
    <circle cx="100" cy="176" r="4" fill="{GOLD}"/>
    <path d="M84 150 L74 200 M116 150 L126 200" stroke="{GOLD}" stroke-width="2.4" opacity="0.65" fill="none"/>
    <ellipse cx="100" cy="{head_cy}" rx="21" ry="24" fill="{skin}"/>
    <path d="M79 {head_cy - 6} C80 {head_cy - 22} 120 {head_cy - 22} 121 {head_cy - 6} C112 {head_cy - 14} 88 {head_cy - 14} 79 {head_cy - 6} Z"
          fill="#5B3A1E"/>
    {extras}
    {crown(rank)}
    {accessory}
  </g>
</svg>
"""


def make_back_svg() -> str:
    lattice = []
    for i in range(-6, 13):
        offset = i * 14
        lattice.append(
            f'<line x1="{offset}" y1="-10" x2="{offset + 190}" y2="180" '
            'stroke="#3D5FA3" stroke-width="1.1" opacity="0.55"/>'
        )
        lattice.append(
            f'<line x1="{offset + 190}" y1="-10" x2="{offset}" y2="180" '
            'stroke="#3D5FA3" stroke-width="1.1" opacity="0.55"/>'
        )
    corners = ""
    for cx, cy in ((16, 16), (100, 16), (16, 144), (100, 144)):
        corners += (
            f'<g transform="translate({cx} {cy})">'
            '<path d="M0 -7 L2.2 -2.2 L7 0 L2.2 2.2 L0 7 L-2.2 2.2 L-7 0 L-2.2 -2.2 Z" '
            'fill="#E8DFC8" opacity="0.9"/></g>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 116 160">
  <defs>
    <linearGradient id="backBase" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#24488A"/>
      <stop offset="0.5" stop-color="#1A3568"/>
      <stop offset="1" stop-color="#12264D"/>
    </linearGradient>
    <clipPath id="innerClip">
      <rect x="9" y="9" width="98" height="142" rx="8"/>
    </clipPath>
  </defs>
  <rect x="1" y="1" width="114" height="158" rx="10" fill="url(#backBase)"
        stroke="#0C1B38" stroke-width="2"/>
  <rect x="4" y="4" width="108" height="152" rx="8" fill="none"
        stroke="{GOLD_LIGHT}" stroke-width="1.4" opacity="0.9"/>
  <rect x="8" y="8" width="100" height="144" rx="7" fill="none"
        stroke="#C9BC97" stroke-width="1.1" opacity="0.55"/>
  <g clip-path="url(#innerClip)">
    <rect x="9" y="9" width="98" height="142" fill="#16294F"/>
    <g>{''.join(lattice)}</g>
    <circle cx="58" cy="80" r="30" fill="#E9E2CC" opacity="0.97"/>
    <circle cx="58" cy="80" r="30" fill="none" stroke="{GOLD}" stroke-width="2"/>
    <circle cx="58" cy="80" r="25" fill="none" stroke="#1A3568" stroke-width="1.2"/>
    <g transform="translate(38.7 60.4) scale(0.4)">
      {suit_body("spades", "#16294F")}
    </g>
    {corners}
  </g>
</svg>
"""


def make_felt_tile(path: Path, size: int = 320, seed: int = 200) -> None:
    """Render a tileable woven casino felt texture deterministically."""
    rng = random.Random(seed)
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor("#0D4D24"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # Weave: alternating horizontal / vertical bands.
    band = 4
    for y in range(0, size, band):
        light = (y // band) % 2 == 0
        painter.fillRect(0, y, size, band, QColor(255, 255, 255, 10 if light else 0))
        painter.fillRect(0, y, size, band, QColor(0, 0, 0, 14 if not light else 0))
    for x in range(0, size, band):
        painter.fillRect(x, 0, 1, size, QColor(0, 0, 0, 10))
        painter.fillRect(x, 0, 1, size, QColor(255, 255, 255, 6))

    # Fibre noise.
    for _ in range(size * 26):
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
    for _ in range(900):
        x = rng.randrange(size)
        y = rng.randrange(size)
        length = rng.randrange(4, 12)
        painter.drawLine(x, y, min(size - 1, x + length), y)

    # Faint diamond quilting, echoing the reference screenshot.
    painter.setPen(QPen(QColor(255, 255, 255, 9), 1))
    step = 64
    for start in range(-size, size * 2, step):
        painter.drawLine(start, 0, start + size, size)
        painter.drawLine(start + size, 0, start, size)

    painter.end()
    image.save(str(path), "PNG")


def main() -> None:
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
