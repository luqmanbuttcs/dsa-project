# Technical Requirements Document

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Status:** Implementation baseline  
**Related documents:** 01 Product Requirements, 03 App Flow, 05 Backend Schema

## 1. Technology decisions

The supplied PDF does not prescribe a programming language or GUI framework. The following are project implementation decisions, not instructor requirements.

| Concern | Selected baseline | Reason |
|---|---|---|
| Language | Python 3.12+ | Readable implementation and straightforward testing of custom structures |
| Desktop UI | PyQt6 with QMainWindow | Native desktop application and control over card widgets/animations |
| UI architecture | Qt Widgets; custom-painted/card widgets where useful | Avoid a web-based UI and keep the application desktop-native |
| Tests | pytest | Clear unit and integration tests |
| Persistence | In-memory game state for MVP; optional local JSON preferences/history later | The PDF does not require a database or server |
| Packaging | Python virtual environment; packaging decision deferred | Keep development reproducible before choosing a distribution tool |

Use a Python interpreter for which the selected PyQt6 release provides a compatible wheel. Keep dependency versions in a requirements file once the project scaffold is created. Do not add a web server or cloud database: neither is required by the brief.

## 2. Architecture principles

1. **Domain-first:** Rules and state transitions must not depend on PyQt widgets.
2. **One source of truth:** A card exists in exactly one pile/zone at a time. The dictionary is an index, not a second card store.
3. **Real data structures:** Required structures must be implemented in project code; do not substitute a built-in container and label it a custom implementation.
4. **Observable operations:** Data structures/domain services emit operation events that the DSA monitor consumes.
5. **Atomic moves:** Validate a move before mutating state. A failed move must leave the game unchanged.
6. **Undoable state transitions:** A move should be represented by a reversible command/record.
7. **UI separation:** The UI requests actions from a controller/game engine and renders returned state/events. It must not directly alter pile internals.
8. **Accessible visual design:** Maintain breathing space, readable cards, predictable controls, and a reduced-motion option.

## 3. Required data-structure implementation

### 3.1 Array/List — deck

- Use a Python list as the 52-card deck during creation, shuffling, and dealing.
- Generate exactly one card for each suit/rank pair.
- Shuffle the list with a randomized shuffle operation.
- Deal 28 cards to tableau columns in increasing column sizes (1 through 7); enqueue or transfer the remaining 24 cards into the stock queue.
- The deck list is the setup representation. After dealing, do not keep a second mutable copy of the cards as an active game pile.
- Instrument deck creation, shuffle, and deal actions for the DSA monitor.

### 3.2 Linked List — tableau storage and sequence manipulation

Use a custom **doubly linked list** with Node, previous/next references, head, tail, and size.

Reason for choosing a doubly linked list: a Klondike move may transfer a visible run of multiple cards, not only one top card. Previous and next links make it possible to detach and attach a run while keeping the source and destination chains consistent.

Required linked-list operations:
- append/insert at an end;
- remove from an end;
- locate a node/card when needed;
- detach a contiguous run;
- attach a detached run;
- iterate in display order;
- validate head/tail/previous/next/size invariants.

The UI may draw the tableau from bottom to top or top to bottom, but the internal ordering convention must be documented once and used consistently.

### 3.3 Stack — pile interface

Implement a custom Stack ADT with:
- push;
- pop;
- peek;
- is_empty;
- size.

**Reconciliation of the PDF's Stack and Linked List requirements:** Each tableau column exposes stack behavior for top-card operations while its nodes are stored in the custom doubly linked list. The Stack implementation delegates storage to the linked list. Tableau sequence movement uses explicit linked-list detach/attach operations. Foundations are stacks as required by the PDF; the waste pile and undo/redo histories may also use stacks.

This gives the same cards one canonical storage location while demonstrating both the Stack abstraction and linked-list mechanics. Do not maintain separate Stack and Linked List copies of a tableau column.

### 3.4 Queue — stockpile

Implement a custom FIFO queue for the stockpile. A circular-buffer queue or a list-backed queue with a front index is acceptable; do not use list.pop(0) as the normal dequeue implementation because it shifts remaining entries.

Required operations:
- enqueue;
- dequeue;
- peek/front;
- is_empty;
- size.

Draw 1 or Draw 3 dequeues up to the configured number of cards. Each drawn card is pushed onto the waste stack in draw order; the most recently drawn card is the waste top. The exact recycling policy must remain configurable because the PDF does not specify pass limits.

### 3.5 Dictionary — card index

Maintain a dictionary keyed by stable card ID. Each index entry records:
- zone: stock, waste, tableau, or foundation;
- pile ID: stock, waste, a tableau column ID, or a suit foundation ID;
- position within that pile;
- face-up/face-down state.

The dictionary is an index for lookup and UI explanation. It must not own a second copy of the cards. After any state transition, all affected entries must be updated. Add invariant checks that compare the index against the actual piles.

### 3.6 Undo and redo stacks

Use custom Stack instances for undo and redo history. A successful new action is recorded on undo and clears redo. Undo applies the inverse state change and transfers the history record to redo. Redo reapplies it and returns the record to undo. Undo/redo must include card locations, sequence order, face-up changes, and stock/waste effects.

## 4. Domain model and services

Suggested responsibilities:

| Component | Responsibility |
|---|---|
| Card | Immutable identity/rank/suit plus controlled face-up state |
| DeckFactory | Create and shuffle the 52-card list |
| LinkedList / Node | Tableau node storage and sequence links |
| Stack | LIFO pile abstraction |
| Queue | FIFO stockpile |
| CardIndex | Dictionary mapping card IDs to current location/state |
| GameState | Own stock, waste, tableau, foundations, rules, counters, and status |
| RuleValidator | Answer whether a proposed move is legal without mutating state |
| GameEngine | Apply draw/move/flip/recycle/restart and win-check transitions |
| MoveCommand / MoveRecord | Capture reversible actions for undo/redo |
| OperationTracker | Record real structure operations and aggregate counts |
| GameController | Coordinate engine events with UI requests |
| MainWindow / widgets | Render cards, controls, monitor, and move history |

## 5. Event and monitor contract

Every meaningful action should produce structured events. At minimum, support:
- GameStarted, DeckShuffled, CardsDealt;
- CardDrawn, WasteRecycled;
- MoveValidated, MoveRejected, CardMoved;
- CardFlipped, FoundationUpdated;
- UndoPerformed, RedoPerformed;
- GameWon, GameRestarted.

The DSA monitor should receive lower-level operation records such as:
- ARRAY_CREATE / ARRAY_SHUFFLE / ARRAY_DEAL;
- STACK_PUSH / STACK_POP / STACK_PEEK;
- QUEUE_ENQUEUE / QUEUE_DEQUEUE / QUEUE_PEEK;
- LINKED_LIST_APPEND / REMOVE / DETACH_RUN / ATTACH_RUN;
- DICTIONARY_LOOKUP / INSERT / UPDATE / REMOVE.

Each operation event should contain a monotonically increasing sequence number, timestamp, structure name, operation name, affected card/pile identifiers where relevant, outcome, and an optional parent action ID. Parent IDs let the UI group low-level operations under one player move.

Do not fabricate counts. Counters must be incremented by instrumented methods when they really execute. Failed validation may produce a MoveRejected event, but must not produce card pop/push operations because no mutation occurred.

## 6. Move execution and animation contract

1. UI identifies source and destination.
2. Controller asks RuleValidator to validate the proposed move.
3. If invalid, state is not mutated; UI gives brief, non-blocking feedback.
4. If valid, GameEngine executes an atomic command and emits real operation events.
5. UI animates the changed card/sequence and any newly exposed card.
6. DSA monitor highlights the matching operation events in order.
7. Move log records the player-level action.
8. Win checker evaluates the resulting state.

The model state must not depend on animation completion. Animation is a presentation of an already validated transition. Prevent a second drag/action from corrupting a move while its animation is running; either queue it or temporarily disable conflicting interaction.

## 7. UI and interaction requirements

- Main window: PyQt6 QMainWindow.
- Board: custom card widgets or a board widget with child card widgets.
- Drag and drop: clear source selection, legal destination highlighting, invalid-drop feedback, and keyboard-accessible alternatives.
- Card flip: visually reveal the face without changing the card's identity.
- DSA monitor: compact five-structure overview; expandable detail views and operation history.
- Move log: separate from low-level DSA operation history.
- Controls: New Game, Draw 1/3, Hint (optional), Undo, Redo, Settings, and Game Stats.
- Layout: responsive proportions; no overlapping controls; maintain card readability.
- Breathing space: target 20–24 px outer margins, 12–16 px section gaps, and consistent card gutters. On narrower windows, collapse secondary detail or allow scrolling rather than compressing text/cards beyond readability.
- Animations: use Qt animation facilities with short, consistent durations; provide a reduced-motion setting.
- Avoid modal popups for ordinary invalid moves. Use small inline status feedback.

## 8. Suggested repository structure

    docs/
      01-product-requirements.md
      02-technical-requirements.md
      03-app-flow.md
      04-design-brief.md
      05-backend-schema.md
      06-implementation-plan.md
    src/
      solitaire/
        main.py
        domain/
        structures/
        services/
        ui/
        resources/
    tests/
      unit/
      integration/
      ui/

The exact package/file names can be adjusted during scaffolding, but the separation between domain, structures, services, UI, and tests should remain.

## 9. Quality and test requirements

- Unit-test each custom data structure independently, including empty, one-item, and multi-item states.
- Test list links and size after append, remove, detach, and attach.
- Test queue FIFO order and wraparound if a circular buffer is used.
- Test all legal and illegal move categories.
- Test card conservation: exactly 52 unique cards across all zones after every successful action.
- Test dictionary-to-pile consistency after draw, move, flip, undo, redo, recycle, and restart.
- Test undo/redo round trips by comparing serialized logical states.
- Test that invalid moves do not mutate the state or increment mutation counters.
- Test win detection with a deterministic completed-game state.
- Smoke-test UI launch, resize, drag/drop, keyboard actions, and monitor updates.

## 10. Performance expectations

A 52-card game should feel immediate. Aim for O(1) stack push/pop/peek, O(1) queue enqueue/dequeue, average O(1) dictionary lookup/update, and O(1) linked-list end operations. A sequence transfer should be O(1) once its boundary nodes are known; locating a selected node may be O(n). Do not optimize at the expense of clarity for a 52-card deck.

## 11. Technical decisions deliberately deferred

- Exact PyQt6 version pin and packaging tool.
- Exact score formula; the PDF only says a scoring mechanism is optional.
- Hint strategy; the PDF only asks for a suggestion of valid moves.
- Stock recycle/pass limit.
- Whether local game history/preferences need persistence.
- Final minimum window dimensions after the first visual prototype.



## 12. Phase implementation mapping

The source code implementing the instructor's first two phases is:

| Instructor phase | Implementation |
|---|---|
| Phase 1 — Card | `src/solitaire/domain/card.py` |
| Phase 1 — Deck creation and shuffle | `src/solitaire/domain/deck.py` |
| Phase 1 — Initial deal | `create_new_game()` in `src/solitaire/domain/game_state.py` |
| Phase 2 — Tableau pile | `TableauColumn` in `src/solitaire/domain/game_state.py` |
| Phase 2 — Stack operations | `src/solitaire/structures/stack.py` |
| Phase 2 — Linked-list node/run operations | `src/solitaire/structures/linked_list.py` and `TableauColumn.detach_run_from()/attach_run()` |
| Phase 2 — Foundation piles | `GameState.foundations`, a suit-keyed dictionary of custom Stack instances |
| Phase 2 — Card movement | `src/solitaire/domain/game_engine.py` |
| Phase 2 — Rule validation | `src/solitaire/domain/rules.py` |

Tableau columns expose a Stack interface backed by the custom doubly linked list. This is intentional: Stack operations provide LIFO pile semantics, while linked-list node splicing moves a complete face-up suffix without copying cards or keeping duplicate stores. Foundation piles are Stack instances; the Stack implementation also uses the linked-list implementation as its backing storage.
