"""
OpenAI API Fallback

Fallback LLM provider using OpenAI GPT-4.
"""

import os
import json
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai library not installed")


class OpenAIFallback:
    """OpenAI API fallback provider."""

    def __init__(self, timeout: int = 5):
        """
        Initialize OpenAI fallback.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not OPENAI_AVAILABLE:
            logger.error("openai library not available")
            return

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set")
            return

        try:
            self.client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
            logger.info("OpenAI fallback initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def get_recommendation(self, prompt: str) -> Optional[Dict]:
        """
        Get recommendation from OpenAI GPT-4.

        Args:
            prompt: Formatted poker decision prompt

        Returns:
            Recommendation dict or None if fails
        """
        if not OPENAI_AVAILABLE or not self.client:
            logger.error("OpenAI not available")
            return None

        try:
            logger.debug("Calling OpenAI API")

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional poker advisor providing optimal GTO-based recommendations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content

            logger.debug(f"OpenAI response: {content[:200]}...")

            # Parse response
            return self._parse_response(content)

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        """Parse OpenAI response to extract recommendation."""
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
                    logger.warning("No JSON in OpenAI response")
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
            logger.error(f"Error parsing OpenAI response: {e}")
            return None

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return OPENAI_AVAILABLE and self.client is not None
