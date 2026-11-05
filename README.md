# Klondike Solitaire — CSC200 DSA Edition

A Python desktop Klondike Solitaire project designed to demonstrate the five data structures required by the CSC200 project brief: Array/List, Stack, Queue, Linked List, and HashMap/Dictionary.

The approved UI direction uses a green-felt game board, dark navy panels, animated card movement, a move log, and a live DSA monitor. The interface must retain breathing space and keep the playing board visually dominant.

## Project documentation

The six project documents are maintained in [docs/](docs/):

1. [Product Requirements](docs/01-product-requirements.md)
2. [Technical Requirements](docs/02-technical-requirements.md)
3. [Application Flow](docs/03-app-flow.md)
4. [Design Brief](docs/04-design-brief.md)
5. [Backend / Domain Schema](docs/05-backend-schema.md)
6. [Implementation Plan](docs/06-implementation-plan.md)

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
- [x] Unit tests and GitHub Actions CI (75 tests passing on the current branch).

### Phase 4 — Basic PyQt6 User Interface: implemented
- [x] PyQt6 `QMainWindow` with a green-felt board and navy application shell.
- [x] Stock pile, visible waste cards, four suit foundations, and seven tableau columns.
- [x] Click-to-select and click-to-move interactions for tableau and waste cards.
- [x] Draw 1 / Draw 3 selector, New Game, Undo, and Redo controls.
- [x] Move count, non-blocking status feedback, and a separate player Move Log.
- [x] Offscreen UI smoke tests for board rendering and real game-engine interactions.

### Still to implement
- [ ] Drag-and-drop interaction and card movement/flip animations.
- [ ] Live five-structure DSA Monitor and low-level operation history view.
- [ ] Hint, timer/score polish, settings, and final UI validation.

The current branch includes a runnable PyQt6 board. Animation and the expanded DSA Monitor remain later milestones.

## Development setup (Windows PowerShell)

Use Python 3.12 or another version supported by the selected PyQt6 release.

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

Run the desktop game:

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

Verification at Phase 3 completion: **69 passing tests**. The current Phase 4 branch has 75 passing tests including UI smoke tests.


## Phase 4 — User Interface

The basic desktop board is implemented in `src/solitaire/ui/` and starts with `python -m solitaire.main`. It displays the stock, waste, four foundations, and seven tableau columns. Use click-to-select followed by a click on a legal destination; the interface delegates every move to `GameEngine`. Drag-and-drop, animation, and the expanded DSA Monitor are not part of this initial UI milestone. GitHub Actions verifies the board with **75 passing tests**, including the six offscreen UI smoke tests.
