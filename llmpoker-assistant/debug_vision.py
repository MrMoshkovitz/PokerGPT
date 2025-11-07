#!/usr/bin/env python
"""
Debug Vision Extraction

Captures screenshot and tests FastVLM extraction with full debug logging.
Shows RAW model output to diagnose JSON parsing issues.
"""

import logging
import sys
from pathlib import Path
import subprocess
import tempfile
import os

# Setup debug logging BEFORE any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vision.fastvlm_inference import FastVLMInference
from PIL import Image
import yaml

# Load region config
with open('config/region.yaml', 'r') as f:
    region = yaml.safe_load(f)['region']

print(f"Monitoring region: {region}")
print("\n" + "="*60)
print("STEP 1: Capturing screenshot from monitored region")
print("="*60)

# Use macOS screencapture for reliability
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
    tmp_path = tmp.name

cmd = [
    'screencapture',
    '-x',
    '-R', f"{region['left']},{region['top']},{region['width']},{region['height']}",
    tmp_path
]

subprocess.run(cmd, check=True, capture_output=True)
screenshot = Image.open(tmp_path)

# Save for manual inspection
screenshot.save('debug_screenshot.png')
print(f"✓ Screenshot saved to: debug_screenshot.png")
print(f"  Size: {screenshot.size}")
os.unlink(tmp_path)

print("\n" + "="*60)
print("STEP 2: Initializing FastVLM model")
print("="*60)
model = FastVLMInference('data/models/fastvlm-0.5b', device='cpu')

print("\n" + "="*60)
print("STEP 3: Extracting game state (watch for DEBUG: raw response)")
print("="*60)
result = model.extract_game_state(screenshot)

print("\n" + "="*60)
print("STEP 4: EXTRACTION RESULT")
print("="*60)
import json
print(json.dumps(result, indent=2))

print("\n" + "="*60)
print("ANALYSIS")
print("="*60)
print(f"Hole cards detected: {result.get('hole_cards', [])}")
print(f"Board cards detected: {result.get('board', [])}")
print(f"Pot: ${result.get('pot', 0)}")
print(f"Stack: ${result.get('your_stack', 0)}")
print(f"Position: {result.get('position', 'UNKNOWN')}")
print(f"Action on you: {result.get('action_on_you', False)}")
print(f"Confidence scores: {result.get('confidence', {})}")
print("="*60)
