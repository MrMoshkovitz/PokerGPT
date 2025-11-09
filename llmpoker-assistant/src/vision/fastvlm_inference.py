"""
FastVLM Inference Module

Integrates FastVLM-0.5B for poker game state extraction from screenshots.
"""

import torch
from PIL import Image
from typing import Dict, Any, Optional
import logging
import json
import re

logger = logging.getLogger(__name__)


class FastVLMInference:
    """FastVLM-0.5B model for poker game state extraction."""

    def __init__(self, model_path: str, device: str = "auto"):
        """
        Initialize FastVLM model.

        Args:
            model_path: Path to FastVLM model directory
            device: Device to run on ('cpu', 'cuda', 'mps', or 'auto')
        """
        self.model_path = model_path
        self.device = self._get_device(device)

        logger.info(f"Loading FastVLM model from {model_path}")
        logger.info(f"Using device: {self.device}")

        try:
            # Import LLaVA components
            from llava.model.builder import load_pretrained_model
            from llava.conversation import conv_templates
            from llava.mm_utils import get_model_name_from_path

            # Load model
            model_name = get_model_name_from_path(model_path)
            self.tokenizer, self.model, self.image_processor, self.context_len = (
                load_pretrained_model(
                    model_path=model_path,
                    model_base=None,
                    model_name=model_name,
                    device=self.device,
                )
            )

            self.model.eval()
            self.conv_template = conv_templates.get("qwen_2", conv_templates["default"])

            logger.info(f"✓ FastVLM model loaded successfully (context_len={self.context_len})")

        except Exception as e:
            logger.error(f"Failed to load FastVLM model: {e}")
            raise

    def _get_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device

    def extract_game_state(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract poker game state from screenshot.

        Args:
            image: PIL Image of poker table

        Returns:
            {
                "hole_cards": ["Ah", "Kd"],
                "board": ["Qh", "Js", "10c"],
                "pot": 450,
                "your_stack": 2500,
                "position": "BTN",
                "action_on_you": True,
                "confidence": {
                    "hole_cards": 0.92,
                    "board": 0.88,
                    "pot": 0.85,
                    "stacks": 0.90
                }
            }
        """
        try:
            prompt = self._build_extraction_prompt()

            # Prepare conversation
            conv = self.conv_template.copy()
            conv.append_message(conv.roles[0], prompt)
            conv.append_message(conv.roles[1], None)
            prompt_formatted = conv.get_prompt()

            # Tokenize
            input_ids = self.tokenizer([prompt_formatted], return_tensors="pt").input_ids
            input_ids = input_ids.to(self.device)

            # Process image
            image_tensor = self.image_processor.preprocess(image, return_tensors="pt")[
                "pixel_values"
            ]
            image_tensor = image_tensor.to(self.device, dtype=torch.float16)

            # Generate (greedy decoding for deterministic output)
            with torch.inference_mode():
                output_ids = self.model.generate(
                    input_ids,
                    images=image_tensor,
                    max_new_tokens=512,
                    use_cache=True,
                    do_sample=False,  # Greedy decoding, no sampling
                )

            # Decode response
            response = self.tokenizer.decode(
                output_ids[0][input_ids.shape[1]:], skip_special_tokens=True
            ).strip()

            logger.debug(f"FastVLM raw response: {response}")

            # Parse JSON response
            game_state = self._parse_response(response)

            logger.info(f"Game state extracted: {game_state.get('hole_cards', [])} vs {game_state.get('board', [])}")
            return game_state

        except Exception as e:
            logger.error(f"Error extracting game state: {e}")
            return self._empty_game_state()

    def _build_extraction_prompt(self) -> str:
        """Build vision prompt for game state extraction."""
        return """Analyze poker table. Extract: hole cards, board cards, pot amount, stack, position, action status.

Response format (JSON only):
{"hole_cards":["As","Kh"],"board":["Qh","Js","Tc"],"pot":450,"your_stack":2500,"position":"BTN","action_on_you":true,"confidence":{"hole_cards":0.9,"board":0.85,"pot":0.8,"stacks":0.9}}

Your turn (JSON only):
{"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse FastVLM JSON response.

        Handles cases where LLM wraps JSON in markdown code blocks or generates multiple JSONs.
        Note: Prompt ends with '{' to prime JSON, but model may not include it in output.
        """
        try:
            # If response doesn't start with '{', prepend it (prompt priming artifact)
            if not response.strip().startswith('{'):
                response = '{' + response

            # Try to extract JSON from markdown code blocks first
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Find ALL JSON objects in the response
                json_objects = list(re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL))

                if not json_objects:
                    logger.warning("No JSON found in response")
                    logger.error(f"Raw response: {response[:500]}")
                    return self._empty_game_state()

                # Try to parse JSON objects from last to first (model's actual output comes last)
                for match in reversed(json_objects):
                    json_str = match.group(0)
                    try:
                        data = json.loads(json_str)
                        # Successfully parsed - validate and return
                        return self._validate_game_state(data)
                    except json.JSONDecodeError:
                        continue  # Try next JSON object

                # None of the JSON objects parsed successfully
                logger.error("Found JSON-like text but none parsed successfully")
                logger.error(f"Raw response: {response[:500]}")
                return self._empty_game_state()

            # Parse the JSON we found
            data = json.loads(json_str)

            # Validate and normalize
            return self._validate_game_state(data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw response that failed to parse: {response[:500]}")  # First 500 chars
            logger.debug(f"Full response: {response}")
            return self._empty_game_state()

    def _validate_game_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize extracted game state."""
        # Get confidence and ensure it's a dict
        confidence = data.get("confidence", {})
        if not isinstance(confidence, dict):
            logger.warning(f"Confidence is {type(confidence).__name__}, not dict. Resetting to empty dict.")
            confidence = {}

        validated = {
            "hole_cards": data.get("hole_cards", []),
            "board": data.get("board", []),
            "pot": float(data.get("pot", 0)) if data.get("pot") else 0,
            "your_stack": float(data.get("your_stack", 0)) if data.get("your_stack") else 0,
            "position": data.get("position", "UNKNOWN"),
            "action_on_you": bool(data.get("action_on_you", False)),
            "confidence": confidence,
        }

        # Ensure confidence scores exist
        if not validated["confidence"]:
            validated["confidence"] = {
                "hole_cards": 0.5,
                "board": 0.5,
                "pot": 0.5,
                "stacks": 0.5,
            }

        return validated

    def _empty_game_state(self) -> Dict[str, Any]:
        """Return empty game state (all zeros/nulls)."""
        return {
            "hole_cards": [],
            "board": [],
            "pot": 0,
            "your_stack": 0,
            "position": "UNKNOWN",
            "action_on_you": False,
            "confidence": {
                "hole_cards": 0.0,
                "board": 0.0,
                "pot": 0.0,
                "stacks": 0.0,
            },
        }

    def close(self):
        """Clean up model resources."""
        if hasattr(self, "model"):
            del self.model
        if hasattr(self, "tokenizer"):
            del self.tokenizer
        if hasattr(self, "image_processor"):
            del self.image_processor
        torch.cuda.empty_cache()
        logger.info("FastVLM model resources released")
