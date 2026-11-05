# Product Requirements Document

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Status:** Baseline for implementation  
**Source of mandatory requirements:** CSC200 Mid Term Project PDF (deadline stated in the brief: November 22, 2026)  
**Repository:** luqmanbuttcs/dsa-project

## 1. Product summary

Build a desktop implementation of Klondike Solitaire that follows the instructor's project brief and makes the required data structures visible during real gameplay. The player should be able to play a complete game while an integrated DSA monitor explains which data structures are being used and records the operations caused by each action.

The interface should resemble the approved visual reference: a green felt playing surface, dark navy header and side panels, clear playing cards, restrained blue controls, gold movement trails, a move log, and a right-side DSA monitor. The interface must have breathing room. The board must remain the main focus; technical information should be compact by default and expandable when the player wants detail.

## 2. Source and requirement labels

This document distinguishes three kinds of decisions:

- **PDF requirement:** Explicitly stated in the instructor's brief. These are the project's non-negotiable academic requirements.
- **Project decision:** A design or engineering choice made to deliver a coherent desktop application. It is not presented as a direct instructor requirement.
- **Optional enhancement:** A feature identified as optional in the PDF or deliberately deferred beyond the core implementation.

The PDF asks for a Klondike game, card representation, game setup, valid moves, undo/redo, win detection, and the use of Stack, Queue, Array/List, Linked List, and HashMap/Dictionary. It describes a text or graphical UI as optional and lists Hint, Timer, and Scoring as bonus features.

## 3. Goals

1. Deliver a complete, playable Klondike Solitaire game.
2. Implement all five required data structures as genuine custom components with clear responsibilities.
3. Keep card state correct through moves, draws, flips, undo, redo, and restart.
4. Demonstrate actual data-structure operations in the UI rather than displaying decorative or fabricated counters.
5. Make the game convenient and visually clear, with a spacious layout and understandable feedback.
6. Keep game logic independent from the UI so the rules and data structures can be tested without opening a window.

## 4. Non-goals for the initial release

The initial release does not require online accounts, multiplayer, cloud synchronization, network APIs, advertisements, payments, an online leaderboard, or a remote database. These are outside the instructor's stated scope. Do not add them unless the project requirements change.

## 5. Target users and user stories

### Player
- As a player, I can start a new shuffled game with the correct 52-card setup.
- As a player, I can draw one or three cards from the stock according to the selected draw mode.
- As a player, I can move a card or valid face-up sequence between tableau columns.
- As a player, I can move eligible cards to the correct foundation pile.
- As a player, I receive clear feedback when a move is invalid.
- As a player, I can undo and redo moves without corrupting the board.
- As a player, I can see elapsed time, move count, score (if enabled), and a readable move history.

### Student / demonstrator
- As a student, I can see which required data structures are active.
- As a student, I can inspect the actual operation sequence caused by a move or draw.
- As a student, I can expand a structure to inspect its logical contents, such as a stack top, queue front/rear, or linked-list node chain.
- As a student, I can explain how the dictionary maps a card to its current pile and face state.

## 6. Functional requirements

| ID | Requirement | Classification | Acceptance condition |
|---|---|---|---|
| FR-01 | Represent a card with suit, rank, and face-up/face-down state. | PDF requirement | Every card has one suit, one rank, and an explicit visibility state. |
| FR-02 | Create a standard 52-card deck. | PDF requirement | Four suits × thirteen ranks; no duplicate or missing card IDs. |
| FR-03 | Shuffle and deal the deck. | PDF requirement | Seven tableau columns receive 1 through 7 cards; only each column's last card is face-up; 24 cards remain in stock. |
| FR-04 | Use an Array/List for deck creation, shuffling, and access. | PDF requirement | The deck is represented by an array/list before dealing. |
| FR-05 | Use a Queue for the stockpile and FIFO drawing. | PDF requirement | Drawn cards leave the front of the stock queue in order. |
| FR-06 | Use Stack for tableau and foundation pile behavior. | PDF requirement | Stack operations are used for pile top access and card insertion/removal. |
| FR-07 | Use a Linked List to represent and manipulate tableau piles. | PDF requirement | Tableau storage uses the custom linked-list implementation; sequence moves update links. |
| FR-08 | Use a HashMap/Dictionary to track card location and state. | PDF requirement | Each card ID can be resolved to its current zone, pile, position, and face state. |
| FR-09 | Validate tableau moves. | PDF requirement | A card/sequence can be placed only on a card one rank higher and of the opposite color; only a King-led sequence may enter an empty tableau column. |
| FR-10 | Validate foundation moves. | PDF requirement | An Ace starts an empty foundation; subsequent cards must be the same suit and one rank higher. |
| FR-11 | Draw one or three cards from stock. | PDF requirement | The selected draw count is applied, limited by cards remaining. |
| FR-12 | Flip a newly exposed tableau card. | PDF requirement | When a face-up card/sequence leaves a column, the newly exposed top card flips face-up if it was face-down. |
| FR-13 | Detect a win. | PDF requirement | Win is reported only when all 52 cards are in the four foundations. |
| FR-14 | Support undo. | PDF scope and Phase 3 | Undo restores the exact previous logical state for the last supported action. |
| FR-15 | Support redo. | Project decision / bonus interpretation | Redo reapplies the action that was most recently undone. |
| FR-16 | Provide a graphical desktop UI. | Project decision; PDF says UI is optional | Player can operate the complete game through the approved desktop layout. |
| FR-17 | Animate legal card movement and card flips. | Project decision | Animation corresponds to a validated state transition and does not change game rules. |
| FR-18 | Show a live DSA monitor and operation history. | Project decision | Monitor events and counts originate from actual data-structure methods. |
| FR-19 | Provide Draw 1 / Draw 3 selection. | Project decision based on PDF draw options | Selected mode is visible and can be changed between games or when allowed by rules. |
| FR-20 | Provide New Game, Hint, timer, and scoring. | New Game: project decision; Hint/Timer/Scoring: optional | Optional controls are clearly labeled and do not block core gameplay. |

## 7. Game rules and initial state

### Deck
- Suits: Hearts, Diamonds, Clubs, Spades.
- Ranks: Ace through King (1 through 13 internally).
- Hearts and Diamonds are red; Clubs and Spades are black.
- A stable card ID must uniquely identify each suit/rank combination.

### Initial deal
The tableau receives 28 cards in seven columns:

| Column | Total cards | Face-down | Face-up |
|---|---:|---:|---:|
| 1 | 1 | 0 | 1 |
| 2 | 2 | 1 | 1 |
| 3 | 3 | 2 | 1 |
| 4 | 4 | 3 | 1 |
| 5 | 5 | 4 | 1 |
| 6 | 6 | 5 | 1 |
| 7 | 7 | 6 | 1 |
| **Total** | **28** | **21** | **7** |

The remaining 24 cards form the stock. The four foundations and waste pile start empty. The stock/waste behavior is a necessary product detail for playable Klondike; the PDF names the stockpile but does not separately describe a waste pile.

### Move rules
- Tableau: descending rank, alternating red/black colors.
- Empty tableau column: only a King or a valid King-led sequence can be placed there.
- Foundation: build ascending from Ace to King, one suit per foundation.
- Stock: draw one or three cards according to the selected mode.
- Waste: the most recently drawn available card is the playable top card.
- Victory: all 52 cards must be in foundations.

**Explicit implementation assumption:** When the stock is empty, the waste may be recycled into the stock in the correct order. The PDF does not specify recycle limits or pass limits. Keep this rule configurable and document the selected default in the technical implementation; change it if the instructor gives a different rule.

## 8. DSA visibility requirements

The DSA monitor is an educational view of actual game state, not a separate simulation.

| Structure | Visible explanation | Events to record |
|---|---|---|
| Array/List | 52-card deck, shuffle, deal progress | create, shuffle, deal/read |
| Stack | Tableau/foundation/waste top and size | push, pop, peek |
| Queue | Stock front, rear, and size | enqueue, dequeue, peek |
| Linked List | Tableau nodes and next links | append/insert, detach, attach, remove |
| Dictionary | Card ID → zone/pile/index/face-up | lookup, insert, update, remove |

The monitor must show:
- Current operation and its reason.
- The pile/card affected.
- A chronological operation history.
- Real counts derived from instrumentation.
- A way to expand the details of each structure.
- A clear empty state before any operations occur.

Do not claim that a method ran merely because a UI animation was shown. Emit monitor events from the actual data structure or domain methods.

## 9. User experience and visual requirements

- The game board is the primary visual focus.
- Use the approved green-felt, dark-navy, blue-control, and gold-animation identity.
- Reserve a stable right-side panel for the DSA monitor; allow details/history to expand without covering cards.
- Keep meaningful whitespace between the header, stock/foundation row, tableau, move log, and monitor.
- Use consistent spacing: approximately 20–24 px outer padding, 12–16 px between related controls/cards, and clear separation between major sections.
- Avoid unnecessary borders, excessive glow, oversized labels, dense statistics, and persistent popups.
- Cards must remain legible at the supported window size. Layout must adapt to window resizing without clipping card columns or important controls.
- Highlight only valid destinations during drag; communicate invalid drops without interrupting the player.
- Provide keyboard focus, tooltips for icon-only controls, and a reduced-motion option.

## 10. Success criteria

The product is acceptable when:
1. All 52 unique cards are present exactly once throughout the game.
2. Initial dealing matches the 1–7 tableau distribution and 24-card stock.
3. All legal/illegal move tests pass.
4. Drawing, waste behavior, card flipping, foundation building, undo, redo, and win detection work.
5. All five required custom data structures are used in the running game.
6. DSA monitor records real operations and stays consistent with the game state.
7. Animations complete without changing the logical result of a move.
8. The UI is readable, spacious, and usable at the project's target window sizes.

## 11. Open points to confirm with the instructor

- Whether the required programming language or GUI framework is specified outside the supplied PDF. The PDF itself does not name one.
- Whether stock recycling is expected and how many recycle passes are allowed.
- Whether a written report, demo video, source-code submission format, or specific rubric exists outside the supplied PDF.
- Whether redo is expected as part of the core submission. This project will implement it alongside undo to avoid ambiguity.

