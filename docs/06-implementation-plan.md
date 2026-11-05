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
- [x] Create QMainWindow and main layout.
- [x] Implement card widgets and green-felt board.
- [x] Render stock, waste, four foundations, and seven tableau columns.
- [x] Add New Game, Draw 1/3, Undo, Redo, Hint, timer, score, and move count.
- [x] Support click/drag interaction and legal destination highlighting.
- [x] Connect all player actions to GameEngine.
- [x] Keep the DSA panel as a compact, collapsible right-side dock.

**Exit criteria**
- The application can be played through the UI without directly editing internal state.
- The game board remains readable at target desktop sizes.
- Invalid moves have understandable feedback.
- Core controls are enabled/disabled correctly.

### Milestone 6 — Card animations and DSA monitor

**Tasks**
- [x] Animate card travel, stock draw, foundation placement, and card flips.
- [x] Synchronize visual transitions with the committed GameEngine state and action operation events.
- [x] Implement the five-structure DSA monitor.
- [x] Add expandable structure detail views:
  - Array/List deck setup;
  - Stack top and size;
  - Queue front/rear and size;
  - Linked-list node chain;
  - Dictionary card lookup.
- [x] Add Latest Operation and timestamped DSA Operation History.
- [x] Add a separate player Move Log.
- [x] Add Play Mode / DSA Lab states through the collapsible monitor dock, without duplicating the game engine.

**Exit criteria**
- The monitor reports actual data-structure operations.
- A sample legal move shows the correct card at the destination and the correct operation trace.
- A newly exposed card visibly flips and its Dictionary state updates.
- Draw events show Queue dequeue and waste Stack push.
- Reduced-motion mode keeps the operation explanation available.

### Milestone 7 — Optional enhancements and visual polish

**Tasks**
- [x] Implement Hint using legal-move enumeration.
- [x] Define and document a transparent scoring formula before enabling score.
- [x] Add an elapsed-time display that starts on the first successful action and pauses at victory.
- [x] Verify that undo/redo restores score but does not rewind elapsed real time.
- [x] Refine settings, keyboard shortcuts, focus states, and tooltips (including Reduce motion).
- [ ] Add sound only if time remains (not needed for the assignment).
- [x] Test minimum-size resizing, card spacing, panel scrolling, and monitor show/hide behavior in offscreen Qt tests.
- [x] Add restart confirmation and a non-blocking victory banner.
- [ ] Complete the final visual/mouse-feel checks on the target Windows display.

**Exit criteria**
- Optional features do not destabilize core gameplay.
- No overlapping/clipped controls at target sizes.
- The visual hierarchy keeps the board dominant and monitor readable.

### Milestone 8 — Final validation and demonstration

**Tasks**
- [x] Run all unit, integration, and UI smoke tests in GitHub Actions.
- [x] Run deterministic initial-deal and endgame flow tests through GameEngine.
- [x] Run seeded random legal-action sequences and assert card conservation and Dictionary consistency after every action.
- [x] Document how to demonstrate each required data structure through real player actions.
- [x] Test Undo, Redo, victory, and Undo/Redo animation state restoration.
- [x] Prepare the project walkthrough and Windows playtest checklist in `docs/07-demo-and-playtest.md`.
- [ ] Complete the manual playtest on the user's Windows machine.

**Exit criteria**
- [x] All mandatory PDF requirements are implemented and covered by automated tests.
- [x] Five required data structures can be located in code and demonstrated in the running application.
- [x] Seeded legal-action tests preserve all 52 unique cards and exact Dictionary consistency.
- [x] Repository documentation matches implemented behavior.
- [ ] Final screen-scaling and real mouse drag/drop check on Windows is completed by the project owner.

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

**Active branch:** `feat/core-data-structures`  
**Pull request:** [#1](https://github.com/luqmanbuttcs/dsa-project/pull/1) (draft, open, not merged)

Completed and covered by automated tests:
- Custom doubly linked list, Stack, and FIFO circular-buffer Queue.
- Card/Deck model, 52-card Array/List, exact initial deal, and Dictionary card index.
- Tableau and foundation movement, legal-move validation, stock recycling, card flipping, and strict victory.
- Full-state Stack-based Undo/Redo, including score and move-state restoration.
- Non-mutating legal Hint enumeration and Hint UI.
- Monotonic session timer and documented scoring.
- PyQt6 game board with click-to-move and drag-and-drop routes for Tableau and Foundation targets.
- Legal-destination preview; rejected drops preserve all piles and Dictionary entries.
- Animated card travel, Draw 1/Draw 3 presentation, and exposed-card flip; Undo/Redo also animate visible card moves.
- Reduced-motion setting, keyboard shortcuts, New Game discard confirmation, and non-blocking victory banner.
- Live five-structure DSA Monitor with current size/state, structure details, latest action breakdown, timestamped event history, and separate player Move Log.
- Responsive minimum-size/scroll tests, deterministic endgame tests, and seeded random legal-action invariant tests.

**Manual verification still belongs to the project owner:** real mouse drag/drop feel, screen scaling, clipped controls, and visual smoothness need to be checked on the target Windows display using `docs/07-demo-and-playtest.md`. Offscreen CI is not a substitute for that check.

### Game-mechanics verification addendum

The latest game-mechanics pass adds/strengthens:
- Multi-card face-up tableau suffix transfer with order preservation.
- Tableau visibility invariant: face-down cards cannot appear above a face-up card.
- Stock cards must remain face-down and waste/foundation cards face-up.
- Foundation invariant: each suit pile is a correctly ordered Ace-first prefix.
- Strict victory check: stock, waste, and all tableau columns must be empty; every foundation must contain exactly Ace through King of its own suit.
- Automated coverage for correct and corrupted foundation states.

Latest confirmed CI result: **69 passed**.


## 8. Phase 1 and Phase 2 implementation status

**Completed on `feat/core-data-structures`:**

### Phase 1 — Card and Deck
- Card entity holds Suit, Rank, and face_up state.
- Card validates its suit/rank/visibility attribute types.
- DeckFactory creates the 52 unique suit/rank combinations.
- DeckFactory validates the exact standard deck before shuffling.
- Shuffling operates in place on the Array/List representation.
- Initial deal produces seven tableau piles sized 1 through 7, with only each pile's last card face-up, and 24 cards in stock.

### Phase 2 — Tableau and Foundation
- TableauColumn exposes Stack operations for push/pop/peek.
- Its Stack uses the custom doubly linked list as the canonical node storage.
- TableauColumn has explicit detach-run and attach-run methods.
- Foundations are four suit-keyed Stack piles.
- GameEngine implements tableau-to-tableau, waste-to-tableau, tableau-to-foundation, and waste-to-foundation movement.
- Move validation checks rank/color/suit rules and rejects invalid moves before mutation.
- Exposed cards flip face-up and the Dictionary index is refreshed after successful movement.

**Validation:** GitHub Actions reports **69 passing tests** for the current phase implementation. The PyQt6 UI and related interaction/monitor work remain later milestones.


## 9. Phase 3 — Game Logic implementation status

**Completed on `feat/core-data-structures`:**

- Existing `RuleValidator` and `GameEngine` validate tableau and foundation actions before mutation.
- Stock supports Draw 1 / Draw 3 through the FIFO Queue, including waste recycling.
- Newly exposed tableau cards are flipped face-up and their Dictionary locations are refreshed.
- A frozen `GameSnapshot` captures card IDs by zone/pile, exact pile order, each card's face state, game status, move count, score, and the minimal move-log tail needed for round-trip restoration.
- The custom `undo_stack` and `redo_stack` hold snapshots. Undo/redo rebuild zones through the project's actual Stack and Queue methods and restore linked-list-backed tableau columns.
- Undo also works after a win; redo can restore the WON state.
- A new successful move after undo clears the redo branch. Failed moves do not create undo entries.
- The operation log remains append-only. Undo and redo emit their own action contexts; internal history-stack maintenance is recorded separately so it does not pollute a player's move-level trace.
- Undo does not rewind elapsed real time or override the current Draw 1 / Draw 3 preference; those are not card-move state.

**Verification:** GitHub Actions completed with **69 passing tests**. New coverage includes tableau move/flip round trips, Draw 3 order and face state, stock recycle round trips, foundation movement, redo invalidation, empty-history behavior, multi-action undo/redo, and multi-card sequence restoration.

**Still pending:** PyQt6 desktop interface, card interaction/animations, visible DSA monitor, final UI smoke tests, and optional enhancements.


## 10. Phase 4 — Basic User Interface implementation status

**Completed on `feat/core-data-structures`:**
- Added the application entry point: `python -m solitaire.main`.
- Added a PyQt6 `QMainWindow` with the approved navy/green-felt visual direction and deliberate outer spacing.
- Rendered the stock pile, up to three visible waste cards, four suit foundations, and seven tableau columns.
- Added click-to-select and click-to-move for face-up tableau sequences and the top waste card.
- Added stock Draw 1 / Draw 3 selection, New Game, Undo, Redo, move count, inline status feedback, and a separate player Move Log.
- Kept all state mutation inside `GameEngine`; widgets render the domain state and request engine actions.
- Added offscreen Qt smoke tests and installed the Qt system runtime libraries in GitHub Actions.

**Not included in this basic UI milestone:** drag-and-drop, card movement/flip animations, and the expanded live DSA Monitor. Those remain later UI/monitor milestones.

**Entry point:** `python -m solitaire.main`

**Phase 4 verification:** GitHub Actions passes **75 tests**, including six offscreen PyQt6 UI smoke tests. Latest confirmed run: https://github.com/luqmanbuttcs/dsa-project/actions/runs/41991249772


## 11. Validation and Testing — completed

Automated integration and unit tests now cover the requested validation checklist:

- Legal tableau moves require descending sequential ranks and alternating colors. Multi-card runs are checked internally as well as against the destination.
- Illegal tableau moves cover same-color targets, incorrect destination ranks, same-color cards inside a selected run, and face-down source cards. Tests assert that rejected actions do not mutate piles, Dictionary locations, or move count.
- Tableau movement tests verify that the newly exposed card turns face-up, its Dictionary entry updates, and exactly one corresponding flip event is recorded.
- Foundation tests verify same-suit Ace-first ascending order through actual engine actions.
- Win-condition tests verify that the game is not won before all four Kings reach their correct foundations; the final move sets WON. Undo and redo restore the state on either side of the victory transition.
- Game-flow tests verify new-game initialization (52 unique cards, 28 tableau, 24 stock, seven columns, and correct visibility) and a deterministic four-King endgame played through GameEngine.

**Deterministic endgame note:** a random shuffled Klondike deal is not guaranteed to be solvable. The win-flow test therefore uses a valid, deterministic near-complete endgame state to test the final legal moves and win transition. It does not pretend to solve a random shuffle automatically.

**Verification:** GitHub Actions reports **85 passing tests** across unit, integration, and offscreen UI coverage. Latest successful run: https://github.com/luqmanbuttcs/dsa-project/actions/runs/41991955530


## 12. Bonus Features — implemented

The optional Undo/Redo, Hint, Timer, and Scoring features are implemented on the active feature branch.

### Undo/Redo
- The existing two custom Stack history piles remain the single undo/redo mechanism.
- Score is part of each logical game snapshot, so undo restores the prior score and redo restores the earned score.
- Elapsed real time and the Draw 1 / Draw 3 preference are deliberately not rewound by undo/redo.

### Hint system
- `GameEngine.find_hints()` enumerates legal moves using the same `RuleValidator` used by real player actions.
- The hint list prioritizes foundation moves, then waste-to-tableau moves, then tableau moves that expose a hidden card, followed by other legal tableau rearrangements.
- When no visible move is legal, it suggests drawing from Stock or recycling Waste.
- Hint generation is read-only: it does not move cards, change the Dictionary, increment the move count, or append operation/history events.
- The PyQt6 Hint control selects the suggested source card and explains the destination. Repeated clicks cycle through the current legal suggestions.

### Timer and scoring
- The timer begins after the first successful player action, not while the player is idle on a new deal.
- It pauses when all cards reach the foundations, resumes if the final winning move is undone, and resets on New Game.
- The timer is based on a monotonic clock and the elapsed seconds are not part of the undo snapshot.
- Scoring is intentionally simple and disclosed in the UI/documentation:
  - +10 points for a card moved to a foundation.
  - +5 points for moving the Waste top card to the Tableau.
  - +5 points when a move turns over a newly exposed face-down Tableau card.
  - 0 points for stock draws and ordinary tableau rearrangements.
- These rules avoid awarding repeatable points for cycling the same tableau move.

### Verification
- Added unit coverage for legal hint enumeration, hint prioritization, stock-draw fallback, non-mutating hints, score awards, and score undo/redo restoration.
- Added offscreen UI coverage for Hint selection, the visible score, timer progression, timer persistence across undo, and timer reset on New Game.
- GitHub Actions confirmed **92 passing tests** on November 5, 2026: [run #41993667114](https://github.com/luqmanbuttcs/dsa-project/actions/runs/41993667114).
