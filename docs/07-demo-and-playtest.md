# Demo and Playtest Guide

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Interface:** Python + PyQt6  
**Launch module:** `solitaire.main`

This guide separates automated verification from the final hands-on Windows check. The CI suite verifies game logic and offscreen widget behavior; it cannot verify mouse feel, screen scaling, or visual smoothness on the target computer.

## 1. Run the application on Windows

Open PowerShell in the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m solitaire.main
```

Run all automated tests:

```powershell
python -m pytest
```

Use Python 3.12 for the documented setup. The project requires PyQt6 and pytest for development tests.

## 2. Player controls

| Control | Behavior |
|---|---|
| Click a face-up Tableau or top Waste card | Select a source card / sequence |
| Click a Tableau card or empty Tableau column | Attempt the selected move |
| Click a Foundation | Attempt to place the selected top card |
| Drag a Waste or face-up Tableau card/sequence | Drop on a Tableau or Foundation target |
| Draw Mode | Choose Draw 1 or Draw 3 |
| Stock | Draw cards, or recycle Waste after Stock is empty |
| Hint | Selects the source for the next highest-priority legal suggestion |
| Undo / Redo | Reverses or reapplies the last successful action |
| New Game | Starts a shuffled deal; asks before discarding a played game |
| DSA Monitor | Shows/hides the five-structure monitor |
| Reduce motion | Skips card travel/flip animations but preserves state and operation feedback |

Keyboard shortcuts:

- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo
- `Ctrl+N`: New Game
- `H`: Hint
- `Space`: Draw from Stock

The timer starts on the first successful action, stops when the game is won, resumes if the winning move is undone, and resets on New Game. Scoring is +10 for a foundation move, +5 for Waste-to-Tableau, and +5 for exposing a hidden Tableau card. Stock draws and ordinary Tableau rearrangements earn zero points.

## 3. DSA monitor demonstration

Open **DSA Monitor**. The Overview shows current counts and the latest real action group. The Structures tab exposes the details; History lists the low-level tracker events with sequence number and UTC time. The player's Move Log remains separate.

| Required structure | Where it is implemented | What to demonstrate |
|---|---|---|
| Array / List | `src/solitaire/domain/deck.py`, `game_state.py` | A standard 52-card list is created, shuffled, popped for dealing, then cleared after the deal. Open the Array / List detail tab to see the setup trace. |
| Stack | `src/solitaire/structures/stack.py`, `game_engine.py` | Waste is LIFO, foundations are suit Stacks, tableau exposes Stack operations, and Undo/Redo use two history Stacks. Draw cards and move one to a foundation. |
| Queue | `src/solitaire/structures/queue.py`, `game_engine.py` | Stock draws from the Queue front (FIFO). Draw 1 or 3 and inspect front, rear, size, and Queue dequeue events. |
| Linked List | `src/solitaire/structures/linked_list.py`, `game_state.py` | Tableau columns use the custom doubly linked list. Move a multi-card face-up run and inspect the node links for the selected column. |
| Dictionary | `src/solitaire/domain/game_state.py`, `game_engine.py` | The `card_index` maps each card ID to its live zone, pile, position, and face state. Move a card and inspect the selected card lookup. |

Suggested presentation order:

1. Start a new game and show 52 unique cards, seven Tableau columns, and 24 Stock cards.
2. Open Array / List details to show creation, shuffle, and deal operations.
3. Draw three cards and show three Queue dequeues and Waste Stack pushes.
4. Move a card or multi-card run between Tableau columns. Show Stack and Linked List operations and the exposed-card flip.
5. Move an Ace to its Foundation. Show the Foundation Stack push and Dictionary location update.
6. Select a card and request a Hint. Explain that hint enumeration does not mutate the game.
7. Undo and Redo a move. Show the two history Stacks and the corresponding operation context.
8. Finish with the deterministic victory test or a prepared near-complete demo state, then show the non-modal victory banner.

A random shuffled Klondike deal is not guaranteed to be solvable. Do not promise that an arbitrary new deal can always be completed.

## 4. Windows manual playtest checklist

Complete this list on the target Windows computer before submission. CI cannot substitute for this hands-on check.

### Launch and layout
- [ ] Run `python -m solitaire.main` from the activated project environment.
- [ ] Confirm the board, stock, waste, four foundations, seven Tableau columns, footer, and Move Log render.
- [ ] Resize the window to approximately 1600 × 900 and 1280 × 800.
- [ ] Confirm the board does not overlap the DSA Monitor; verify the Tableau's horizontal scrollbar appears when needed.
- [ ] Toggle DSA Monitor closed/open and confirm the board regains the released space.
- [ ] Check that no important button, label, card rank, or suit is clipped at the intended screen scaling.

### Gameplay and drag/drop
- [ ] Draw one card, then use Draw 3 in a fresh game.
- [ ] Drag the top Waste card to a legal Tableau destination.
- [ ] Drag a legal face-up Tableau card to another Tableau column.
- [ ] Drag a multi-card face-up sequence and verify the sequence order is preserved.
- [ ] Drag a legal Ace/next-rank card to its matching Foundation.
- [ ] Try an invalid same-color or wrong-rank drop; verify the source and destination piles remain unchanged and an error message appears.
- [ ] Try a non-King sequence on an empty Tableau column; verify rejection.
- [ ] Empty the Stock, recycle Waste, and verify the next draw order.

### Animations and accessibility
- [ ] Confirm card travel starts at the old location and ends at the committed destination.
- [ ] Confirm a newly exposed face-down card flips to face-up.
- [ ] Turn on Reduce motion; repeat a move and confirm the game still updates and the DSA trace remains available.
- [ ] Use keyboard shortcuts for Undo, Redo, Hint, and Stock draw.
- [ ] Confirm Undo/Redo restores card positions and score; elapsed time continues rather than rewinding.

### Monitor, timer, score, and victory
- [ ] Draw from Stock and confirm Queue counts/latest action/history update.
- [ ] Move a card and confirm Stack, Linked List, and Dictionary details update.
- [ ] Select a card and check its Dictionary location.
- [ ] Confirm Move Log and DSA Operation History are separate.
- [ ] Confirm the timer starts after the first successful move and increases each second.
- [ ] Confirm score follows the documented formula and rolls back/restores with Undo/Redo.
- [ ] Complete a prepared winning game and confirm the victory banner appears without blocking the app.
- [ ] Undo the winning move and confirm the banner disappears; Redo and confirm it returns.
- [ ] Start New Game after moves; answer No and confirm the current game remains; answer Yes and confirm a fresh deal starts.

### Close and repeat
- [ ] Close the window while idle and while an animation is running; confirm it exits cleanly.
- [ ] Relaunch and confirm a new session starts with a fresh deal and zero score/time.

## 5. Automated verification

The final GitHub Actions run is the authoritative automated test count for the PR. It runs pytest on Python 3.12 with Qt's offscreen platform, including engine, integration, bonus-feature, drag/drop, monitor, animation, resizing, keyboard, and victory-banner tests.

Manual Windows results should be recorded only after the checklist above is actually performed. Do not mark the visual/manual playtest complete based on CI alone.
