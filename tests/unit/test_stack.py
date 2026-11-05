import pytest

from solitaire.structures.stack import Stack


def test_stack_is_lifo():
    stack = Stack[str]()

    assert stack.is_empty()
    stack.push("first")
    stack.push("second")
    stack.push("third")

    assert stack.size() == 3
    assert stack.peek() == "third"
    assert stack.pop() == "third"
    assert stack.pop() == "second"
    assert stack.pop() == "first"
    assert stack.is_empty()


def test_peek_does_not_remove_item():
    stack = Stack[int]()
    stack.push(42)

    assert stack.peek() == 42
    assert stack.size() == 1


def test_stack_clear():
    stack = Stack[int]()
    stack.push(1)
    stack.push(2)
    stack.clear()

    assert stack.is_empty()
    assert stack.to_list() == []


def test_pop_and_peek_empty_stack_raise():
    stack = Stack[int]()

    with pytest.raises(IndexError):
        stack.pop()

    with pytest.raises(IndexError):
        stack.peek()
