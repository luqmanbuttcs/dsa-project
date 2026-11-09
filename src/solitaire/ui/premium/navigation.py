"""Workspace navigation identifiers for the premium shell."""

from __future__ import annotations

from enum import Enum


class Workspace(str, Enum):
    """Top-level screens of the premium application shell."""

    PLAY = "play"
    DSA_LAB = "dsa-lab"


class LabPage(str, Enum):
    """Sections inside the DSA Lab workspace."""

    OVERVIEW = "overview"
    ARRAY = "array"
    STACK = "stack"
    QUEUE = "queue"
    LINKED_LIST = "linked-list"
    DICTIONARY = "dictionary"
    TIMELINE = "timeline"
    STATS = "stats"
