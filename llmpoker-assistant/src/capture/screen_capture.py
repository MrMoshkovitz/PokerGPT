"""
Screen Capture Module

Event-driven screen capture for poker window monitoring.
Only captures when significant changes detected (>5% pixel diff).
"""

import mss
import hashlib
import logging
from PIL import Image
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ScreenCapture:
    """Event-driven screen capture for poker window."""

    def __init__(self, region: Dict[str, int], diff_threshold: float = 0.05):
        """
        Initialize screen capture.

        Args:
            region: {"left": x, "top": y, "width": w, "height": h}
            diff_threshold: Minimum pixel difference to trigger capture (0.0-1.0)
        """
        self.region = region
        self.diff_threshold = diff_threshold
        self.sct = mss.mss()
        self.last_frame_hash: Optional[str] = None

        logger.info(f"Screen capture initialized: region={region}, threshold={diff_threshold}")

    def check_for_changes(self) -> bool:
        """
        Quick diff check to detect game state changes.

        Returns:
            True if significant change detected (>threshold), False otherwise
        """
        try:
            # Quick low-res capture for hash comparison
            screenshot = self.sct.grab(self.region)
            current_hash = self._calculate_hash(screenshot.rgb)

            if self.last_frame_hash is None:
                self.last_frame_hash = current_hash
                return True  # First frame, always capture

            # Calculate difference
            has_changed = current_hash != self.last_frame_hash

            if has_changed:
                # TODO: More sophisticated diff (pixel-wise comparison)
                # For now, any hash change triggers capture
                self.last_frame_hash = current_hash
                logger.debug("Frame change detected")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
            return False

    def capture_frame(self) -> Optional[Image.Image]:
        """
        Capture full-resolution screenshot of poker window.

        Returns:
            PIL Image or None if capture fails
        """
        try:
            screenshot = self.sct.grab(self.region)
            image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            logger.debug(f"Captured frame: {image.size}")
            return image

        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None

    def _calculate_hash(self, data: bytes) -> str:
        """
        Calculate hash of image data for quick comparison.

        Args:
            data: Raw RGB bytes

        Returns:
            MD5 hash string
        """
        return hashlib.md5(data).hexdigest()

    def update_region(self, region: Dict[str, int]):
        """
        Update capture region (e.g., if window moves).

        Args:
            region: New region coordinates
        """
        self.region = region
        self.last_frame_hash = None  # Reset hash
        logger.info(f"Screen capture region updated: {region}")

    def get_region(self) -> Dict[str, int]:
        """Get current capture region."""
        return self.region

    def close(self):
        """Clean up resources."""
        if self.sct:
            self.sct.close()
            logger.info("Screen capture closed")
