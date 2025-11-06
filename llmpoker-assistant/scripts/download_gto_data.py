"""
Download/Generate GTO Data

Creates simplified GTO strategy tables for preflop and postflop play.
In production, this would download from GTOBase or similar sources.
For MVP, we generate simplified ranges.
"""

import os
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_simplified_preflop_ranges():
    """
    Generate simplified preflop ranges by position.

    Note: These are basic ranges, not full GTO.
    In production, download from GTOBase/GTOwizard.
    """
    ranges = {
        "BTN": {  # Button - widest range
            "AA": {"action": "RAISE", "sizing": 3.0},
            "KK": {"action": "RAISE", "sizing": 3.0},
            "QQ": {"action": "RAISE", "sizing": 3.0},
            "JJ": {"action": "RAISE", "sizing": 3.0},
            "TT": {"action": "RAISE", "sizing": 3.0},
            "99": {"action": "RAISE", "sizing": 3.0},
            "88": {"action": "RAISE", "sizing": 2.5},
            "77": {"action": "RAISE", "sizing": 2.5},
            "AK": {"action": "RAISE", "sizing": 3.0},
            "AQ": {"action": "RAISE", "sizing": 3.0},
            "AJ": {"action": "RAISE", "sizing": 2.5},
            "KQ": {"action": "RAISE", "sizing": 2.5},
            # ... (simplified for MVP)
        },
        "CO": {  # Cut-off
            "AA": {"action": "RAISE", "sizing": 3.0},
            "KK": {"action": "RAISE", "sizing": 3.0},
            "QQ": {"action": "RAISE", "sizing": 3.0},
            "JJ": {"action": "RAISE", "sizing": 3.0},
            "TT": {"action": "RAISE", "sizing": 3.0},
            "AK": {"action": "RAISE", "sizing": 3.0},
            "AQ": {"action": "RAISE", "sizing": 3.0},
            # ...
        },
        "MP": {},  # Middle position
        "UTG": {},  # Under the gun - tightest range
        "SB": {},  # Small blind
        "BB": {},  # Big blind
    }

    logger.info("Generated simplified preflop ranges")
    return ranges


def generate_simplified_postflop_buckets():
    """
    Generate simplified postflop decision buckets.

    Buckets: (hand_strength, board_texture, SPR) → action
    """
    buckets = {
        # (hand_strength, board_texture, SPR_bucket) → action
        ("NUTS", "WET", "DEEP"): {"action": "BET", "sizing": 0.75},  # 75% pot
        ("NUTS", "WET", "MEDIUM"): {"action": "BET", "sizing": 1.0},  # 100% pot
        ("NUTS", "WET", "SHALLOW"): {"action": "BET", "sizing": 1.5},  # All-in
        ("NUTS", "DRY", "DEEP"): {"action": "BET", "sizing": 0.5},  # 50% pot
        ("STRONG", "WET", "DEEP"): {"action": "BET", "sizing": 0.66},
        ("STRONG", "DRY", "DEEP"): {"action": "BET", "sizing": 0.5},
        ("MEDIUM", "WET", "DEEP"): {"action": "CHECK", "sizing": 0},
        ("MEDIUM", "DRY", "DEEP"): {"action": "CHECK", "sizing": 0},
        ("WEAK", "WET", "DEEP"): {"action": "CHECK", "sizing": 0},
        ("WEAK", "DRY", "DEEP"): {"action": "CHECK", "sizing": 0},
        ("BLUFF", "WET", "DEEP"): {"action": "CHECK", "sizing": 0},
        # ... (more combinations)
    }

    logger.info("Generated simplified postflop buckets")
    return buckets


def save_gto_data(output_dir: str = "data/gto"):
    """
    Save GTO data as pickle files.

    Args:
        output_dir: Directory to save GTO data
    """
    os.makedirs(output_dir, exist_ok=True)

    # Generate data
    preflop_ranges = generate_simplified_preflop_ranges()
    postflop_buckets = generate_simplified_postflop_buckets()

    # Save as pickle
    with open(os.path.join(output_dir, "preflop_ranges.pkl"), "wb") as f:
        pickle.dump(preflop_ranges, f)

    with open(os.path.join(output_dir, "postflop_buckets.pkl"), "wb") as f:
        pickle.dump(postflop_buckets, f)

    logger.info(f"✓ GTO data saved to {output_dir}")
    logger.info(f"  - preflop_ranges.pkl: {len(preflop_ranges)} positions")
    logger.info(f"  - postflop_buckets.pkl: {len(postflop_buckets)} buckets")

    logger.warning(
        "NOTE: These are simplified ranges for MVP. "
        "For production, download full GTO data from GTOBase or GTOwizard."
    )


if __name__ == "__main__":
    save_gto_data()
