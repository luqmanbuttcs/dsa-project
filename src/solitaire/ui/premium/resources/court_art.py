"""Baroque court-card artwork: twelve individualised royal illustrations.

Each rank × suit combination is a genuinely distinct composition — unique
pose orientation, headgear, hair, beard/hairstyle, held regalia, embroidered
robe palette and radiant background — while all twelve share one construction
grammar (200×280 viewBox, ivory ground, gold frame, rank medallions) so the
deck reads as a coherent premium casino set.

Rendered by QtSvg at card size (116×160 logical), so only SVG-Tiny features
are used: paths, gradients, groups, transforms and <text>.
"""

from __future__ import annotations

GOLD = "#C9A227"
GOLD_LIGHT = "#E7C55C"
GOLD_DEEP = "#8C6D1D"
GOLD_PALE = "#F3E3AE"

SUIT_GLYPHS = {
    "hearts": "♥",
    "diamonds": "♦",
    "clubs": "♣",
    "spades": "♠",
}

# (robe light, robe deep, accent, metal, gem, heraldic blazon)
SUIT_STYLE = {
    "hearts": ("#A32636", "#54101A", "#E0505E", "#D4AF37", "#E43D4A", "crimson"),
    "diamonds": ("#B45E1D", "#5E2A08", "#F09140", "#E7C55C", "#F2A63C", "amber"),
    "clubs": ("#2F6B39", "#123318", "#69B876", "#B9962B", "#3FA060", "verdant"),
    "spades": ("#31497E", "#141D36", "#7B9CD4", "#AEB6C4", "#4C6FB0", "azure"),
}

HAIR_BY_SUIT = {
    "hearts": "#7A4A22",
    "diamonds": "#B0762E",
    "clubs": "#4A3320",
    "spades": "#2C2C34",
}
SKIN_BY_SUIT = {
    "hearts": "#F0C69E",
    "diamonds": "#E9BD92",
    "clubs": "#D9A87C",
    "spades": "#E3B58C",
}


def _wedge_sunburst(suit: str) -> str:
    """Radiant courtly backdrop — alternating translucent rays."""
    accent = SUIT_STYLE[suit][2]
    rays = []
    for index in range(20):
        angle = index * 18.0
        if index % 2:
            continue
        rays.append(
            f'<path d="M100 148 L{100 + 108 * _cosx(angle - 9):.1f} '
            f"{148 + 108 * _cosy(angle - 9):.1f} L{100 + 108 * _cosx(angle + 9):.1f} "
            f'{148 + 108 * _cosy(angle + 9):.1f} Z" fill="{accent}" opacity="0.10"/>'
        )
    return (
        '<g clip-path="url(#artClip)">'
        + "".join(rays)
        + f'<circle cx="100" cy="148" r="74" fill="{accent}" opacity="0.05"/>'
        "</g>"
    )


def _cosx(deg: float) -> float:
    import math

    return math.cos(math.radians(deg))


def _cosy(deg: float) -> float:
    import math

    return math.sin(math.radians(deg))


def _suit_motif_row(suit: str, y: float, x0: float, x1: float, step: float,
                    size: float, color: str, opacity: float) -> str:
    glyph = SUIT_GLYPHS[suit]
    out = []
    x = x0
    while x <= x1:
        out.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="middle" '
            f'fill="{color}" opacity="{opacity}" font-family="Georgia, serif">{glyph}</text>'
        )
        x += step
    return "".join(out)


def _ermine_band(x0: float, y0: float, x1: float, y1: float, height: float,
                 dots: int = 5) -> str:
    """Ermine trim band (ivory with charcoal tufts) along a straight edge."""
    out = [
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{height}" '
        f'fill="#F6F1E1" stroke="{GOLD_DEEP}" stroke-width="1"/>'
    ]
    for index in range(dots):
        t = (index + 0.5) / dots
        cx = x0 + (x1 - x0) * t
        cy = y0 + height * 0.5
        out.append(
            f'<path d="M{cx:.1f} {cy - 2.2:.1f} C{cx + 1.8:.1f} {cy - 2.0:.1f} '
            f"{cx + 1.8:.1f} {cy + 2.0:.1f} {cx:.1f} {cy + 2.4:.1f} "
            f"C{cx - 1.8:.1f} {cy + 2.0:.1f} {cx - 1.8:.1f} {cy - 2.0:.1f} "
            f'{cx:.1f} {cy - 2.2:.1f} Z" fill="#23242B"/>'
        )
    return "".join(out)


def _crown(suit: str) -> str:
    """Arched royal crown with jewels, pearls and a cross finial."""
    metal = SUIT_STYLE[suit][3]
    gem = SUIT_STYLE[suit][4]
    return f"""
    <g transform="translate(100 0)">
      <path d="M-30 52 C-30 30 -18 20 -12 34 C-10 18 -4 8 0 4 C4 8 10 18 12 34
               C18 20 30 30 30 52 Z"
            fill="url(#metalGrad)" stroke="{GOLD_DEEP}" stroke-width="1.8"/>
      <path d="M-30 52 C-30 30 -18 20 -12 34" fill="none" stroke="#FFF3C9" stroke-width="1.1" opacity="0.8"/>
      <rect x="-33" y="50" width="66" height="11" rx="4"
            fill="url(#metalGrad)" stroke="{GOLD_DEEP}" stroke-width="1.8"/>
      <circle cx="-20" cy="55.5" r="2.6" fill="{gem}" stroke="{GOLD_DEEP}" stroke-width="0.8"/>
      <circle cx="0" cy="55.5" r="3.2" fill="#3E8EC4" stroke="{GOLD_DEEP}" stroke-width="0.8"/>
      <circle cx="20" cy="55.5" r="2.6" fill="{gem}" stroke="{GOLD_DEEP}" stroke-width="0.8"/>
      <circle cx="-12" cy="30" r="2.4" fill="{gem}"/>
      <circle cx="12" cy="30" r="2.4" fill="{gem}"/>
      <g transform="translate(0 -1)">
        <rect x="-1.6" y="-8" width="3.2" height="7" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="0.7"/>
        <rect x="-3.4" y="-6" width="6.8" height="2.4" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="0.7"/>
      </g>
      <circle cx="-33" cy="52" r="2" fill="#F7F2DF" stroke="{GOLD_DEEP}" stroke-width="0.6"/>
      <circle cx="33" cy="52" r="2" fill="#F7F2DF" stroke="{GOLD_DEEP}" stroke-width="0.6"/>
    </g>"""


def _diadem(suit: str) -> str:
    metal = SUIT_STYLE[suit][3]
    gem = SUIT_STYLE[suit][4]
    return f"""
    <g transform="translate(100 0)">
      <path d="M-26 50 L-20 30 L-9 44 L0 22 L9 44 L20 30 L26 50 Z"
            fill="url(#metalGrad)" stroke="{GOLD_DEEP}" stroke-width="1.5"/>
      <circle cx="0" cy="18" r="3.4" fill="{gem}" stroke="{GOLD_DEEP}" stroke-width="0.9"/>
      <circle cx="-20" cy="26" r="2.4" fill="#F7F2DF" stroke="{GOLD_DEEP}" stroke-width="0.7"/>
      <circle cx="20" cy="26" r="2.4" fill="#F7F2DF" stroke="{GOLD_DEEP}" stroke-width="0.7"/>
      <rect x="-28" y="48" width="56" height="8" rx="3.5"
            fill="url(#metalGrad)" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
      <circle cx="-14" cy="52" r="1.8" fill="#FFF6D8"/>
      <circle cx="0" cy="52" r="1.8" fill="#FFF6D8"/>
      <circle cx="14" cy="52" r="1.8" fill="#FFF6D8"/>
    </g>"""


def _beret(suit: str) -> str:
    metal = SUIT_STYLE[suit][3]
    plume = {"hearts": "#D96A78", "diamonds": "#E8A05A", "clubs": "#7FBF8C", "spades": "#8FA9DA"}[suit]
    return f"""
    <g transform="translate(100 0)">
      <path d="M6 34 C22 28 36 34 40 44 C30 40 18 42 10 48 Z"
            fill="{plume}" stroke="{GOLD_DEEP}" stroke-width="1.2"/>
      <path d="M-30 50 C-28 28 -10 18 4 20 C20 22 30 36 28 52
               C14 40 -16 40 -30 50 Z"
            fill="url(#metalGrad)" stroke="{GOLD_DEEP}" stroke-width="1.6"/>
      <path d="M-30 50 C-16 40 14 40 28 52 L26 57 C12 46 -18 46 -28 55 Z"
            fill="{GOLD_DEEP}" opacity="0.85"/>
      <circle cx="2" cy="24" r="3" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1"/>
    </g>"""


def _beard(style: str, skin: str) -> str:
    if style == "full":
        return f"""
    <path d="M82 88 C80 112 88 130 100 134 C112 130 120 112 118 88
             C112 100 88 100 82 88 Z" fill="#5E4326" opacity="0.95"/>
    <path d="M88 96 C90 112 95 122 100 126 C105 122 110 112 112 96 C106 104 94 104 88 96 Z"
          fill="#7A5A34" opacity="0.85"/>"""
    if style == "forked":
        return f"""
    <path d="M84 90 C84 108 90 122 100 126 C110 122 116 108 116 90
             C110 100 90 100 84 90 Z" fill="#3A3A44" opacity="0.95"/>
    <path d="M96 122 C96 132 98 138 100 142 C102 138 104 132 104 122 Z"
          fill="#3A3A44" opacity="0.95"/>"""
    if style == "grey":
        return f"""
    <path d="M82 88 C78 110 88 128 100 132 C112 128 122 110 118 88
             C110 102 90 102 82 88 Z" fill="#C9C4B8" opacity="0.95"/>
    <path d="M88 98 C90 112 94 120 100 124 C106 120 110 112 112 98 C104 106 96 106 88 98 Z"
          fill="#E4E0D4" opacity="0.9"/>"""
    return f"""
    <path d="M86 90 C86 104 92 114 100 118 C108 114 114 104 114 90
             C108 98 92 98 86 90 Z" fill="#4A3320" opacity="0.92"/>"""


def _face(rank: str, suit: str) -> str:
    skin = SKIN_BY_SUIT[suit]
    eye_y = 84
    look = {"king": (-1, 5), "queen": (-2, 4), "jack": (0, 6)}[rank]
    lx, rx = 100 + look[0] - 6, 100 + look[1] + 1
    out = [f"""
    <ellipse cx="100" cy="86" rx="21" ry="24" fill="url(#skinGrad)"/>
    <path d="M79 84 C79 66 88 58 100 58 C112 58 121 66 121 84 C121 72 112 66 100 66 C88 66 79 72 79 84 Z"
          fill="#000000" opacity="0.12"/>
    <ellipse cx="80" cy="88" rx="2.6" ry="4" fill="{skin}" stroke="#00000030" stroke-width="0.6"/>
    <ellipse cx="120" cy="88" rx="2.6" ry="4" fill="{skin}" stroke="#00000030" stroke-width="0.6"/>"""]
    # eyes with shine
    for cx in (lx, rx):
        out.append(
            f'<ellipse cx="{cx}" cy="{eye_y}" rx="3.1" ry="3.6" fill="#FFFFFF"/>'
            f'<circle cx="{cx + 0.4}" cy="{eye_y + 0.3}" r="1.8" fill="#2A2118"/>'
            f'<circle cx="{cx + 1.1}" cy="{eye_y - 0.8}" r="0.7" fill="#FFFFFF"/>'
        )
    # brows
    out.append(
        f'<path d="M{lx - 5} {eye_y - 7} Q{lx} {eye_y - 10} {lx + 5} {eye_y - 7}" '
        'stroke="#3E2A16" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
        f'<path d="M{rx - 5} {eye_y - 7} Q{rx} {eye_y - 10} {rx + 5} {eye_y - 7}" '
        'stroke="#3E2A16" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
    )
    # nose + mouth
    out.append(
        f'<path d="M100 {eye_y + 3} C98.6 {eye_y + 8} 98 {eye_y + 10} 100 {eye_y + 11}" '
        'stroke="#00000038" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
    )
    if rank == "queen":
        out.append(
            f'<path d="M95 {eye_y + 17} Q100 {eye_y + 20} 105 {eye_y + 17}" '
            'stroke="#B4525A" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
            '<circle cx="86" cy="94" r="3.4" fill="#E88A8A" opacity="0.35"/>'
            '<circle cx="114" cy="94" r="3.4" fill="#E88A8A" opacity="0.35"/>'
        )
    else:
        out.append(
            f'<path d="M94 {eye_y + 17} Q100 {eye_y + 20} 106 {eye_y + 17}" '
            'stroke="#8E4A3A" stroke-width="2" fill="none" stroke-linecap="round"/>'
        )
    return "".join(out)


def _king_body(suit: str) -> str:
    robe_a, robe_b, accent, metal, gem, _ = SUIT_STYLE[suit]
    return f"""
    <clipPath id="robeClip">
      <path d="M100 122 C56 122 38 154 36 198 L34 248 L166 248 L164 198 C162 154 144 122 100 122 Z"/>
    </clipPath>
    <path d="M100 122 C56 122 38 154 36 198 L34 248 L166 248 L164 198 C162 154 144 122 100 122 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.45" stroke-width="2.2"/>
    <path d="M100 126 C66 128 50 156 48 198 L47 246 L64 246 L66 196 C68 160 80 136 100 130 Z"
          fill="#FFFFFF" opacity="0.10"/>
    <path d="M100 132 L82 246 L118 246 Z" fill="#F6EFD8" opacity="0.16"/>
    <g clip-path="url(#robeClip)">
      {_suit_motif_row(suit, 176, 52, 148, 24, 12, accent, 0.5)}
      {_suit_motif_row(suit, 200, 40, 160, 24, 12, accent, 0.45)}
      {_suit_motif_row(suit, 224, 52, 148, 24, 12, accent, 0.5)}
    </g>
    {_ermine_band(34, 236, 166, 246, 12, dots=7)}
    <path d="M78 126 C88 138 112 138 122 126 L116 120 L84 120 Z"
          fill="#F6F1E1" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
    <path d="M84 121 L100 137 L116 121" fill="none" stroke="{GOLD_DEEP}" stroke-width="1.8"/>
    <path d="M40 176 L66 176 M134 176 L160 176" stroke="{GOLD}" stroke-width="2" opacity="0.6"/>
    <circle cx="100" cy="158" r="5.5" fill="{gem}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
    <circle cx="100" cy="158" r="2" fill="#FFFFFF" opacity="0.7"/>"""


def _queen_body(suit: str) -> str:
    robe_a, robe_b, accent, metal, gem, _ = SUIT_STYLE[suit]
    lacing = []
    for index in range(4):
        y = 138 + index * 11
        lacing.append(
            f'<path d="M{93 - index * 1.4:.1f} {y} L{107 + index * 1.4:.1f} {y + 7:.1f}" '
            f'stroke="{GOLD_DEEP}" stroke-width="1.2" opacity="0.8"/>'
            f'<path d="M{107 + index * 1.4:.1f} {y} L{93 - index * 1.4:.1f} {y + 7:.1f}" '
            f'stroke="{GOLD_DEEP}" stroke-width="1.2" opacity="0.8"/>'
        )
    return f"""
    <clipPath id="robeClip">
      <path d="M100 126 C64 126 48 154 46 196 L44 248 L156 248 L154 196 C152 154 136 126 100 126 Z"/>
    </clipPath>
    <path d="M100 126 C64 126 48 154 46 196 L44 248 L156 248 L154 196 C152 154 136 126 100 126 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.45" stroke-width="2.2"/>
    <path d="M100 132 L86 246 L114 246 Z" fill="#F6EFD8" opacity="0.18"/>
    <g clip-path="url(#robeClip)">
      {_suit_motif_row(suit, 214, 52, 148, 26, 11, accent, 0.5)}
      {_suit_motif_row(suit, 236, 46, 154, 26, 11, accent, 0.45)}
    </g>
    <path d="M100 130 L84 168 L100 176 L116 168 Z" fill="#F6F1E1"
          stroke="{GOLD_DEEP}" stroke-width="1.3" opacity="0.95"/>
    {''.join(lacing)}
    <path d="M78 128 C84 140 92 146 100 148 C108 146 116 140 122 128 L116 122 L84 122 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.3" stroke-width="1.6"/>
    <path d="M92 152 C92 158 108 158 108 152 C108 149 92 149 92 152 Z"
          fill="none" stroke="{GOLD}" stroke-width="1.6" opacity="0.9"/>
    <circle cx="96" cy="153" r="1.6" fill="#F7F2DF"/>
    <circle cx="100" cy="154" r="1.6" fill="#F7F2DF"/>
    <circle cx="104" cy="153" r="1.6" fill="#F7F2DF"/>
    <circle cx="100" cy="182" r="4.6" fill="{gem}" stroke="{GOLD_DEEP}" stroke-width="1.2"/>
    {_ermine_band(44, 236, 156, 248, 12, dots=6)}"""


def _jack_body(suit: str) -> str:
    robe_a, robe_b, accent, metal, gem, _ = SUIT_STYLE[suit]
    slashes = []
    for index in range(4):
        y = 150 + index * 13
        slashes.append(
            f'<ellipse cx="56" cy="{y}" rx="6.5" ry="4.2" fill="#F6F1E1" '
            f'stroke="{GOLD_DEEP}" stroke-width="1" opacity="0.9"/>'
            f'<ellipse cx="144" cy="{y}" rx="6.5" ry="4.2" fill="#F6F1E1" '
            f'stroke="{GOLD_DEEP}" stroke-width="1" opacity="0.9"/>'
        )
    return f"""
    <clipPath id="robeClip">
      <path d="M100 128 C70 128 56 152 54 194 L52 248 L148 248 L146 194 C144 152 130 128 100 128 Z"/>
    </clipPath>
    <path d="M100 128 C70 128 56 152 54 194 L52 248 L148 248 L146 194 C144 152 130 128 100 128 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.45" stroke-width="2.2"/>
    <path d="M100 134 L88 246 L112 246 Z" fill="#F6EFD8" opacity="0.15"/>
    <g clip-path="url(#robeClip)">
      {_suit_motif_row(suit, 218, 58, 142, 22, 11, accent, 0.5)}
      {_suit_motif_row(suit, 238, 52, 148, 22, 11, accent, 0.45)}
    </g>
    {_ermine_band(52, 236, 148, 248, 12, dots=6)}
    <path d="M100 128 C84 132 68 130 58 138 L60 158 C74 150 90 148 100 146 Z"
          fill="{accent}" opacity="0.85" stroke="#10131B" stroke-opacity="0.3" stroke-width="1.4"/>
    <path d="M100 128 C116 132 132 130 142 138 L140 158 C126 150 110 148 100 146 Z"
          fill="url(#robe)" stroke="#10131B" stroke-opacity="0.3" stroke-width="1.4"/>
    {''.join(slashes)}
    <path d="M80 128 C88 138 112 138 120 128 L114 121 L86 121 Z"
          fill="#F6F1E1" stroke="{GOLD_DEEP}" stroke-width="1.3"/>
    <rect x="92" y="130" width="16" height="15" rx="3" fill="{accent}"
          stroke="{GOLD_DEEP}" stroke-width="1.3"/>
    <path d="M95 133 L105 142 M105 133 L95 142" stroke="{GOLD_DEEP}" stroke-width="1.1"/>"""


def _scepter(suit: str, x: float, y: float, angle: float) -> str:
    metal = SUIT_STYLE[suit][3]
    accent = SUIT_STYLE[suit][2]
    gem = SUIT_STYLE[suit][4]
    topper = {
        "hearts": f'<path d="M0 -26 C7 -18 12 -12 12 -6 C12 0 6 3 0 0 C-6 3 -12 0 -12 -6 C-12 -12 -7 -18 0 -26 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "diamonds": f'<path d="M0 -30 L9 -16 L0 -2 L-9 -16 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
        "clubs": f'<circle cx="0" cy="-20" r="5.5" fill="{accent}"/><circle cx="-7" cy="-12" r="5.5" fill="{accent}"/><circle cx="7" cy="-12" r="5.5" fill="{accent}"/><path d="M-2 -12 L2 -12 L1 -4 L-1 -4 Z" fill="{accent}"/>',
        "spades": f'<path d="M0 -28 C6 -20 13 -14 13 -7 C13 -1 7 2 0 -1 C-7 2 -13 -1 -13 -7 C-13 -14 -6 -20 0 -28 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.4"/>',
    }[suit]
    return f"""
    <g transform="translate({x} {y}) rotate({angle})">
      <rect x="-3" y="0" width="6" height="66" rx="2.6" fill="{GOLD_DEEP}"/>
      <rect x="-1.8" y="0" width="3.6" height="66" rx="1.8" fill="{metal}" opacity="0.9"/>
      {topper}
      <circle cx="0" cy="4" r="4" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.3"/>
      <circle cx="0" cy="-9" r="1.8" fill="{gem}" opacity="0.9"/>
    </g>"""


def _orb(suit: str) -> str:
    metal = SUIT_STYLE[suit][3]
    return f"""
    <g transform="translate(58 194)">
      <circle cx="0" cy="0" r="9" fill="url(#metalGrad)" stroke="{GOLD_DEEP}" stroke-width="1.5"/>
      <path d="M-9 -2 A9 9 0 0 1 9 -2" fill="#FFFFFF" opacity="0.25"/>
      <rect x="-1.4" y="-16" width="2.8" height="6.5" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="0.7"/>
      <rect x="-3.6" y="-14.4" width="7.2" height="2.4" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="0.7"/>
      <ellipse cx="-3" cy="-4" rx="2.4" ry="1.4" fill="#FFFFFF" opacity="0.5"/>
    </g>"""


def _queen_prop(suit: str) -> str:
    accent = SUIT_STYLE[suit][2]
    if suit == "hearts":
        return f"""
    <g transform="translate(56 186) rotate(-14)">
      <rect x="-1.6" y="0" width="3.2" height="46" rx="1.6" fill="#5E4326"/>
      <path d="M0 -14 C6 -8 11 -3 11 2 C11 7 6 10 0 7 C-6 10 -11 7 -11 2 C-11 -3 -6 -8 0 -14 Z"
            fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.3"/>
      <path d="M0 7 L0 14" stroke="#3E7A3E" stroke-width="2.4"/>
    </g>"""
    if suit == "diamonds":
        return f"""
    <g transform="translate(56 192) rotate(-8)">
      <path d="M0 0 C10 -4 22 -4 30 0 C22 3 10 3 0 0 Z" fill="{accent}" opacity="0.9"
            stroke="{GOLD_DEEP}" stroke-width="1.1"/>
      <path d="M0 6 C10 2 22 2 30 6 C22 9 10 9 0 6 Z" fill="{accent}" opacity="0.7"
            stroke="{GOLD_DEEP}" stroke-width="1.1"/>
      <rect x="-2" y="-2" width="4" height="30" rx="2" fill="{GOLD_DEEP}"/>
    </g>"""
    if suit == "clubs":
        return f"""
    <g transform="translate(56 188) rotate(-10)">
      <rect x="-1.8" y="0" width="3.6" height="52" rx="1.8" fill="{GOLD_DEEP}"/>
      <circle cx="0" cy="-8" r="5" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.1"/>
      <circle cx="-6" cy="-1" r="5" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.1"/>
      <circle cx="6" cy="-1" r="5" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.1"/>
    </g>"""
    return f"""
    <g transform="translate(56 190) rotate(-12)">
      <rect x="-1.8" y="0" width="3.6" height="50" rx="1.8" fill="{GOLD_DEEP}"/>
      <path d="M0 -24 C5 -17 11 -12 11 -6 C11 -1 6 2 0 -1 C-6 2 -11 -1 -11 -6 C-11 -12 -5 -17 0 -24 Z"
            fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.3"/>
    </g>"""


def _jack_prop(suit: str) -> str:
    accent = SUIT_STYLE[suit][2]
    if suit == "hearts":
        blade = f'<path d="M0 -34 C-8 -24 -8 -12 0 -4 C8 -12 8 -24 0 -34 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.3"/>'
    elif suit == "diamonds":
        blade = f'<path d="M0 -34 L8 -20 L0 -6 L-8 -20 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.3"/>'
    elif suit == "clubs":
        blade = (
            f'<circle cx="0" cy="-24" r="4.6" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.1"/>'
            f'<circle cx="-6.4" cy="-18" r="4.6" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.1"/>'
            f'<circle cx="6.4" cy="-18" r="4.6" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.1"/>'
        )
    else:
        blade = f'<path d="M0 -34 C5 -27 11 -22 11 -16 C11 -11 6 -8 0 -11 C-6 -8 -11 -11 -11 -16 C-11 -22 -5 -27 0 -34 Z" fill="{accent}" stroke="{GOLD_DEEP}" stroke-width="1.3"/>'
    return f"""
    <g transform="translate(146 190) rotate(13)">
      <rect x="-2.6" y="-6" width="5.2" height="62" rx="2.4" fill="#54575F"/>
      <rect x="-1.5" y="-6" width="3" height="62" rx="1.5" fill="#8A8F99" opacity="0.9"/>
      {blade}
      <circle cx="0" cy="-4" r="3.4" fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.2"/>
    </g>"""


_POSE_MIRROR = {
    ("king", "diamonds"), ("king", "spades"),
    ("queen", "clubs"), ("queen", "spades"),
    ("jack", "hearts"), ("jack", "clubs"),
}

_BEARD_BY_SUIT = {"hearts": "full", "diamonds": "forked", "clubs": "grey", "spades": "pointed"}


def make_court_svg(rank: str, suit: str) -> str:
    """One baroque court illustration; unique per (rank, suit)."""
    robe_a, robe_b, accent, metal, gem, _ = SUIT_STYLE[suit]
    skin = SKIN_BY_SUIT[suit]
    hair = HAIR_BY_SUIT[suit]
    glyph = SUIT_GLYPHS[suit]
    ink = "#B03040" if suit in ("hearts", "diamonds") else "#20242E"
    head_cy = 86
    mirrored = (rank, suit) in _POSE_MIRROR

    if rank == "king":
        body = _king_body(suit)
        headgear = _crown(suit)
        beard = _beard(_BEARD_BY_SUIT[suit], skin)
        left_prop = _orb(suit) + (
            '<ellipse cx="58" cy="198" rx="7" ry="6" fill="' + skin + '" '
            'stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>'
        )
        right_prop = (
            _scepter(suit, 144, 148, 9)
            + '<ellipse cx="142" cy="172" rx="7" ry="6" fill="' + skin + '" '
            'stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>'
        )
        hair_svg = (
            f'<path d="M78 84 C78 62 88 54 100 54 C112 54 122 62 122 84 '
            f'C118 72 110 68 100 68 C90 68 82 72 78 84 Z" fill="{hair}"/>'
        )
    elif rank == "queen":
        body = _queen_body(suit)
        headgear = _diadem(suit)
        beard = ""
        left_prop = _queen_prop(suit) + (
            '<ellipse cx="57" cy="198" rx="6.5" ry="5.5" fill="' + skin + '" '
            'stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>'
        )
        right_prop = (
            _scepter(suit, 146, 150, 8)
            + '<ellipse cx="144" cy="176" rx="6.5" ry="5.5" fill="' + skin + '" '
            'stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>'
        )
        hair_svg = (
            f'<path d="M76 88 C72 110 64 124 56 136 C66 130 74 116 78 100 '
            f'L78 78 Z" fill="{hair}"/>'
            f'<path d="M124 88 C128 110 136 124 144 136 C134 130 126 116 122 100 '
            f'L122 78 Z" fill="{hair}"/>'
            f'<path d="M78 84 C78 62 88 54 100 54 C112 54 122 62 122 84 '
            f'C118 70 110 64 100 64 C90 64 82 70 78 84 Z" fill="{hair}"/>'
        )
    else:
        body = _jack_body(suit)
        headgear = _beret(suit)
        beard = ""
        left_prop = ""
        right_prop = (
            _jack_prop(suit)
            + '<ellipse cx="145" cy="200" rx="6.5" ry="5.5" fill="' + skin + '" '
            'stroke="#10131B" stroke-opacity="0.3" stroke-width="1.2"/>'
        )
        hair_svg = (
            f'<path d="M78 88 C76 66 84 52 100 50 C116 52 124 66 122 88 '
            f'C118 72 110 66 100 66 C90 66 82 72 78 88 Z" fill="{hair}"/>'
            f'<path d="M84 60 C92 54 108 54 116 60 C108 58 92 58 84 60 Z" fill="{hair}"/>'
        )

    pose_open = f'<g transform="translate(200 0) scale(-1 1)">' if mirrored else "<g>"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 280">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FDF9EC"/>
      <stop offset="1" stop-color="#EDE0BE"/>
    </linearGradient>
    <linearGradient id="robe" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{robe_a}"/>
      <stop offset="1" stop-color="{robe_b}"/>
    </linearGradient>
    <linearGradient id="metalGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GOLD_LIGHT}"/>
      <stop offset="0.5" stop-color="{metal}"/>
      <stop offset="1" stop-color="{GOLD_DEEP}"/>
    </linearGradient>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F7D7B2"/>
      <stop offset="1" stop-color="{skin}"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.30"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="artClip"><rect x="20" y="20" width="160" height="240" rx="8"/></clipPath>
  </defs>

  <rect x="3" y="3" width="194" height="274" rx="13" fill="url(#bg)"
        stroke="#C4B58E" stroke-width="2.4"/>
  <rect x="9.5" y="9.5" width="181" height="261" rx="10" fill="none"
        stroke="{GOLD}" stroke-width="1.9" opacity="0.95"/>
  <rect x="14" y="14" width="172" height="252" rx="8" fill="none"
        stroke="{GOLD_DEEP}" stroke-width="1" opacity="0.55"/>
  <rect x="20" y="20" width="160" height="240" rx="8" fill="none"
        stroke="{GOLD}" stroke-width="0.8" opacity="0.5"/>

  <g clip-path="url(#artClip)">
    <rect x="20" y="20" width="160" height="240" fill="url(#halo)"/>
    {_wedge_sunburst(suit)}
    <ellipse cx="100" cy="250" rx="66" ry="9" fill="#3A2E14" opacity="0.18"/>
  </g>

  <g transform="translate(16 16)" opacity="0.6">
    <path d="M0 26 C0 10 10 0 26 0 C16 5 7 14 3 30 Z" fill="{accent}"/>
    <path d="M7 36 C12 20 20 12 36 7 C24 15 17 24 14 39 Z" fill="{GOLD}" opacity="0.85"/>
    <circle cx="4.5" cy="4.5" r="2.6" fill="{GOLD}"/>
  </g>
  <g transform="translate(184 16) scale(-1 1)" opacity="0.6">
    <path d="M0 26 C0 10 10 0 26 0 C16 5 7 14 3 30 Z" fill="{accent}"/>
    <path d="M7 36 C12 20 20 12 36 7 C24 15 17 24 14 39 Z" fill="{GOLD}" opacity="0.85"/>
    <circle cx="4.5" cy="4.5" r="2.6" fill="{GOLD}"/>
  </g>
  <g transform="translate(16 264) scale(1 -1)" opacity="0.6">
    <path d="M0 26 C0 10 10 0 26 0 C16 5 7 14 3 30 Z" fill="{accent}"/>
    <path d="M7 36 C12 20 20 12 36 7 C24 15 17 24 14 39 Z" fill="{GOLD}" opacity="0.85"/>
    <circle cx="4.5" cy="4.5" r="2.6" fill="{GOLD}"/>
  </g>
  <g transform="translate(184 264) scale(-1 -1)" opacity="0.6">
    <path d="M0 26 C0 10 10 0 26 0 C16 5 7 14 3 30 Z" fill="{accent}"/>
    <path d="M7 36 C12 20 20 12 36 7 C24 15 17 24 14 39 Z" fill="{GOLD}" opacity="0.85"/>
    <circle cx="4.5" cy="4.5" r="2.6" fill="{GOLD}"/>
  </g>

  {pose_open}
    {body}
    {left_prop}
    {right_prop}
    <ellipse cx="100" cy="{head_cy}" rx="22" ry="25" fill="{skin}"/>
    {hair_svg}
    {beard}
    {_face(rank, suit)}
    {headgear}
  </g>

  <g>
    <circle cx="34" cy="34" r="12.5" fill="#F6F1E1" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
    <text x="34" y="40" font-size="14" text-anchor="middle" fill="{ink}"
          font-family="Georgia, serif" font-weight="bold">{glyph}</text>
    <circle cx="166" cy="246" r="12.5" fill="#F6F1E1" stroke="{GOLD_DEEP}" stroke-width="1.4"/>
    <text x="166" y="252" font-size="14" text-anchor="middle" fill="{ink}"
          font-family="Georgia, serif" font-weight="bold">{glyph}</text>
  </g>
</svg>
"""
