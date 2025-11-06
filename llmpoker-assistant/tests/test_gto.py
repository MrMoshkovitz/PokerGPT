"""
Tests for GTO Engine
"""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.gto.hand_evaluator import (
    calculate_hand_strength,
    classify_board_texture,
    _has_straight_potential,
)
from src.gto.strategy_cache import GTOStrategyCache
from src.utils.card_utils import normalize_hand


def test_hand_strength_high_card():
    """Test hand strength calculation for high card."""
    hole = ["Ah", "Kd"]
    board = ["Qh", "Js", "3c"]

    strength = calculate_hand_strength(hole, board)

    # Should be MEDIUM or WEAK (high card)
    assert strength in ["MEDIUM", "WEAK"]


def test_hand_strength_pair():
    """Test hand strength calculation for pair."""
    hole = ["Ah", "Kd"]
    board = ["Ac", "Js", "3c"]

    strength = calculate_hand_strength(hole, board)

    # Should be MEDIUM or STRONG (top pair)
    assert strength in ["MEDIUM", "STRONG"]


def test_board_texture_dry():
    """Test board texture classification for dry board."""
    board = ["Ah", "7d", "3c"]  # Rainbow, no connects

    texture = classify_board_texture(board)

    assert texture == "DRY"


def test_board_texture_wet():
    """Test board texture classification for wet board (flush draw)."""
    board = ["Ah", "Kh", "Qh"]  # Three hearts

    texture = classify_board_texture(board)

    assert texture == "WET"


def test_board_texture_paired():
    """Test board texture classification for paired board."""
    board = ["Ah", "Ad", "Kc"]  # Pair of aces

    texture = classify_board_texture(board)

    assert texture == "PAIRED"


def test_board_texture_coordinated():
    """Test board texture classification for coordinated board."""
    board = ["Qh", "Js", "Tc"]  # Straight potential

    texture = classify_board_texture(board)

    assert texture == "COORDINATED"


def test_straight_potential_yes():
    """Test straight potential detection (positive)."""
    ranks = ["Q", "J", "T"]  # Q-J-10 = straight potential

    assert _has_straight_potential(ranks) is True


def test_straight_potential_no():
    """Test straight potential detection (negative)."""
    ranks = ["A", "7", "3"]  # No connects

    assert _has_straight_potential(ranks) is False


def test_normalize_hand():
    """Test hand normalization."""
    assert normalize_hand(["Ah", "Kd"]) == "AKo"
    assert normalize_hand(["Ah", "Kh"]) == "AKs"
    assert normalize_hand(["Ah", "Ad"]) == "AA"


def test_strategy_cache_initialization():
    """Test GTOStrategyCache initialization."""
    cache = GTOStrategyCache()

    assert cache.loaded is False
    assert len(cache.preflop_ranges) == 0
    assert len(cache.postflop_buckets) == 0


@pytest.mark.skipif(
    not os.path.exists("data/gto/preflop_ranges.pkl"),
    reason="GTO data not available",
)
def test_strategy_cache_load():
    """Test loading GTO data (requires data files)."""
    cache = GTOStrategyCache()
    cache.load_from_disk("data/gto")

    assert cache.loaded is True
    assert len(cache.preflop_ranges) > 0


def test_strategy_cache_bucket_spr():
    """Test SPR bucketing."""
    cache = GTOStrategyCache()

    assert cache._bucket_spr(15) == "DEEP"
    assert cache._bucket_spr(5) == "MEDIUM"
    assert cache._bucket_spr(2) == "SHALLOW"
