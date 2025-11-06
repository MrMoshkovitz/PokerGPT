#!/usr/bin/env python
"""
Visual Region Indicator
Shows where the app is monitoring on your screen with a red border.
"""

import tkinter as tk
import yaml

# Load region from config
with open('config/region.yaml', 'r') as f:
    data = yaml.safe_load(f)
    region = data['region']

print(f"Monitoring region: {region}")
print("Creating visual indicator window...")
print("This red box shows where the app is watching.")
print("Position your poker window inside this box!")
print("\nPress Ctrl+C in terminal to close.\n")

# Create transparent overlay window
root = tk.Tk()
root.title("LLMPoker Monitor Region")
root.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
root.attributes("-alpha", 0.3)  # Semi-transparent
root.attributes("-topmost", True)  # Always on top
root.configure(bg='red')

# Add text label
label = tk.Label(
    root,
    text=f"📹 LLMPoker is watching this area\n{region['width']}x{region['height']} at ({region['left']}, {region['top']})\n\nPosition your poker window HERE",
    bg='red',
    fg='white',
    font=('Arial', 16, 'bold'),
    pady=20
)
label.pack(expand=True)

# Add close button
close_btn = tk.Button(
    root,
    text="Close",
    command=root.destroy,
    bg='white',
    fg='red',
    font=('Arial', 12, 'bold'),
    padx=20,
    pady=10
)
close_btn.pack(pady=20)

root.mainloop()
