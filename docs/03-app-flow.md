# Application Flow

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Purpose:** Define how users move through the game and how each action reaches the DSA layer, game engine, monitor, and UI.

## 1. Application states

| State | Meaning | Available actions |
|---|---|---|
| Launch | Application is opening | Load settings, show new-game prompt |
| Ready | No active game yet | New Game, Settings, Exit |
| Playing | A game is active | Draw, move, undo, redo, hint, settings |
| Animating | A validated transition is being presented | Wait for animation or queue permitted input |
| Won | All 52 cards are in foundations | New Game, review operation history |
| Restart confirmation | User is about to discard current game | Confirm or cancel |

The DSA monitor is a panel/view, not a separate game state. It can be expanded while the game remains in Playing.

## 2. Launch and new-game flow

1. Launch the PyQt application and create the main window.
2. Load user preferences such as appearance, animation, draw mode, and sound. If no preferences exist, use sensible defaults.
3. Show the board shell and offer New Game.
4. On New Game:
   - Clear old piles, history, counters, and transient UI feedback.
   - Create a list containing 52 unique Card objects.
   - Shuffle the deck list.
   - Deal tableau columns in order: column 1 gets one card, column 2 gets two, through column 7 gets seven.
   - Keep all dealt cards face-down while dealing, then turn the final card in each column face-up.
   - Transfer the remaining 24 cards to the stock Queue.
   - Create four empty foundation Stacks and an empty waste Stack.
   - Build/refresh the card Dictionary index for all 52 cards.
   - Initialize undo/redo history and operation tracking for the new session.
   - Run invariants: 52 unique cards, 28 tableau, 24 stock, 0 waste, 0 foundations, 7 face-up tableau cards.
5. Render the board and reset the timer/move/score display.

The initial distribution is specified in the instructor PDF. The waste pile is included as a normal Klondike implementation detail because drawn stock cards need a visible/playable destination.

## 3. Stock draw flow

1. Player chooses Draw 1 or Draw 3 (the mode is visible near the stock).
2. Player activates the stock.
3. GameEngine checks whether the stock Queue is non-empty.
4. For each card up to the selected count:
   - Dequeue the front stock card.
   - Set it face-up.
   - Push it onto the waste Stack.
   - Update its Dictionary location and face state.
   - Emit Queue, Stack, and Dictionary operation events grouped under one draw action.
5. Animate the card from stock to waste; show the most recently drawn card on top.
6. Record the draw in the player move log and update the move count according to the chosen move-count policy.
7. If stock is empty, apply the configured recycle rule only when the player requests a draw. Reverse/re-enqueue waste in the correct order so the next draw preserves intended order. Record the recycle operation. The recycle rule remains configurable because the PDF does not define it.

## 4. Tableau-to-tableau move flow

Example: move 8 of Hearts onto 9 of Clubs.

1. Player presses/drags 8♥ (or a valid face-up sequence beginning with it).
2. UI marks the source and asks the engine for valid destinations.
3. RuleValidator checks:
   - source card and every card in the selected sequence are face-up;
   - destination is a tableau card exactly one rank higher and opposite color; or
   - destination is empty and the moving sequence begins with a King.
4. If invalid: do not mutate anything; clear selection and show concise feedback.
5. If valid:
   - Capture a reversible MoveRecord.
   - Detach the selected run from the source tableau's linked-list chain.
   - Execute Stack/Linked List source and destination operations through the pile APIs.
   - Attach the run to the destination pile.
   - Update Dictionary locations for every moved card.
   - If the source exposes a face-down card, flip it face-up and update the card index.
   - Push the MoveRecord onto undo; clear redo.
   - Increment the player move count and update score if scoring is enabled.
6. Emit a completed action event with its child DSA operation events.
7. Animate the card/run to the destination. Animate the newly exposed card's flip.
8. Synchronize the monitor's highlighted operation sequence and operation history.
9. Check invariants and evaluate victory.

The visual animation should match the committed game-state transition. It must not create or simulate operations that did not occur.

## 5. Tableau-to-foundation and waste-to-foundation flow

1. Player selects a face-up eligible card from tableau or waste.
2. RuleValidator checks the target suit foundation:
   - empty foundation accepts only Ace;
   - non-empty foundation accepts only the same suit and next rank.
3. On success, remove the card from the source, push it onto the foundation Stack, update Dictionary location, and expose/flip the next source card if applicable.
4. Record an undoable command, emit operation events, animate the card to the foundation, and update the move log.
5. Check victory after the move.

## 6. Waste-to-tableau flow

1. Only the waste top card is available for a normal single-card move.
2. Validate it against the tableau destination using alternating-color descending rules, or King-only placement on an empty column.
3. On success, pop waste, push/attach to the tableau, update the Dictionary, record undo, animate, and check victory.

## 7. Undo flow

1. Player activates Undo or the keyboard shortcut.
2. If undo history is empty, show a disabled/no-history state.
3. Otherwise, pop the most recent MoveRecord from the undo Stack.
4. Apply its inverse through the same domain/data-structure APIs, restoring:
   - card order and pile locations;
   - stock/waste order for draw/recycle actions;
   - face-up states;
   - relevant counters and game status.
5. Push the record onto redo.
6. Emit events marked with context = undo so the monitor distinguishes reversal operations from ordinary gameplay.
7. Animate the reverse transition when practical; update the move log and monitor.
8. Recheck invariants.

## 8. Redo flow

1. Player activates Redo or the keyboard shortcut.
2. If redo history is empty, show disabled/no-history state.
3. Otherwise, pop the most recent redo record, reapply it through domain/data-structure APIs, and push it back to undo.
4. Emit events marked with context = redo, animate the transition, update logs/counters, and recheck invariants.

A new successful move after undo clears the redo Stack.

## 9. Hint flow

Hint is optional. If implemented:
1. Ask the engine to enumerate legal moves without mutating state.
2. Prefer a useful move based on a documented simple priority order (for example: move an Ace/next foundation card, reveal a hidden tableau card, make a legal tableau build, then use a stock draw).
3. Highlight the source and destination for a short period.
4. Do not perform the move automatically unless a separate Auto Move control is explicitly added.
5. Record a hint-use event, not fake stack/queue operations.

## 10. Game completion flow

After every successful move:
1. Check whether the sum of foundation cards is 52.
2. Verify each foundation is a same-suit sequence from Ace through King.
3. If both conditions hold, set game status to Won, stop the timer, disable invalid game actions, and show a non-blocking win panel.
4. Allow the player to inspect the move/DSA history or start a new game.

## 11. Invalid move flow

1. Player attempts a move.
2. RuleValidator rejects the move with a reason code (wrong rank, same color, wrong suit, invalid empty-column card, face-down card, or unavailable source card).
3. Game state and data-structure mutation counts remain unchanged.
4. UI briefly highlights the source/destination and displays a clear reason.
5. Record a MoveRejected entry in the player-facing history only if useful; do not log POP/PUSH or link mutations for a rejected move.

## 12. Settings and layout flow

- Draw mode: choose one or three cards; show the current mode near stock.
- Animation: normal/reduced/off; reduced-motion settings must still show the operation history.
- Appearance: preserve the chosen green felt/navy/gold identity; optional card contrast settings.
- DSA monitor: compact overview by default; expand individual structures or open operation history for detail.
- Restart: ask for confirmation when an active game would be discarded.
- Resize: board and monitor adapt; if space is limited, collapse secondary details or enable scrolling rather than crowding cards.

## 13. Operation-trace example

For moving 8♥ onto 9♣ and then flipping a newly exposed card, a grouped trace may contain:
1. STACK_POP (source top/run extraction);
2. LINKED_LIST_DETACH_RUN (source links);
3. LINKED_LIST_ATTACH_RUN (destination links);
4. STACK_PUSH (destination top insertion);
5. DICTIONARY_UPDATE (moved card location);
6. DICTIONARY_UPDATE (newly exposed card face-up state).

The exact low-level order depends on the chosen pile API, but the trace must accurately describe the methods actually called. The operation monitor must not imply that Linked List and Stack are two copies of the same pile.

