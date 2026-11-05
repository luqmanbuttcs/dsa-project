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
