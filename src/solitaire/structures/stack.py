"""LIFO Stack implementation backed by the custom LinkedList."""

from __future__ import annotations

from typing import Generic, TypeVar

from solitaire.structures.linked_list import LinkedList

T = TypeVar("T")


class Stack(Generic[T]):
    """A stack whose top is the tail of its linked-list backing store."""

    __slots__ = ("_items",)

    def __init__(self) -> None:
        self._items: LinkedList[T] = LinkedList()

    def push(self, item: T) -> None:
        """Add an item to the top of the stack."""
        self._items.append(item)

    def pop(self) -> T:
        """Remove and return the top item."""
        return self._items.pop()

    def peek(self) -> T:
        """Return the top item without removing it."""
        return self._items.peek()

    def is_empty(self) -> bool:
        return self._items.is_empty()

    def size(self) -> int:
        return self._items.size()

    def to_list(self) -> list[T]:
        """Return items from bottom to top without changing the stack."""
        return self._items.to_list()

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return self._items.size()

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"Stack(bottom_to_top={self.to_list()!r})"
