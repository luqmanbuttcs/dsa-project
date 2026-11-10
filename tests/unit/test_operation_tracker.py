from solitaire.domain.operations import OperationTracker, StructureName


def test_tracker_records_ordered_events_and_counts():
    tracker = OperationTracker()

    first = tracker.record(
        StructureName.QUEUE, "DEQUEUE",
        action_id="draw-1", pile_id="stock", card_ids=("H-A",)
    )
    second = tracker.record(
        StructureName.STACK, "PUSH",
        action_id="draw-1", pile_id="waste", card_ids=("H-A",)
    )

    assert first.sequence == 1
    assert second.sequence == 2
    assert tracker.events_for_action("draw-1") == (first, second)
    assert tracker.count(StructureName.QUEUE) == 1
    assert tracker.count(StructureName.STACK) == 1
    assert tracker.count_operation(StructureName.STACK, "PUSH") == 1


def test_tracker_clear_resets_events_and_counts():
    tracker = OperationTracker()
    tracker.record(
        StructureName.ARRAY_LIST, "SHUFFLE", action_id="setup"
    )

    tracker.clear()

    assert tracker.events == ()
    assert tracker.count(StructureName.ARRAY_LIST) == 0
