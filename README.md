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
- [x] Unit tests and GitHub Actions CI (64 tests passing on the current branch).

### Still to implement
- [ ] Full PyQt6 desktop interface.
- [ ] Card drag-and-drop and movement/flip animations.
- [ ] Live DSA Monitor widgets and move/operation history views.
- [ ] Hint, timer/score polish, settings, and final UI validation.

The current branch contains the tested domain/game-engine foundation. The graphical interface is not yet runnable.

## Development setup (Windows PowerShell)

Use Python 3.12 or another version supported by the selected PyQt6 release.

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

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
- Undo restores pile order, stock/waste order, card face states, move history, counters, draw mode, and win status.
- Redo reapplies the saved state; a new successful action clears the redo branch.
- Undo/redo restoration uses the custom Stack, Queue, Linked List, and Dictionary-backed model. Operation events remain append-only and identify PLAY, UNDO, REDO, and HISTORY contexts.

Verification: GitHub Actions reports **64 passing tests** on the current branch.
