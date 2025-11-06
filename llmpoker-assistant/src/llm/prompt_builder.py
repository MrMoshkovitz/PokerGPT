"""
Prompt Builder

Constructs rich context prompts for LLM poker decision-making.
"""

import json
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds comprehensive prompts for LLM reasoning."""

    @staticmethod
    def build_decision_prompt(
        game_state: Dict[str, Any],
        gto_baseline: Dict[str, Any],
        hand_history: List[Dict[str, Any]] = None,
        session_stats: Dict[str, Any] = None,
    ) -> str:
        """
        Build comprehensive poker decision prompt.

        Args:
            game_state: Current game state from vision
            gto_baseline: GTO baseline recommendation
            hand_history: Recent hands (optional)
            session_stats: Session statistics (optional)

        Returns:
            Formatted prompt string
        """
        hand_history = hand_history or []
        session_stats = session_stats or {}

        prompt = f"""You are a professional poker advisor using GTO strategy as your foundation. Analyze this decision point and provide optimal action.

**Current Situation:**
- Your Hand: {' '.join(game_state.get('hole_cards', []))}
- Board: {' '.join(game_state.get('board', [])) or 'Preflop'}
- Pot: ${game_state.get('pot', 0):.2f}
- Your Stack: ${game_state.get('your_stack', 0):.2f}
- Position: {game_state.get('position', 'UNKNOWN')}
- Action on you: {game_state.get('action_on_you', False)}

**GTO Baseline Recommendation:**
```json
{json.dumps(gto_baseline, indent=2)}
```

**Recent Hand History (last {len(hand_history)} hands):**
{PromptBuilder._format_hand_history(hand_history)}

**Session Statistics:**
- Hands Played: {session_stats.get('hands_played', 0)}
- VPIP: {session_stats.get('vpip', 0):.1f}%
- Win Rate: ${session_stats.get('win_rate', 0):.2f}/hour

**Task:**
Provide a recommendation in JSON format:
```json
{{
    "action": "<FOLD|CALL|RAISE>",
    "amount": <numeric amount if RAISE, null otherwise>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "alternatives": [
        {{"action": "...", "confidence": <0.0-1.0>}}
    ]
}}
```

**Think deeply about:**
1. Hand strength vs opponent range
2. Position and initiative
3. Pot odds and implied odds
4. Board texture and equity distribution
5. Stack-to-pot ratio (SPR)
6. GTO baseline vs exploitative adjustments

Use extended thinking to analyze all factors thoroughly. Your recommendation will be shown to the user with full accountability.
"""

        return prompt

    @staticmethod
    def _format_hand_history(history: List[Dict[str, Any]]) -> str:
        """Format recent hand history for context."""
        if not history:
            return "No recent hands"

        formatted = []
        for h in history[-5:]:  # Last 5 hands only
            outcome = h.get("outcome", "unknown")
            amount = h.get("amount_won", 0)
            action = h.get("action_taken", "?")

            formatted.append(
                f"- Hand #{h.get('hand_number', '?')}: "
                f"{' '.join(h.get('hole_cards', []))} → "
                f"{action} → "
                f"{outcome} "
                f"({'+' if amount > 0 else ''}{amount:.2f})"
            )

        return "\n".join(formatted)

    @staticmethod
    def build_simple_prompt(game_state: Dict[str, Any]) -> str:
        """
        Build simplified prompt (minimal context).

        For testing or when full context unavailable.
        """
        return f"""Analyze this poker situation and recommend an action:

Your Hand: {' '.join(game_state.get('hole_cards', []))}
Board: {' '.join(game_state.get('board', [])) or 'Preflop'}
Pot: ${game_state.get('pot', 0)}
Your Stack: ${game_state.get('your_stack', 0)}

Respond in JSON format with action, amount, confidence (0-1), and reasoning.
"""
