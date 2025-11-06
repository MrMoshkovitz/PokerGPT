"""
Tests for Card Utilities
"""

import pytest
from src.utils.card_utils import (
    validate_card,
    normalize_card,
    normalize_hand,
    parse_cards,
)


def test_validate_card_valid():
    """Test card validation with valid cards."""
    assert validate_card("Ah") is True
    assert validate_card("Kd") is True
    assert validate_card("Ts") is True
    assert validate_card("2c") is True


def test_validate_card_invalid():
    """Test card validation with invalid cards."""
    assert validate_card("Xx") is False
    assert validate_card("A") is False
    assert validate_card("Ahh") is False
    assert validate_card("") is False
    assert validate_card(None) is False


def test_normalize_card():
    """Test card normalization."""
    assert normalize_card("ah") == "Ah"
    assert normalize_card("AH") == "Ah"
    assert normalize_card("Ah") == "Ah"
    assert normalize_card("kD") == "Kd"
    assert normalize_card("ts") == "Ts"


def test_normalize_card_invalid():
    """Test card normalization with invalid cards."""
    assert normalize_card("Xx") is None
    assert normalize_card("A") is None
    assert normalize_card("") is None


def test_normalize_hand_pair():
    """Test hand normalization for pairs."""
    assert normalize_hand(["Ah", "As"]) == "AA"
    assert normalize_hand(["Kh", "Kd"]) == "KK"
    assert normalize_hand(["2s", "2c"]) == "22"


def test_normalize_hand_suited():
    """Test hand normalization for suited hands."""
    assert normalize_hand(["Ah", "Kh"]) == "AKs"
    assert normalize_hand(["Kh", "Ah"]) == "AKs"  # Order shouldn't matter
    assert normalize_hand(["Qs", "Js"]) == "QJs"


def test_normalize_hand_offsuit():
    """Test hand normalization for offsuit hands."""
    assert normalize_hand(["Ah", "Kd"]) == "AKo"
    assert normalize_hand(["Kd", "Ah"]) == "AKo"  # Order shouldn't matter
    assert normalize_hand(["Qs", "Jh"]) == "QJo"


def test_parse_cards():
    """Test parsing cards from text."""
    assert parse_cards("Ah Kd Qs") == ["Ah", "Kd", "Qs"]
    assert parse_cards("ah kd qs") == ["Ah", "Kd", "Qs"]  # Case-insensitive
    assert parse_cards("The cards are Ah, Kd, and Qs") == ["Ah", "Kd", "Qs"]
    assert parse_cards("Ts 9h 8c") == ["Ts", "9h", "8c"]


def test_parse_cards_empty():
    """Test parsing with no cards."""
    assert parse_cards("") == []
    assert parse_cards("No cards here") == []
