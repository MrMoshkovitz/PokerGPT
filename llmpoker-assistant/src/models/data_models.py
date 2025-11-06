"""
Data Models

Pydantic models for type-safe game state and recommendations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Any
from enum import Enum


class Position(str, Enum):
    """Poker table positions."""

    BTN = "BTN"  # Button
    CO = "CO"  # Cut-off
    MP = "MP"  # Middle position
    UTG = "UTG"  # Under the gun
    SB = "SB"  # Small blind
    BB = "BB"  # Big blind
    UNKNOWN = "UNKNOWN"


class Action(str, Enum):
    """Poker actions."""

    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    BET = "BET"
    RAISE = "RAISE"
    ALL_IN = "ALL_IN"


class GameState(BaseModel):
    """Poker game state extracted from vision."""

    hole_cards: List[str] = Field(default_factory=list, description="Your two hole cards")
    board: List[str] = Field(default_factory=list, description="Community cards (0-5)")
    pot: float = Field(default=0.0, description="Current pot size")
    your_stack: float = Field(default=0.0, description="Your chip stack")
    position: Position = Field(default=Position.UNKNOWN, description="Your position")
    action_on_you: bool = Field(default=False, description="Is it your turn?")
    confidence: Dict[str, float] = Field(
        default_factory=dict, description="Confidence scores per element"
    )

    class Config:
        use_enum_values = True


class GTOAction(BaseModel):
    """GTO baseline recommendation."""

    action: Action = Field(description="Recommended action")
    sizing: Optional[float] = Field(
        default=None, description="Bet/raise size ($ amount or % pot)"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="GTO confidence")
    range: Optional[str] = Field(default=None, description="Hand range (e.g., 'top 15%')")


class Recommendation(BaseModel):
    """Final LLM recommendation with reasoning."""

    action: str = Field(description="Recommended action (e.g., 'RAISE to $450')")
    amount: Optional[float] = Field(default=None, description="Exact amount if applicable")
    confidence: float = Field(ge=0.0, le=1.0, description="Recommendation confidence")
    reasoning: str = Field(description="Detailed reasoning for the action")
    alternatives: List[Dict[str, Any]] = Field(
        default_factory=list, description="Alternative actions with confidence"
    )
    gto_baseline: Optional[GTOAction] = Field(
        default=None, description="GTO baseline for comparison"
    )
    llm_provider: str = Field(default="claude_cli", description="LLM provider used")
    fallback_used: bool = Field(default=False, description="Whether fallback was triggered")


class HandHistory(BaseModel):
    """Single hand record for database."""

    session_id: str
    hand_number: int
    timestamp: float
    position: Position
    hole_cards: List[str]
    board: List[str]
    pot: float
    stack: float
    gto_action: Optional[GTOAction]
    recommendation: Optional[Recommendation]
    action_taken: Optional[str] = None
    outcome: Optional[str] = None  # "won", "lost", "folded"
    amount_won: Optional[float] = None
    vision_confidence: float
    latency_ms: int
