"""Generate the bundled UI sound set as tiny WAV files (stdlib only).

Sounds are short, soft and lo-fi by design: card picks, placements, a
stock slide, a flip, a foundation chime, a gentle invalid buzz and a
victory arpeggio. 22.05 kHz mono 16-bit keeps every file under ~40 KB.
Run once:  python tools/generate_audio.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

RATE = 22_050
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "solitaire" / "ui" / "premium" / "resources" / "audio"


def _envelope(index: int, total: int, attack: float = 0.008, release: float = 0.35) -> float:
    """Perceptual envelope: fast attack, exponential-ish release."""
    t = index / RATE
    duration = total / RATE
    attack_samples = max(1, int(attack * RATE))
    if index < attack_samples:
        return index / attack_samples
    remaining = max(0.0, 1.0 - (t - attack) / max(0.001, duration - attack))
    return remaining ** (1.0 / max(0.05, release * 3.0))


def _render(name: str, duration: float, generator) -> None:
    total = int(duration * RATE)
    frames = bytearray()
    for index in range(total):
        t = index / RATE
        sample = max(-1.0, min(1.0, generator(t, index, total)))
        frames += struct.pack("<h", int(sample * 32767 * 0.9))
    path = OUT_DIR / f"{name}.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(bytes(frames))
    print(f"  {path.name}: {len(frames) / 1024:.1f} KB")


def noise_burst(t, index, total, *, cutoff: float = 0.35, brightness: float = 2600.0):
    """Filtered noise burst — paper/foam 'tick' of cards handling."""
    import random

    rng = random.Random(7)
    state = getattr(noise_burst, "_state", None)
    if state is None:
        state = noise_burst._state = 0.0
    # One-pole low-pass gives a soft 'thock' rather than white hiss.
    alpha = min(0.95, 2 * math.pi * brightness / RATE)
    value = rng.uniform(-1.0, 1.0)
    noise_burst._state = state = state + alpha * (value - state)
    body = 120.0 * math.exp(-t * 22.0) * math.sin(2 * math.pi * 165 * t)
    return (state * 0.9 + body * 0.35) * _envelope(index, total, 0.002, 0.5)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating bundled UI audio...")

    def card_pick(t, index, total):
        return 0.55 * noise_burst(t, index, total, brightness=3400.0)

    _render("card_pick", 0.09, card_pick)

    def card_place(t, index, total):
        body = 0.5 * math.sin(2 * math.pi * (210 - 60 * t) * t) * math.exp(-t * 26.0)
        return body + 0.4 * noise_burst(t, index, total, brightness=1800.0)

    _render("card_place", 0.12, card_place)

    def stock_draw(t, index, total):
        sweep = math.sin(2 * math.pi * (500 + 900 * t) * t) * 0.12
        return sweep + 0.5 * noise_burst(t, index, total, brightness=2600.0)

    _render("stock_draw", 0.13, stock_draw)

    def card_flip(t, index, total):
        flick = math.sin(2 * math.pi * (900 - 400 * t) * t) * 0.2 * math.exp(-t * 30.0)
        return flick + 0.45 * noise_burst(t, index, total, brightness=3200.0)

    _render("card_flip", 0.1, card_flip)

    def foundation(t, index, total):
        # Two-partial chime: warm major third with shimmer.
        base = 523.25  # C5
        partials = ((1.0, 0.42), (1.26, 0.22), (2.0, 0.12))
        value = sum(amplitude * math.sin(2 * math.pi * base * ratio * t) for ratio, amplitude in partials)
        return value * _envelope(index, total, 0.004, 0.55) * 0.8

    _render("foundation", 0.5, foundation)

    def invalid(t, index, total):
        buzz = math.sin(2 * math.pi * 132.0 * t) + 0.4 * math.sin(2 * math.pi * 99.0 * t)
        wobble = 1.0 - 0.25 * math.sin(2 * math.pi * 26.0 * t)
        return 0.32 * buzz * wobble * _envelope(index, total, 0.006, 0.4)

    _render("invalid", 0.16, invalid)

    def victory(t, index, total):
        # Rising arpeggio C5-E5-G5-C6 with chime tails.
        notes = (523.25, 659.25, 783.99, 1046.5)
        note_index = min(3, int(t / 0.16))
        local_t = t - note_index * 0.16
        frequency = notes[note_index]
        value = 0.4 * math.sin(2 * math.pi * frequency * local_t)
        value += 0.18 * math.sin(2 * math.pi * frequency * 2.0 * local_t)
        tail = math.exp(-local_t * 7.0)
        return value * tail * 0.85

    _render("victory", 0.95, victory)

    print("done.")


if __name__ == "__main__":
    main()
