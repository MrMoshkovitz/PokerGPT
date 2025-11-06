"""
Confidence Validator

3-frame temporal consistency validation for vision output.
Ensures game state is stable before making recommendations.
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ConfidenceValidator:
    """3-frame temporal consistency validation."""

    def __init__(self, buffer_size: int = 3, threshold: float = 0.70):
        """
        Initialize confidence validator.

        Args:
            buffer_size: Number of frames to keep in history (default: 3)
            threshold: Minimum confidence to pass validation (default: 0.70)
        """
        self.buffer_size = buffer_size
        self.threshold = threshold
        self.state_buffer: List[Dict[str, Any]] = []

        logger.info(f"Confidence validator initialized: buffer_size={buffer_size}, threshold={threshold}")

    def validate(self, game_state: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Validate game state confidence with temporal consistency.

        Args:
            game_state: Current game state with confidence scores

        Returns:
            (is_confident, aggregate_confidence)
        """
        # Add to buffer
        self.state_buffer.append(game_state)
        if len(self.state_buffer) > self.buffer_size:
            self.state_buffer.pop(0)

        # Calculate aggregate confidence
        aggregate_confidence = self._aggregate_confidence(game_state)

        # Check temporal consistency if we have enough frames
        if len(self.state_buffer) >= 2:
            consistency_score = self._check_consistency()
            # Penalize confidence if inconsistent
            final_confidence = aggregate_confidence * consistency_score

            logger.debug(
                f"Confidence: aggregate={aggregate_confidence:.2f}, "
                f"consistency={consistency_score:.2f}, "
                f"final={final_confidence:.2f}"
            )
        else:
            final_confidence = aggregate_confidence
            logger.debug(f"Confidence: {final_confidence:.2f} (insufficient frames for consistency check)")

        # Determine if confident enough
        is_confident = final_confidence >= self.threshold

        if not is_confident:
            logger.warning(
                f"Low confidence: {final_confidence:.2f} < {self.threshold:.2f}"
            )

        return is_confident, final_confidence

    def _aggregate_confidence(self, state: Dict[str, Any]) -> float:
        """Calculate average confidence across all elements."""
        confidences = state.get("confidence", {})

        if not confidences:
            return 0.0

        # Average all confidence scores
        scores = [v for v in confidences.values() if isinstance(v, (int, float))]

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def _check_consistency(self) -> float:
        """
        Check temporal consistency across buffered frames.

        Returns:
            Consistency score (0.0-1.0, where 1.0 = fully consistent)
        """
        if len(self.state_buffer) < 2:
            return 1.0

        current = self.state_buffer[-1]
        previous = self.state_buffer[-2]

        consistency_scores = []

        # Check hole cards consistency (shouldn't change mid-hand)
        hole_cards_consistent = self._check_hole_cards_consistency(current, previous)
        consistency_scores.append(hole_cards_consistent)

        # Check board progression (should only add cards)
        board_consistent = self._check_board_consistency(current, previous)
        consistency_scores.append(board_consistent)

        # Check pot progression (should only increase or stay same)
        pot_consistent = self._check_pot_consistency(current, previous)
        consistency_scores.append(pot_consistent)

        # Average consistency scores
        return sum(consistency_scores) / len(consistency_scores)

    def _check_hole_cards_consistency(
        self, current: Dict[str, Any], previous: Dict[str, Any]
    ) -> float:
        """
        Check if hole cards are consistent.

        Hole cards should NOT change mid-hand.
        """
        current_cards = set(current.get("hole_cards", []))
        previous_cards = set(previous.get("hole_cards", []))

        # If either is empty, can't check consistency
        if not current_cards or not previous_cards:
            return 0.5  # Neutral score

        # If cards changed, this is suspicious (unless new hand started)
        if current_cards != previous_cards:
            logger.warning(
                f"Hole cards changed: {previous_cards} → {current_cards} (possible new hand or vision error)"
            )
            return 0.3  # Low consistency (penalize)

        return 1.0  # Fully consistent

    def _check_board_consistency(
        self, current: Dict[str, Any], previous: Dict[str, Any]
    ) -> float:
        """
        Check if board progression is logical.

        Board should only ADD cards (preflop → flop → turn → river).
        Cards should never disappear or change.
        """
        current_board = current.get("board", [])
        previous_board = previous.get("board", [])

        # Empty boards are okay (preflop)
        if not current_board and not previous_board:
            return 1.0

        # Board grew (expected)
        if len(current_board) > len(previous_board):
            # Check that previous cards are still present
            for i, card in enumerate(previous_board):
                if i >= len(current_board) or current_board[i] != card:
                    logger.warning(
                        f"Board cards changed unexpectedly: {previous_board} → {current_board}"
                    )
                    return 0.3
            return 1.0  # Consistent growth

        # Board stayed same size
        elif len(current_board) == len(previous_board):
            # Cards should match exactly
            if current_board == previous_board:
                return 1.0
            else:
                logger.warning(
                    f"Board cards changed: {previous_board} → {current_board}"
                )
                return 0.3

        # Board shrank (suspicious - possible new hand or error)
        else:
            logger.warning(
                f"Board cards decreased: {len(previous_board)} → {len(current_board)} cards (possible new hand)"
            )
            return 0.5  # Could be new hand, not necessarily error

    def _check_pot_consistency(
        self, current: Dict[str, Any], previous: Dict[str, Any]
    ) -> float:
        """
        Check if pot progression is logical.

        Pot should only INCREASE or stay the same (never decrease mid-hand).
        """
        current_pot = current.get("pot", 0)
        previous_pot = previous.get("pot", 0)

        # Both zero is okay
        if current_pot == 0 and previous_pot == 0:
            return 1.0

        # Pot increased (expected)
        if current_pot > previous_pot:
            return 1.0

        # Pot stayed same (okay)
        elif current_pot == previous_pot:
            return 1.0

        # Pot decreased (suspicious - possible new hand or error)
        else:
            logger.warning(
                f"Pot decreased: ${previous_pot} → ${current_pot} (possible new hand or vision error)"
            )
            return 0.5  # Could be new hand

    def reset(self):
        """Reset buffer (e.g., when new hand starts)."""
        self.state_buffer.clear()
        logger.debug("Confidence validator buffer reset")

    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self.state_buffer)
