"""
Card Utilities

Helper functions for poker card manipulation and validation.
"""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Card ranks and suits
RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
SUITS = ["s", "h", "d", "c"]  # spades, hearts, diamonds, clubs

RANK_MAP = {
    "A": 14,
    "K": 13,
    "Q": 12,
    "J": 11,
    "T": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
}


def validate_card(card: str) -> bool:
    """
    Validate card format (e.g., "Ah", "Kd", "Ts").

    Args:
        card: Card string

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(card, str) or len(card) != 2:
        return False

    rank = card[0].upper()
    suit = card[1].lower()

    return rank in RANKS and suit in SUITS


def normalize_card(card: str) -> Optional[str]:
    """
    Normalize card format to standard (e.g., "ah" → "Ah").

    Args:
        card: Card string (case-insensitive)

    Returns:
        Normalized card or None if invalid
    """
    if not card or len(card) != 2:
        return None

    rank = card[0].upper()
    suit = card[1].lower()

    if rank not in RANKS or suit not in SUITS:
        return None

    return f"{rank}{suit}"


def normalize_hand(cards: List[str]) -> Optional[str]:
    """
    Normalize hand to standard format (e.g., ["Ah", "Kd"] → "AKo").

    Args:
        cards: List of 2 cards

    Returns:
        Normalized hand string (e.g., "AKo", "AKs", "AA") or None if invalid
    """
    if not cards or len(cards) != 2:
        return None

    # Validate and normalize
    card1 = normalize_card(cards[0])
    card2 = normalize_card(cards[1])

    if not card1 or not card2:
        return None

    rank1 = card1[0]
    suit1 = card1[1]
    rank2 = card2[0]
    suit2 = card2[1]

    # Order by rank (higher first)
    if RANK_MAP[rank1] < RANK_MAP[rank2]:
        rank1, rank2 = rank2, rank1
        suit1, suit2 = suit2, suit1

    # Determine suited/offsuit
    if rank1 == rank2:
        return f"{rank1}{rank2}"  # Pocket pair (e.g., "AA")
    elif suit1 == suit2:
        return f"{rank1}{rank2}s"  # Suited (e.g., "AKs")
    else:
        return f"{rank1}{rank2}o"  # Offsuit (e.g., "AKo")


def parse_cards(text: str) -> List[str]:
    """
    Parse cards from text (e.g., "Ah Kd Qs" → ["Ah", "Kd", "Qs"]).

    Args:
        text: Text containing cards

    Returns:
        List of normalized cards
    """
    # Match card patterns (e.g., "Ah", "10c", "Ts")
    pattern = r"([AKQJT98765432]|10)([shdc])"
    matches = re.findall(pattern, text, re.IGNORECASE)

    cards = []
    for rank, suit in matches:
        # Normalize "10" to "T"
        if rank == "10":
            rank = "T"
        card = normalize_card(f"{rank}{suit}")
        if card:
            cards.append(card)

    return cards


def card_to_treys_format(card: str) -> str:
    """
    Convert card to treys library format.

    Args:
        card: Card in our format (e.g., "Ah")

    Returns:
        Card in treys format (e.g., "Ah" stays "Ah")
    """
    # treys uses same format, just validate
    if validate_card(card):
        return card
    return None


def cards_to_treys_format(cards: List[str]) -> List[str]:
    """Convert list of cards to treys format."""
    return [card_to_treys_format(c) for c in cards if card_to_treys_format(c)]
