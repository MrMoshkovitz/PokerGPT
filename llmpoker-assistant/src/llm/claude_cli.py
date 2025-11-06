"""
Claude Code CLI Executor

Executes Claude Code CLI with extended thinking for poker decision reasoning.
"""

import subprocess
import json
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)


class ClaudeCLI:
    """Claude Code CLI executor with ultrathink mode."""

    def __init__(self, timeout: int = 5, extended_thinking: bool = True):
        """
        Initialize Claude CLI executor.

        Args:
            timeout: Timeout in seconds (default: 5)
            extended_thinking: Enable extended thinking mode (default: True)
        """
        self.timeout = timeout
        self.extended_thinking = extended_thinking

        # Verify Claude CLI is available
        if not self._check_cli_available():
            logger.warning("Claude Code CLI not found in PATH")

    def _check_cli_available(self) -> bool:
        """Check if Claude CLI is installed and accessible."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_recommendation(self, prompt: str) -> Optional[Dict]:
        """
        Execute Claude Code CLI with poker decision prompt.

        Args:
            prompt: Formatted prompt with game state and context

        Returns:
            {
                "action": "RAISE",
                "amount": 450,
                "confidence": 0.87,
                "reasoning": "Strong draw...",
                "alternatives": [...]
            }
            or None if execution fails
        """
        try:
            # Build command
            cmd = ["claude", "-p"]

            if self.extended_thinking:
                prompt = f"--extended-thinking\n\n{prompt}"

            cmd.append(prompt)

            logger.debug(f"Executing Claude CLI (timeout={self.timeout}s)")

            # Execute
            result = subprocess.run(
                cmd,
                timeout=self.timeout,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error(f"Claude CLI error (code {result.returncode}): {result.stderr}")
                return None

            response = result.stdout.strip()
            logger.debug(f"Claude CLI response: {response[:200]}...")

            # Parse response
            return self._parse_response(response)

        except subprocess.TimeoutExpired:
            logger.warning(f"Claude CLI timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Claude CLI exception: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        """
        Parse Claude CLI JSON response.

        Handles markdown code blocks and various JSON formats.
        """
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.warning("No JSON found in Claude CLI response")
                    return None

            # Parse JSON
            data = json.loads(json_str)

            # Validate required fields
            if "action" not in data:
                logger.warning("Missing 'action' in Claude CLI response")
                return None

            # Ensure all expected fields exist
            return {
                "action": data.get("action"),
                "amount": data.get("amount"),
                "confidence": float(data.get("confidence", 0.75)),
                "reasoning": data.get("reasoning", ""),
                "alternatives": data.get("alternatives", []),
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response was: {response}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Claude CLI response: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Claude CLI is available."""
        return self._check_cli_available()
