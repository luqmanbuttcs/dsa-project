"""GameBoardScene: composition, state projection and interaction.

The scene is a *projection* of the authoritative GameState. After every
controller action it re-derives every card's zone/position/z-order from the
engine and reuses existing CardGraphicsItems (keyed by card_id) so items
keep their identity across refreshes. Animation is cosmetic and always
reconciles to the final engine state.
"""

from __future__ import annotations

import json

from PyQt6.QtCore import QPointF, QRectF, Qt
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
from solitaire.ui.premium.graphics.stock_item import StockGraphicsItem
from solitaire.ui.premium.graphics.tableau_item import TableauColumnGraphicsItem
from solitaire.ui.premium.graphics.waste_item import WasteGraphicsItem
from solitaire.ui.premium.theme import (
    CARD_H,
    CARD_W,
    FAN_FACE_DOWN,
    FAN_FACE_UP,
    TABLEAU_GAP,
    WASTE_FAN,
)

MARGIN = 30.0
TOP_ROW_H = float(CARD_H)
COLUMNS_TOP = TOP_ROW_H + 62.0
SCENE_MARGIN_BOTTOM = 26.0

CONTENT_W = MARGIN * 2 + 7 * CARD_W + 6 * TABLEAU_GAP
CONTENT_H = COLUMNS_TOP + (FAN_FACE_DOWN * 6 + FAN_FACE_UP * 6 + CARD_H) + SCENE_MARGIN_BOTTOM

FOUNDATION_GAP = 20.0
STOCK_WASTE_GAP = 52.0


class GameBoardScene(QGraphicsScene):
    """Projects GameState onto the felt table and routes player intent."""

    def __init__(self, game: GameController, selection: SelectionController, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._selection = selection
        self._animation = None  # set via set_animation_manager
        self._drag_active = False

        self.setSceneRect(0.0, 0.0, float(CONTENT_W), float(CONTENT_H))
        self.setBackgroundBrush(QColor(8, 18, 12))

        self.felt = FeltBackgroundItem(float(CONTENT_W), float(CONTENT_H))
        self.addItem(self.felt)

        # --- slot geometry ---------------------------------------------------
        self._slots: dict[str, QPointF] = {}
        x = MARGIN
        self._slots["stock"] = QPointF(x, 16.0)
        self._slots["waste"] = QPointF(x + CARD_W + STOCK_WASTE_GAP, 16.0)

        foundations_width = 4 * CARD_W + 3 * FOUNDATION_GAP
        foundation_x = float(CONTENT_W) - MARGIN - foundations_width
        for index, suit in enumerate(Suit):
            self._slots[f"foundation-{suit.code.lower()}"] = QPointF(
                foundation_x + index * (CARD_W + FOUNDATION_GAP), 16.0
            )

        for index in range(1, 8):
            column_id = f"tableau-{index}"
            self._slots[column_id] = QPointF(
                MARGIN + (index - 1) * (CARD_W + TABLEAU_GAP), COLUMNS_TOP
            )

        # --- slot items ---------------------------------------------------------
        self.stock_item = StockGraphicsItem()
        self.stock_item.setPos(self._slots["stock"])
        self.stock_item.on_clicked = lambda _item: self._game.draw_from_stock()
        self.addItem(self.stock_item)

        self.waste_item = WasteGraphicsItem()
        self.waste_item.setPos(self._slots["waste"])
        self.waste_item.on_clicked = lambda _item: self._selection.clear()
        self.addItem(self.waste_item)

        self.foundation_items: dict[str, FoundationGraphicsItem] = {}
        for suit in Suit:
            item = FoundationGraphicsItem(suit)
            item.setPos(self._slots[f"foundation-{suit.code.lower()}"])
            item.on_clicked = lambda clicked: self._on_slot_clicked(clicked.pile_id)
            self.foundation_items[item.pile_id] = item
            self.addItem(item)

        self.tableau_items: dict[str, TableauColumnGraphicsItem] = {}
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            item = TableauColumnGraphicsItem(column_id)
            item.setPos(self._slots[column_id])
            item.on_clicked = lambda clicked: self._on_slot_clicked(clicked.pile_id)
            self.tableau_items[column_id] = item
            self.addItem(item)

        self._foundation_label = QGraphicsSimpleTextItem("Foundations")
        font = QFont("Georgia")
        font.setPixelSize(17)
        font.setBold(True)
        self._foundation_label.setFont(font)
        self._foundation_label.setBrush(QColor("#E8C766"))
        label_center = foundation_x + foundations_width / 2.0
        label_rect = self._foundation_label.boundingRect()
        self._foundation_label.setPos(
            label_center - label_rect.width() / 2.0, TOP_ROW_H + 20.0
        )
        self.addItem(self._foundation_label)

        # --- card items -------------------------------------------------------
        self.card_items: dict[str, CardGraphicsItem] = {}
        self.card_zone: dict[str, str] = {}
        self.card_top: dict[str, bool] = {}
        self._trails = []
        self.sync(animate=False)

    def set_animation_manager(self, manager) -> None:
        self._animation = manager

    # --- projection -----------------------------------------------------------
    def slot_position(self, pile_id: str) -> QPointF:
        return self._slots[pile_id]

    def sync(self, animate: bool = True) -> None:
        """Re-derive all card positions/z-orders from the engine state."""
        state = self._game.state
        seen: set[str] = set()
        previous_positions: dict[str, QPointF] = {
            card_id: item.pos() for card_id, item in self.card_items.items()
        }
        was_face_up = {card_id: item.card.face_up for card_id, item in self.card_items.items()}

        placements: list[tuple[CardGraphicsItem, QPointF, float, bool]] = []

        # Stock (front of the FIFO queue renders on top of the pile).
        stock_cards = state.stock.to_list()
        stock_pos = self._slots["stock"]
        for index, card in enumerate(stock_cards):
            item = self._item_for(card)
            offset = 2.0 * max(0, min(index, 2))
            placements.append((item, QPointF(stock_pos.x() - offset, stock_pos.y() - offset), 5.0 + index, False))
            seen.add(card.card_id)

        # Waste: fan the newest three cards.
        waste_cards = state.waste.to_list()
        visible = waste_cards[-3:]
        waste_pos = self._slots["waste"]
        for index, card in enumerate(waste_cards):
            item = self._item_for(card)
            fan_index = visible.index(card) if card in visible else len(visible) - 1
            target = QPointF(waste_pos.x() + fan_index * WASTE_FAN, waste_pos.y())
            placements.append((item, target, 5.0 + index, True))
            seen.add(card.card_id)

        # Foundations: the full stack sits on the slot, top card visible.
        for suit in Suit:
            pile_id = f"foundation-{suit.code.lower()}"
            foundation_cards = state.foundations[suit].to_list()
            pos = self._slots[pile_id]
            for index, card in enumerate(foundation_cards):
                item = self._item_for(card)
                placements.append((item, QPointF(pos), 5.0 + index, True))
                seen.add(card.card_id)

        # Tableau columns with fan offsets.
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            column = state.tableau[column_id]
            pos = self._slots[column_id]
            y = pos.y()
            for card_index, card in enumerate(column.cards_bottom_to_top()):
                item = self._item_for(card)
                placements.append((item, QPointF(pos.x(), y), 10.0 + card_index, card.face_up))
                y += FAN_FACE_DOWN if not card.face_up else FAN_FACE_UP
                seen.add(card.card_id)

        # Drop items that vanished from play (defensive; all 52 should stay).
        for card_id in set(self.card_items) - seen:
            item = self.card_items.pop(card_id)
            self.removeItem(item)

        self.card_top = {card_id: False for card_id in seen}
        for item, target, z_value, _face_up in placements:
            card_id = item.card_id
            old = previous_positions.get(card_id)
            moved = old is not None and (old - target).manhattanLength() > 0.5
            if old is None:
                item.setPos(target)
            elif moved and animate and self._animation is not None:
                self._animation.animate_move(item, item.pos(), target, z_value)
            else:
                if self._animation is not None:
                    self._animation.snap(item, target, z_value)
                else:
                    item.setPos(target)
                    item.setZValue(z_value)

        # Faces: flip items whose card changed visibility.
        for item, _target, _z, _face in placements:
            card = item.card
            if was_face_up.get(item.card_id) != card.face_up:
                item.refresh_face(animated=animate and self._animation is not None)

        # Slot decorations.
        self.stock_item.set_state(
            len(stock_cards),
            len(stock_cards) == 0 and not state.waste.is_empty(),
        )
        for suit in Suit:
            pile_id = f"foundation-{suit.code.lower()}"
            self.foundation_items[pile_id].set_occupied(not state.foundations[suit].is_empty())
        for index in range(1, 8):
            column_id = f"tableau-{index}"
            self.tableau_items[column_id].set_empty(state.tableau[column_id].is_empty())

        self.refresh_zone_map()
        self.refresh_highlights()

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
            item.set_interactive(self.card_top.get(card_id, False))

    def refresh_highlights(self) -> None:
        """Apply selection + legal destination effects from the selection."""
        legal = set(self._selection.legal_destinations())
        for pile_id, item in self.tableau_items.items():
            item.set_legal_target(pile_id in legal)
        for pile_id, item in self.foundation_items.items():
            item.set_legal_target(pile_id in legal)

        selected_id = self._selection.card_id
        for card_id, item in self.card_items.items():
            if selected_id and card_id == selected_id:
                item.set_highlight(1.0)
            else:
                if item.get_highlight() > 0.0:
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
            self.card_items[card.card_id] = item
            self.addItem(item)
        else:
            item.refresh_card(card)
        return item

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

    def _pile_id_at(self, pos: QPointF) -> str | None:
        for pile_id, item in self.foundation_items.items():
            if item.isUnderMouse() or item.sceneBoundingRect().contains(pos):
                return pile_id
        for pile_id, item in self.tableau_items.items():
            if item.isUnderMouse() or item.sceneBoundingRect().contains(pos):
                return pile_id
        # Occupied piles: resolve via cards under the drop point.
        item = next(
            (graphics for graphics in self.items(pos) if isinstance(graphics, CardGraphicsItem)),
            None,
        )
        if item is not None:
            return self.card_zone.get(item.card_id)
        if self.stock_item.isUnderMouse():
            return "stock"
        if self.waste_item.isUnderMouse():
            return "waste"
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
