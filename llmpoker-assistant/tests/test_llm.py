"""
Tests for LLM Module
"""

import pytest
from src.llm.prompt_builder import PromptBuilder
from src.llm.claude_cli import ClaudeCLI


def test_prompt_builder_basic():
    """Test basic prompt building."""
    game_state = {
        "hole_cards": ["Ah", "Kd"],
        "board": ["Qh", "Js", "10c"],
        "pot": 450,
        "your_stack": 2500,
        "position": "BTN",
        "action_on_you": True,
    }

    gto_baseline = {"action": "RAISE", "sizing": 337.5, "confidence": 0.85}

    prompt = PromptBuilder.build_decision_prompt(game_state, gto_baseline)

    # Check that key elements are in prompt
    assert "Ah Kd" in prompt
    assert "Qh Js 10c" in prompt
    assert "$450" in prompt
    assert "BTN" in prompt
    assert "RAISE" in prompt


def test_prompt_builder_with_history():
    """Test prompt building with hand history."""
    game_state = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "your_stack": 1000,
        "position": "BTN",
    }

    gto_baseline = {"action": "RAISE", "sizing": 15}

    hand_history = [
        {
            "hand_number": 1,
            "hole_cards": ["As", "Ks"],
            "action_taken": "RAISE",
            "outcome": "won",
            "amount_won": 100,
        },
        {
            "hand_number": 2,
            "hole_cards": ["2h", "3d"],
            "action_taken": "FOLD",
            "outcome": "folded",
            "amount_won": 0,
        },
    ]

    prompt = PromptBuilder.build_decision_prompt(
        game_state, gto_baseline, hand_history=hand_history
    )

    # Check history is included
    assert "Hand #1" in prompt
    assert "Hand #2" in prompt
    assert "won" in prompt


def test_prompt_builder_with_session_stats():
    """Test prompt building with session stats."""
    game_state = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "your_stack": 1000,
        "position": "BTN",
    }

    gto_baseline = {"action": "RAISE", "sizing": 15}

    session_stats = {"hands_played": 45, "vpip": 22.5, "win_rate": 45.0}

    prompt = PromptBuilder.build_decision_prompt(
        game_state, gto_baseline, session_stats=session_stats
    )

    # Check stats are included
    assert "45" in prompt  # hands
    assert "22.5" in prompt  # VPIP


def test_prompt_builder_simple():
    """Test simplified prompt."""
    game_state = {
        "hole_cards": ["Ah", "Kd"],
        "board": [],
        "pot": 50,
        "your_stack": 1000,
    }

    prompt = PromptBuilder.build_simple_prompt(game_state)

    assert "Ah Kd" in prompt
    assert "$50" in prompt
    assert len(prompt) < 500  # Should be short


@pytest.mark.manual
def test_claude_cli_integration():
    """
    Manual test: Claude CLI integration.

    Requires Claude Code CLI installed.
    """
    cli = ClaudeCLI(timeout=10)

    if not cli.is_available():
        pytest.skip("Claude Code CLI not available")

    # Simple test prompt
    prompt = """Respond in JSON format with this exact structure:
{
    "action": "TEST",
    "confidence": 1.0,
    "reasoning": "This is a test"
}
"""

    result = cli.get_recommendation(prompt)

    if result:
        assert "action" in result
        assert "confidence" in result
        print(f"✓ Claude CLI test passed: {result}")
    else:
        pytest.fail("Claude CLI returned None")
