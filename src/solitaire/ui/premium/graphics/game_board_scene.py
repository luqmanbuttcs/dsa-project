"""GameBoardScene: composition, state projection and interaction.

The scene is a *projection* of the authoritative GameState. After every
controller action it re-derives every card's zone/position/z-order from the
engine and reuses existing CardGraphicsItems (keyed by card_id) so items
keep their identity across refreshes. Animation is cosmetic and always
reconciles to the final engine state.
"""

from __future__ import annotations

import json
import math

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsObject,
    QGraphicsScene,
    QGraphicsSceneDragDropEvent,
    QGraphicsSimpleTextItem,
)

from solitaire.domain.card import Suit
from solitaire.domain.game_state import Zone
from solitaire.ui.premium.controllers.drag_controller import MIME_TYPE
from solitaire.ui.premium.controllers.game_controller import GameController
from solitaire.ui.premium.controllers.selection_controller import SelectionController
from solitaire.ui.premium.graphics.card_item import CardGraphicsItem
from solitaire.ui.premium.graphics.foundation_item import FoundationGraphicsItem
from solitaire.ui.premium.graphics.felt_background import FeltBackgroundItem
from solitaire.ui.premium.graphics.effects.light_sweep import LightSweepItem
from solitaire.ui.premium.graphics.stock_item import StockGraphicsItem
from solitaire.ui.premium.graphics.tableau_item import TableauColumnGraphicsItem
from solitaire.ui.premium.graphics.waste_item import WasteGraphicsItem
from solitaire.ui.premium.theme import (
    ANIMATION_MS,
    CARD_H,
    CARD_W,
    WASTE_FAN,
)

MARGIN = 30.0
TOP_MARGIN = 18.0
# Reserved caption band under the top pile row. The Stock and Waste status
# chips (and the Foundations caption) live *only* inside this band, so the
# Tableau row can never cover them regardless of fan depth or window size.
LABEL_BAND = 58.0
CHIP_GAP_ABOVE = 12.0
CHIP_HEIGHT = 30.0
CHIP_GAP_BELOW = 16.0
assert CHIP_GAP_ABOVE + CHIP_HEIGHT + CHIP_GAP_BELOW == LABEL_BAND
COLUMNS_TOP = TOP_MARGIN + float(CARD_H) + LABEL_BAND
SCENE_MARGIN_BOTTOM = 26.0

TABLEAU_GAP = 24
FOUNDATION_GAP = 20.0
STOCK_WASTE_GAP = 52.0
MIN_GAP = 8.0
MAX_GAP = 56.0

# Minimum horizontal footprint of the board at full card size. The view
# scales the scene down slightly below this width instead of cropping cards.
MIN_CONTENT_W = MARGIN * 2 + 7 * CARD_W + 6 * MIN_GAP
CONTENT_W = MARGIN * 2 + 7 * CARD_W + 6 * TABLEAU_GAP
CONTENT_H = COLUMNS_TOP + (14 * 6 + 30 * 6 + CARD_H) + SCENE_MARGIN_BOTTOM


def columns_top_for() -> float:
    """Scene y where the Tableau row starts (top of the reserved caption band)."""
    return COLUMNS_TOP


class GameBoardScene(QGraphicsScene):
    """Projects GameState onto the felt table and routes player intent."""

    def __init__(self, game: GameController, selection: SelectionController, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._selection = selection
        self._animation = None  # set via set_animation_manager
        self._drag_active = False
        # --- manual drag session state (cards follow the pointer) ----------
        self._drag_run: list[CardGraphicsItem] = []
        self._drag_card_ids: list[str] = []
        self._drag_source: str | None = None
        self._drag_offsets: list[QPointF] = []
        self._drag_grab_offset = QPointF()
        self._drag_legal: set[str] = set()
        self._drag_velocity = 0.0
        self._last_drag_pos = QPointF()
        self._target_pulse: QVariantAnimation | None = None
        self._pending_bounce: set[str] = set()
        # Invalid-drop feedback sequencing: the shake plays at the drop point
        # first, the fly-home sync is deferred to its `finished`. The counter
        # invalidates a pending callback as soon as anything authoritative
        # happens (any sync, any new drag) so feedback can never fight real
        # state projection.
        self._reject_seq = 0
        self.on_sound = None  # callback(name) wired by the workspace

        # Dynamic layout state (recomputed by `relayout`).
        self.fan_down = 14.0
        self.fan_up = 30.0
        self._slots: dict[str, QPointF] = {}

        self.setBackgroundBrush(QColor(8, 18, 12))
        self.felt = FeltBackgroundItem(float(CONTENT_W), float(CONTENT_H))
        self.addItem(self.felt)
        # Ambient light sweep: above the felt, below every pile and card.
        # The driving timer belongs to the scene (QObject) so the sweep can
        # never outlive its owner.
        self.light_sweep = LightSweepItem(float(CONTENT_W), float(CONTENT_H))
        self.addItem(self.light_sweep)
        self._sweep_timer = QTimer(self)
        self._sweep_timer.setInterval(42)
        self._sweep_timer.timeout.connect(lambda: self.light_sweep.step(42))

        # --- slot items (positions are set by `relayout`) -----------------------
        self.stock_item = StockGraphicsItem()
        self.stock_item.on_clicked = lambda _item: self._game.draw_from_stock()
        self.addItem(self.stock_item)

        self.waste_item = WasteGraphicsItem()
        self.waste_item.on_clicked = lambda _item: self._selection.clear()
        self.addItem(self.waste_item)

        self.foundation_items: dict[str, FoundationGraphicsItem] = {}
        for suit in Suit:
            item = FoundationGraphicsItem(suit)
            item.on_clicked = lambda clicked: self._on_slot_clicked(clicked.pile_id)
            self.foundation_items[item.pile_id] = item
            self.addItem(item)

        self.tableau_items: dict[str, TableauColumnGraphicsItem] = {}
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            item = TableauColumnGraphicsItem(column_id)
            item.on_clicked = lambda clicked: self._on_slot_clicked(clicked.pile_id)
            self.tableau_items[column_id] = item
            self.addItem(item)

        self._foundation_label = QGraphicsSimpleTextItem("Foundations")
        font = QFont("Georgia")
        font.setPixelSize(17)
        font.setBold(True)
        self._foundation_label.setFont(font)
        self._foundation_label.setBrush(QColor("#E8C766"))
        self.addItem(self._foundation_label)

        # --- card items -------------------------------------------------------
        self.card_items: dict[str, CardGraphicsItem] = {}
        self.card_zone: dict[str, str] = {}
        self.card_top: dict[str, bool] = {}
        self._trails = []

        self.relayout(float(CONTENT_W), float(CONTENT_H))

    # --- responsive layout ------------------------------------------------------
    def relayout(self, width: float, height: float) -> None:
        """Recompute the whole board geometry for a viewport of `width`x`height`
        scene units so the felt table fills the game viewport edge to edge.

        Card dimensions never shrink inside the scene; the view applies a
        mild uniform scale only when even the minimum footprint cannot fit.
        """
        width = max(width, MIN_CONTENT_W)
        height = max(height, 480.0)

        content_w = 7 * CARD_W + 6 * MIN_GAP
        # Distribute extra width into the gaps, capped for taste.
        free = width - 2 * MARGIN - 7 * CARD_W
        gap = max(MIN_GAP, min(MAX_GAP, free / 6.0))
        content_w = 7 * CARD_W + 6 * gap
        x0 = max(MARGIN, (width - content_w) / 2.0)

        top_y = TOP_MARGIN
        # The caption band is a fixed scene-space reservation, so the chips
        # under Stock/Waste stay collision-free at every viewport size; the
        # view scales the whole board uniformly when space is tight.
        columns_top = top_y + CARD_H + LABEL_BAND

        self._slots["stock"] = QPointF(x0, top_y)
        self._slots["waste"] = QPointF(x0 + CARD_W + STOCK_WASTE_GAP, top_y)

        foundations_width = 4 * CARD_W + 3 * FOUNDATION_GAP
        foundation_x = x0 + content_w - foundations_width
        for index, suit in enumerate(Suit):
            self._slots[f"foundation-{suit.code.lower()}"] = QPointF(
                foundation_x + index * (CARD_W + FOUNDATION_GAP), top_y
            )

        for index in range(1, 8):
            self._slots[f"tableau-{index}"] = QPointF(
                x0 + (index - 1) * (CARD_W + gap), columns_top
            )

        # Fan spacing adapts to the available column height so even tall
        # piles stay inside the felt; cards themselves never shrink here.
        bottom_reserve = 14.0
        column_available = height - columns_top - bottom_reserve
        self.fan_down = 13.0
        self.fan_up = (column_available - CARD_H - 6 * self.fan_down) / 6.0
        if self.fan_up < 14.0:
            self.fan_up = 14.0
            self.fan_down = max(8.0, (column_available - CARD_H - 6 * self.fan_up) / 6.0)
        self.fan_up = min(self.fan_up, 30.0)

        self.felt.set_size(float(width), float(height))
        self.light_sweep.set_size(float(width), float(height))
        self.setSceneRect(0.0, 0.0, float(width), float(height))

        self.stock_item.setPos(self._slots["stock"])
        self.waste_item.setPos(self._slots["waste"])
        for suit in Suit:
            pile_id = f"foundation-{suit.code.lower()}"
            self.foundation_items[pile_id].setPos(self._slots[pile_id])
        for index in range(1, 8):
            self.tableau_items[f"tableau-{index}"].setPos(self._slots[f"tableau-{index}"])

        label_rect = self._foundation_label.boundingRect()
        label_center = foundation_x + foundations_width / 2.0
        # Centred inside the reserved caption band, below the foundation row.
        self._foundation_label.setPos(
            label_center - label_rect.width() / 2.0,
            top_y + CARD_H + 15.0,
        )

        self.sync(animate=False)

    def set_animation_manager(self, manager) -> None:
        self._animation = manager
        self.apply_reduce_motion(manager.reduce_motion)

    def apply_reduce_motion(self, reduce_motion: bool) -> None:
        """Ambient effects obey Reduce Motion; call when the setting changes."""
        self.light_sweep.set_enabled(not reduce_motion)
        if reduce_motion:
            self._sweep_timer.stop()
        elif self.light_sweep.enabled:
            self._sweep_timer.start()

    def prepare_shutdown(self) -> None:
        """Stop all cosmetic animation before the widget tree is destroyed.

        Called from the main window's closeEvent so teardown happens while
        every item is alive and idle — never during Python garbage
        collection of a partially destroyed Qt object graph.
        """
        if self._animation is not None:
            self._animation.interrupt_all()
        self._sweep_timer.stop()

    def settle_all(self) -> None:
        """Force every card to its authoritative engine-derived position.

        Cosmetic moves are interrupted and the projection re-snaps without
        animation. Game state is untouched — this only settles the *paint*,
        so screenshots and tests never observe a card mid-flight.
        """
        if self._animation is not None:
            self._animation.interrupt_all()
        self.sync(animate=False)

    # --- projection -----------------------------------------------------------
    def slot_position(self, pile_id: str) -> QPointF:
        return self._slots[pile_id]

    def sync(self, animate: bool = True, reason: str | None = None) -> None:
        """Re-derive all card positions/z-orders from the engine state."""
        # Any authoritative reconciliation supersedes a pending invalid-drop
        # feedback sequence: its deferred fly-home must never fire after (or
        # during) a sync that projects real state.
        self._reject_seq += 1
        # A state change during an active manual drag (header button,
        # shortcut) ends the drag first so the projection stays authoritative.
        if self._drag_run:
            self._end_drag_session()
        state = self._game.state
        seen: set[str] = set()
        previous_positions: dict[str, QPointF] = {
            card_id: item.pos() for card_id, item in self.card_items.items()
        }
        was_face_up = {card_id: item.card.face_up for card_id, item in self.card_items.items()}
        previous_zones = dict(self.card_zone)

        placements: list[tuple[CardGraphicsItem, QPointF, float, bool, int]] = []

        # Stock (front of the FIFO queue renders on top of the pile).
        stock_cards = state.stock.to_list()
        stock_pos = self._slots["stock"]
        for index, card in enumerate(stock_cards):
            item = self._item_for(card)
            offset = 2.0 * max(0, min(index, 2))
            placements.append(
                (item, QPointF(stock_pos.x() - offset, stock_pos.y() - offset), 5.0 + index, False, -1)
            )
            seen.add(card.card_id)

        # Waste: fan the newest three cards.
        waste_cards = state.waste.to_list()
        visible = waste_cards[-3:]
        waste_pos = self._slots["waste"]
        for index, card in enumerate(waste_cards):
            item = self._item_for(card)
            fan_index = visible.index(card) if card in visible else len(visible) - 1
            target = QPointF(waste_pos.x() + fan_index * WASTE_FAN, waste_pos.y())
            placements.append((item, target, 5.0 + index, True, fan_index))
            seen.add(card.card_id)

        # Foundations: the full stack sits on the slot, top card visible.
        for suit in Suit:
            pile_id = f"foundation-{suit.code.lower()}"
            foundation_cards = state.foundations[suit].to_list()
            pos = self._slots[pile_id]
            for index, card in enumerate(foundation_cards):
                item = self._item_for(card)
                placements.append((item, QPointF(pos), 5.0 + index, True, -1))
                seen.add(card.card_id)

        # Tableau columns with fan offsets.
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            column = state.tableau[column_id]
            pos = self._slots[column_id]
            y = pos.y()
            for card_index, card in enumerate(column.cards_bottom_to_top()):
                item = self._item_for(card)
                placements.append((item, QPointF(pos.x(), y), 10.0 + card_index, card.face_up, -1))
                y += self.fan_down if not card.face_up else self.fan_up
                seen.add(card.card_id)

        # Drop items that vanished from play (defensive; all 52 should stay).
        for card_id in set(self.card_items) - seen:
            item = self.card_items.pop(card_id)
            self.removeItem(item)

        self.card_top = {card_id: False for card_id in seen}
        stock_pos = self._slots["stock"]
        for item, target, z_value, _face_up, draw_fan_index in placements:
            card_id = item.card_id
            old = previous_positions.get(card_id)
            moved = old is not None and (old - target).manhattanLength() > 0.5
            bounce = card_id in self._pending_bounce and moved
            if bounce:
                self._pending_bounce.discard(card_id)
            # Draw-3 stagger: cards that just left the Stock land on the
            # Waste fan left-to-right with small delays (scaled by the
            # animation speed like every other cosmetic duration).
            delay_ms = 0
            if (
                draw_fan_index >= 0
                and moved
                and old is not None
                and (old - stock_pos).manhattanLength() < 16.0
            ):
                delay_ms = draw_fan_index * self._animation.duration_for(60)
            if old is None:
                item.setPos(target)
            elif moved and animate and self._animation is not None:
                self._animation.animate_move(
                    item, item.pos(), target, z_value, bounce=bounce, delay_ms=delay_ms
                )
            else:
                if self._animation is not None:
                    self._animation.snap(item, target, z_value)
                else:
                    item.setPos(target)
                    item.setZValue(z_value)
        self._pending_bounce.clear()

        # Faces: flip items whose card changed visibility.
        for item, _target, _z, _face, _fan in placements:
            card = item.card
            if was_face_up.get(item.card_id) != card.face_up:
                item.refresh_face(animated=animate and self._animation is not None)
                if animate and self._animation is not None and self.on_sound is not None:
                    self.on_sound("card_flip")

        # Slot decorations.
        self.stock_item.set_state(
            len(stock_cards),
            len(stock_cards) == 0 and not state.waste.is_empty(),
        )
        self.waste_item.set_state(len(waste_cards))
        for suit in Suit:
            pile_id = f"foundation-{suit.code.lower()}"
            self.foundation_items[pile_id].set_occupied(not state.foundations[suit].is_empty())
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            self.tableau_items[column_id].set_empty(state.tableau[column_id].is_empty())

        self.refresh_zone_map()
        self.refresh_highlights()

        # Universal Foundation celebration: any card that *lands* on a
        # foundation since the previous projection gets the gold welcome —
        # whether it arrived by drag, click-to-move or a redo replay.
        if animate:
            for card_id, pile_id in self.card_zone.items():
                old_pile = previous_zones.get(card_id)
                if (
                    pile_id != old_pile
                    and pile_id.startswith("foundation-")
                    and not (old_pile or "").startswith("foundation-")
                ):
                    self._celebrate_foundation(pile_id)

    def refresh_zone_map(self) -> None:
        """Recompute the card_id -> pile_id and top-card maps from state."""
        state = self._game.state
        zone_map: dict[str, str] = {}
        top_map: dict[str, bool] = {}
        for card in state.stock.to_list():
            zone_map[card.card_id] = "stock"
            top_map[card.card_id] = False
        waste_cards = state.waste.to_list()
        for index, card in enumerate(waste_cards):
            zone_map[card.card_id] = "waste"
            top_map[card.card_id] = index == len(waste_cards) - 1
        for suit in Suit:
            pile_id = f"foundation-{suit.code.lower()}"
            foundation_cards = state.foundations[suit].to_list()
            for index, card in enumerate(foundation_cards):
                zone_map[card.card_id] = pile_id
                top_map[card.card_id] = index == len(foundation_cards) - 1
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            cards = state.tableau[column_id].cards_bottom_to_top()
            for position, card in enumerate(cards):
                zone_map[card.card_id] = column_id
                top_map[card.card_id] = position == len(cards) - 1
        self.card_zone = zone_map
        self.card_top = top_map

        for card_id, item in self.card_items.items():
            pile_id = self.card_zone.get(card_id)
            if pile_id is not None and pile_id.startswith("tableau-"):
                # Any face-up card in a tableau column can start a run drag.
                interactive = item.card.face_up
            else:
                interactive = self.card_top.get(card_id, False)
            item.set_interactive(interactive)

    def refresh_highlights(self, drag_legal: set[str] | None = None) -> None:
        """Apply selection + legal destination effects from the selection.

        During a manual drag `drag_legal` replaces the click-selection as
        the source of legal targets, and the dragged run glows mint.
        """
        legal = set(self._selection.legal_destinations()) if drag_legal is None else set(drag_legal)
        for pile_id, item in self.tableau_items.items():
            item.set_legal_target(pile_id in legal)
        for pile_id, item in self.foundation_items.items():
            item.set_legal_target(pile_id in legal)

        if drag_legal is None:
            run_ids = set(self._selection.selected_run())
        else:
            run_ids = set(self._drag_card_ids)
        for card_id, item in self.card_items.items():
            if run_ids:
                item.set_highlight(1.0 if card_id in run_ids else 0.0)
            elif item.get_highlight() > 0.0:
                item.set_highlight(0.0)

        # Gold ring on destination top cards (occupied legal targets).
        state = self._game.state
        for pile_id in legal:
            if pile_id.startswith("tableau-"):
                column = state.tableau[pile_id]
                if not column.is_empty():
                    top_id = column.peek().card_id
                    item = self.card_items.get(top_id)
                    if item is not None:
                        item.set_hint(0.55)
            elif pile_id.startswith("foundation-"):
                foundation = state.foundations[_suit_for_pile(pile_id)]
                if not foundation.is_empty():
                    top_id = foundation.peek().card_id
                    item = self.card_items.get(top_id)
                    if item is not None:
                        item.set_hint(0.55)

    def show_hint(self, hint) -> None:
        """Pulse the hint's source card and destination pile."""
        if hint is None:
            return
        if self._animation is not None:
            for card_id in hint.card_ids:
                item = self.card_items.get(card_id)
                if item is not None:
                    self._animation.pulse_hint(item)
        destination_item = self.tableau_items.get(hint.destination_pile) or self.foundation_items.get(
            hint.destination_pile
        )
        if destination_item is not None and self._animation is not None:
            self._animation.pulse_property(destination_item, "legal_glow")

    # --- internals -------------------------------------------------------------
    def _item_for(self, card) -> CardGraphicsItem:
        item = self.card_items.get(card.card_id)
        if item is None:
            item = CardGraphicsItem(card)
            item.on_clicked = self._on_card_clicked
            item.drag_provider = self._drag_payload_for
            item.on_drag_started = self.begin_card_drag
            item.on_drag_moved = self.update_card_drag
            item.on_drag_dropped = self.finish_card_drag
            self.card_items[card.card_id] = item
            self.addItem(item)
        else:
            item.refresh_card(card)
        return item

    def _drag_payload_for(self, card_id: str) -> tuple[list[str], str] | None:
        """Resolve a card press into a draggable run (card_ids, source pile)."""
        pile_id = self.card_zone.get(card_id)
        if pile_id is None or pile_id == "stock":
            return None
        if pile_id.startswith("foundation-"):
            return None  # foundations are fixed home piles
        if pile_id == "waste":
            waste = self._game.state.waste
            if waste.is_empty() or waste.peek().card_id != card_id:
                return None
            return [card_id], pile_id
        column = self._game.state.tableau.get(pile_id)
        if column is None:
            return None
        cards = column.cards_bottom_to_top()
        for position, card in enumerate(cards):
            if card.card_id == card_id:
                if not card.face_up:
                    return None
                return [entry.card_id for entry in cards[position:]], pile_id
        return None

    def _on_card_clicked(self, item: CardGraphicsItem) -> None:
        card_id = item.card_id
        pile_id = self.card_zone.get(card_id)
        if pile_id is None:
            return
        if pile_id == "stock":
            self._game.draw_from_stock()
            return
        self._selection.click_card(
            pile_id,
            card_id,
            face_up=item.card.face_up,
            top_of_pile=self.card_top.get(card_id, False),
        )

    def _on_slot_clicked(self, pile_id: str) -> None:
        if pile_id == "stock":
            self._game.draw_from_stock()
            return
        self._selection.click_pile(pile_id)

    # --- manual drag session -----------------------------------------------------
    def begin_card_drag(self, item: CardGraphicsItem, scene_pos: QPointF) -> None:
        """Start a manual drag: the grabbed run will follow the pointer."""
        if self._drag_run:
            return
        # Grabbing during an invalid-drop shake supersedes the pending
        # fly-home: the interrupt below would otherwise fire the deferred
        # sync *inside this method*, starting movement animations that fight
        # the manual drag over `pos`. The next drop syncs instead.
        self._reject_seq += 1
        payload = item.drag_provider(item.card_id) if item.drag_provider else None
        if not payload:
            return
        card_ids, source = payload
        run_items = []
        for card_id in card_ids:
            run_item = self.card_items.get(card_id)
            if run_item is None:
                return
            if self._animation is not None:
                self._animation.interrupt_for(run_item)
            run_items.append(run_item)
        self._drag_run = run_items
        self._drag_card_ids = list(card_ids)
        self._drag_source = source
        self._drag_offsets = [run_item.pos() - run_items[0].pos() for run_item in run_items]
        self._drag_grab_offset = QPointF(scene_pos) - run_items[0].pos()
        self._last_drag_pos = QPointF(scene_pos)
        self._drag_velocity = 0.0
        self._drag_legal = set(self._game.legal_destinations(source, card_ids[0]))
        for index, run_item in enumerate(run_items):
            run_item.begin_drag_session()
            run_item.setZValue(300.0 + index)
        self._drag_active = True
        self._selection.clear()
        self.refresh_highlights(drag_legal=self._drag_legal)
        self._start_target_pulse()
        if self.on_sound is not None:
            self.on_sound("card_pick")

    def update_card_drag(self, item: CardGraphicsItem, scene_pos: QPointF) -> None:
        """Move the run with the pointer one-to-one; tilt from velocity."""
        if not self._drag_run:
            return
        leader = self._drag_run[0]
        target = QPointF(scene_pos) - self._drag_grab_offset
        velocity = QPointF(scene_pos).x() - self._last_drag_pos.x()
        self._drag_velocity = 0.7 * self._drag_velocity + 0.3 * velocity
        tilt = max(-1.0, min(1.0, self._drag_velocity / 30.0))
        # Velocity is already smoothed; set directly (no per-event animation).
        leader.set_drag_tilt(tilt)
        self._last_drag_pos = QPointF(scene_pos)
        for index, run_item in enumerate(self._drag_run):
            run_item.setPos(target + self._drag_offsets[index])

    def finish_card_drag(self, item: CardGraphicsItem, scene_pos: QPointF) -> None:
        """Resolve the drop through the engine; reject safely when invalid."""
        if not self._drag_run:
            return
        run_items = list(self._drag_run)
        card_ids = list(self._drag_card_ids)
        source = self._drag_source
        target_pile = self._pile_id_at(QPointF(scene_pos), exclude=set(card_ids))
        self._end_drag_session()

        # Optimistic bounce: try_move emits state_changed, and the sync it
        # triggers attaches the settle pop to these exact cards. Cleared on
        # rejection so no later move inherits a phantom bounce.
        self._pending_bounce.update(card_ids)
        moved = False
        if target_pile is not None and target_pile != source:
            moved = self._game.try_move(source, card_ids[0], target_pile)

        if moved:
            # Foundation celebration is handled universally inside sync()
            # (it detects the zone change), so nothing extra is needed here.
            self.refresh_highlights()
        else:
            self._pending_bounce.clear()
            self.refresh_highlights()
            if target_pile is not None and target_pile != source:
                # Rejected by the rules: coral flash + shake play here, at
                # the drop point. The fly-home sync is deferred until the
                # shake finishes — starting it right away would let the
                # movement animation manager's interrupt cancel the shake.
                # The engine never mutated, so the deferred `sync` restores
                # the exact authoritative layout.
                self._start_reject_fly_home(run_items[0])
            else:
                # Dropped on no pile (or the source pile): no shake, the run
                # simply returns home.
                self.sync(animate=True)

    def _start_reject_fly_home(self, grabbed: CardGraphicsItem) -> None:
        """Coral flash + shake now, fly the run home when the shake ends."""
        # Invalidate any pending rejection feedback *before* the new shake
        # may stop the old one (stop() fires its callback synchronously).
        self._reject_seq += 1
        token = self._reject_seq
        grabbed.animate_error()
        shake = None
        if self._animation is not None:
            shake = self._animation.invalid_shake(grabbed)
        if shake is None:
            # Reduce Motion (or no manager): skip straight to the return trip.
            self.sync(animate=True)
            return

        def _fly_home() -> None:
            try:
                if token != self._reject_seq:
                    return  # superseded by a real sync or a newer interaction
                if self._drag_run:
                    return  # user grabbed cards again; their drop will sync
                self.sync(animate=True)
            except RuntimeError:
                pass  # scene torn down mid-shake; nothing left to project

        shake.finished.connect(_fly_home)

    def _end_drag_session(self) -> None:
        self._stop_target_pulse()
        for run_item in self._drag_run:
            run_item.end_drag_session()
        self._drag_run = []
        self._drag_card_ids = []
        self._drag_source = None
        self._drag_offsets = []
        self._drag_legal = set()
        self._drag_active = False

    def _start_target_pulse(self) -> None:
        """Legal targets breathe while a drag is in flight."""
        if self._animation is None or self._animation.reduce_motion:
            return
        if self._target_pulse is not None:
            return
        pulse = QVariantAnimation(self)
        pulse.setDuration(760)
        pulse.setLoopCount(-1)
        pulse.setStartValue(0.0)
        pulse.setEndValue(1.0)
        pulse.valueChanged.connect(self._on_target_pulse)
        self._target_pulse = pulse
        pulse.start()

    def _on_target_pulse(self, value) -> None:
        phase = 0.5 - 0.5 * math.cos(2.0 * math.pi * float(value))
        for pile_id in self._drag_legal:
            slot = self.tableau_items.get(pile_id) or self.foundation_items.get(pile_id)
            if slot is not None:
                slot.set_legal_glow(0.55 + 0.45 * phase)

    def _stop_target_pulse(self) -> None:
        if self._target_pulse is not None:
            self._target_pulse.stop()
            self._target_pulse.deleteLater()
            self._target_pulse = None

    def _celebrate_foundation(self, pile_id: str) -> None:
        """Distinctive feedback when a card reaches a Foundation."""
        foundation_item = self.foundation_items.get(pile_id)
        if foundation_item is not None and self._animation is not None:
            self._animation.pulse_property(foundation_item, "legal_glow")
        if self._animation is None or self._animation.reduce_motion:
            return
        from solitaire.ui.premium.graphics.effects.particle_burst import ParticleBurstItem

        slot = self._slots[pile_id]
        center = QPointF(slot.x() + CARD_W / 2.0, slot.y() + CARD_H / 2.0)
        burst = ParticleBurstItem(center)
        self.addItem(burst)
        burst.start()
        if self.on_sound is not None:
            self.on_sound("foundation")

    # --- new-game dealing choreography ------------------------------------------
    def play_deal_sequence(self) -> None:
        """Cosmetic dealer choreography after a fresh game.

        All 28 dealt tableau cards visually depart from the Stock and fly
        to their authoritative positions in true dealing order (row-major
        across the seven columns), face-up cards flipping as they land.
        Pure projection: the engine state is untouched, and any user action
        during the sequence simply supersedes the flight (see the animation
        manager's supersede rule).
        """
        if self._animation is None or self._animation.reduce_motion:
            return
        state = self._game.state
        columns = [state.tableau[f"tableau-{index}"] for index in range(1, 8)]
        max_depth = max((len(column.cards_bottom_to_top()) for column in columns), default=0)
        order: list[tuple[CardGraphicsItem, float, bool]] = []
        for depth in range(max_depth):
            for column in columns:
                cards = column.cards_bottom_to_top()
                if depth < len(cards):
                    card = cards[depth]
                    item = self.card_items.get(card.card_id)
                    if item is not None:
                        order.append((item, item.zValue(), card.face_up))
        if not order:
            return
        stock_pos = self._slots["stock"]
        # Stagger and travel both follow the animation speed: 2.0x deals
        # twice as fast (half the gap, half the flight), so the whole
        # choreography halves instead of keeping long pauses between cards.
        stagger = self._animation.duration_for(36)
        travel = self._animation.duration_for(ANIMATION_MS["move"])
        for index, (item, z_value, face_up) in enumerate(order):
            target = item.pos()
            delay = index * stagger
            item.set_flip(1.0)  # every dealt card leaves the deck face-down
            item.setPos(stock_pos)
            self._animation.animate_move(
                item, stock_pos, target, z_value, base_ms=ANIMATION_MS["move"], delay_ms=delay
            )
            if face_up:
                flip_at = delay + max(90, travel - 90)
                QTimer.singleShot(
                    flip_at,
                    lambda target_item=item: self._flip_after_deal(target_item),
                )
        if self.on_sound is not None:
            self.on_sound("stock_draw")

    def _flip_after_deal(self, item: CardGraphicsItem) -> None:
        try:
            if item.scene() is None:
                return
            item.refresh_face(animated=True)
        except RuntimeError:
            return

    # --- Qt drag & drop ----------------------------------------------------------
    def dragEnterEvent(self, event: QGraphicsDragDropEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
            self._drag_active = True
        else:
            event.ignore()

    def dragMoveEvent(self, event: QGraphicsDragDropEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QGraphicsDragDropEvent) -> None:  # noqa: N802
        self._drag_active = False
        payload = _parse_payload(event.mimeData())
        if payload is None:
            event.ignore()
            return
        card_ids, source = payload
        target = self._pile_id_at(event.scenePos())
        if target is None:
            event.ignore()
            return
        event.acceptProposedAction()
        if target == source and not card_ids:
            return
        self._game.try_move(source, card_ids[0] if card_ids else None, target)

    def dragLeaveEvent(self, event: QGraphicsDragDropEvent) -> None:  # noqa: N802
        self._drag_active = False
        super().dragLeaveEvent(event)

    def _pile_id_at(self, pos: QPointF, exclude: set[str] | None = None) -> str | None:
        """Resolve a drop using the supplied scene coordinate only.

        ``QGraphicsItem.isUnderMouse()`` describes the real cursor position,
        not the event's scenePos. During QtTest delivery (and with a moving
        cursor on slower systems) those can differ, so mixing it with
        ``contains(pos)`` can select an unrelated pile and turn a rejected
        drop into a source-pile no-op. Drop routing must be a pure function of
        the release coordinate.
        """
        excluded = exclude or set()
        for pile_id, item in self.foundation_items.items():
            if item.sceneBoundingRect().contains(pos):
                return pile_id
        for pile_id, item in self.tableau_items.items():
            if item.sceneBoundingRect().contains(pos):
                return pile_id
        if self.stock_item.sceneBoundingRect().contains(pos):
            return "stock"
        if self.waste_item.sceneBoundingRect().contains(pos):
            return "waste"

        # Occupied piles: resolve via cards under the drop point, ignoring
        # the dragged run itself (it hovers exactly under the cursor).
        item = next(
            (
                graphics
                for graphics in self.items(pos)
                if isinstance(graphics, CardGraphicsItem) and graphics.card_id not in excluded
            ),
            None,
        )
        if item is not None:
            return self.card_zone.get(item.card_id)
        return None


def _suit_for_pile(pile_id: str) -> Suit:
    code = pile_id.rsplit("-", 1)[1].upper()
    for suit in Suit:
        if suit.code == code:
            return suit
    raise ValueError(f"unknown foundation pile: {pile_id}")


def _parse_payload(mime) -> tuple[list[str], str] | None:
    from solitaire.ui.premium.controllers.drag_controller import parse_payload

    return parse_payload(mime)
