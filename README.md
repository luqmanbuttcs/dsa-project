# Klondike Solitaire — CSC200 DSA Edition

A Python desktop Klondike Solitaire project designed to demonstrate the five data structures required by the CSC200 project brief: Array/List, Stack, Queue, Linked List, and HashMap/Dictionary.

The approved UI direction uses a green-felt game board, dark navy panels, animated card movement, a move log, and a live DSA monitor. The interface must retain breathing space and keep the playing board visually dominant.

## Project documentation

The project documentation is maintained in [docs/](docs/):

1. [Product Requirements](docs/01-product-requirements.md)
2. [Technical Requirements](docs/02-technical-requirements.md)
3. [Application Flow](docs/03-app-flow.md)
4. [Design Brief](docs/04-design-brief.md)
5. [Backend / Domain Schema](docs/05-backend-schema.md)
6. [Implementation Plan](docs/06-implementation-plan.md)
7. [Demo and Playtest Guide](docs/07-demo-and-playtest.md)

## Implementation status

### Implemented and tested
- [x] Custom doubly linked list with detach/attach run operations.
- [x] Custom Stack ADT backed by the linked list.
- [x] Custom FIFO Queue using a resizable circular buffer.
- [x] Card, Suit, Rank, and stable card IDs.
- [x] Array/List deck creation and shuffle.
- [x] Exact initial Klondike deal: tableau sizes 1–7 and 24-card stock.
- [x] Dictionary index for card zone, pile, position, and face state.
- [x] Tableau descending/alternating-color and King-to-empty-column rules.
- [x] Foundation Ace-to-King same-suit rules.
- [x] Draw 1 / Draw 3, waste pile handling, and stock recycling.
- [x] Tableau run transfer, waste-to-tableau, and tableau/waste-to-foundation moves.
- [x] Automatic face-up flip of a newly exposed tableau card.
- [x] Win detection only when all four foundations contain complete, correctly ordered Ace-to-King suit sequences (52 cards total).
- [x] Undo and redo using two custom Stack history piles and complete logical game snapshots.
- [x] Structured DSA operation tracker for setup and game actions.
- [x] Legal move hints generated from the current face-up game state.
- [x] Timer that starts on the first successful action, pauses at victory, and survives undo/redo without rewinding.
- [x] Performance scoring: +10 for a foundation move, +5 for waste-to-tableau, and +5 for exposing a face-down tableau card.
- [x] Unit tests and GitHub Actions CI (**111 tests passed** on November 5, 2026; [run #41997048543](https://github.com/luqmanbuttcs/dsa-project/actions/runs/41997048543)).

### Phase 4 — Basic PyQt6 User Interface: implemented
- [x] PyQt6 `QMainWindow` with a green-felt board and navy application shell.
- [x] Stock pile, visible waste cards, four suit foundations, and seven tableau columns.
- [x] Click-to-select and click-to-move interactions for tableau and waste cards.
- [x] Draw 1 / Draw 3 selector, New Game, Undo, Redo, and Hint controls.
- [x] Move count, score, elapsed-time display, non-blocking status feedback, and a separate player Move Log.
- [x] Drag-and-drop from Waste/Tableau to legal Tableau/Foundation targets through GameEngine validation.
- [x] Gold-highlighted legal destinations, animated card travel, stock draw, and face-up reveal transitions.
- [x] Reduced-motion option, keyboard shortcuts, restart confirmation, and non-modal victory banner.
- [x] Live five-structure DSA Monitor with current state, expandable structure details, latest action summary, and timestamped low-level operation history.
- [x] Offscreen UI tests for drag/drop acceptance/rejection, animations, monitor events, victory banner, keyboard shortcuts, and resizing.

### Phase 5 — Premium Casino PyQt6 UI rebuild: implemented on `feat/premium-pyqt6-ui-rebuild`
- [x] Full presentation-layer rebuild in `src/solitaire/ui/premium/` (PyQt6 `QWidget` + `QGraphicsView`/`QGraphicsScene` hybrid; no Tkinter, Pygame, web, or QML).
- [x] Casino art direction: emerald felt with cached weave texture and vignette, full-width deep-navy header with spade logo, CSC200 DSA Edition badge, gold Time/Moves/Score metric chips, and Hint / Undo / Redo / Settings actions.
- [x] Fixed right dashboard (410 px = 25.6% of the 1600 px design width) with live structure counts, latest OperationTracker event, recent player moves, and foundation progress.
- [x] Vector card art generated at build time into local SVG assets (single central suit illustration for A–10, unique court artwork for J/Q/K, royal-blue card backs with a spade crest); rendered through SVG + QPainter, fully offline at runtime.
- [x] 116×160 px cards, 8 px spacing system, Stock + Waste top-left, four Foundations top-right, seven tableau columns, Move Log + feedback panel beneath the board.
- [x] `GameController` is the only boundary to the untouched domain layer; every move is delegated to `GameEngine`, QGraphicsItems never mutate game state, and the scene re-projects the authoritative `GameState` after every action.
- [x] Dedicated full-screen DSA Lab workspace: Overview, Array/List, Stack, Queue, Linked List, Dictionary, Operation Timeline, and Game Stats pages — every number read from the live `OperationTracker` and piles, nothing simulated.
- [x] `CardAnimationManager` (move 220 ms, flip 200 ms, hint pulse, invalid shake) that never blocks engine state, plus a Reduce Motion option and persisted animation-speed setting.
- [x] Responsive board layout: the emerald felt table fills the whole game viewport at every supported size (no letterbox bands), the multi-layer gold/brass frame has a bevelled inner edge, and tableau fan spacing adapts to the available height. Cards never shrink inside the scene; a mild uniform scale applies only below the minimum full-size footprint.
- [x] Upgraded deck artwork: richer suit illustrations, twelve individualised court figures (distinct headgear, held attributes, suit palettes and embroidered robes for every rank × suit), and a baroque royal-blue back with lattice, corner scrollwork, petal ring and central spade crest.
- [x] Premium header (minted gold medallion logo, zone separators, gradient chips) with a compact mode that guarantees no clipping at 1280×800.
- [x] Dashboard upgrade: per-structure icons and live count badges (click a row to inspect it in the DSA Lab), a player-facing Latest Operation panel (internal HISTORY bookkeeping is never shown), a vertical Recent Player Moves timeline and a gold foundation-progress meter.
- [x] Game Mode page: Draw 1 / Draw 3 mode cards, Reduce-motion and dashboard switches, animation-speed slider, Deal a New Game and Return to Play Workspace.
- [x] DSA Lab dashboard overhaul: overview metric cards + structure card grid with live previews, deck-lifecycle visualisation (array), vertical bottom→top stack viewer with TOP badge and pile selector, FRONT/REAR queue strip, expanding node diagram, searchable/filterable dictionary table and filterable event timeline.
- [x] Functional defect fixes with regression tests: CI exit-134 GC abort during undo/redo (deterministic teardown + animation lifecycle guards), real QDrag initiation from card items, multi-card run selection from any face-up tableau card, the game clock no longer starts on rejected moves, the Latest Operation panel no longer shows HISTORY bookkeeping, and the Move Log no longer duplicates moves after undo. The merged UI carries **157 passing tests** (113 baseline + 44 premium).

### Remaining before submission
- [x] Review and merge the `feat/premium-pyqt6-ui-rebuild` pull request (#2, merge commit `15442c7`), then switch the main entry point (`python -m solitaire.main`) to the premium shell.
- [ ] Complete the manual Windows playtest checklist (see the premium-shell checklist in [Windows Manual Playtest Checklist](docs/08-windows-playtest-checklist.md), adapted from the [Demo and Playtest Guide](docs/07-demo-and-playtest.md)).
- [ ] Capture final screenshots and prepare the live demonstration.

## Running the game

`python -m solitaire.main` launches the premium shell by default:

    python -m solitaire.main

The legacy Phase 4 window remains available as a fallback:

    python -m solitaire.main --legacy

## Development setup (Windows PowerShell)

Use Python 3.12 or another version supported by the selected PyQt6 release.

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

Run the desktop game (premium shell by default; add `--legacy` for the Phase 4 window):

    python -m solitaire.main

Run the unit tests:

    python -m pytest

## Data-structure design

- **Array/List:** temporary 52-card deck for creation, shuffle, and deal.
- **Queue:** custom FIFO circular-buffer queue for the stockpile.
- **Stack:** custom LIFO abstraction for tableau, foundation, and waste piles.
- **Linked List:** custom doubly linked nodes underpin tableau columns; runs can be detached and attached without copying card objects.
- **Dictionary:** card ID to current zone, pile, position, and face state.

Tableau stacks are backed by the custom linked list. This gives tableau columns Stack behavior while preserving one canonical set of card nodes rather than maintaining duplicate card copies.

The operation tracker records events after real methods/actions execute. It is not a simulated counter layer.


## Phase 1 and Phase 2 completion

The instructor's Card and Deck phase and Tableau and Foundation phase are implemented on `feat/core-data-structures`.

- Phase 1: Card exposes suit, rank, and face-up/down state; the deck factory creates, validates, and shuffles the complete standard 52-card list.
- Phase 2: Tableau columns expose Stack operations backed by custom doubly linked-list nodes; complete face-up runs can be detached/attached without copying cards; four suit foundations are Stack piles; game-engine methods implement tableau, waste, and foundation transfers.

## Phase 3 — Game Logic: complete

- Move validation rejects illegal tableau and foundation moves before changing piles.
- Draw 1 / Draw 3 uses the FIFO stock Queue; recycling waste is treated as one atomic player action.
- Newly exposed tableau cards flip face-up and the Dictionary is refreshed.
- Undo restores pile order, stock/waste order, card face states, move history, move count, score, and win status while preserving elapsed time and the current Draw 1 / Draw 3 preference.
- Redo reapplies the saved state; a new successful action clears the redo branch.
- Undo/redo restoration uses the custom Stack, Queue, Linked List, and Dictionary-backed model. Operation events remain append-only and identify PLAY, UNDO, REDO, and HISTORY contexts.

Historical checkpoints: 69 tests at Phase 3 completion and 75 tests at the initial Phase 4 UI baseline. The final completed branch now has 111 passing tests (link below).


## Phase 4 — User Interface

The desktop board in `src/solitaire/ui/` starts with `python -m solitaire.main`. It displays stock, waste, four foundations, and seven tableau columns; supports click-to-move and drag-and-drop; animates card travel and reveals; and provides a collapsible live DSA Monitor. All moves are delegated to `GameEngine`, so invalid drops do not mutate game state. Use the [Demo and Playtest Guide](docs/07-demo-and-playtest.md) for controls and manual validation.


## Validation and Testing

The automated suite now covers the assignment's validation checklist:

- **Legal moves:** alternating colors, sequential tableau ranks, valid face-up runs, King-only empty-column moves, and same-suit ascending foundations.
- **Rejected moves:** same-color destinations, wrong ranks, malformed runs, and face-down selections are rejected without changing pile order, the Dictionary, or the move count.
- **Card flipping:** moving a card from a tableau exposes and flips the newly uncovered card; its Dictionary entry and operation event are checked.
- **Win condition:** four complete, ordered suit foundations are required. A deterministic four-King endgame test verifies the final legal moves, win status, and undo/redo of the victory transition.
- **Game flow:** fresh-game initialization is checked for 52 unique cards, 28 tableau cards, 24 stock cards, seven columns, and the required face-up/down arrangement. The endgame test then exercises legal completion through the engine.

GitHub Actions confirms **111 passing tests** on November 5, 2026: [final expanded test run #41997048543](https://github.com/luqmanbuttcs/dsa-project/actions/runs/41997048543).


## Keyboard controls

| Shortcut | Action |
|---|---|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+N` | New Game (asks before discarding a played game) |
| `H` | Show the next legal-move hint |
| `Space` | Draw from Stock |

Use the **DSA Monitor** button to show or hide the five-structure monitor. Enable **Reduce motion** to skip card travel/flip animations while retaining game feedback and operation history.

## Final project walkthrough

See [Demo and Playtest Guide](docs/07-demo-and-playtest.md) for the five data-structure demonstration sequence, feature walkthrough, and Windows manual checklist.
