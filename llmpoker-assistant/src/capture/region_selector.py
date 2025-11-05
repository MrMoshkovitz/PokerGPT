"""
Region Selector UI

Interactive drag-to-select interface for choosing poker window region.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RegionSelector:
    """Interactive region selection UI using tkinter."""

    def __init__(self):
        self.region: Optional[Dict[str, int]] = None
        self.start_x = 0
        self.start_y = 0
        self.rect = None
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None

    def select_region(self) -> Dict[str, int]:
        """
        Launch drag-to-select UI for poker window region.

        Returns:
            {"left": x, "top": y, "width": w, "height": h}
        """
        logger.info("Launching region selector UI")

        # Create transparent overlay window
        self.root = tk.Tk()
        self.root.title("Select Poker Window Region")
        self.root.attributes("-alpha", 0.3)  # Semi-transparent
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)

        # Instructions
        instructions = tk.Label(
            self.root,
            text="Drag to select poker table region. Press ENTER when done or ESC to cancel.",
            bg="yellow",
            fg="black",
            font=("Arial", 16, "bold"),
            padx=20,
            pady=10,
        )
        instructions.pack()

        # Canvas for drawing selection rectangle
        self.canvas = tk.Canvas(
            self.root, cursor="cross", bg="black", highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Bind keyboard events
        self.root.bind("<Return>", self._on_confirm)
        self.root.bind("<Escape>", self._on_cancel)

        logger.info("Region selector UI launched. Awaiting user selection...")
        self.root.mainloop()

        if self.region is None:
            logger.warning("Region selection cancelled by user")
            raise ValueError("Region selection cancelled")

        logger.info(f"Region selected: {self.region}")
        return self.region

    def _on_press(self, event):
        """Handle mouse button press - start selection."""
        self.start_x = event.x
        self.start_y = event.y

        # Clear previous rectangle
        if self.rect:
            self.canvas.delete(self.rect)

        # Create new rectangle
        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="red",
            width=3,
        )

    def _on_drag(self, event):
        """Handle mouse drag - update selection rectangle."""
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def _on_release(self, event):
        """Handle mouse release - finalize selection."""
        end_x = event.x
        end_y = event.y

        # Calculate region (ensure positive width/height)
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)

        # Minimum size validation
        if width < 100 or height < 100:
            messagebox.showwarning(
                "Selection Too Small",
                "Selected region is too small. Please select a larger area.",
            )
            return

        self.region = {"left": left, "top": top, "width": width, "height": height}

        # Update canvas to show selected region with info
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            left, top, left + width, top + height, outline="green", width=5
        )
        self.canvas.create_text(
            left + width // 2,
            top + height // 2,
            text=f"Selected: {width}x{height}\nPress ENTER to confirm",
            fill="white",
            font=("Arial", 14, "bold"),
        )

    def _on_confirm(self, event):
        """Handle ENTER key - confirm selection."""
        if self.region is None:
            messagebox.showwarning("No Selection", "Please select a region first.")
            return

        logger.info(f"Region confirmed: {self.region}")
        self.root.quit()
        self.root.destroy()

    def _on_cancel(self, event):
        """Handle ESC key - cancel selection."""
        logger.info("Region selection cancelled by user (ESC)")
        self.region = None
        self.root.quit()
        self.root.destroy()


def load_saved_region(config_path: str = "config/region.yaml") -> Optional[Dict[str, int]]:
    """
    Load previously saved region from config file.

    Args:
        config_path: Path to region config file

    Returns:
        Region dict or None if not found
    """
    try:
        import yaml
        import os

        if not os.path.exists(config_path):
            return None

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
            return data.get("region")

    except Exception as e:
        logger.error(f"Error loading saved region: {e}")
        return None


def save_region(region: Dict[str, int], config_path: str = "config/region.yaml"):
    """
    Save region to config file for future sessions.

    Args:
        region: Region coordinates to save
        config_path: Path to save region config
    """
    try:
        import yaml
        import os

        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump({"region": region}, f)

        logger.info(f"Region saved to {config_path}")

    except Exception as e:
        logger.error(f"Error saving region: {e}")
