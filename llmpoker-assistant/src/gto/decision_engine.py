"""
GTO Decision Engine

High-level interface for GTO-based decision making.
"""

from typing import Dict, List
import logging
from src.gto.strategy_cache import GTOStrategyCache
from src.models.data_models import GTOAction, Action

logger = logging.getLogger(__name__)


class GTODecisionEngine:
    """High-level GTO decision engine."""

    def __init__(self, data_path: str):
        """
        Initialize GTO decision engine.

        Args:
            data_path: Path to GTO data directory
        """
        self.cache = GTOStrategyCache()
        self.cache.load_from_disk(data_path)

        logger.info("GTO decision engine initialized")

    def get_recommendation(
        self,
        position: str,
        hole_cards: List[str],
        board: List[str],
        pot: float,
        stack: float,
    ) -> GTOAction:
        """
        Get GTO recommendation for current situation.

        Args:
            position: Your position (BTN, CO, etc.)
            hole_cards: Your two hole cards
            board: Community cards (empty for preflop)
            pot: Current pot size
            stack: Your stack size

        Returns:
            GTOAction with recommended action, sizing, and confidence
        """
        # Get raw action from cache
        action_data = self.cache.get_action(position, hole_cards, board, pot, stack)

        # Convert to GTOAction model
        try:
            return GTOAction(
                action=Action(action_data["action"]),
                sizing=action_data.get("sizing"),
                confidence=action_data.get("confidence", 0.75),
                range=action_data.get("range"),
            )
        except Exception as e:
            logger.error(f"Error creating GTOAction: {e}")
            # Return default action
            return GTOAction(
                action=Action.CHECK, sizing=None, confidence=0.50, range=None
            )

    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return self.cache.get_stats()

    def is_loaded(self) -> bool:
        """Check if GTO data is loaded."""
        return self.cache.loaded
