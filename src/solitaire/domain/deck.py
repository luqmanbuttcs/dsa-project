"""Array/List-based standard deck creation, validation, and shuffling."""

from __future__ import annotations

from random import Random
from typing import Sequence

from solitaire.domain.card import Card, Rank, Suit


class DeckFactory:
    """Creates and validates a standard 52-card deck represented by a list."""

    @staticmethod
    def create_standard_deck() -> list[Card]:
        """Return one face-down card for every suit/rank combination."""
        return [
            Card(suit=suit, rank=rank)
            for suit in Suit
            for rank in Rank
        ]

    @staticmethod
    def validate_standard_deck(cards: Sequence[Card]) -> None:
        """Raise ValueError unless cards contain exactly one of all 52 cards."""
        if len(cards) != 52:
            raise ValueError("A standard Klondike deck must contain exactly 52 cards")

        if any(not isinstance(card, Card) for card in cards):
            raise TypeError("Every deck entry must be a Card instance")

        actual_ids = [card.card_id for card in cards]
        if len(set(actual_ids)) != 52:
            raise ValueError("Deck contains duplicate card identities")

        expected_ids = {
            f"{suit.code}-{rank.label}"
            for suit in Suit
            for rank in Rank
        }
        if set(actual_ids) != expected_ids:
            raise ValueError("Deck must contain every standard suit/rank combination")

    @staticmethod
    def shuffle(cards: list[Card], rng: Random | None = None) -> None:
        """Shuffle the supplied deck list in place after validating it."""
        DeckFactory.validate_standard_deck(cards)
        random_source = rng if rng is not None else Random()
        random_source.shuffle(cards)
