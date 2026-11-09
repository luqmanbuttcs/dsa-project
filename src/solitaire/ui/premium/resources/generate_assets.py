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
# Court cards: twelve individualised illustrations
# ---------------------------------------------------------------------------


def _filigree_corner(suit: str, transform: str) -> str:
    accent = SUIT_COURT_STYLE[suit][2]
    return f"""<g transform="{transform}" opacity="0.55">
      <path d="M0 22 C0 8 8 0 22 0 C14 4 6 12 2 24 Z" fill="{accent}"/>
      <path d="M6 30 C10 16 16 10 30 6 C20 12 14 20 12 32 Z" fill="{GOLD}" opacity="0.8"/>
      <circle cx="4" cy="4" r="2.4" fill="{GOLD}"/>
    </g>"""


def _robe_pattern(suit: str) -> str:
    """Small repeating suit motifs embroidered on the robe."""
    glyph = SUIT_GLYPHS[suit]
    accent = SUIT_COURT_STYLE[suit][2]
    dots = []
    for row, y in enumerate((182, 212, 240)):
        for col, x in enumerate((60, 84, 108, 132)):
            if (row + col) % 2 == 0:
                dots.append(
                    f'<text x="{x}" y="{y}" font-size="17" text-anchor="middle" '
                    f'fill="{accent}" opacity="0.55" font-family="Georgia, serif">{glyph}</text>'
                )
    return "".join(dots)


def _headgear(rank: str, suit: str) -> str:
    accent = SUIT_COURT_STYLE[suit][2]
    metal = SUIT_COURT_STYLE[suit][3]
    if rank == "king":
        return f"""
    <path d="M60 52 L58 28 L74 44 L84 22 L94 44 L110 28 L108 52 Z"
          fill="{metal}" stroke="{GOLD_DEEP}" stroke-width="2"/>
    <circle cx="84" cy="20" r="4.4" fill="#C0392B" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
    <circle cx="61" cy="34" r="3.2" fill="#2E6DB4"/>
    <circle cx="107" cy="34" r="3.2" fill="#2E6DB4"/>
    <rect x="56" y="50" width="56" height="10" rx="3.5"
          fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="2"/>
    <circle cx="66" cy="55" r="2" fill="{GOLD_DEEP}"/>
    <circle cx="84" cy="55" r="2" fill="{GOLD_DEEP}"/>
    <circle cx="102" cy="55" r="2" fill="{GOLD_DEEP}"/>"""
    if rank == "queen":
        return f"""
    <path d="M62 52 L58 32 L72 44 L84 26 L96 44 L110 32 L106 52 Z"
          fill="{metal}" stroke="{GOLD_DEEP}" stroke-width="2"/>
    <circle cx="84" cy="24" r="4" fill="#3E8EC4" stroke="{GOLD_DEEP}" stroke-width="1.3"/>
    <path d="M58 52 C64 48 104 48 110 52 L108 58 L60 58 Z"
          fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.8"/>
    <circle cx="70" cy="44" r="2.6" fill="#E8B4C8"/>
    <circle cx="98" cy="44" r="2.6" fill="#E8B4C8"/>"""
    # Jack: beret with feather
    feather = "#C46A6A" if suit in RED_SUITS else "#7FA3D1"
    return f"""
    <path d="M62 52 C60 38 74 30 88 32 C104 34 110 44 108 52
             C96 46 74 46 62 52 Z"
          fill="{metal}" stroke="{GOLD_DEEP}" stroke-width="2"/>
    <path d="M104 34 C114 24 126 22 132 26 C124 30 116 34 110 40 Z"
          fill="{feather}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
    <circle cx="86" cy="34" r="3" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.2"/>"""


def _hair(rank: str, head_cy: int) -> str:
    if rank == "king":
        return (
            f'<path d="M79 {head_cy - 8} C80 {head_cy - 24} 120 {head_cy - 24} '
            f'121 {head_cy - 8} C118 {head_cy - 14} 108 {head_cy - 17} 100 {head_cy - 17} '
            f'C92 {head_cy - 17} 82 {head_cy - 14} 79 {head_cy - 8} Z" fill="#6B4423"/>'
            f'<path d="M78 {head_cy + 6} C74 {head_cy + 22} 76 {head_cy + 30} 82 {head_cy + 34} '
            f'L86 {head_cy + 20} Z" fill="#6B4423"/>'
            f'<path d="M122 {head_cy + 6} C126 {head_cy + 22} 124 {head_cy + 30} 118 {head_cy + 34} '
            f'L114 {head_cy + 20} Z" fill="#6B4423"/>'
        )
    if rank == "queen":
        return (
            f'<path d="M76 {head_cy - 4} C72 {head_cy + 26} 66 {head_cy + 40} 58 {head_cy + 52} '
            f'C70 {head_cy + 46} 76 {head_cy + 30} 78 {head_cy + 12} Z" fill="#8A5A2B"/>'
            f'<path d="M124 {head_cy - 4} C128 {head_cy + 26} 134 {head_cy + 40} 142 {head_cy + 52} '
            f'C130 {head_cy + 46} 124 {head_cy + 30} 122 {head_cy + 12} Z" fill="#8A5A2B"/>'
            f'<path d="M79 {head_cy - 8} C80 {head_cy - 24} 120 {head_cy - 24} 121 {head_cy - 8} '
            f'C110 {head_cy - 18} 90 {head_cy - 18} 79 {head_cy - 8} Z" fill="#8A5A2B"/>'
        )
    return (
        f'<path d="M80 {head_cy - 6} C82 {head_cy - 22} 118 {head_cy - 22} 120 {head_cy - 6} '
        f'C112 {head_cy - 14} 88 {head_cy - 14} 80 {head_cy - 6} Z" fill="#3E2A16"/>'
    )


def _beard(head_cy: int) -> str:
    return (
        f'<path d="M84 {head_cy + 10} C86 {head_cy + 30} 92 {head_cy + 38} 100 {head_cy + 40} '
        f'C108 {head_cy + 38} 114 {head_cy + 30} 116 {head_cy + 10} '
        f'C110 {head_cy + 20} 90 {head_cy + 20} 84 {head_cy + 10} Z" fill="#6B4423" opacity="0.92"/>'
    )


def _accessory(rank: str, suit: str) -> str:
    """Rank × suit attribute so every court card is recognisably unique."""
    metal = SUIT_COURT_STYLE[suit][3]
    accent = SUIT_COURT_STYLE[suit][2]

    scepter_top = {
        "hearts": f'<path d="M142 74 C136 66 142 56 150 52 C152 62 150 70 142 74 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "diamonds": f'<rect x="136" y="64" width="15" height="15" transform="rotate(45 143.5 71.5)" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "clubs": f'<circle cx="143" cy="60" r="6" fill="{accent}"/><circle cx="136" cy="68" r="6" fill="{accent}"/><circle cx="150" cy="68" r="6" fill="{accent}"/>',
        "spades": f'<path d="M143 52 C148 60 156 66 156 72 C156 78 150 81 143 78 C136 81 130 78 130 72 C130 66 138 60 143 52 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
    }
    if rank == "king":
        staff = scepter_top[suit]
        return f"""
    <g transform="rotate(14 142 120)">
      <rect x="139" y="78" width="8" height="92" rx="3.5" fill="{GOLD_DEEP}"/>
      <rect x="140.5" y="78" width="5" height="92" rx="2.5" fill="{metal}" opacity="0.85"/>
      {staff}
      <circle cx="143" cy="86" r="5" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.6"/>
    </g>"""
    if rank == "queen":
        held = {
            "hearts": f'<circle cx="58" cy="118" r="11" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.6"/><circle cx="58" cy="118" r="5" fill="#F4D8D8"/>',
            "diamonds": f'<path d="M58 106 C62 113 69 119 76 122 C69 125 62 131 58 138 C54 131 47 125 40 122 C47 119 54 113 58 106 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.6"/>',
            "clubs": f'<circle cx="58" cy="112" r="7" fill="{accent}"/><circle cx="51" cy="120" r="7" fill="{accent}"/><circle cx="65" cy="120" r="7" fill="{accent}"/><rect x="56" y="126" width="4" height="12" rx="2" fill="{GOLD_DEEP}"/>',
            "spades": f'<circle cx="58" cy="120" r="12" fill="none" stroke="{GOLD}" stroke-width="2"/><path d="M58 110 C61 114 65 117 68 119 C65 121 61 124 58 128 C55 124 51 121 48 119 C51 117 55 114 58 110 Z" fill="{accent}"/>',
        }
        return f"""
    <g transform="rotate(-12 58 124)">
      <rect x="55.5" y="128" width="5" height="52" rx="2.5" fill="{GOLD_DEEP}"/>
      {held[suit]}
    </g>"""
    # Jack staff: halberd / leaf blade
    blade = {
        "hearts": f'<path d="M141 84 C133 74 141 62 149 58 C151 68 149 78 141 84 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "diamonds": f'<path d="M141 56 L150 70 L141 84 L132 70 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "clubs": f'<path d="M141 56 C133 66 133 76 141 86 C149 76 149 66 141 56 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "spades": f'<path d="M141 54 C147 64 155 70 155 76 C155 82 148 85 141 82 C134 85 127 82 127 76 C127 70 135 64 141 54 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
    }
    return f"""
    <g transform="rotate(16 142 120)">
      <rect x="138.5" y="84" width="6.5" height="86" rx="3" fill="#54575F"/>
      <rect x="139.5" y="84" width="4.5" height="86" rx="2" fill="#8A8F99" opacity="0.9"/>
      {blade[suit]}
    </g>"""


def _face(rank: str, head_cy: int) -> str:
    """Face details: eyes, brows and a mouth; slight profile per rank."""
    look = {"king": (4, 5), "queen": (3, 5), "jack": (5, 5)}[rank]
    left_x, right_x = 100 - look[0], 100 + look[1]
    eye_y = head_cy - 2
    return f"""
    <ellipse cx="{left_x}" cy="{eye_y}" rx="2.6" ry="3.2" fill="#2A2118"/>
    <ellipse cx="{right_x}" cy="{eye_y}" rx="2.6" ry="3.2" fill="#2A2118"/>
    <path d="M{left_x - 5} {eye_y - 6} Q{left_x} {eye_y - 9} {left_x + 5} {eye_y - 6}"
          stroke="#3E2A16" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <path d="M{right_x - 5} {eye_y - 6} Q{right_x} {eye_y - 9} {right_x + 5} {eye_y - 6}"
          stroke="#3E2A16" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <path d="M94 {head_cy + 12} Q100 {head_cy + 15} 106 {head_cy + 12}"
          stroke="#8E4A3A" stroke-width="2" fill="none" stroke-linecap="round"/>"""


def make_court_svg(rank: str, suit: str) -> str:
    red = suit in RED_SUITS
    robe_a, robe_b, accent, metal = SUIT_COURT_STYLE[suit]
    skin = "#EFC49C" if rank != "king" else "#E9BD92"
    head_cy = {"jack": 76, "queen": 78, "king": 78}[rank]
    glyph = SUIT_GLYPHS[suit]
    ink = RED_LIGHT if red else INK_DEEP

    collar = (
        f'<path d="M78 138 C88 148 112 148 122 138 L116 128 L84 128 Z" '
        f'fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.6"/>'
    )
    if rank == "king":
        collar += (
            f'<path d="M84 128 L100 144 L116 128" fill="none" stroke="{GOLD_DEEP}" stroke-width="2"/>'
        )
    elif rank == "queen":
        collar += (
            f'<circle cx="100" cy="140" r="3.2" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.2"/>'
        )
    else:
        collar += (
            f'<rect x="92" y="128" width="16" height="16" rx="3" fill="{accent}" '
            f'stroke="{GOLD_DEEP}" stroke-width="1.4"/>'
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 280">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FCF8EA"/>
      <stop offset="1" stop-color="#EEE2C4"/>
    </linearGradient>
    <linearGradient id="robe" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{robe_a}"/>
      <stop offset="1" stop-color="{robe_b}"/>
    </linearGradient>
    <linearGradient id="inner" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F8F2DE"/>
      <stop offset="1" stop-color="#E2D5B2"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.5" cy="0.42" r="0.62">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.22"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="robeClip">
      <path d="M100 132 C60 132 42 158 40 200 L38 244 L162 244 L160 200 C158 158 140 132 100 132 Z"/>
    </clipPath>
  </defs>

  <rect x="3" y="3" width="194" height="274" rx="13" fill="url(#bg)"
        stroke="#C4B58E" stroke-width="2.4"/>
  <rect x="10" y="10" width="180" height="260" rx="10" fill="none"
        stroke="{GOLD}" stroke-width="1.8" opacity="0.9"/>
  <rect x="15" y="15" width="170" height="250" rx="8" fill="none"
        stroke="{GOLD_DEEP}" stroke-width="1" opacity="0.5"/>

  {_filigree_corner(suit, "translate(16 16)")}
  {_filigree_corner(suit, "translate(184 16) scale(-1 1)")}
  {_filigree_corner(suit, "translate(16 264) scale(1 -1)")}
  {_filigree_corner(suit, "translate(184 264) scale(-1 -1)")}

  <rect x="24" y="24" width="152" height="232" rx="7" fill="url(#halo)"/>
  <path d="M40 244 L40 120 Q40 60 100 52 Q160 60 160 120 L160 244"
        fill="none" stroke="{GOLD}" stroke-width="1.2" opacity="0.45"/>
  <text x="100" y="44" font-size="21" text-anchor="middle"
        fill="{ink}" font-family="Georgia, serif">{glyph}</text>
  <text x="100" y="262" font-size="21" text-anchor="middle"
        fill="{ink}" font-family="Georgia, serif">{glyph}</text>

  <g>
    <path d="M100 132 C60 132 42 158 40 200 L38 244 L162 244 L160 200 C158 158 140 132 100 132 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.4" stroke-width="2.2"/>
    <g clip-path="url(#robeClip)">
      <path d="M100 134 L76 244 L124 244 Z" fill="url(#inner)" opacity="0.92"/>
      <path d="M100 136 L84 244 M100 136 L116 244" stroke="{GOLD_DEEP}" stroke-width="1.2" opacity="0.5" fill="none"/>
      {_robe_pattern(suit)}
      <path d="M30 232 C60 224 140 224 170 232 L170 244 L30 244 Z"
            fill="#F3EBD3" stroke="{GOLD_DEEP}" stroke-width="1.2"/>
      <g opacity="0.85">
        <circle cx="52" cy="238" r="3.4" fill="#1A1A1A"/>
        <circle cx="76" cy="236" r="3.4" fill="#1A1A1A"/>
        <circle cx="100" cy="238" r="3.4" fill="#1A1A1A"/>
        <circle cx="124" cy="236" r="3.4" fill="#1A1A1A"/>
        <circle cx="148" cy="238" r="3.4" fill="#1A1A1A"/>
      </g>
      <path d="M36 200 L164 200" stroke="{GOLD}" stroke-width="1.4" opacity="0.45"/>
    </g>
    <!-- sleeves / arms -->
    <path d="M64 150 C52 160 46 176 44 194 C54 198 64 198 72 194 C70 178 72 162 78 150 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.35" stroke-width="1.8"/>
    <path d="M136 150 C148 160 154 176 156 194 C146 198 136 198 128 194 C130 178 128 162 122 150 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.35" stroke-width="1.8"/>
    <circle cx="58" cy="196" r="7.5" fill="{skin}" stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>
    <circle cx="142" cy="196" r="7.5" fill="{skin}" stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>
    <path d="M100 136 C88 148 76 152 66 152 L74 132 C82 138 92 140 100 140 C108 140 118 138 126 132 L134 152 C124 152 112 148 100 136 Z"
          fill="#F6EFD8" opacity="0.95"/>
    {collar}
    <ellipse cx="100" cy="{head_cy}" rx="23" ry="26" fill="{skin}"/>
    {_hair(rank, head_cy)}
    {"" if rank != "king" else _beard(head_cy)}
    {_headgear(rank, suit)}
    {_face(rank, head_cy)}
    {_accessory(rank, suit)}
  </g>
</svg>
"""


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
    image.fill(QColor("#0B4A22"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # Weave: alternating horizontal / vertical bands.
    band = 4
    for y in range(0, size, band):
        light = (y // band) % 2 == 0
        painter.fillRect(0, y, size, band, QColor(255, 255, 255, 11 if light else 0))
        painter.fillRect(0, y, size, band, QColor(0, 0, 0, 15 if not light else 0))
    for x in range(0, size, band):
        painter.fillRect(x, 0, 1, size, QColor(0, 0, 0, 11))
        painter.fillRect(x, 0, 1, size, QColor(255, 255, 255, 6))

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
    painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
    step = 96
    for start in range(-size, size * 2, step):
        painter.drawLine(start, 0, start + size, size)
        painter.drawLine(start + size, 0, start, size)

    glyphs = ("♥", "♦", "♣", "♠")
    painter.setPen(QPen(QColor(255, 255, 255, 13), 1))
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
