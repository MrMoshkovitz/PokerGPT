"""
Hand Evaluator

Poker hand strength calculation and board texture classification.
"""

from typing import List, Set
import logging

logger = logging.getLogger(__name__)

try:
    from treys import Card, Evaluator

    TREYS_AVAILABLE = True
except ImportError:
    TREYS_AVAILABLE = False
    logger.warning("treys library not available. Using simplified hand evaluation.")


def calculate_hand_strength(hole_cards: List[str], board: List[str]) -> str:
    """
    Calculate hand strength bucket.

    Args:
        hole_cards: Your two hole cards
        board: Community cards (3-5 cards)

    Returns:
        "NUTS", "STRONG", "MEDIUM", "WEAK", or "BLUFF"
    """
    if TREYS_AVAILABLE:
        return _calculate_hand_strength_treys(hole_cards, board)
    else:
        return _calculate_hand_strength_simple(hole_cards, board)


def _calculate_hand_strength_treys(hole_cards: List[str], board: List[str]) -> str:
    """Calculate hand strength using treys library."""
    try:
        evaluator = Evaluator()

        # Convert to treys format
        hole = [Card.new(c) for c in hole_cards]
        board_cards = [Card.new(c) for c in board]

        # Evaluate hand
        rank = evaluator.evaluate(board_cards, hole)

        # Bucket by rank (lower is better in treys)
        # Max rank is 7462 (worst hand)
        if rank < 500:  # Top ~7%
            return "NUTS"
        elif rank < 1500:  # Top ~20%
            return "STRONG"
        elif rank < 3000:  # Top ~40%
            return "MEDIUM"
        elif rank < 5000:  # Top ~67%
            return "WEAK"
        else:
            return "BLUFF"

    except Exception as e:
        logger.error(f"Error evaluating hand with treys: {e}")
        return "MEDIUM"  # Default


def _calculate_hand_strength_simple(hole_cards: List[str], board: List[str]) -> str:
    """Simplified hand strength calculation (fallback)."""
    # Very basic: just check for pairs/high cards
    # In production, use treys or similar library

    if not hole_cards or not board:
        return "MEDIUM"

    # Extract ranks
    hole_ranks = [c[0] for c in hole_cards]
    board_ranks = [c[0] for c in board]
    all_ranks = hole_ranks + board_ranks

    # Count rank frequencies
    rank_counts = {}
    for rank in all_ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    max_count = max(rank_counts.values())

    # Very simplified bucketing
    if max_count >= 4:  # Quads
        return "NUTS"
    elif max_count == 3:  # Trips or full house
        if len([c for c in rank_counts.values() if c >= 2]) >= 2:
            return "NUTS"  # Full house
        return "STRONG"  # Trips
    elif max_count == 2:  # Pair(s)
        pairs = [r for r, c in rank_counts.items() if c == 2]
        if len(pairs) >= 2:
            return "STRONG"  # Two pair
        return "MEDIUM"  # One pair
    else:
        # High card
        high_cards = {"A", "K", "Q"}
        if any(r in high_cards for r in hole_ranks):
            return "MEDIUM"
        return "WEAK"


def classify_board_texture(board: List[str]) -> str:
    """
    Classify board texture.

    Args:
        board: Community cards (3-5 cards)

    Returns:
        "WET", "DRY", "PAIRED", or "COORDINATED"
    """
    if not board or len(board) < 3:
        return "DRY"

    # Extract suits and ranks
    suits = [c[1] for c in board]
    ranks = [c[0] for c in board]

    # Count suit frequencies
    suit_counts = {}
    for suit in suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1

    # Count rank frequencies
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    # Check for paired board
    if max(rank_counts.values()) >= 2:
        return "PAIRED"

    # Check for flush draw (3+ cards of same suit)
    if max(suit_counts.values()) >= 3:
        return "WET"

    # Check for straight potential (consecutive ranks)
    if _has_straight_potential(ranks):
        return "COORDINATED"

    # Default: dry board
    return "DRY"


def _has_straight_potential(ranks: List[str]) -> bool:
    """Check if board has straight draw potential."""
    # Map ranks to numbers
    rank_map = {"A": 14, "K": 13, "Q": 12, "J": 11, "T": 10}
    for i in range(2, 10):
        rank_map[str(i)] = i

    # Convert to numbers
    rank_nums = sorted([rank_map.get(r, 0) for r in ranks if r in rank_map], reverse=True)

    if len(rank_nums) < 3:
        return False

    # Check for consecutive or near-consecutive cards
    for i in range(len(rank_nums) - 2):
        gap1 = rank_nums[i] - rank_nums[i + 1]
        gap2 = rank_nums[i + 1] - rank_nums[i + 2]

        # If gaps are small (≤2), there's straight potential
        if gap1 <= 2 and gap2 <= 2:
            return True

    return False


def get_outs(hole_cards: List[str], board: List[str]) -> int:
    """
    Calculate number of outs (cards that improve your hand).

    Args:
        hole_cards: Your two hole cards
        board: Community cards

    Returns:
        Estimated number of outs
    """
    # Simplified outs calculation
    # In production, use proper poker library

    if not TREYS_AVAILABLE:
        logger.warning("Outs calculation requires treys library")
        return 0

    # This would require more complex logic
    # For MVP, return placeholder
    return 0
