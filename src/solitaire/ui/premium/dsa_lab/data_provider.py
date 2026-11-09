"""Pure read-model helpers turning the live GameState + OperationTracker
into presentation data for the dashboard and the DSA Lab inspectors.

Nothing here mutates state, and every number is derived from the real
tracker events or the real piles — never simulated or hard-coded.
"""

from __future__ import annotations

from dataclasses import dataclass

from solitaire.domain.card import Suit
from solitaire.domain.game_state import Zone
from solitaire.domain.operations import OperationEvent, OperationTracker, StructureName

STRUCTURE_LABELS = {
    StructureName.ARRAY_LIST: "Array / List",
    StructureName.STACK: "Stack",
    StructureName.QUEUE: "Queue",
    StructureName.LINKED_LIST: "Linked List",
    StructureName.DICTIONARY: "Dictionary",
    StructureName.GAME: "Game",
}


def structure_counts(tracker: OperationTracker) -> dict[str, int]:
    """Real per-structure event counts."""
    return {
        STRUCTURE_LABELS[structure]: tracker.count(structure) for structure in StructureName
    }


def operation_counts(tracker: OperationTracker, structure: StructureName) -> dict[str, int]:
    counts: dict[str, int] = {}
    for (event_structure, operation), count in tracker._operation_counts.items():
        if event_structure is structure:
            counts[operation] = count
    return counts


def latest_operation(tracker: OperationTracker) -> OperationEvent | None:
    events = tracker.events
    return events[-1] if events else None


def events_for_structure(tracker: OperationTracker, structure: StructureName) -> tuple[OperationEvent, ...]:
    return tuple(event for event in tracker.events if event.structure is structure)


# --- array / list ---------------------------------------------------------------


@dataclass(frozen=True)
class ArrayReport:
    create_deck_events: int
    shuffle_events: int
    deal_events: int
    clear_events: int
    deck_size_now: int
    deal_order: tuple[str, ...]


def array_report(tracker: OperationTracker, deck_size_now: int) -> ArrayReport:
    events = tracker.events
    deal_order: list[str] = []
    for event in events:
        if event.structure is StructureName.ARRAY_LIST and event.operation == "POP_FOR_DEAL":
            deal_order.extend(event.card_ids)
    return ArrayReport(
        create_deck_events=sum(
            1 for e in events if e.structure is StructureName.ARRAY_LIST and e.operation == "CREATE_DECK"
        ),
        shuffle_events=sum(
            1 for e in events if e.structure is StructureName.ARRAY_LIST and e.operation == "SHUFFLE"
        ),
        deal_events=sum(
            1 for e in events if e.structure is StructureName.ARRAY_LIST and e.operation == "POP_FOR_DEAL"
        ),
        clear_events=sum(
            1 for e in events if e.structure is StructureName.ARRAY_LIST and e.operation == "CLEAR_AFTER_DEAL"
        ),
        deck_size_now=deck_size_now,
        deal_order=tuple(deal_order),
    )


# --- stack ------------------------------------------------------------------------


@dataclass(frozen=True)
class StackReport:
    pile_label: str
    size: int
    top_card_id: str | None
    order_bottom_to_top: tuple[str, ...]
    operations: dict[str, int]


def stack_report_for_pile(game, pile_id: str) -> StackReport:
    """Build a real stack view for waste / tableau / foundation piles."""
    state = game.state
    if pile_id == "waste":
        cards = state.waste.to_list()
        label = "Waste"
    elif pile_id.startswith("tableau-"):
        cards = state.tableau[pile_id].cards_bottom_to_top()
        label = pile_id.replace("tableau-", "Tableau ")
    elif pile_id.startswith("foundation-"):
        suit = _suit_for_pile(pile_id)
        cards = state.foundations[suit].to_list()
        label = f"{suit.value} Foundation"
    elif pile_id == "undo-history":
        label = "Undo History"
        size = game.engine.undo_stack.size()
        operations = operation_counts(game.tracker, StructureName.STACK)
        return StackReport(label, size, None, (), {
            key: value for key, value in operations.items() if key in ("PUSH", "POP")
        })
    elif pile_id == "redo-history":
        label = "Redo History"
        size = game.engine.redo_stack.size()
        operations = operation_counts(game.tracker, StructureName.STACK)
        return StackReport(label, size, None, (), {
            key: value for key, value in operations.items() if key in ("PUSH", "POP")
        })
    else:
        raise ValueError(f"unknown stack pile: {pile_id}")

    return StackReport(
        pile_label=label,
        size=len(cards),
        top_card_id=cards[-1].card_id if cards else None,
        order_bottom_to_top=tuple(card.card_id for card in cards),
        operations=_stack_operations_for(game.tracker, pile_id),
    )


def _stack_operations_for(tracker: OperationTracker, pile_id: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in tracker.events:
        if event.structure is not StructureName.STACK:
            continue
        if event.pile_id == pile_id or (
            pile_id.startswith("tableau-") and event.pile_id == pile_id
        ):
            counts[event.operation] = counts.get(event.operation, 0) + 1
    return counts


# --- queue ------------------------------------------------------------------------


@dataclass(frozen=True)
class QueueReport:
    size: int
    front_card_id: str | None
    rear_card_id: str | None
    fifo_order: tuple[str, ...]
    enqueue_count: int
    dequeue_count: int
    recycle_events: int


def queue_report(game) -> QueueReport:
    stock = game.state.stock
    cards = stock.to_list()
    events = game.tracker.events
    return QueueReport(
        size=stock.size(),
        front_card_id=cards[0].card_id if cards else None,
        rear_card_id=cards[-1].card_id if cards else None,
        fifo_order=tuple(card.card_id for card in cards),
        enqueue_count=sum(
            1 for e in events if e.structure is StructureName.QUEUE and e.operation == "ENQUEUE"
        ),
        dequeue_count=sum(
            1 for e in events if e.structure is StructureName.QUEUE and e.operation == "DEQUEUE"
        ),
        recycle_events=sum(
            1 for e in events if e.structure is StructureName.GAME and e.operation == "WASTE_RECYCLED"
        ),
    )


# --- linked list --------------------------------------------------------------------


@dataclass(frozen=True)
class LinkedListNodeView:
    card_id: str
    has_previous: bool
    has_next: bool


@dataclass(frozen=True)
class LinkedListReport:
    column_id: str
    head_card_id: str | None
    tail_card_id: str | None
    nodes: tuple[LinkedListNodeView, ...]
    append_count: int
    remove_count: int
    detach_count: int
    attach_count: int
    valid: bool


def linked_list_report(game, column_id: str) -> LinkedListReport:
    column = game.state.tableau[column_id]
    linked = column.linked_list
    nodes = tuple(
        LinkedListNodeView(
            card_id=node.value.card_id,
            has_previous=node.previous is not None,
            has_next=node.next is not None,
        )
        for node in linked.iter_nodes()
    )
    events = game.tracker.events
    return LinkedListReport(
        column_id=column_id,
        head_card_id=linked.head.value.card_id if linked.head else None,
        tail_card_id=linked.tail.value.card_id if linked.tail else None,
        nodes=nodes,
        append_count=sum(
            1
            for e in events
            if e.structure is StructureName.LINKED_LIST
            and e.operation == "APPEND_NODE"
            and e.pile_id == column_id
        ),
        remove_count=sum(
            1
            for e in events
            if e.structure is StructureName.LINKED_LIST
            and e.operation == "REMOVE_TOP_NODE"
            and e.pile_id == column_id
        ),
        detach_count=sum(
            1
            for e in events
            if e.structure is StructureName.LINKED_LIST
            and e.operation == "DETACH_RUN"
            and e.pile_id == column_id
        ),
        attach_count=sum(
            1
            for e in events
            if e.structure is StructureName.LINKED_LIST
            and e.operation == "ATTACH_RUN"
            and e.pile_id == column_id
        ),
        valid=linked.validate(),
    )


# --- dictionary ----------------------------------------------------------------------


def dictionary_rows(game) -> list[tuple[str, str, str, int, str]]:
    state = game.state
    rows: list[tuple[str, str, str, int, str]] = []
    for card_id in sorted(state.card_index):
        location = state.card_index[card_id]
        rows.append(
            (
                card_id,
                location.zone.value,
                location.pile_id,
                location.position,
                "Face Up" if location.face_up else "Face Down",
            )
        )
    return rows


def dictionary_operation_counts(tracker: OperationTracker) -> dict[str, int]:
    return operation_counts(tracker, StructureName.DICTIONARY)


# --- timeline ------------------------------------------------------------------------


def timeline_rows(
    tracker: OperationTracker,
    structure_filter: str = "All",
    action_filter: str = "All",
) -> list[tuple[int, str, str, str, str, str, str, str]]:
    rows: list[tuple[int, str, str, str, str, str, str, str]] = []
    for event in tracker.events:
        structure_label = STRUCTURE_LABELS[event.structure]
        if structure_filter != "All" and structure_label != structure_filter:
            continue
        if action_filter != "All" and event.operation != action_filter:
            continue
        rows.append(
            (
                event.sequence,
                event.timestamp,
                structure_label,
                event.operation,
                event.pile_id or "—",
                ", ".join(event.card_ids) if event.card_ids else "—",
                event.context,
                event.outcome,
            )
        )
    return rows


def distinct_operations(tracker: OperationTracker) -> list[str]:
    seen: list[str] = []
    for event in tracker.events:
        if event.operation not in seen:
            seen.append(event.operation)
    return sorted(seen)


# --- game stats -----------------------------------------------------------------------


def game_stats(game) -> dict[str, str]:
    state = game.state
    minutes, seconds = divmod(game.elapsed_seconds, 60)
    foundation_counts = ", ".join(
        f"{suit.code}-{state.foundations[suit].size()}" for suit in Suit
    )
    tableau_counts = ", ".join(
        f"Col {index}: {state.tableau[f'tableau-{index}'].size()}" for index in range(1, 8)
    )
    in_foundations, total = game.foundation_progress()
    return {
        "Moves": str(state.move_count),
        "Score": str(state.score),
        "Time": f"{minutes:02d}:{seconds:02d}",
        "Draw mode": f"Draw {state.draw_count}",
        "Stock": f"{state.stock.size()} cards",
        "Waste": f"{state.waste.size()} cards",
        "Tableau": tableau_counts,
        "Foundations": f"{foundation_counts}  ({in_foundations}/{total})",
        "Status": "WON" if state.status.value == "won" else "Playing",
    }


def _suit_for_pile(pile_id: str) -> Suit:
    code = pile_id.rsplit("-", 1)[1].upper()
    for suit in Suit:
        if suit.code == code:
            return suit
    raise ValueError(f"unknown foundation pile: {pile_id}")
