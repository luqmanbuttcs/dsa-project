# Backend Schema and Domain Model

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Important clarification:** The supplied PDF does not require a web backend, API, or database. This document defines the local game-engine state and data contracts used by the desktop application. “Backend” here means the domain/model layer behind the PyQt UI.

## 1. Storage approach

- The active game is held in memory.
- Custom Stack, Queue, Linked List, Array/List, and Dictionary implementations own or index the live state.
- No remote service or server database is needed for the initial project.
- Optional local preferences or saved-game persistence may be added later, but is not a core PDF requirement.
- If persistence is added, serialize card IDs and pile order, not Python object pointers or linked-list node references.

## 2. Core enums and value types

### Suit
- HEARTS
- DIAMONDS
- CLUBS
- SPADES

### Rank
Integer values 1 through 13:
- 1 = ACE
- 2–10 = numeric ranks
- 11 = JACK
- 12 = QUEEN
- 13 = KING

### Zone
- STOCK
- WASTE
- TABLEAU
- FOUNDATION

### GameStatus
- READY
- PLAYING
- WON

### DrawMode
- ONE
- THREE

A card's color is derived from suit: Hearts/Diamonds are red; Clubs/Spades are black.

## 3. Card entity

| Field | Type | Constraint |
|---|---|---|
| card_id | string | Unique stable ID, e.g. H-A, D-10, S-K |
| suit | Suit | Exactly one of the four suits |
| rank | integer | 1–13 |
| face_up | boolean | False or True |

Identity fields (card_id, suit, rank) do not change during a game. face_up changes when a card is dealt/revealed/moved according to game rules.

The deck must contain exactly 52 unique card IDs.

## 4. Pile identifiers and canonical order

Use stable pile IDs:
- stock
- waste
- tableau-1 through tableau-7
- foundation-hearts
- foundation-diamonds
- foundation-clubs
- foundation-spades

Choose and document one canonical order for each collection:
- Stack/linked-list pile: bottom-to-top, with the tail representing the top.
- Queue: front-to-rear.
- Tableau display: bottom-to-top in storage; the UI lays cards downward with overlap.
- A moved tableau run is a contiguous suffix ending at the current top, preserving order when attached to the destination.

The order convention must be used by the model, serializer, dictionary index, tests, and UI.

## 5. Dictionary index schema

The card tracker is a dictionary keyed by card_id.

| Entry field | Type | Description |
|---|---|---|
| card_id | string | Key / stable card identity |
| zone | Zone | Current logical area |
| pile_id | string | Current pile identifier |
| position | integer | Zero-based position in that pile's canonical order |
| face_up | boolean | Indexed visibility state |

Example entry (illustrative):

    card_index["H-8"] = {
        "card_id": "H-8",
        "zone": "TABLEAU",
        "pile_id": "tableau-7",
        "position": 4,
        "face_up": true
    }

The index must be updated on draw, waste transfer, tableau move, foundation move, stock recycle, undo, redo, and card flip. After each committed transition, compare the index with actual pile contents in invariant tests. The index is not a second card store.

## 6. GameState schema

GameState owns the current logical session.

| Field | Type / structure | Purpose |
|---|---|---|
| game_id | string/UUID | Identify this session |
| status | GameStatus | Ready, playing, or won |
| draw_mode | DrawMode | Draw one or three |
| stock | Queue[Card] | FIFO stockpile |
| waste | Stack[Card] | Most recently drawn card is top |
| tableau | mapping of 7 IDs to TableauColumn | Seven tableau piles |
| foundations | mapping of Suit to Stack[Card] | Four suit foundations |
| card_index | dict[card_id, CardIndexEntry] | Fast card location/state lookup |
| undo_history | Stack[MoveRecord] | Reversible actions |
| redo_history | Stack[MoveRecord] | Actions that can be reapplied |
| move_count | integer | Number of currently applied player moves under the chosen counter policy |
| elapsed_seconds | integer | Elapsed game time |
| score | integer | Optional score; formula must be defined before enabling |
| operation_events | list/event buffer | DSA operation history |
| move_events | list/event buffer | Player-facing action history |

The temporary shuffled deck list belongs to game initialization and can be discarded once dealing is complete; it must not remain a second active copy of the cards.

## 7. Supporting model contracts

### Node
- card: Card reference
- previous: Node reference or null
- next: Node reference or null

### LinkedList
- head, tail, size
- append/remove end operations
- detach_run(first_node, last_node)
- attach_run_at_end(run)
- iteration and invariant validation

### Stack
- backing_list: LinkedList[Card]
- push(card), pop(), peek(), is_empty(), size()
- tableau columns expose Stack operations while retaining linked-list run manipulation.

### Queue
- internal buffer, front index, rear/size metadata
- enqueue(card), dequeue(), peek(), is_empty(), size()
- dequeue returns the oldest enqueued card.

### CardLocation
- zone
- pile_id
- position
- face_up

### MoveRecord
| Field | Type | Purpose |
|---|---|---|
| action_id | string | Link all events from this action |
| action_type | enum/string | draw, tableau move, foundation move, recycle, etc. |
| source_pile_id | string/null | Source pile |
| destination_pile_id | string/null | Destination pile |
| card_ids | list[string] | Cards involved, in canonical order |
| previous_face_states | map[string, boolean] | Restore face-up states on undo |
| prior_auxiliary_state | structured data/null | Capture stock/waste order or other action-specific changes |
| move_count_before | integer | Restore the displayed count |
| score_before | integer | Restore score if enabled |

MoveRecord stores the minimum reversible delta needed by its action type. Do not store duplicate live Card objects as an alternate game state.

## 8. OperationEvent schema

Each DSA event should contain:

| Field | Type | Purpose |
|---|---|---|
| sequence | integer | Monotonic event order within a session |
| action_id | string | Groups low-level operations under one player action |
| timestamp | datetime/elapsed offset | Display order/time |
| structure | enum | ARRAY_LIST, STACK, QUEUE, LINKED_LIST, DICTIONARY |
| operation | string | PUSH, POP, ENQUEUE, DEQUEUE, DETACH_RUN, UPDATE, etc. |
| pile_id | string/null | Affected pile |
| card_ids | list[string] | Affected card IDs where applicable |
| context | enum/string | PLAY, UNDO, REDO, SETUP, SYSTEM |
| outcome | enum | SUCCESS or FAILURE |
| details | short structured payload | Human-readable explanation and optional before/after facts |

Counts in the DSA monitor are calculated from these events or incremented by the same instrumentation layer that emits them. The UI must not maintain an independent counter disconnected from the structures.

## 9. Player MoveEvent schema

Keep player actions distinct from low-level data-structure operations.

| Field | Type | Purpose |
|---|---|---|
| action_id | string | Correlates with DSA events |
| sequence | integer | Player action order |
| action_type | string | draw, move, foundation, undo, redo, restart |
| description | string | E.g. “Moved 8♥ to Tableau 7” |
| card_ids | list[string] | Cards involved |
| source | string/null | Source pile |
| destination | string/null | Destination pile |
| result | string | success, rejected, undone, redone |
| elapsed_seconds | integer | Optional display time |

## 10. Invariants

Run these checks after setup and in tests after every committed action:

1. Exactly 52 unique card IDs exist across stock, waste, tableau, and foundations.
2. No card exists in more than one pile.
3. Every card in a pile has a matching Dictionary entry.
4. Every Dictionary entry points to a card that exists in exactly one pile.
5. Dictionary zone, pile ID, position, and face-up state match the actual card/pile.
6. Queue order remains FIFO.
7. Stack top matches the last element of the pile's canonical order.
8. Linked-list head/tail/previous/next/size invariants hold.
9. Each foundation contains only one suit in ascending order.
10. Face-down cards cannot be selected for ordinary moves.
11. A successful move preserves card count.
12. A rejected move changes no pile, card, index, history, or mutation counter.

## 11. Initial state fixture

After New Game and before player interaction:
- deck creation list: 52 unique cards before dealing;
- tableau: 7 columns, sizes 1–7, total 28;
- tableau face-up cards: exactly 7;
- stock Queue: 24 cards;
- waste Stack: 0 cards;
- foundations: 4 empty stacks;
- card index: 52 entries;
- undo/redo: empty;
- move count: 0;
- status: PLAYING.

## 12. Persistence boundary

Persistence is not required by the supplied PDF. For the first working release, reset/close may discard the active session after an appropriate confirmation. If save/resume is added later, use a versioned JSON format containing:
- schema_version;
- game settings and status;
- card identity plus face-up state;
- ordered card IDs in stock, waste, each tableau column, and each foundation;
- move count, elapsed time, and optional score.

Reconstruct custom stacks, queues, linked-list nodes, dictionary index, and history from the serialized data. Never serialize raw object pointers or Qt widgets. Add migration/version handling before changing a saved format.

