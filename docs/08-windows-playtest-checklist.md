# Windows Manual Playtest Checklist — Premium Shell

**Project:** Klondike Solitaire — CSC200 DSA Edition
**Interface:** PyQt6 premium shell (default entry point since PR #2)
**Launch module:** `solitaire.main`
**Basis:** Adapted from [Demo and Playtest Guide](07-demo-and-playtest.md) §4 to the premium shell. That guide's §2 (player controls) and §3 (DSA demonstration script) remain the authority for *how* to play and *what to demonstrate*; this checklist is the pass/fail record for the final Windows check.

Automated CI runs 157 tests with Qt's offscreen platform. It verifies game logic, widget behavior, layout at 1280×800, and data provenance — it **cannot** verify mouse feel, screen scaling, animation smoothness, or visual fit on real hardware. Complete this list on the target Windows computer before submission, and record results only for items actually performed.

## 1. Pre-flight

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest          # must end: 157 passed
python -m solitaire.main  # premium shell
```

- [ ] `python -m pytest` reports **157 passed** (113 baseline + 44 premium).
- [ ] `python -m solitaire.main` opens the **premium shell** (navy header with gold medallion logo, emerald felt board, right-hand DSA dashboard).
- [ ] `python -m solitaire.main --legacy` still opens the Phase 4 window (fallback intact).

## 2. Launch and layout

- [ ] Fresh deal renders: stock + waste top-left, four foundations with gold frames, seven tableau columns, Move Log and feedback panel beneath the board, dashboard on the right.
- [ ] Header metric chips show Time `00:00`, Moves `0`, Score `0` before any action.
- [ ] Resize to ~1600×900 (design size) and to 1280×800 (minimum): the header switches to its compact mode, and no button, label, card rank, suit, or dashboard text is clipped or overlapping.
- [ ] **Responsive regression (final UI fix):** on a short screen (1280×720 logical — e.g. 1920×1080 at 150% scaling, or 1366×768) the whole window fits the work area: Game Progress and the pinned **Open DSA Lab** button are visible (the dashboard scrolls internally if needed) and nothing sits permanently below the taskbar.
- [ ] **Settings regression (final UI fix):** in Settings at any window size no label/description is clipped, all six shortcut badges show their full text, the Animation Speed row (slider + value) is complete, and **Deal a New Game** is reachable in the footer without scrolling; at 1600×900 and maximized the page fits with no scrollbar.
- [ ] **Resize-transition regression:** maximize → restore → manually resize → minimize → restore → maximize: the board refits every time, no card lands outside the felt, and no control disappears or stays at stale coordinates.
- [ ] Toggle the dashboard off and on from **Game Mode** (settings gear → switches): the felt regains the released width and the dashboard returns unchanged.
- [ ] Open **Settings → Game Mode**: Draw 1 / Draw 3 mode cards, Reduce-motion switch, dashboard switch, and animation-speed slider are all present and labeled.
- [ ] Return to the play workspace via **Return to Play Workspace**; the board state is unchanged by visiting settings.

## 3. Gameplay and drag/drop

- [ ] Draw one card (click stock or `Space`); the card appears face-up on the waste and Queue/Stock counters update.
- [ ] Start a fresh game in Draw 3 mode (Game Mode → mode card → Deal a New Game); drawing reveals three cards.
- [ ] Drag the top waste card to a legal tableau destination; the card lands committed (no snap-back).
- [ ] Drag a face-up tableau card to another column; the newly exposed card flips face-up automatically.
- [ ] Click a *lower* face-up card in a column and drag: the whole face-up run above it moves as one unit and keeps its order.
- [ ] Drag an Ace (or next rank) to its matching suit foundation; the gold frame accepts it.
- [ ] **Drag-lift feel (regression for the Windows CI fix):** press on a card and hold — the card visibly lifts (up to ~10px) with a soft shadow within ~0.2s of the grab, even if you do not move the mouse; it settles flat again within ~0.2s of the drop.
- [ ] During a drag the lifted run follows the pointer one-to-one (no lag/spring-back) and tilts slightly with horizontal velocity; releasing over a legal target commits the move, releasing over nothing returns the run home.
- [ ] Rapid grab → release → re-grab the same card: no visible jitter or "fighting" between the lift and settle animations, and no card remains stuck lifted after the interaction.
- [ ] Attempt an invalid drop (same color / wrong rank): the move is rejected, an explanatory message appears in the feedback panel, and both piles are visually unchanged.
- [ ] Attempt to drop a non-King sequence on an empty tableau column: rejected.
- [ ] Empty the stock and recycle the waste; drawing continues from the recycled order (recycle is reflected in the Queue page's counters).

## 4. DSA dashboard and Lab (live data only)

- [ ] Latest Operation panel shows only player-perceivable actions (e.g. "Draw — Stock", "Move — Column 3 → Column 4"); it never shows `undo-history` bookkeeping or "Card index updated" noise.
- [ ] Open the DSA Lab (dashboard structure row or navigation): Overview shows five structure cards whose counters derive from the running game.
- [ ] **Array / List** page: deck lifecycle shows create → shuffle → deal (28) → clear, and "Remaining in the stock" matches the real stock count and FIFO order.
- [ ] **Stack** page: pick the waste pile — size, top card, push/pop counts, card order, *Recent events on this pile*, and the *Pile composition* panel (per-suit counts, face up/down) all match the visible cards.
- [ ] **Queue** page: FIFO strip front/rear markers match the stock; the recent-operations table shows 8 real tracker events.
- [ ] **Linked List** page: node chain head/tail match the chosen column; chain integrity reads *valid*; a multi-card run move produces DETACH_RUN / ATTACH_RUN events.
- [ ] **Dictionary** page: 52/52 entries; searching a card ID shows its live zone, pile, position, and face state that match the board.
- [ ] **Timeline** and **Game Stats** pages update with real tracker data and structure filters work.
- [ ] Move Log (player moves) and the Lab's operation timeline (tracker events) remain visibly separate.

## 5. Keyboard, timer, score, victory

- [ ] `Ctrl+Z` / `Ctrl+Y` undo and redo; the Move Log removes (not duplicates) the undone entry and board positions restore.
- [ ] `H` runs a hint; hint selection alone never mutates the game or starts the clock.
- [ ] The timer starts on the **first successful** action (a rejected drag does not start it) and advances each second.
- [ ] Score follows the formula: +10 foundation, +5 waste→tableau, +5 exposing a hidden card; Undo/Redo restores the score exactly.
- [ ] Complete a prepared winning game: the victory banner appears without blocking the window; undoing the winning move removes it; redoing restores it.
- [ ] New Game after moves asks for confirmation: answering **No** keeps the current game; **Yes** deals fresh with score/time reset and the feedback panel back to idle.

## 6. Animations, motion, close and repeat

- [ ] Card travel animates from the source to the committed destination (reduce-motion off); flips animate.
- [ ] **Animation speed regression (final UI fix):** with the slider at **2.0×** card moves, flips and the deal are visibly FASTER than at 1.0× (2.0× halves durations — the old build multiplied and slowed everything down). At 0.5× everything is roughly twice as slow. The deal has no long pauses between cards at any speed.
- [ ] Reduce-motion on: moves apply instantly with the same feedback and DSA trace; animation-speed slider has a visible effect when reduce-motion is off.
- [ ] Close the window while idle and mid-animation: both exit cleanly with no console traceback.
- [ ] Relaunch: fresh deal, zero score/time, no leftovers from the previous session.

## 7. Sign-off

| Field | Value |
|---|---|
| Tester name | |
| Date | |
| Windows version / display scaling | |
| Python version | |
| Commit tested | |
| Items passed | / |
| Items failed or skipped (reasons) | |
| Notes (visual smoothness, mouse feel, lag) | |

Do not mark this checklist complete based on CI alone; record manual results only after performing the items above.
