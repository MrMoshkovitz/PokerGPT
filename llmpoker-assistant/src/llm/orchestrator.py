"""
LLM Orchestrator

Manages LLM execution with fallback chain: Claude CLI → OpenAI → Gemini → GTO-only
"""

from typing import Dict, Optional, List
import logging
import time
from src.llm.claude_cli import ClaudeCLI
from src.llm.openai_fallback import OpenAIFallback
from src.llm.gemini_fallback import GeminiFallback
from src.llm.prompt_builder import PromptBuilder
from src.models.data_models import Recommendation

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Orchestrates LLM execution with fallback chain."""

    def __init__(self, timeout: int = 5):
        """
        Initialize LLM orchestrator.

        Args:
            timeout: Timeout per LLM provider (seconds)
        """
        self.timeout = timeout

        # Initialize providers
        self.claude = ClaudeCLI(timeout=timeout)
        self.openai = OpenAIFallback(timeout=timeout)
        self.gemini = GeminiFallback(timeout=timeout)

        logger.info("LLM orchestrator initialized")
        logger.info(f"  - Claude CLI: {'✓' if self.claude.is_available() else '✗'}")
        logger.info(f"  - OpenAI: {'✓' if self.openai.is_available() else '✗'}")
        logger.info(f"  - Gemini: {'✓' if self.gemini.is_available() else '✗'}")

    def get_recommendation(
        self,
        game_state: Dict,
        gto_baseline: Dict,
        hand_history: List[Dict] = None,
        session_stats: Dict = None,
    ) -> Recommendation:
        """
        Get poker recommendation with fallback chain.

        Args:
            game_state: Current game state
            gto_baseline: GTO baseline recommendation
            hand_history: Recent hands
            session_stats: Session statistics

        Returns:
            Recommendation object (always returns something)
        """
        start_time = time.time()

        # Build prompt
        prompt = PromptBuilder.build_decision_prompt(
            game_state, gto_baseline, hand_history, session_stats
        )

        # Try providers in order
        providers = [
            ("claude_cli", self.claude),
            ("openai", self.openai),
            ("gemini", self.gemini),
        ]

        for provider_name, provider in providers:
            if not provider.is_available():
                logger.debug(f"{provider_name} not available, skipping")
                continue

            logger.info(f"Trying {provider_name}...")

            result = provider.get_recommendation(prompt)

            if result:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"✓ {provider_name} succeeded in {latency_ms}ms: {result['action']}"
                )

                # Convert to Recommendation model
                return Recommendation(
                    action=result["action"],
                    amount=result.get("amount"),
                    confidence=result.get("confidence", 0.75),
                    reasoning=result.get("reasoning", ""),
                    alternatives=result.get("alternatives", []),
                    gto_baseline=gto_baseline,
                    llm_provider=provider_name,
                    fallback_used=(provider_name != "claude_cli"),
                )

            logger.warning(f"{provider_name} failed, trying next...")

        # All providers failed → Fallback to GTO-only
        logger.error("All LLM providers failed! Falling back to GTO-only")
        return self._gto_only_recommendation(gto_baseline)

    def _gto_only_recommendation(self, gto_baseline: Dict) -> Recommendation:
        """Create recommendation from GTO baseline only (ultimate fallback)."""
        action_str = gto_baseline.get("action", "CHECK")
        sizing = gto_baseline.get("sizing", 0)

        if action_str == "RAISE" and sizing:
            action_display = f"RAISE to ${sizing:.2f}"
        elif action_str == "BET" and sizing:
            action_display = f"BET ${sizing:.2f}"
        else:
            action_display = action_str

        return Recommendation(
            action=action_display,
            amount=sizing,
            confidence=gto_baseline.get("confidence", 0.75),
            reasoning="LLM reasoning unavailable. Using GTO baseline only.",
            alternatives=[],
            gto_baseline=gto_baseline,
            llm_provider="gto_only",
            fallback_used=True,
        )

    def get_provider_status(self) -> Dict[str, bool]:
        """Get availability status of all providers."""
        return {
            "claude_cli": self.claude.is_available(),
            "openai": self.openai.is_available(),
            "gemini": self.gemini.is_available(),
        }
