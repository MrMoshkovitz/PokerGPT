#!/usr/bin/env python
"""
Visual Region Indicator
Shows where the app is monitoring on your screen with a red border.
Includes live preview and verification before closing.
"""

import tkinter as tk
from tkinter import messagebox
import yaml
from PIL import Image, ImageGrab, ImageTk
import threading
import time
import sys
import subprocess

# Load region from config
with open('config/region.yaml', 'r') as f:
    data = yaml.safe_load(f)
    region = data['region']

print(f"Monitoring region: {region}")
print("Creating visual indicator window...")
print("This red box shows where the app is watching.")
print("Position your poker window inside this box!")
print("\nClick 'Capture & Verify Region' to see what's being captured.")

# Multi-monitor check
if region['left'] > 1728 or region['top'] > 1117:
    print("\n⚠️  Note: Coordinates suggest secondary monitor")
    print("   Overlay window may not appear correctly on secondary displays")
    print("   Main capture (main.py) will work fine on any monitor")

# Check screen recording permissions on macOS
if sys.platform == 'darwin':
    print("\n⚠️  IMPORTANT: macOS Screen Recording Permission Required")
    print("If preview shows blank/wallpaper instead of poker game:")
    print("1. Open System Settings > Privacy & Security > Screen Recording")
    print("2. Enable permission for 'Terminal' or 'Python'")
    print("3. Restart this script\n")

# Create transparent overlay window
overlay = tk.Tk()
overlay.title("LLMPoker Monitor Region - Red Overlay")
overlay.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
overlay.attributes("-alpha", 0.3)  # Semi-transparent
overlay.attributes("-topmost", True)  # Always on top
overlay.configure(bg='red')

# Add text label
label = tk.Label(
    overlay,
    text=f"📹 LLMPoker is watching this area\n{region['width']}x{region['height']} at ({region['left']}, {region['top']})\n\nPosition your poker window HERE",
    bg='red',
    fg='white',
    font=('Arial', 16, 'bold'),
    pady=20
)
label.pack(expand=True)

# Button frame
btn_frame = tk.Frame(overlay, bg='red')
btn_frame.pack(pady=20)

# Preview window reference
preview_window = None
preview_active = False
preview_label = None

def capture_screenshot_once():
    """Capture a single screenshot of the monitored region."""
    import tempfile
    import os

    # Hide overlay window
    overlay.withdraw()
    time.sleep(0.2)  # Wait for window to hide

    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        # Use screencapture with specific region
        cmd = [
            'screencapture',
            '-x',  # No sound
            '-R', f"{region['left']},{region['top']},{region['width']},{region['height']}",
            tmp_path
        ]

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            raise Exception(f"screencapture failed: {result.stderr.decode() if result.stderr else 'Unknown error'}")

        # Load image
        screenshot = Image.open(tmp_path)

        # Cleanup
        os.unlink(tmp_path)

        return screenshot

    except Exception as e:
        print(f"⚠️  Screenshot capture failed: {e}")
        print("\nPlease enable Screen Recording permission:")
        print("System Settings > Privacy & Security > Screen Recording")
        print("Enable permission for 'Terminal' or 'Python'\n")
        raise
    finally:
        # Show overlay again
        overlay.deiconify()

def show_preview():
    """Show single screenshot preview of captured region."""
    global preview_window, preview_label

    if preview_window and preview_window.winfo_exists():
        preview_window.lift()
        return

    # Capture screenshot ONCE
    print("📸 Capturing screenshot...")
    try:
        screenshot = capture_screenshot_once()
    except Exception as e:
        messagebox.showerror(
            "Screenshot Failed",
            f"Could not capture screenshot.\n\n"
            f"Error: {e}\n\n"
            f"Please check Screen Recording permissions in System Settings."
        )
        return

    print("✓ Screenshot captured successfully")

    # Create preview window
    preview_window = tk.Toplevel(overlay)
    preview_window.title("Region Preview - What LLMPoker Sees")
    preview_window.configure(bg='black')

    # Position next to monitored region
    screen_width = overlay.winfo_screenwidth()
    preview_width = 820
    preview_height = 750

    preview_x = region['left'] + region['width'] + 20
    if preview_x + preview_width > screen_width:
        preview_x = max(0, region['left'] - preview_width - 20)

    preview_y = max(0, region['top'])
    preview_window.geometry(f"{preview_width}x{preview_height}+{preview_x}+{preview_y}")

    # Info label
    info = tk.Label(
        preview_window,
        text=f"Preview of monitored region\nRegion: {region['width']}x{region['height']} at ({region['left']}, {region['top']})",
        bg='black',
        fg='white',
        font=('Arial', 12, 'bold'),
        pady=15
    )
    info.pack()

    # Preview label with screenshot
    preview_label = tk.Label(preview_window, bg='black')
    preview_label.pack(padx=10, pady=10)

    # Resize for display
    preview_size = (800, 600)
    screenshot.thumbnail(preview_size, Image.LANCZOS)
    photo = ImageTk.PhotoImage(screenshot)
    preview_label.configure(image=photo)
    preview_label.image = photo  # Keep reference

    # Verification buttons
    verify_frame = tk.Frame(preview_window, bg='black')
    verify_frame.pack(pady=15)

    def verify_and_close():
        """User confirms region is correct."""
        if messagebox.askyesno(
            "Verify Region",
            f"Confirm this is the correct area to monitor?\n\n"
            f"Region: {region['width']}x{region['height']}\n"
            f"Position: ({region['left']}, {region['top']})\n\n"
            f"The screenshot shows what LLMPoker will analyze."
        ):
            print("\n✅ Region verified successfully!")
            print(f"   Monitoring: {region['width']}x{region['height']} at ({region['left']}, {region['top']})")
            print("\nYou can now start the main application:\n")
            print("   python src/main.py\n")
            preview_window.destroy()
            overlay.destroy()

    def retake_screenshot():
        """Retake the screenshot."""
        preview_window.destroy()
        show_preview()

    tk.Button(
        verify_frame,
        text="✅ Looks Good - Verify & Close",
        command=verify_and_close,
        bg='green',
        fg='white',
        font=('Arial', 12, 'bold'),
        padx=20,
        pady=10
    ).pack(side=tk.LEFT, padx=10)

    tk.Button(
        verify_frame,
        text="🔄 Retake Screenshot",
        command=retake_screenshot,
        bg='blue',
        fg='white',
        font=('Arial', 12, 'bold'),
        padx=20,
        pady=10
    ).pack(side=tk.LEFT, padx=10)

    tk.Button(
        verify_frame,
        text="❌ Close Preview",
        command=preview_window.destroy,
        bg='gray',
        fg='white',
        font=('Arial', 12, 'bold'),
        padx=20,
        pady=10
    ).pack(side=tk.LEFT, padx=10)

# Verify button
verify_btn = tk.Button(
    btn_frame,
    text="📸 Capture & Verify Region",
    command=show_preview,
    bg='white',
    fg='blue',
    font=('Arial', 12, 'bold'),
    padx=20,
    pady=10
)
verify_btn.pack(side=tk.LEFT, padx=5)

# Close button
close_btn = tk.Button(
    btn_frame,
    text="Close Without Verifying",
    command=overlay.destroy,
    bg='white',
    fg='red',
    font=('Arial', 12, 'bold'),
    padx=20,
    pady=10
)
close_btn.pack(side=tk.LEFT, padx=5)

overlay.mainloop()
