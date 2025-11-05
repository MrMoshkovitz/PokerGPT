"""
Gemini CLI Fallback

Fallback LLM provider using Google Gemini.
"""

import os
import json
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai library not installed")


class GeminiFallback:
    """Gemini API fallback provider."""

    def __init__(self, timeout: int = 5):
        """
        Initialize Gemini fallback.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not GEMINI_AVAILABLE:
            logger.error("google-generativeai library not available")
            return

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-pro")
            logger.info("Gemini fallback initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    def get_recommendation(self, prompt: str) -> Optional[Dict]:
        """
        Get recommendation from Gemini.

        Args:
            prompt: Formatted poker decision prompt

        Returns:
            Recommendation dict or None if fails
        """
        if not GEMINI_AVAILABLE or not self.model:
            logger.error("Gemini not available")
            return None

        try:
            logger.debug("Calling Gemini API")

            # Add system message to prompt
            full_prompt = f"""You are a professional poker advisor providing optimal GTO-based recommendations.

{prompt}"""

            response = self.model.generate_content(full_prompt)

            content = response.text

            logger.debug(f"Gemini response: {content[:200]}...")

            # Parse response
            return self._parse_response(content)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        """Parse Gemini response to extract recommendation."""
        try:
            # Try to extract JSON
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.warning("No JSON in Gemini response")
                    return None

            data = json.loads(json_str)

            return {
                "action": data.get("action"),
                "amount": data.get("amount"),
                "confidence": float(data.get("confidence", 0.75)),
                "reasoning": data.get("reasoning", ""),
                "alternatives": data.get("alternatives", []),
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return GEMINI_AVAILABLE and self.model is not None
