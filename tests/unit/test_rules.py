from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.rules import MoveError, RuleValidator


def card(suit: Suit, rank: Rank, face_up: bool = True) -> Card:
    return Card(suit=suit, rank=rank, face_up=face_up)


def test_tableau_accepts_descending_alternating_color():
    result = RuleValidator.validate_tableau_run(
        [card(Suit.HEARTS, Rank.EIGHT)],
        card(Suit.CLUBS, Rank.NINE),
    )
    assert result.allowed


def test_tableau_rejects_same_color():
    result = RuleValidator.validate_tableau_run(
        [card(Suit.HEARTS, Rank.EIGHT)],
        card(Suit.DIAMONDS, Rank.NINE),
    )
    assert not result.allowed
    assert result.reason is MoveError.SAME_TABLEAU_COLOR


def test_tableau_rejects_wrong_rank():
    result = RuleValidator.validate_tableau_run(
        [card(Suit.HEARTS, Rank.SEVEN)],
        card(Suit.CLUBS, Rank.NINE),
    )
    assert not result.allowed
    assert result.reason is MoveError.WRONG_TABLEAU_RANK


def test_empty_tableau_accepts_only_king_led_run():
    assert RuleValidator.validate_tableau_run(
        [card(Suit.SPADES, Rank.KING)], None
    ).allowed

    result = RuleValidator.validate_tableau_run(
        [card(Suit.SPADES, Rank.QUEEN)], None
    )
    assert not result.allowed
    assert result.reason is MoveError.EMPTY_COLUMN_REQUIRES_KING


def test_tableau_rejects_face_down_card_or_sequence():
    face_down = card(Suit.HEARTS, Rank.EIGHT, face_up=False)
    assert RuleValidator.validate_tableau_run([face_down], None).reason is MoveError.CARD_FACE_DOWN

    invalid_sequence = [
        card(Suit.HEARTS, Rank.EIGHT),
        card(Suit.CLUBS, Rank.SEVEN, face_up=False),
    ]
    assert (
        RuleValidator.validate_tableau_run(
            invalid_sequence, card(Suit.CLUBS, Rank.NINE)
        ).reason
        is MoveError.SEQUENCE_HAS_FACE_DOWN_CARD
    )


def test_tableau_rejects_malformed_sequence():
    invalid_sequence = [
        card(Suit.HEARTS, Rank.EIGHT),
        card(Suit.CLUBS, Rank.SIX),
    ]
    result = RuleValidator.validate_tableau_run(
        invalid_sequence, card(Suit.CLUBS, Rank.NINE)
    )
    assert not result.allowed
    assert result.reason is MoveError.INVALID_SEQUENCE_ORDER


def test_foundation_accepts_ace_then_same_suit_next_rank():
    ace = card(Suit.HEARTS, Rank.ACE)
    two = card(Suit.HEARTS, Rank.TWO)

    assert RuleValidator.validate_foundation(ace, Suit.HEARTS, None).allowed
    assert RuleValidator.validate_foundation(
        two, Suit.HEARTS, ace
    ).allowed


def test_foundation_rejects_non_ace_start_wrong_suit_and_wrong_rank():
    king = card(Suit.HEARTS, Rank.KING)
    assert (
        RuleValidator.validate_foundation(king, Suit.HEARTS, None).reason
        is MoveError.FOUNDATION_REQUIRES_ACE
    )

    ace_of_spades = card(Suit.SPADES, Rank.ACE)
    assert (
        RuleValidator.validate_foundation(ace_of_spades, Suit.HEARTS, None).reason
        is MoveError.FOUNDATION_WRONG_SUIT
    )

    ace = card(Suit.HEARTS, Rank.ACE)
    three = card(Suit.HEARTS, Rank.THREE)
    assert (
        RuleValidator.validate_foundation(three, Suit.HEARTS, ace).reason
        is MoveError.FOUNDATION_WRONG_RANK
    )
