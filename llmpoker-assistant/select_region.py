#!/usr/bin/env python
"""
Interactive Region Selector

Drag to select the poker window region. Press ENTER to save.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from capture.region_selector import RegionSelector, save_region

print("="*60)
print("INTERACTIVE REGION SELECTOR")
print("="*60)
print()
print("Instructions:")
print("1. A transparent overlay will cover your screen")
print("2. DRAG your mouse to select the poker window area")
print("3. Press ENTER to confirm and save")
print("4. Press ESC to cancel")
print()
print("Launching selector...")
print("="*60)

try:
    selector = RegionSelector()
    region = selector.select_region()

    print()
    print("="*60)
    print("REGION SELECTED")
    print("="*60)
    print(f"Position: ({region['left']}, {region['top']})")
    print(f"Size: {region['width']} x {region['height']}")
    print()

    # Save to config
    save_region(region, "config/region.yaml")

    print("✅ Region saved to config/region.yaml")
    print()
    print("Next steps:")
    print("1. Run: python show_region.py  (to verify)")
    print("2. Run: python src/main.py     (to start app)")
    print("="*60)

except ValueError as e:
    print()
    print("❌ Region selection cancelled")
    print("No changes made to config/region.yaml")
    sys.exit(1)
except Exception as e:
    print()
    print(f"❌ Error: {e}")
    sys.exit(1)
