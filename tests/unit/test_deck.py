from random import Random

from solitaire.domain.card import CardColor, Rank, Suit
from solitaire.domain.deck import DeckFactory


def test_standard_deck_contains_52_unique_cards():
    deck = DeckFactory.create_standard_deck()

    assert len(deck) == 52
    assert len({card.card_id for card in deck}) == 52
    assert {card.suit for card in deck} == set(Suit)
    assert {card.rank for card in deck} == set(Rank)
    assert all(not card.face_up for card in deck)


def test_suit_colors_are_correct():
    assert Suit.HEARTS.color is CardColor.RED
    assert Suit.DIAMONDS.color is CardColor.RED
    assert Suit.CLUBS.color is CardColor.BLACK
    assert Suit.SPADES.color is CardColor.BLACK


def test_shuffle_is_seedable_and_preserves_all_cards():
    first = DeckFactory.create_standard_deck()
    second = DeckFactory.create_standard_deck()

    DeckFactory.shuffle(first, Random(12345))
    DeckFactory.shuffle(second, Random(12345))

    assert [card.card_id for card in first] == [card.card_id for card in second]
    assert {card.card_id for card in first} == {
        card.card_id for card in DeckFactory.create_standard_deck()
    }


def test_shuffle_rejects_incomplete_or_duplicate_deck():
    deck = DeckFactory.create_standard_deck()

    try:
        DeckFactory.shuffle(deck[:-1], Random(1))
    except ValueError as error:
        assert "52 cards" in str(error)
    else:
        raise AssertionError("Expected incomplete deck to be rejected")

    duplicate_deck = DeckFactory.create_standard_deck()
    duplicate_deck[-1] = duplicate_deck[0]

    try:
        DeckFactory.shuffle(duplicate_deck, Random(1))
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("Expected duplicate card identity to be rejected")


def test_rank_labels():
    assert Rank.ACE.label == "A"
    assert Rank.TEN.label == "10"
    assert Rank.JACK.label == "J"
    assert Rank.QUEEN.label == "Q"
    assert Rank.KING.label == "K"


def test_shuffle_changes_order_for_known_seed():
    deck = DeckFactory.create_standard_deck()
    original_order = [card.card_id for card in deck]

    DeckFactory.shuffle(deck, Random(20261105))

    assert [card.card_id for card in deck] != original_order
    assert len({card.card_id for card in deck}) == 52


def test_created_cards_expose_suit_rank_and_face_state():
    from solitaire.domain.card import Card

    card = Card(Suit.HEARTS, Rank.ACE)

    assert card.suit is Suit.HEARTS
    assert card.rank is Rank.ACE
    assert card.face_up is False
    card.turn_face_up()
    assert card.face_up is True
    card.turn_face_down()
    assert card.face_up is False
    assert card.card_id == "H-A"


def test_card_rejects_invalid_attributes():
    from solitaire.domain.card import Card

    try:
        Card("Hearts", Rank.ACE)  # type: ignore[arg-type]
    except TypeError as error:
        assert "suit" in str(error)
    else:
        raise AssertionError("Expected invalid suit type to be rejected")

    try:
        Card(Suit.HEARTS, 1)  # type: ignore[arg-type]
    except TypeError as error:
        assert "rank" in str(error)
    else:
        raise AssertionError("Expected invalid rank type to be rejected")

    try:
        Card(Suit.HEARTS, Rank.ACE, 1)  # type: ignore[arg-type]
    except TypeError as error:
        assert "face_up" in str(error)
    else:
        raise AssertionError("Expected non-boolean face state to be rejected")


def test_deck_validation_rejects_missing_standard_card():
    deck = DeckFactory.create_standard_deck()
    deck[-1] = deck[0]

    try:
        DeckFactory.validate_standard_deck(deck)
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("Expected duplicate/missing card to be rejected")
