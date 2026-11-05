# Klondike Solitaire — CSC200 DSA Edition

A desktop Klondike Solitaire project designed to demonstrate the five data structures required by the CSC200 project brief: Array/List, Stack, Queue, Linked List, and HashMap/Dictionary.

The approved UI direction uses a green-felt game board, dark navy panels, animated card movement, a move log, and a live DSA monitor. The interface must retain breathing space and keep the playing board visually dominant.

## Project documentation

The six project documents are maintained in [docs/](docs/):

1. [Product Requirements](docs/01-product-requirements.md)
2. [Technical Requirements](docs/02-technical-requirements.md)
3. [Application Flow](docs/03-app-flow.md)
4. [Design Brief](docs/04-design-brief.md)
5. [Backend / Domain Schema](docs/05-backend-schema.md)
6. [Implementation Plan](docs/06-implementation-plan.md)

## Current implementation status

- [x] Requirements and design baseline
- [x] Initial Python package configuration
- [x] Custom doubly linked list
- [x] Linked-list-backed Stack
- [x] Circular-buffer FIFO Queue
- [x] Unit tests for the core structures
- [ ] Card and deck model
- [ ] Initial game setup
- [ ] Klondike move validation and game engine
- [ ] Undo/redo and operation instrumentation
- [ ] PyQt6 board, card animations, and DSA monitor

The project is being implemented in small, testable milestones. The current UI is not yet runnable.

## Development setup (Windows PowerShell)

Use Python 3.12 or another version supported by the selected PyQt6 release.

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

Run the unit tests:

    python -m pytest

## Data-structure design

- The deck is created and shuffled as a Python list.
- The stockpile uses a custom FIFO circular-buffer Queue.
- Tableau columns expose Stack behavior backed by the custom doubly linked list, allowing both top-card operations and linked-list run transfers without duplicate card storage.
- Foundations and the waste pile use Stack behavior.
- A Dictionary index tracks every card's current zone, pile, position, and face state.

See the technical requirements and backend/domain schema documents for the full contracts.
