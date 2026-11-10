"""Drag-and-drop payload handling.

Card graphics items start a Qt drag carrying a JSON payload. Pile targets
resolve drops through the SelectionController/GameController, so the scene
never mutates game state directly.
"""

from __future__ import annotations

import json

from PyQt6.QtCore import QMimeData

MIME_TYPE = "application/x-klondike-cards"


def create_payload(card_ids: list[str], source_pile: str) -> QMimeData:
    mime = QMimeData()
    mime.setData(
        MIME_TYPE,
        json.dumps({"card_ids": card_ids, "source": source_pile}).encode("utf-8"),
    )
    return mime


def parse_payload(mime: QMimeData) -> tuple[list[str], str] | None:
    """Return (card_ids, source_pile) or None when the payload is foreign."""
    data = mime.data(MIME_TYPE)
    if data.isEmpty():
        return None
    try:
        document = json.loads(bytes(data))
        card_ids = [str(card_id) for card_id in document["card_ids"]]
        source = str(document["source"])
    except (ValueError, KeyError, TypeError):
        return None
    if not source:
        return None
    return card_ids, source
