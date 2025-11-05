"""
Tests for Screen Capture Module
"""

import pytest
from PIL import Image
from src.capture.screen_capture import ScreenCapture


def test_screen_capture_initialization():
    """Test ScreenCapture initialization."""
    region = {"left": 0, "top": 0, "width": 800, "height": 600}
    capture = ScreenCapture(region, diff_threshold=0.05)

    assert capture.region == region
    assert capture.diff_threshold == 0.05
    assert capture.last_frame_hash is None


def test_capture_frame():
    """Test frame capture (requires display)."""
    region = {"left": 0, "top": 0, "width": 100, "height": 100}
    capture = ScreenCapture(region)

    frame = capture.capture_frame()

    # Check that frame is valid PIL Image
    assert frame is not None
    assert isinstance(frame, Image.Image)
    assert frame.size == (100, 100)


def test_check_for_changes_first_frame():
    """Test that first frame check always returns True."""
    region = {"left": 0, "top": 0, "width": 100, "height": 100}
    capture = ScreenCapture(region)

    # First check should always return True
    assert capture.check_for_changes() is True
    assert capture.last_frame_hash is not None


def test_update_region():
    """Test region update functionality."""
    region1 = {"left": 0, "top": 0, "width": 800, "height": 600}
    capture = ScreenCapture(region1)

    # Trigger initial hash
    capture.check_for_changes()
    assert capture.last_frame_hash is not None

    # Update region
    region2 = {"left": 100, "top": 100, "width": 640, "height": 480}
    capture.update_region(region2)

    assert capture.region == region2
    assert capture.last_frame_hash is None  # Hash reset


def test_get_region():
    """Test get_region method."""
    region = {"left": 10, "top": 20, "width": 300, "height": 400}
    capture = ScreenCapture(region)

    assert capture.get_region() == region


# Integration test (requires manual verification)
@pytest.mark.manual
def test_capture_poker_window():
    """
    Manual test: Capture poker window and verify output.

    Setup: Open a poker client before running this test.
    """
    from src.capture.region_selector import RegionSelector

    # User selects region
    selector = RegionSelector()
    region = selector.select_region()

    # Capture and save frame
    capture = ScreenCapture(region)
    frame = capture.capture_frame()

    if frame:
        frame.save("tests/output/poker_capture_test.png")
        print(f"Captured frame saved: {frame.size}")
        assert frame.size[0] > 0
        assert frame.size[1] > 0
    else:
        pytest.fail("Frame capture failed")
