# Game-Feel & Visual Upgrade — Design Notes

**Project:** Klondike Solitaire — CSC200 DSA Edition
**Branch:** `feat/game-feel-visual-upgrade` (targets `feat/core-data-structures`)
**Scope:** presentation layer only — `src/solitaire/ui/**`, `tools/`, `tests/ui/`.
The domain layer (`src/solitaire/domain`, `src/solitaire/structures`) is untouched;
the board remains a pure projection of the authoritative `GameEngine` state.

## 1. What changed, in one paragraph

The premium casino identity (emerald felt, navy chrome, gold detailing, custom card
artwork) is preserved and elevated with a reserved caption band, tactile card
interaction, coordinated choreography and a restrained ambient layer. Every effect is
cosmetic: it reads game state, never writes it, and every animation reconciles to the
engine-derived layout the moment it is interrupted.

## 2. Stock & Waste caption band (the mandatory layout fix)

The old captions were painted at offsets the Tableau row could cover. Layout now
reserves a fixed scene-space **caption band** (`game_board_scene.LABEL_BAND = 58px`)
under the top pile row; the Stock chip, Waste chip and the *Foundations* caption live
only inside it and the Tableau row starts below it by construction, at every window
size, because the whole board scales uniformly.

The chips are compact premium pills with a luminous accent dot and **genuine dynamic
data**: `STOCK • 24 CARDS`, `WASTE • 3 CARDS`, `STOCK • RECYCLE` when the deck is
exhausted. Regression tests pin the geometry at 1280×800, 1600×900 and 1920×1029
(chip inside the band, clear of the Tableau row, unclipped by the scene edge).

## 3. Tactile card interaction

- **Hover** — the card lifts 4px with a deepening shadow (130ms ease).
- **Selection** — the run floats slightly higher and gains a gold ring (mint while
  dragging).
- **Dragging** — drags are now *manual* (no `QDrag` hand-off): the grabbed run follows
  the pointer one-to-one with a velocity tilt (≤6°), a floating shadow and a breathing
  glow pulse on every legal destination. The card cannot lag the cursor.
- **Invalid drop** — coral flash + shake, then the run flies home; the engine never
  mutated, so `sync` restores the exact authoritative layout.
- **Placement** — landed cards pop with a tiny spring (`settle_pop`).

All micro-animations are `QPropertyAnimation`s parented to their item, so no animation
can outlive its target (the historical exit-134 abort family stays impossible).

## 4. Coordinated choreography

| Action | Experience |
|---|---|
| New Game | 28 tableau cards fly from the Stock in true dealing order (36ms stagger), face-up cards flipping mid-air as they land |
| Draw 1 / Draw 3 | Card(s) travel Stock → Waste; Draw 3 staggers the three arrivals by fan position (60ms steps) |
| Card flip | Horizontal squeeze illusion, face switches at 50% |
| Foundation landing | Radial gold/mint particle burst + slot pulse + chime — fires for drags, click-to-moves and redo replays alike |
| Undo / Redo | Natural reverse/forward motion (the projection animates every zone change) |
| Hint | Pulsing highlight on source cards and destination slot |
| Invalid move | Shake + coral ring, never a state change |
| Victory | Non-blocking golden overlay: confetti, serif VICTORY title, real score/moves/time, New Game / Return to Play; Escape or backdrop click dismisses |

Rapid user actions are safe: a new movement always supersedes the in-flight animation
of the same item, state changes end any active drag first, and `interrupt_all` clears
staggered starts.

## 5. Ambient layer (restrained by design)

- **Lighting** — cached overhead lamp pool, secondary cool pool over the Tableau row,
  edge illumination washes, deepened vignette; all blitted from cached pixmaps.
- **Light sweep** — one 19-second diagonal sheen at ~5% alpha, driven by a scene-owned
  QTimer at ~24fps from a cached gradient band. Toggleable in Game Mode ("Ambient light
  sweep") and automatically off under Reduce Motion.
- **Slots** — recessed wells with contact shadows and a faint bottom bounce light.

## 6. Dashboard feedback & optional sound

- **Metric chips** flash gold (score increase) or mint (any change) for ~0.5s. The
  timer chip never flashes.
- **Sound** — seven tiny procedural WAVs (`tools/generate_audio.py`, stdlib-only,
  ~88KB total: pickup, place, stock slide, flip, foundation chime, invalid buzz,
  victory arpeggio) played via `QSoundEffect` at low volume. A "Sound effects" toggle
  in Game Mode persists the mute choice in `QSettings`. Everything degrades silently
  when QtMultimedia or an audio backend is unavailable — no new Python dependencies.

## 7. DSA Lab

Deliberately left visually quiet: its tables, node diagrams and counters carry the
educational value, so only the application-wide stability and typography improvements
apply. All eight pages and their real OperationTracker data are unchanged.

## 8. Performance & stability

- No full-screen repaints per frame: the sweep is one clipped pixmap blit at 24fps;
  lighting layers are cached; bursts are ≤14 motes for ≤0.7s.
- Reduce Motion skips the deal choreography, drag pulse, bursts, confetti and sweep;
  every interaction stays fully usable.
- The interaction sweep (`tools/interaction_sweep.py`) drives the live event loop
  across card clicks, real press-move-release drags, delivered drops, header buttons,
  Game Mode toggles, victory overlay, all 8 Lab pages, resize and clean close —
  and reports **SWEEP CLEAN** (no exception escaped any slot). 186 automated tests
  pass (`python -m pytest`).

## 9. Review corrections (PR #3 review round)

**Invalid-move sequencing.** The fly-home `sync(animate=True)` used to start
immediately after `invalid_shake()`, and the movement manager's `interrupt_for()`
cancelled the shake before it rendered a single frame. The shake now owns the drop
point first; the return trip is deferred to the shake's `finished` signal behind a
generation counter (`scene._reject_seq`) that any real sync or new drag invalidates —
so feedback can never fight authoritative projection, a re-grab mid-shake never
starts movement animations under the user's hand, and Reduce Motion (no shake)
returns home immediately. Regression tests pin all three paths.

**Victory Escape.** `present()` now takes keyboard focus (StrongFocus) so a real
Escape press reaches the overlay's `keyPressEvent`, and a window-level Escape
shortcut — armed only while the overlay is visible, disarmed by the `dismissed`
signal — dismisses it when focus stays on the board. `new_game()` dismisses a
still-open celebration before dealing. QtTest regression tests cover Escape with
overlay focus, Escape with focus elsewhere, and the disarm cycle.

**End-to-end victory test.** A deterministic test builds a one-move-from-victory
position with the real domain structures (three complete foundations, the spade
King alone on tableau-7), completes the game through the real `GameEngine`, and
asserts the real `game_won` signal opens the overlay with the engine's actual
score, move count and elapsed time. The committed victory screenshot
(`docs/screenshots/pr_13_victory.png`) shows this same real win: score 20,
3 moves, 00:00.

**Visual evidence.** `docs/screenshots/pr_*.png` are captured from the running
application by `scripts/capture_pr_evidence.py` — real engine deals, real QTest
interactions, real win; nothing mocked.
