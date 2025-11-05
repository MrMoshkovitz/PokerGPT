"""
Logging Infrastructure

Structured logging with JSON Lines format for decisions and standard logging for application.
"""

import logging
import json
import time
from logging.handlers import RotatingFileHandler
from typing import Dict, Any
import os


def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    Configure application and decision logging.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    os.makedirs(log_dir, exist_ok=True)

    # Application logs (standard format)
    app_handler = RotatingFileHandler(
        f"{log_dir}/app.log", maxBytes=100 * 1024 * 1024, backupCount=5  # 100MB
    )
    app_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s - %(name)s - %(message)s")
    )

    # Root logger configuration
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[app_handler, console_handler],
    )

    # Decision logs (JSON Lines format)
    decision_handler = RotatingFileHandler(
        f"{log_dir}/decisions.jsonl",
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=5,
    )
    decision_handler.setFormatter(logging.Formatter("%(message)s"))

    decision_logger = logging.getLogger("decisions")
    decision_logger.addHandler(decision_handler)
    decision_logger.setLevel(logging.INFO)
    decision_logger.propagate = False  # Don't propagate to root logger

    # Error logs (separate file)
    error_handler = RotatingFileHandler(
        f"{log_dir}/errors.log", maxBytes=50 * 1024 * 1024, backupCount=3  # 50MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logging.getLogger().addHandler(error_handler)

    logging.info(f"Logging initialized: level={log_level}, dir={log_dir}")


def log_decision(
    game_state: Dict[str, Any],
    gto_action: Dict[str, Any],
    recommendation: Dict[str, Any],
    vision_confidence: float,
    latency_ms: int,
    session_id: str,
    hand_number: int,
):
    """
    Log a poker decision in JSON Lines format.

    Args:
        game_state: Current game state (cards, pot, stacks)
        gto_action: GTO baseline recommendation
        recommendation: Final LLM recommendation
        vision_confidence: Aggregate vision confidence
        latency_ms: Total processing time
        session_id: Current session ID
        hand_number: Hand number in session
    """
    decision_logger = logging.getLogger("decisions")

    log_entry = {
        "timestamp": time.time(),
        "session_id": session_id,
        "hand_number": hand_number,
        "game_state": game_state,
        "gto_baseline": gto_action,
        "recommendation": recommendation,
        "vision_confidence": vision_confidence,
        "latency_ms": latency_ms,
    }

    decision_logger.info(json.dumps(log_entry))


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)
