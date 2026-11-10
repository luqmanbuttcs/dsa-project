"""A small generic doubly linked list for game-pile storage.

The tail is the top of a pile. This makes stack push/pop O(1) while
also allowing a contiguous tableau run to be detached and attached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


@dataclass(slots=True, eq=False)
class LinkedListNode(Generic[T]):
    """A node in a doubly linked list."""

    value: T
    previous: LinkedListNode[T] | None = None
    next: LinkedListNode[T] | None = None


class LinkedList(Generic[T]):
    """Doubly linked list with O(1) end operations and run splicing."""

    __slots__ = ("_head", "_tail", "_size")

    def __init__(self, values: Iterable[T] | None = None) -> None:
        self._head: LinkedListNode[T] | None = None
        self._tail: LinkedListNode[T] | None = None
        self._size = 0

        if values is not None:
            for value in values:
                self.append(value)

    @property
    def head(self) -> LinkedListNode[T] | None:
        return self._head

    @property
    def tail(self) -> LinkedListNode[T] | None:
        return self._tail

    def append(self, value: T) -> LinkedListNode[T]:
        """Append a value at the tail and return its node."""
        node = LinkedListNode(value=value, previous=self._tail)

        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node

        self._tail = node
        self._size += 1
        return node

    def appendleft(self, value: T) -> LinkedListNode[T]:
        """Insert a value at the head and return its node."""
        node = LinkedListNode(value=value, next=self._head)

        if self._head is None:
            self._tail = node
        else:
            self._head.previous = node

        self._head = node
        self._size += 1
        return node

    def pop(self) -> T:
        """Remove and return the tail value."""
        if self._tail is None:
            raise IndexError("pop from empty linked list")

        return self._remove_node(self._tail)

    def popleft(self) -> T:
        """Remove and return the head value."""
        if self._head is None:
            raise IndexError("pop from empty linked list")

        return self._remove_node(self._head)

    def peek(self) -> T:
        """Return the tail value without removing it."""
        if self._tail is None:
            raise IndexError("peek from empty linked list")
        return self._tail.value

    def node_at(self, index: int) -> LinkedListNode[T]:
        """Return the node at a zero-based index from the head."""
        if index < 0 or index >= self._size:
            raise IndexError("linked-list index out of range")

        if index <= self._size // 2:
            current = self._head
            for _ in range(index):
                assert current is not None
                current = current.next
        else:
            current = self._tail
            for _ in range(self._size - 1 - index):
                assert current is not None
                current = current.previous

        assert current is not None
        return current

    def remove_node(self, node: LinkedListNode[T]) -> T:
        """Remove a node belonging to this list and return its value."""
        self._assert_contains(node)
        return self._remove_node(node)

    def detach_range(
        self,
        first: LinkedListNode[T],
        last: LinkedListNode[T],
    ) -> LinkedList[T]:
        """Detach a contiguous first-to-last run into a new linked list.

        The order of nodes is preserved. The supplied boundary nodes must
        belong to this list, and last must be reachable from first.
        """
        self._assert_contains(first)
        self._assert_contains(last)

        count = 1
        current = first
        while current is not last:
            current = current.next
            if current is None:
                raise ValueError("last node does not follow first node")
            count += 1

        before = first.previous
        after = last.next

        if before is None:
            self._head = after
        else:
            before.next = after

        if after is None:
            self._tail = before
        else:
            after.previous = before

        first.previous = None
        last.next = None
        self._size -= count

        if self._size == 0:
            self._head = None
            self._tail = None

        detached: LinkedList[T] = LinkedList()
        detached._head = first
        detached._tail = last
        detached._size = count
        return detached

    def append_list(self, other: LinkedList[T]) -> None:
        """Move every node from other to this list in O(1).

        The other list becomes empty. Values and nodes are not copied.
        """
        if other is self:
            raise ValueError("cannot append a linked list to itself")
        if other._size == 0:
            return

        if self._tail is None:
            self._head = other._head
            self._tail = other._tail
        else:
            assert other._head is not None
            self._tail.next = other._head
            other._head.previous = self._tail
            self._tail = other._tail

        self._size += other._size
        other._head = None
        other._tail = None
        other._size = 0

    def clear(self) -> None:
        """Remove all nodes from this list."""
        current = self._head
        while current is not None:
            following = current.next
            current.previous = None
            current.next = None
            current = following

        self._head = None
        self._tail = None
        self._size = 0

    def is_empty(self) -> bool:
        return self._size == 0

    def size(self) -> int:
        return self._size

    def validate(self) -> bool:
        """Return whether head/tail, links, and size are consistent."""
        if self._size == 0:
            return self._head is None and self._tail is None

        if self._head is None or self._tail is None:
            return False
        if self._head.previous is not None or self._tail.next is not None:
            return False

        count = 0
        previous = None
        current = self._head

        while current is not None:
            if current.previous is not previous:
                return False
            previous = current
            current = current.next
            count += 1
            if count > self._size:
                return False

        return previous is self._tail and count == self._size

    def iter_nodes(self) -> Iterator[LinkedListNode[T]]:
        current = self._head
        while current is not None:
            yield current
            current = current.next

    def to_list(self) -> list[T]:
        return list(self)

    def __iter__(self) -> Iterator[T]:
        for node in self.iter_nodes():
            yield node.value

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"LinkedList({self.to_list()!r})"

    def _remove_node(self, node: LinkedListNode[T]) -> T:
        before = node.previous
        after = node.next

        if before is None:
            self._head = after
        else:
            before.next = after

        if after is None:
            self._tail = before
        else:
            after.previous = before

        node.previous = None
        node.next = None
        self._size -= 1

        if self._size == 0:
            self._head = None
            self._tail = None

        return node.value

    def _assert_contains(self, target: LinkedListNode[T]) -> None:
        for node in self.iter_nodes():
            if node is target:
                return
        raise ValueError("node does not belong to this linked list")
