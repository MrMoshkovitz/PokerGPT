#!/usr/bin/env python
"""
Visual Region Indicator
Shows where the app is monitoring on your screen with a red border.
Includes live preview and verification before closing.
"""

import tkinter as tk
from tkinter import messagebox
import yaml
from PIL import ImageGrab, ImageTk
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
print("\nClick 'Verify & Preview' to see what's being captured.")

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

def stop_preview():
    """Stop the preview update loop."""
    global preview_active
    preview_active = False

def capture_screenshot_macos():
    """Capture screenshot using macOS screencapture command (triggers permission dialog)."""
    import tempfile
    import os
    from PIL import Image

    # Temporarily hide overlay
    overlay.withdraw()
    time.sleep(0.1)

    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        # Use screencapture with specific region
        # Format: screencapture -R x,y,w,h output.png
        cmd = [
            'screencapture',
            '-x',  # No sound
            '-R', f"{region['left']},{region['top']},{region['width']},{region['height']}",
            tmp_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # Load image
        screenshot = Image.open(tmp_path)

        # Cleanup
        os.unlink(tmp_path)

        return screenshot

    finally:
        overlay.deiconify()

def update_preview():
    """Update preview with current screenshot."""
    global preview_active, preview_label, preview_window

    while preview_active:
        try:
            # Use macOS native screencapture on macOS, PIL on other platforms
            if sys.platform == 'darwin':
                screenshot = capture_screenshot_macos()
            else:
                # Temporarily hide overlay to capture what's underneath
                overlay.withdraw()
                time.sleep(0.05)

                screenshot = ImageGrab.grab(
                    bbox=(region['left'], region['top'],
                          region['left'] + region['width'],
                          region['top'] + region['height'])
                )

                overlay.deiconify()

            # Resize for preview (fit to 800x600 max)
            preview_size = (800, 600)
            screenshot.thumbnail(preview_size, ImageTk.Image.LANCZOS)

            # Update preview label
            photo = ImageTk.PhotoImage(screenshot)
            if preview_label and preview_window.winfo_exists():
                preview_label.configure(image=photo)
                preview_label.image = photo  # Keep reference

            time.sleep(0.5)  # Update every 500ms

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Screen recording permission denied!")
            print(f"Error: {e.stderr.decode() if e.stderr else 'Unknown'}")
            print("\nPlease enable Screen Recording permission:")
            print("System Settings > Privacy & Security > Screen Recording")
            overlay.deiconify()
            break
        except Exception as e:
            print(f"Preview update error: {e}")
            overlay.deiconify()
            break

def show_preview():
    """Show live preview of captured region."""
    global preview_window, preview_active, preview_label

    if preview_window and preview_window.winfo_exists():
        preview_window.lift()
        return

    # Create preview window
    preview_window = tk.Toplevel(overlay)
    preview_window.title("Region Preview - What LLMPoker Sees")
    preview_window.configure(bg='black')

    # Position to the right of the monitored region
    preview_x = region['left'] + region['width'] + 20
    preview_y = region['top']
    preview_window.geometry(f"820x700+{preview_x}+{preview_y}")

    # Info label
    info = tk.Label(
        preview_window,
        text=f"Live preview updating every 500ms\nRegion: {region['width']}x{region['height']} at ({region['left']}, {region['top']})",
        bg='black',
        fg='white',
        font=('Arial', 10),
        pady=10
    )
    info.pack()

    # Preview label
    preview_label = tk.Label(preview_window, bg='black')
    preview_label.pack(padx=10, pady=10)

    # Verification buttons
    verify_frame = tk.Frame(preview_window, bg='black')
    verify_frame.pack(pady=10)

    def verify_and_close():
        """User confirms region is correct."""
        stop_preview()
        if messagebox.askyesno(
            "Verify Region",
            f"Confirm this is the correct area to monitor?\n\n"
            f"Region: {region['width']}x{region['height']}\n"
            f"Position: ({region['left']}, {region['top']})\n\n"
            f"Your poker window should be positioned inside the red box."
        ):
            print("\n✅ Region verified successfully!")
            print(f"   Monitoring: {region['width']}x{region['height']} at ({region['left']}, {region['top']})")
            print("\nYou can now start the main application:\n")
            print("   python src/main.py\n")
            preview_window.destroy()
            overlay.destroy()
        else:
            # Keep showing preview
            pass

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
        text="❌ Close Preview",
        command=lambda: (stop_preview(), preview_window.destroy()),
        bg='gray',
        fg='white',
        font=('Arial', 12, 'bold'),
        padx=20,
        pady=10
    ).pack(side=tk.LEFT, padx=10)

    # Start preview updates
    preview_active = True
    preview_thread = threading.Thread(target=update_preview, daemon=True)
    preview_thread.start()

    # Handle window close
    def on_close():
        stop_preview()
        preview_window.destroy()

    preview_window.protocol("WM_DELETE_WINDOW", on_close)

# Verify button
verify_btn = tk.Button(
    btn_frame,
    text="🔍 Verify & Preview",
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
