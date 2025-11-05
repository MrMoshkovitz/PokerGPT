"""
GTO Strategy Cache

In-memory cache for fast O(1) GTO strategy lookups.
"""

import pickle
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GTOStrategyCache:
    """In-memory GTO strategy lookup cache."""

    def __init__(self):
        self.preflop_ranges: Dict = {}
        self.postflop_buckets: Dict = {}
        self.loaded = False

    def load_from_disk(self, data_path: str):
        """
        Load GTO data from pickle files into memory.

        Args:
            data_path: Directory containing GTO pickle files
        """
        logger.info(f"Loading GTO data from {data_path}")

        try:
            # Load preflop ranges
            preflop_path = os.path.join(data_path, "preflop_ranges.pkl")
            if os.path.exists(preflop_path):
                with open(preflop_path, "rb") as f:
                    self.preflop_ranges = pickle.load(f)
                logger.info(f"✓ Loaded preflop ranges: {len(self.preflop_ranges)} positions")
            else:
                logger.warning(f"Preflop ranges file not found: {preflop_path}")

            # Load postflop buckets
            postflop_path = os.path.join(data_path, "postflop_buckets.pkl")
            if os.path.exists(postflop_path):
                with open(postflop_path, "rb") as f:
                    self.postflop_buckets = pickle.load(f)
                logger.info(
                    f"✓ Loaded postflop buckets: {len(self.postflop_buckets)} strategies"
                )
            else:
                logger.warning(f"Postflop buckets file not found: {postflop_path}")

            self.loaded = True
            logger.info("✓ GTO data loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load GTO data: {e}")
            raise

    def get_action(
        self,
        position: str,
        hole_cards: List[str],
        board: List[str],
        pot: float,
        stack: float,
    ) -> Dict:
        """
        Get GTO baseline recommendation.

        Args:
            position: Player position (BTN, CO, MP, etc.)
            hole_cards: Your two hole cards
            board: Community cards (empty for preflop)
            pot: Current pot size
            stack: Your stack size

        Returns:
            {
                "action": "RAISE",
                "sizing": 450,
                "confidence": 0.85,
                "range": "top 15%"
            }
        """
        if not self.loaded:
            logger.error("GTO data not loaded!")
            return self._default_action()

        # Preflop: Use preflop ranges
        if not board or len(board) == 0:
            return self._get_preflop_action(position, hole_cards)

        # Postflop: Use bucketed strategies
        return self._get_postflop_action(position, hole_cards, board, pot, stack)

    def _get_preflop_action(self, position: str, hole_cards: List[str]) -> Dict:
        """
        Get preflop GTO action from ranges.

        Args:
            position: Player position
            hole_cards: Your two hole cards

        Returns:
            GTO action dict
        """
        from src.utils.card_utils import normalize_hand

        # Normalize hand (e.g., ["Ah", "Kd"] → "AKo")
        hand_key = normalize_hand(hole_cards)

        if not hand_key:
            logger.warning(f"Failed to normalize hand: {hole_cards}")
            return self._default_action()

        # Lookup in preflop ranges
        position_ranges = self.preflop_ranges.get(position, {})

        if hand_key in position_ranges:
            action_data = position_ranges[hand_key].copy()
            action_data["confidence"] = 0.85  # High confidence for preflop GTO
            return action_data
        else:
            # Hand not in range → FOLD
            logger.debug(f"Hand {hand_key} not in {position} range → FOLD")
            return {"action": "FOLD", "sizing": 0, "confidence": 0.90}

    def _get_postflop_action(
        self, position: str, hole_cards: List[str], board: List[str], pot: float, stack: float
    ) -> Dict:
        """
        Get postflop GTO action from bucketed strategies.

        Args:
            position: Player position
            hole_cards: Your two hole cards
            board: Community cards
            pot: Current pot
            stack: Your stack

        Returns:
            GTO action dict
        """
        from src.gto.hand_evaluator import calculate_hand_strength, classify_board_texture

        # Calculate hand strength bucket
        hand_strength = calculate_hand_strength(hole_cards, board)

        # Classify board texture
        board_texture = classify_board_texture(board)

        # Calculate SPR and bucket it
        spr = stack / pot if pot > 0 else 100
        spr_bucket = self._bucket_spr(spr)

        # Lookup in postflop buckets
        bucket_key = (hand_strength, board_texture, spr_bucket)

        if bucket_key in self.postflop_buckets:
            action_data = self.postflop_buckets[bucket_key].copy()
            action_data["confidence"] = 0.75  # Moderate confidence for bucketed GTO
            return action_data
        else:
            # No bucket found → Default to CHECK
            logger.debug(
                f"No postflop bucket for {bucket_key} → CHECK"
            )
            return {"action": "CHECK", "sizing": 0, "confidence": 0.60}

    def _bucket_spr(self, spr: float) -> str:
        """
        Bucket SPR (stack-to-pot ratio) into categories.

        Args:
            spr: Stack to pot ratio

        Returns:
            "DEEP", "MEDIUM", or "SHALLOW"
        """
        if spr > 10:
            return "DEEP"
        elif spr > 3:
            return "MEDIUM"
        else:
            return "SHALLOW"

    def _default_action(self) -> Dict:
        """Default action when GTO data unavailable."""
        return {"action": "CHECK", "sizing": 0, "confidence": 0.50}

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "loaded": self.loaded,
            "preflop_positions": len(self.preflop_ranges),
            "postflop_buckets": len(self.postflop_buckets),
        }
