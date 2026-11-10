# Design Brief

**Project:** Klondike Solitaire — CSC200 DSA Edition  
**Visual reference:** The user's approved dark-navy / green-felt Solitaire dashboard with animated card trails and a right-side DSA monitor.

## 1. Design objective

Create a desktop game that feels like a polished Solitaire application first and a DSA teaching tool second. The board should be immediately understandable to a casual player, while the monitor should make the academic implementation easy to demonstrate. The interface must be attractive without becoming crowded.

The approved visual direction is retained:
- deep navy application header and side panels;
- rich green felt playing surface;
- white, high-contrast cards with traditional red/black suits;
- blue primary controls;
- gold trails/highlights for card movement;
- restrained green success feedback;
- a dedicated right-side DSA monitor.

## 2. Design principles

1. **Breathing room:** Do not fill every empty region with counters, labels, borders, or decorative effects.
2. **Board first:** The seven tableau columns and stock/foundation area receive the largest visual area.
3. **Progressive disclosure:** Show a concise DSA overview by default; reveal node chains, stack contents, queue front/rear, and dictionary entries when the user expands a structure or enters DSA Lab mode.
4. **State clarity:** A card's location, legal destination, and success/invalid state should be visually obvious.
5. **Animation with purpose:** Movement effects explain where a card went and which operation is happening. Avoid continuous or decorative animation.
6. **Consistency:** Reuse the same spacing, card proportions, typography, colors, and interaction feedback across the application.
7. **Readable at normal zoom:** Do not shrink cards or DSA text just to fit more content.

## 3. Primary window composition

### Header
- Left: spade/game mark, title “Klondike Solitaire”, and CSC200 DSA Edition label.
- Center: elapsed time, move count, and score (score may be hidden until implemented).
- Right: Hint, Undo, Redo, Settings, and other secondary actions.
- Use a stable header height and avoid allowing long labels to push controls off-screen.

### Main workspace
Use a flexible two-column layout:
- **Game board:** approximately 70–74% of the available content width.
- **DSA monitor:** approximately 26–30% of the available content width.
- Keep a deliberate gutter between the board and monitor. The monitor must never overlap the board.

### Game board
- Upper-left: stock and waste.
- Upper area/right: four foundation placeholders labeled or identifiable by suit.
- Main area: seven tableau columns.
- Keep the card spacing/overlap consistent. Face-down cards use a compact vertical offset; face-up cards use enough visible height to read rank and suit.
- Highlight only the current source, legal destinations, and active animation path.
- The 8♥ → 9♣ example may be used in design/demo screenshots, but the live game must render the actual current state rather than a hard-coded scenario.

### DSA monitor
Default compact view:
- Header with “DSA Monitor” and a separate Game Stats tab/section.
- Five rows: Array/List, Stack, Queue, Linked List, Dictionary.
- Each row shows a short responsibility label and actual operation count or current size where relevant.
- Latest Operation panel shows the current grouped action and its real operation sequence.
- Operation History lists timestamp/order, player action, and outcome.
- Expand/collapse affordance for details.

Expanded detail view:
- Array/List: deck size and setup/deal stage; do not show all 52 cards unless the user opens the detail.
- Stack: top card and size for the selected pile; optional compact stack representation.
- Queue: front, rear, and size for stock.
- Linked List: selected tableau column's node order and links.
- Dictionary: selected card ID and its actual zone/pile/index/face-up entry.
- Clearly identify the selected pile/card so the player can relate the model to the board.

### Bottom information area
- Move Log is separate from the DSA Operation History. The Move Log records player actions; the DSA history records lower-level methods.
- A small context/status panel may show “Valid Move”, a win message, or a short invalid-move reason.
- Do not use a large permanent celebratory banner during ordinary gameplay.

## 4. Spacing and layout tokens

Use an 8 px spacing rhythm and preserve whitespace deliberately.

| Token | Value | Use |
|---|---:|---|
| XXS | 4 px | Icon-to-label micro spacing |
| XS | 8 px | Compact control internals |
| SM | 12 px | Related controls and card gutters |
| MD | 16 px | Panel padding and component groups |
| LG | 24 px | Main content margins and section separation |
| XL | 32 px | Major section breathing room |

Additional guidance:
- Main window outer content margin: 20–24 px.
- Major panel internal padding: 16–20 px.
- Gap between board and monitor: 16–20 px.
- Tableau column gap: target 10–14 px.
- Keep at least 12 px between unrelated controls.
- Avoid stacking multiple nested borders. Prefer subtle surface contrast and whitespace.
- Maintain a clear hierarchy: page title > section title > action label > helper text.
- Use a tooltip for a compact icon-only control, but prefer visible labels for important actions.

## 5. Color and typography

These are initial design tokens and may be tuned during the UI prototype.

| Purpose | Suggested color |
|---|---|
| Header / deep panel | Navy #071B2B / #0B2438 |
| Felt surface | Deep green #075B35 with subtle texture |
| Primary action | Blue #0879D1 |
| Movement highlight | Warm gold #F5C84C |
| Success | Green #21A366 |
| Invalid / destructive | Muted red #D94B4B |
| Card surface | Warm white #FFFDF8 |
| Main text on dark | #F4F7FA |
| Secondary text on dark | #B9C7D3 |
| Panel border | Low-contrast blue-gray |

Typography:
- Use a readable sans-serif UI font for controls, statistics, and monitor rows.
- The game title may use a more characterful serif treatment if legibility is preserved.
- Card ranks and suits must be large enough to recognize at a glance.
- Avoid all-caps body copy and tiny monitor text.

## 6. Cards and interaction states

Each card should have clear states:
- face-down;
- face-up and idle;
- selected/source;
- legal destination;
- invalid destination;
- currently moving;
- newly revealed/flipping.

Card visuals:
- red suits: Hearts and Diamonds;
- black suits: Clubs and Spades;
- suit symbol always accompanies color, so color alone is never the only distinction;
- high-contrast card back with a repeatable pattern;
- rank and suit visible in the top-left and a recognizable central face/suit graphic.

Interaction:
- Support click-to-select and drag-and-drop where practical.
- While dragging, highlight only legal destinations.
- On an invalid drop, restore the card without altering the game state and show a short explanation.
- Keep the pointer target large enough for reliable use.
- Provide keyboard alternatives for selection/movement where feasible.

## 7. Animation specification

Animations are part of the DSA explanation, not decoration.

| Transition | Visual treatment | Initial timing target |
|---|---|---:|
| Single-card move | Smooth card translation with short gold trail | 180–260 ms |
| Sequence move | Move the selected run together with consistent offsets | 200–280 ms |
| Card flip | Brief 3D/scale or two-sided reveal | 160–220 ms |
| Stock draw | Card travels from stock to waste | 180–240 ms per visible draw |
| Foundation placement | Card glides to suit foundation; subtle success highlight | 180–260 ms |
| Invalid move | Brief destination/source emphasis; no long shake | 120–180 ms |

Timing is a starting target, not a correctness dependency. The game engine commits a valid state transition independently of the animation. If reduced motion is enabled, use a minimal fade/highlight while still displaying the DSA operation trace.

For every animated action:
1. Validate the move.
2. Execute the actual data-structure operations.
3. Emit the operation trace with an action ID.
4. Animate the resulting card movement.
5. Highlight corresponding DSA steps in the same action order.
6. End with the board, monitor, and move log showing the same state.

## 8. DSA monitor information hierarchy

Default compact row:
- structure name;
- one-line purpose;
- current size or real operation count;
- expand control.

Expanded detail should answer:
- What data is stored here?
- What is the top/front/head/tail?
- Which operation just happened?
- Which player action triggered it?
- Which card/pile was affected?

Do not display raw internal object representations or long identifiers in the default view. Use readable cards, arrows, and short labels. Provide technical IDs only in a detail view useful for debugging.

## 9. Window sizes and responsiveness

- Design target: 1600 × 900 desktop workspace.
- Usability target: 1280 × 800 or larger.
- The window should be resizable.
- When space decreases, reduce decorative space and collapse secondary monitor details before making cards or text unreadably small.
- If the board cannot fit at a smaller width, allow a controlled horizontal board scroll or provide a compact board scale; never overlap the DSA panel with card columns.
- Keep the monitor at a usable minimum width and allow its history/detail area to scroll independently.
- Verify the layout at both target sizes before declaring UI completion.

## 10. Empty, loading, and feedback states

- Before a game: concise “Start a new game” state.
- During deal: brief dealing animation or immediate deal if reduced motion is on.
- Empty stock/waste/foundation: show a subtle empty placeholder, not a misleading card.
- No undo/redo: disable the control and offer a tooltip explaining why.
- Invalid move: short inline reason.
- DSA monitor before events: show zero counts and descriptive empty state.
- Victory: clear, celebratory but non-blocking completion panel.
- Restart: confirmation only when the current game would be discarded.

## 11. Design acceptance checklist

- [x] Main board remains visually dominant in the layout; the DSA Monitor is a collapsible dock.
- [x] The five required structures are visible in the monitor overview.
- [x] The monitor can be shown/hidden without covering the board.
- [x] Stock, waste, foundations, and seven tableau columns are distinguishable.
- [x] Legal destinations are computed from the engine's move hints and highlighted while dragging.
- [x] Card travel and face flips are animated after real game-engine transitions.
- [x] Move Log and timestamped DSA Operation History are separate.
- [x] The interface retains 24 px outer breathing space and consistent internal spacing.
- [ ] No text, card, or control clips at target sizes (must still be checked on the user's Windows display/scaling).
- [x] Reduced-motion mode preserves clear game feedback and the DSA trace.

**Verification boundary:** automated UI tests cover accepted/rejected drop routes, animation completion, monitor updates, minimum-size layout, and dock show/hide behavior. They do not prove the visual fit or mouse feel on every Windows screen/scaling configuration. Use [the manual playtest guide](07-demo-and-playtest.md) for those final checks.

