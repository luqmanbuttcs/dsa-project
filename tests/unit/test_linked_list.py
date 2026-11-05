import pytest

from solitaire.structures.linked_list import LinkedList


def test_append_pop_and_links():
    items = LinkedList[int]()
    first = items.append(10)
    second = items.append(20)
    third = items.append(30)

    assert items.to_list() == [10, 20, 30]
    assert items.head is first
    assert items.tail is third
    assert second.previous is first
    assert second.next is third
    assert items.validate()

    assert items.pop() == 30
    assert items.pop() == 20
    assert items.pop() == 10
    assert items.is_empty()
    assert items.validate()


def test_appendleft_and_popleft():
    items = LinkedList(["middle"])
    items.appendleft("first")
    items.append("last")

    assert items.to_list() == ["first", "middle", "last"]
    assert items.popleft() == "first"
    assert items.popleft() == "middle"
    assert items.popleft() == "last"
    assert items.validate()


def test_detach_and_attach_run_preserves_nodes_and_order():
    source = LinkedList(["K", "Q", "J", "10", "9"])
    destination = LinkedList(["A", "2"])

    first = source.node_at(2)
    last = source.tail
    assert last is not None

    detached = source.detach_range(first, last)

    assert source.to_list() == ["K", "Q"]
    assert detached.to_list() == ["J", "10", "9"]
    assert source.validate()
    assert detached.validate()

    original_nodes = list(detached.iter_nodes())
    destination.append_list(detached)

    assert destination.to_list() == ["A", "2", "J", "10", "9"]
    assert detached.is_empty()
    assert destination.validate()
    assert [node.value for node in original_nodes] == ["J", "10", "9"]


def test_detach_middle_run_updates_both_neighbor_links():
    items = LinkedList([1, 2, 3, 4, 5])
    run = items.detach_range(items.node_at(1), items.node_at(3))

    assert items.to_list() == [1, 5]
    assert run.to_list() == [2, 3, 4]
    assert items.head is not None
    assert items.tail is not None
    assert items.head.next is items.tail
    assert items.tail.previous is items.head
    assert items.validate()
    assert run.validate()


def test_detach_rejects_reversed_or_foreign_nodes():
    items = LinkedList([1, 2, 3])
    foreign = LinkedList([4])

    with pytest.raises(ValueError):
        items.detach_range(items.node_at(2), items.node_at(0))

    assert foreign.head is not None
    with pytest.raises(ValueError):
        items.detach_range(foreign.head, foreign.head)


def test_empty_operations_raise_index_error():
    items = LinkedList()

    with pytest.raises(IndexError):
        items.pop()

    with pytest.raises(IndexError):
        items.popleft()

    with pytest.raises(IndexError):
        items.peek()
