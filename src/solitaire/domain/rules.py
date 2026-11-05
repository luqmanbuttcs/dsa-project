"""Pure Klondike rule validation. No method in this module mutates game state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from solitaire.domain.card import Card, Rank, Suit


class MoveError(str, Enum):
    SAME_COLUMN = "Source and destination columns must be different."
    CARD_NOT_FOUND = "The selected card is not in the source pile."
    CARD_FACE_DOWN = "Face-down cards cannot be moved."
    SEQUENCE_HAS_FACE_DOWN_CARD = "A moved sequence cannot contain face-down cards."
    INVALID_SEQUENCE_ORDER = "The selected tableau sequence is not correctly ordered."
    WRONG_TABLEAU_RANK = "Place a card on the next higher rank."
    SAME_TABLEAU_COLOR = "Tableau cards must alternate red and black."
    EMPTY_COLUMN_REQUIRES_KING = "Only a King-led sequence can fill an empty column."
    FOUNDATION_REQUIRES_ACE = "An empty foundation must start with an Ace."
    FOUNDATION_WRONG_SUIT = "A foundation accepts cards of only one suit."
    FOUNDATION_WRONG_RANK = "A foundation must be built in ascending order."
    INVALID_FOUNDATION_SOURCE = "Only a face-up card can be moved to a foundation."
    INVALID_DESTINATION = "The selected destination is not valid."


@dataclass(frozen=True, slots=True)
class ValidationResult:
    allowed: bool
    reason: MoveError | None = None

    @classmethod
    def accept(cls) -> ValidationResult:
        return cls(True)

    @classmethod
    def reject(cls, reason: MoveError) -> ValidationResult:
        return cls(False, reason)


class RuleValidator:
    """Validates tableau and foundation move rules from the project brief."""

    @staticmethod
    def validate_tableau_run(
        run: list[Card],
        destination_top: Card | None,
    ) -> ValidationResult:
        if not run:
            return ValidationResult.reject(MoveError.CARD_NOT_FOUND)

        if not run[0].face_up:
            return ValidationResult.reject(MoveError.CARD_FACE_DOWN)

        if any(not card.face_up for card in run):
            return ValidationResult.reject(MoveError.SEQUENCE_HAS_FACE_DOWN_CARD)

        # Validate the run itself: storage order is bottom-to-top, so each
        # next card must be one rank lower and the opposite color.
        for lower_card, upper_card in zip(run, run[1:]):
            if int(lower_card.rank) != int(upper_card.rank) + 1:
                return ValidationResult.reject(MoveError.INVALID_SEQUENCE_ORDER)
            if lower_card.color is upper_card.color:
                return ValidationResult.reject(MoveError.SAME_TABLEAU_COLOR)

        moving_card = run[0]

        if destination_top is None:
            if moving_card.rank is Rank.KING:
                return ValidationResult.accept()
            return ValidationResult.reject(MoveError.EMPTY_COLUMN_REQUIRES_KING)

        if not destination_top.face_up:
            return ValidationResult.reject(MoveError.INVALID_DESTINATION)

        if int(moving_card.rank) + 1 != int(destination_top.rank):
            return ValidationResult.reject(MoveError.WRONG_TABLEAU_RANK)

        if moving_card.color is destination_top.color:
            return ValidationResult.reject(MoveError.SAME_TABLEAU_COLOR)

        return ValidationResult.accept()

    @staticmethod
    def validate_foundation(
        card: Card,
        foundation_suit: Suit,
        foundation_top: Card | None,
    ) -> ValidationResult:
        if not card.face_up:
            return ValidationResult.reject(MoveError.INVALID_FOUNDATION_SOURCE)

        if card.suit is not foundation_suit:
            return ValidationResult.reject(MoveError.FOUNDATION_WRONG_SUIT)

        if foundation_top is None:
            if card.rank is Rank.ACE:
                return ValidationResult.accept()
            return ValidationResult.reject(MoveError.FOUNDATION_REQUIRES_ACE)

        if foundation_top.suit is not foundation_suit:
            return ValidationResult.reject(MoveError.FOUNDATION_WRONG_SUIT)

        if int(card.rank) != int(foundation_top.rank) + 1:
            return ValidationResult.reject(MoveError.FOUNDATION_WRONG_RANK)

        return ValidationResult.accept()
