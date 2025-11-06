"""
Game State Manager

Manages game state lifecycle with temporal validation and persistence.
"""

from typing import Dict, Any, Optional, Tuple
import logging
import time
import uuid
from src.vision.confidence_validator import ConfidenceValidator
from src.models.data_models import GameState

logger = logging.getLogger(__name__)


class GameStateManager:
    """Manages game state lifecycle."""

    def __init__(self, confidence_threshold: float = 0.70):
        """
        Initialize game state manager.

        Args:
            confidence_threshold: Minimum confidence for valid state
        """
        self.validator = ConfidenceValidator(threshold=confidence_threshold)
        self.current_state: Optional[GameState] = None
        self.hand_number = 0
        self.session_id = str(uuid.uuid4())[:8]

        logger.info(f"Game state manager initialized (session={self.session_id})")

    def process_vision_output(self, vision_data: Dict[str, Any]) -> Tuple[bool, float, Optional[GameState]]:
        """
        Process vision output with confidence validation.

        Args:
            vision_data: Raw vision extraction output

        Returns:
            (is_confident, confidence_score, game_state)
        """
        # Validate confidence
        is_confident, confidence = self.validator.validate(vision_data)

        if not is_confident:
            logger.warning(f"Low confidence state: {confidence:.2%}")
            return False, confidence, None

        # Convert to GameState model
        try:
            game_state = GameState(
                hole_cards=vision_data.get("hole_cards", []),
                board=vision_data.get("board", []),
                pot=vision_data.get("pot", 0),
                your_stack=vision_data.get("your_stack", 0),
                position=vision_data.get("position", "UNKNOWN"),
                action_on_you=vision_data.get("action_on_you", False),
                confidence=vision_data.get("confidence", {}),
            )

            # Check if new hand started
            if self._is_new_hand(game_state):
                self.hand_number += 1
                self.validator.reset()
                logger.info(f"New hand detected: #{self.hand_number}")

            self.current_state = game_state

            return True, confidence, game_state

        except Exception as e:
            logger.error(f"Error creating GameState: {e}")
            return False, confidence, None

    def _is_new_hand(self, new_state: GameState) -> bool:
        """
        Detect if a new hand has started.

        Heuristics:
        - Board cards decreased (5 → 0)
        - Pot significantly decreased
        - Hole cards changed
        """
        if not self.current_state:
            return True  # First hand

        # Board decreased
        if len(new_state.board) < len(self.current_state.board):
            return True

        # Pot reset (decreased by >50%)
        if new_state.pot < self.current_state.pot * 0.5:
            return True

        # Hole cards changed (if both non-empty)
        if (
            new_state.hole_cards
            and self.current_state.hole_cards
            and set(new_state.hole_cards) != set(self.current_state.hole_cards)
        ):
            return True

        return False

    def get_current_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self.current_state

    def get_session_id(self) -> str:
        """Get current session ID."""
        return self.session_id

    def get_hand_number(self) -> int:
        """Get current hand number."""
        return self.hand_number

    def reset_session(self):
        """Reset session (new session ID)."""
        self.session_id = str(uuid.uuid4())[:8]
        self.hand_number = 0
        self.current_state = None
        self.validator.reset()

        logger.info(f"Session reset (new session={self.session_id})")
