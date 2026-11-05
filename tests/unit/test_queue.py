import pytest

from solitaire.structures.queue import Queue


def test_queue_is_fifo():
    queue = Queue[str]()

    queue.enqueue("first")
    queue.enqueue("second")
    queue.enqueue("third")

    assert queue.size() == 3
    assert queue.peek() == "first"
    assert queue.rear() == "third"
    assert queue.dequeue() == "first"
    assert queue.dequeue() == "second"
    assert queue.dequeue() == "third"
    assert queue.is_empty()


def test_queue_wraparound_and_growth_preserve_order():
    queue = Queue[int](initial_capacity=3)

    queue.enqueue(1)
    queue.enqueue(2)
    assert queue.dequeue() == 1
    queue.enqueue(3)
    queue.enqueue(4)
    queue.enqueue(5)  # Forces growth after wraparound.

    assert queue.to_list() == [2, 3, 4, 5]
    assert [queue.dequeue() for _ in range(4)] == [2, 3, 4, 5]
    assert queue.is_empty()


def test_queue_clear():
    queue = Queue[int]()
    queue.enqueue(10)
    queue.enqueue(20)
    queue.clear()

    assert queue.is_empty()
    assert queue.to_list() == []


def test_empty_queue_operations_raise():
    queue = Queue[int]()

    with pytest.raises(IndexError):
        queue.dequeue()

    with pytest.raises(IndexError):
        queue.peek()

    with pytest.raises(IndexError):
        queue.rear()


def test_initial_capacity_must_be_positive():
    with pytest.raises(ValueError):
        Queue[int](initial_capacity=0)
