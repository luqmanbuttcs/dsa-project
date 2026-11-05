"""Array/List-based deck creation and shuffling."""

from __future__ import annotations

from random import Random

from solitaire.domain.card import Card, Rank, Suit


class DeckFactory:
    """Creates the 52-card deck as a Python list before dealing."""

    @staticmethod
    def create_standard_deck() -> list[Card]:
        return [
            Card(suit=suit, rank=rank)
            for suit in Suit
            for rank in Rank
        ]

    @staticmethod
    def shuffle(cards: list[Card], rng: Random | None = None) -> None:
        """Shuffle the supplied deck list in place."""
        if len(cards) != 52:
            raise ValueError("A standard Klondike deck must contain 52 cards")

        card_ids = [card.card_id for card in cards]
        if len(set(card_ids)) != 52:
            raise ValueError("Deck contains duplicate card identities")

        (rng or Random()).shuffle(cards)
