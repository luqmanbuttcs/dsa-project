# Implementation Plan

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Status:** Ordered execution plan  
**Rule:** Complete and test each milestone before building dependent UI features.

## 1. Delivery strategy

Build the project in dependency order:
1. repository and Python app scaffold;
2. custom data structures;
3. card/deck and initial deal;
4. rules and game engine;
5. undo/redo and operation instrumentation;
6. playable desktop board;
7. synchronized animations and DSA monitor;
8. test, polish, and demonstration readiness.

Do not begin with the full visual interface. A polished board built on unreliable game state will need to be rewritten. The UI should be developed against a tested engine.

## 2. Milestones

### Milestone 0 — Requirements baseline

**Deliverables**
- Product Requirements Document.
- Technical Requirements Document.
- Application Flow.
- Design Brief.
- Backend Schema.
- Implementation Plan.

**Exit criteria**
- All six documents are committed.
- Mandatory PDF requirements are distinguished from design choices and optional features.
- UI breathing-space rules and the Stack/Linked List design decision are recorded.

### Milestone 1 — Project scaffold and custom structures

**Tasks**
- Create Python package layout and virtual environment instructions.
- Add dependency file for the selected PyQt6 release and test tooling.
- Implement custom Node and doubly linked list.
- Implement Stack using the linked-list backing store.
- Implement custom FIFO Queue.
- Define the deck's Array/List representation.
- Add independent unit tests and operation-event hooks.

**Exit criteria**
- Stack passes push/pop/peek/empty/size tests.
- Linked List passes append/remove/detach/attach and link-invariant tests.
- Queue passes FIFO, empty, size, and wraparound tests if applicable.
- DSA counters/events reflect actual method calls.

### Milestone 2 — Cards, deck, and initial deal

**Tasks**
- Implement Suit, Rank, Card, and stable card IDs.
- Generate exactly 52 unique cards.
- Shuffle the deck list.
- Deal seven tableau columns in 1–7 sizes.
- Put 24 remaining cards into stock Queue.
- Create empty waste and foundations.
- Build the Dictionary card index.
- Add a game-state invariant checker.

**Exit criteria**
- Initial setup matches the PDF exactly.
- Tests verify 52 unique cards and correct zone totals.
- Dictionary entries match every actual pile.
- No duplicate active card storage exists.

### Milestone 3 — Rules and core game engine

**Tasks**
- Implement tableau descending/alternating-color validation.
- Implement King-only empty-column rule.
- Implement same-suit ascending foundation validation.
- Implement Draw 1 / Draw 3 and waste behavior.
- Implement card flipping after source removal.
- Implement waste-to-tableau, tableau-to-tableau, and foundation transfers.
- Implement win detection.
- Define and test stock recycle behavior as a configurable assumption.

**Exit criteria**
- Legal and illegal move test matrix passes, including multi-card tableau sequence transfers.
- Failed moves do not mutate state.
- Card count and Dictionary invariants pass after every successful action.
- Deterministic win-state test is detected correctly.

### Milestone 4 — Undo/redo and DSA instrumentation

**Tasks**
- Implement reversible MoveRecord/command objects.
- Implement undo and redo stacks.
- Ensure sequence moves, draws, flips, recycling, and foundation moves can be reversed/reapplied.
- Emit structured OperationEvent and MoveEvent records.
- Aggregate operation counters from real events.
- Group low-level operations under a player action ID.
- Distinguish PLAY, UNDO, REDO, and SETUP contexts.

**Exit criteria**
- Undo restores exact previous logical state.
- Redo reapplies the action exactly.
- New move after undo clears redo.
- Operation history aligns with actual structure calls.
- No operation is counted solely because an animation ran.

### Milestone 5 — Playable PyQt6 desktop board

**Tasks**
- Create QMainWindow and main layout.
- Implement card widgets and green-felt board.
- Render stock, waste, four foundations, and seven tableau columns.
- Add New Game, Draw 1/3, Undo, Redo, Settings, Hint placeholder, timer, and move count.
- Support click/drag interaction and legal destination highlighting.
- Connect all player actions to GameController/GameEngine.
- Keep the DSA panel as a compact visible sidebar.

**Exit criteria**
- The application can be played through the UI without directly editing internal state.
- The game board remains readable at target desktop sizes.
- Invalid moves have understandable feedback.
- Core controls are enabled/disabled correctly.

### Milestone 6 — Card animations and DSA monitor

**Tasks**
- Animate card travel, stock draw, foundation placement, and card flips.
- Synchronize animation with action IDs and emitted operation events.
- Implement the five-structure DSA monitor.
- Add expandable structure detail views:
  - Array/List deck setup;
  - Stack top and size;
  - Queue front/rear and size;
  - Linked-list node chain;
  - Dictionary card lookup.
- Add Latest Operation and DSA Operation History.
- Add separate player Move Log.
- Add Play Mode / DSA Lab presentation states without duplicating the game engine.

**Exit criteria**
- The monitor reports actual data-structure operations.
- A sample legal move shows the correct card at the destination and the correct operation trace.
- A newly exposed card visibly flips and its Dictionary state updates.
- Draw events show Queue dequeue and waste Stack push.
- Reduced-motion mode keeps the operation explanation available.

### Milestone 7 — Optional enhancements and visual polish

**Tasks**
- Implement Hint using legal-move enumeration.
- Define a transparent scoring formula before enabling score.
- Refine settings, keyboard shortcuts, focus states, and tooltips.
- Add sound only if time remains.
- Test resizing, card spacing, panel scrolling, and breathing space.
- Add restart confirmation and a non-blocking win panel.

**Exit criteria**
- Optional features do not destabilize core gameplay.
- No overlapping/clipped controls at target sizes.
- The visual hierarchy keeps the board dominant and monitor readable.

### Milestone 8 — Final validation and demonstration

**Tasks**
- Run all unit, integration, and UI smoke tests.
- Run a full game-flow test.
- Run card-conservation and Dictionary consistency checks after random valid action sequences.
- Demonstrate each required data structure using real player actions.
- Demonstrate undo, redo, and victory.
- Prepare a concise project walkthrough explaining data structures and complexity.

**Exit criteria**
- All mandatory PDF requirements pass.
- Five required data structures can be located in code and demonstrated in the running application.
- No known card duplication/loss/state-index bugs.
- Repository documentation matches implemented behavior.

## 3. Test matrix

| Area | Representative tests |
|---|---|
| Deck | 52 unique IDs; all four suits; all thirteen ranks |
| Initial deal | Column sizes 1–7; 21 face-down; 7 face-up; stock 24 |
| Stack | LIFO order; empty pop handling; peek without removal |
| Queue | FIFO order; draw one; draw three; empty/recycle handling |
| Linked List | head/tail; previous/next; detach/attach run; size invariants |
| Dictionary | lookup each card; update zone/pile/index/face state; no stale entries |
| Tableau rules | opposite color + descending rank; reject same color; King on empty only |
| Foundation rules | Ace starts; same suit ascending; reject wrong suit/rank |
| Card flip | newly exposed hidden card turns face-up exactly once |
| Undo/redo | single move, multi-card sequence, draw, foundation move, flip, recycle |
| Win | all 52 in correct foundations; incomplete state not won |
| Instrumentation | counts equal actual method calls; rejected moves have no mutation events |
| UI | launch, resize, drag/drop, controls, monitor, operation history |

## 4. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Stack and Linked List are implemented as duplicate piles | Use Stack abstraction backed by the custom Linked List; one canonical card store |
| Dictionary becomes stale after moves | Centralize index updates and run invariant checks in tests |
| Undo does not restore face state or order | Use typed reversible commands and state round-trip tests |
| Animation and model state disagree | Engine commits first; UI animates emitted state transition |
| DSA counts are inflated or misleading | Instrument actual methods and group events by action ID |
| UI is crowded | Keep compact monitor by default, use spacing tokens, collapse details before shrinking cards |
| Draw-three waste ordering is wrong | Add deterministic order tests for draw and recycle |
| Optional features delay required work | Complete all core requirements before Hint/Score/Sound polish |

## 5. Work sequencing and commit discipline

Keep commits focused and named by milestone, for example:
- docs: add project blueprint;
- feat: implement linked list and stack;
- feat: implement stock queue and deck setup;
- feat: add Klondike move validation;
- feat: add undo redo and operation events;
- feat: build PyQt6 game board;
- feat: add animated DSA monitor;
- test: cover complete game flow.

After each milestone:
1. run the relevant tests;
2. inspect the diff;
3. update the relevant documentation if behavior changed;
4. commit only a coherent, working increment.

Do not mark a milestone complete just because files exist. Its exit criteria and tests must pass.

## 6. First implementation task

After the six-document baseline is in place, start with the project scaffold and custom data structures. Implement and test Linked List, Stack, Queue, and deck-list behavior before writing the visual board. This is the foundation for all later gameplay and DSA monitoring.



## 7. Implementation progress snapshot

**Latest verified baseline:** `feat/core-data-structures`

Completed and covered by automated tests:
- Custom doubly linked list, including node-preserving run detach/attach.
- Custom Stack abstraction backed by the linked list.
- Custom FIFO circular-buffer Queue.
- Card model and Array/List deck creation/shuffle.
- Exact initial Klondike deal and Dictionary card index.
- Tableau and foundation move validation.
- Draw 1/Draw 3, waste handling, and stock recycling.
- Tableau run moves, waste-to-tableau, and tableau/waste-to-foundation actions.
- Automatic exposed-card flipping and win detection.
- Structured DSA operation events for setup and implemented game actions.

GitHub Actions reports **51 passing tests** on the current implementation branch.

Still pending:
- Undo/Redo stacks and reversible action records.
- PyQt6 board, card widgets, drag/drop, and animation.
- Live DSA monitor presentation, move log, and final UI/resizing/accessibility checks.
- Optional Hint, timer/score behavior, and final demonstration preparation.

This snapshot describes verified implementation status, not a change to the original assignment scope.


### Game-mechanics verification addendum

The latest game-mechanics pass adds/strengthens:
- Multi-card face-up tableau suffix transfer with order preservation.
- Tableau visibility invariant: face-down cards cannot appear above a face-up card.
- Stock cards must remain face-down and waste/foundation cards face-up.
- Foundation invariant: each suit pile is a correctly ordered Ace-first prefix.
- Strict victory check: stock, waste, and all tableau columns must be empty; every foundation must contain exactly Ace through King of its own suit.
- Automated coverage for correct and corrupted foundation states.

Latest confirmed CI result: **51 passed**.
