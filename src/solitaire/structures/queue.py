"""FIFO Queue implementation using a resizable circular buffer."""

from __future__ import annotations

from typing import Generic, TypeVar, cast

T = TypeVar("T")
_EMPTY = object()


class Queue(Generic[T]):
    """A resizable circular-buffer queue.

    Enqueue and dequeue are O(1) amortized. Dequeue does not shift all
    remaining elements, unlike list.pop(0).
    """

    __slots__ = ("_buffer", "_front", "_size")

    def __init__(self, initial_capacity: int = 8) -> None:
        if initial_capacity < 1:
            raise ValueError("initial_capacity must be at least 1")

        self._buffer: list[object] = [_EMPTY] * initial_capacity
        self._front = 0
        self._size = 0

    def enqueue(self, item: T) -> None:
        """Add an item to the rear of the queue."""
        if self._size == len(self._buffer):
            self._resize(len(self._buffer) * 2)

        rear = (self._front + self._size) % len(self._buffer)
        self._buffer[rear] = item
        self._size += 1

    def dequeue(self) -> T:
        """Remove and return the oldest item."""
        if self._size == 0:
            raise IndexError("dequeue from empty queue")

        item = self._buffer[self._front]
        self._buffer[self._front] = _EMPTY
        self._front = (self._front + 1) % len(self._buffer)
        self._size -= 1

        if self._size == 0:
            self._front = 0

        return cast(T, item)

    def peek(self) -> T:
        """Return the next item without removing it."""
        if self._size == 0:
            raise IndexError("peek from empty queue")
        return cast(T, self._buffer[self._front])

    def rear(self) -> T:
        """Return the newest item without removing it."""
        if self._size == 0:
            raise IndexError("rear from empty queue")
        index = (self._front + self._size - 1) % len(self._buffer)
        return cast(T, self._buffer[index])

    def is_empty(self) -> bool:
        return self._size == 0

    def size(self) -> int:
        return self._size

    def clear(self) -> None:
        self._buffer = [_EMPTY] * len(self._buffer)
        self._front = 0
        self._size = 0

    def to_list(self) -> list[T]:
        """Return items in FIFO order without changing the queue."""
        result: list[T] = []
        capacity = len(self._buffer)

        for offset in range(self._size):
            index = (self._front + offset) % capacity
            result.append(cast(T, self._buffer[index]))

        return result

    def __iter__(self):
        return iter(self.to_list())

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"Queue(front_to_rear={self.to_list()!r})"

    def _resize(self, new_capacity: int) -> None:
        new_buffer: list[object] = [_EMPTY] * new_capacity

        for offset, item in enumerate(self.to_list()):
            new_buffer[offset] = item

        self._buffer = new_buffer
        self._front = 0
