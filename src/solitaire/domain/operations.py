"""Structured, truthful operation events for the DSA monitor."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class StructureName(str, Enum):
    ARRAY_LIST = "Array / List"
    STACK = "Stack"
    QUEUE = "Queue"
    LINKED_LIST = "Linked List"
    DICTIONARY = "Dictionary"
    GAME = "Game"


@dataclass(frozen=True, slots=True)
class OperationEvent:
    sequence: int
    action_id: str
    timestamp: str
    structure: StructureName
    operation: str
    pile_id: str | None = None
    card_ids: tuple[str, ...] = ()
    context: str = "PLAY"
    outcome: str = "SUCCESS"
    details: dict[str, Any] = field(default_factory=dict)


class OperationTracker:
    """Collects events emitted by actual data-structure/domain operations."""

    def __init__(self) -> None:
        self._events: list[OperationEvent] = []
        self._counts: Counter[StructureName] = Counter()
        self._operation_counts: Counter[tuple[StructureName, str]] = Counter()
        self._sequence = 0

    def record(
        self,
        structure: StructureName,
        operation: str,
        *,
        action_id: str,
        pile_id: str | None = None,
        card_ids: tuple[str, ...] | list[str] = (),
        context: str = "PLAY",
        outcome: str = "SUCCESS",
        details: dict[str, Any] | None = None,
    ) -> OperationEvent:
        """Record one operation after the corresponding method has executed."""
        self._sequence += 1
        event = OperationEvent(
            sequence=self._sequence,
            action_id=action_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            structure=structure,
            operation=operation,
            pile_id=pile_id,
            card_ids=tuple(card_ids),
            context=context,
            outcome=outcome,
            details=dict(details or {}),
        )
        self._events.append(event)
        self._counts[structure] += 1
        self._operation_counts[(structure, operation)] += 1
        return event

    @property
    def events(self) -> tuple[OperationEvent, ...]:
        return tuple(self._events)

    def events_for_action(self, action_id: str) -> tuple[OperationEvent, ...]:
        return tuple(event for event in self._events if event.action_id == action_id)

    def count(self, structure: StructureName) -> int:
        return self._counts[structure]

    def count_operation(self, structure: StructureName, operation: str) -> int:
        return self._operation_counts[(structure, operation)]

    def counts(self) -> dict[str, int]:
        return {structure.value: self._counts[structure] for structure in StructureName}

    def clear(self) -> None:
        self._events.clear()
        self._counts.clear()
        self._operation_counts.clear()
        self._sequence = 0
