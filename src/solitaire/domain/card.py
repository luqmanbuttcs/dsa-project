"""Playing-card domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class Suit(str, Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"

    @property
    def code(self) -> str:
        return {
            Suit.HEARTS: "H",
            Suit.DIAMONDS: "D",
            Suit.CLUBS: "C",
            Suit.SPADES: "S",
        }[self]

    @property
    def color(self) -> CardColor:
        if self in (Suit.HEARTS, Suit.DIAMONDS):
            return CardColor.RED
        return CardColor.BLACK

    @property
    def symbol(self) -> str:
        return {
            Suit.HEARTS: "♥",
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣",
            Suit.SPADES: "♠",
        }[self]


class CardColor(str, Enum):
    RED = "red"
    BLACK = "black"


class Rank(IntEnum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    @property
    def label(self) -> str:
        return {
            Rank.ACE: "A",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
        }.get(self, str(int(self)))


@dataclass(slots=True)
class Card:
    """A standard playing card with stable identity and visibility state."""

    suit: Suit
    rank: Rank
    face_up: bool = False

    def __post_init__(self) -> None:
        """Reject invalid card attributes at the domain boundary."""
        if not isinstance(self.suit, Suit):
            raise TypeError("suit must be a Suit enum value")
        if not isinstance(self.rank, Rank):
            raise TypeError("rank must be a Rank enum value")
        if not isinstance(self.face_up, bool):
            raise TypeError("face_up must be a bool")

    @property
    def card_id(self) -> str:
        return f"{self.suit.code}-{self.rank.label}"

    @property
    def color(self) -> CardColor:
        return self.suit.color

    def turn_face_up(self) -> None:
        self.face_up = True

    def turn_face_down(self) -> None:
        self.face_up = False

    def __str__(self) -> str:
        return f"{self.rank.label}{self.suit.symbol}"
