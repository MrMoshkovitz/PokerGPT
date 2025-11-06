"""
Tests for Vision Module
"""

import pytest
from PIL import Image
import numpy as np
from src.vision.confidence_validator import ConfidenceValidator


def test_confidence_validator_initialization():
    """Test ConfidenceValidator initialization."""
    validator = ConfidenceValidator(buffer_size=3, threshold=0.70)

    assert validator.buffer_size == 3
    assert validator.threshold == 0.70
    assert len(validator.state_buffer) == 0


def test_aggregate_confidence():
    """Test confidence aggregation."""
    validator = ConfidenceValidator()

    state = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "confidence": {"hole_cards": 0.9, "board": 0.8, "pot": 0.7, "stacks": 0.85},
    }

    aggregate = validator._aggregate_confidence(state)

    # Should be average of all confidence scores
    expected = (0.9 + 0.8 + 0.7 + 0.85) / 4
    assert abs(aggregate - expected) < 0.01


def test_hole_cards_consistency_same():
    """Test hole cards consistency when cards stay same."""
    validator = ConfidenceValidator()

    previous = {"hole_cards": ["Ah", "Kd"]}
    current = {"hole_cards": ["Ah", "Kd"]}

    score = validator._check_hole_cards_consistency(current, previous)

    assert score == 1.0  # Fully consistent


def test_hole_cards_consistency_changed():
    """Test hole cards consistency when cards change (error)."""
    validator = ConfidenceValidator()

    previous = {"hole_cards": ["Ah", "Kd"]}
    current = {"hole_cards": ["2h", "3d"]}

    score = validator._check_hole_cards_consistency(current, previous)

    assert score < 1.0  # Inconsistent


def test_board_consistency_growth():
    """Test board consistency when board grows (expected)."""
    validator = ConfidenceValidator()

    previous = {"board": ["Qh", "Js", "Tc"]}
    current = {"board": ["Qh", "Js", "Tc", "5d"]}  # Turn added

    score = validator._check_board_consistency(current, previous)

    assert score == 1.0  # Consistent growth


def test_board_consistency_changed():
    """Test board consistency when cards change (error)."""
    validator = ConfidenceValidator()

    previous = {"board": ["Qh", "Js", "Tc"]}
    current = {"board": ["Qh", "9s", "Tc"]}  # Middle card changed

    score = validator._check_board_consistency(current, previous)

    assert score < 1.0  # Inconsistent


def test_pot_consistency_increase():
    """Test pot consistency when pot increases."""
    validator = ConfidenceValidator()

    previous = {"pot": 100}
    current = {"pot": 150}

    score = validator._check_pot_consistency(current, previous)

    assert score == 1.0  # Consistent


def test_pot_consistency_decrease():
    """Test pot consistency when pot decreases (new hand)."""
    validator = ConfidenceValidator()

    previous = {"pot": 500}
    current = {"pot": 50}  # New hand started

    score = validator._check_pot_consistency(current, previous)

    assert score < 1.0  # Suspicious (but could be new hand)


def test_validation_pass():
    """Test full validation with passing confidence."""
    validator = ConfidenceValidator(threshold=0.70)

    state = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "confidence": {"hole_cards": 0.9, "board": 0.9, "pot": 0.85, "stacks": 0.9},
    }

    is_confident, confidence = validator.validate(state)

    assert is_confident is True
    assert confidence >= 0.70


def test_validation_fail():
    """Test full validation with failing confidence."""
    validator = ConfidenceValidator(threshold=0.70)

    state = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "confidence": {"hole_cards": 0.5, "board": 0.4, "pot": 0.3, "stacks": 0.4},
    }

    is_confident, confidence = validator.validate(state)

    assert is_confident is False
    assert confidence < 0.70


def test_temporal_consistency_check():
    """Test temporal consistency across multiple frames."""
    validator = ConfidenceValidator()

    # Frame 1: Preflop
    state1 = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "confidence": {"hole_cards": 0.9, "board": 0.9, "pot": 0.9, "stacks": 0.9},
    }
    is_conf1, conf1 = validator.validate(state1)

    # Frame 2: Flop (consistent)
    state2 = {
        "hole_cards": ["Ah", "Kd"],
        "board": ["Qh", "Js", "Tc"],
        "pot": 150,
        "confidence": {"hole_cards": 0.9, "board": 0.9, "pot": 0.9, "stacks": 0.9},
    }
    is_conf2, conf2 = validator.validate(state2)

    assert is_conf2 is True

    # Frame 3: Inconsistent hole cards (error)
    state3 = {
        "hole_cards": ["2h", "3d"],  # Changed!
        "board": ["Qh", "Js", "Tc"],
        "pot": 150,
        "confidence": {"hole_cards": 0.9, "board": 0.9, "pot": 0.9, "stacks": 0.9},
    }
    is_conf3, conf3 = validator.validate(state3)

    # Confidence should be penalized due to inconsistency
    assert conf3 < conf2


def test_reset():
    """Test buffer reset."""
    validator = ConfidenceValidator()

    state = {"hole_cards": ["Ah", "Kd"], "confidence": {"hole_cards": 0.9}}
    validator.validate(state)

    assert validator.get_buffer_size() == 1

    validator.reset()

    assert validator.get_buffer_size() == 0
