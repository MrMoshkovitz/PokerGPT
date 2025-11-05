# LLMPoker Assistant

Real-time poker decision co-pilot that takes full accountability for optimal GTO-grounded recommendations.

## Overview

LLMPoker Assistant watches your poker game via screen capture, analyzes game state with FastVLM vision AI, grounds decisions in GTO strategy, applies advanced reasoning via Claude Code CLI, and displays optimal actions with transparent confidence scoring in a real-time browser dashboard.

**Philosophy**: "Losses → blame the tool is correct and intentional" - We own every recommendation.

## Features

- 🎯 **Real-time Analysis**: <3 second latency from action to recommendation
- 🧠 **GTO-Grounded**: Statistical foundation + LLM reasoning
- 👁️ **Client-Agnostic**: Works with any poker software
- 🔒 **Accountable**: Full confidence scoring + reasoning transparency
- 💾 **Persistent Memory**: Player profiling and session tracking
- ⚡ **Local Execution**: Claude Code CLI, no API latency

## Quick Start

```bash
# 1. Clone and enter directory
cd llmpoker-assistant

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Mac/Linux

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Download models and data
python scripts/download_fastvlm.py
python scripts/download_gto_data.py

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 6. Run application
python src/main.py
```

## System Requirements

- **OS**: macOS 12.0+ (Monterey or later)
- **CPU**: M1/M2 recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Python**: 3.10 or 3.11
- **Claude Code CLI**: Required

## Architecture

```
Screen Capture → FastVLM Vision → GTO Engine → LLM Reasoning → Browser Dashboard
```

See [ARCHITECTURE.md](../../ARCHITECTURE.md) for detailed system design.

## Implementation Status

### ✅ Completed
- Project structure
- Configuration setup
- Documentation

### 🚧 In Progress
- Screen capture module
- Vision inference
- GTO engine

### 📋 Planned
- LLM integration
- Web server & UI
- Testing & polish

## Development

```bash
# Run tests
pytest tests/

# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Documentation

- **[VISION.md](../../VISION.md)** - Project mission
- **[ARCHITECTURE.md](../../ARCHITECTURE.md)** - System overview
- **[PRD.md](../../PRD.md)** - Product requirements
- **[IMPLEMENTATION.md](../../IMPLEMENTATION.md)** - Technical specification
- **[IMPLEMENTATION_INSTRUCTIONS.md](../../IMPLEMENTATION_INSTRUCTIONS.md)** - Build guide
- **[PHILOSOPHY_PHASE4.md](../../PHILOSOPHY_PHASE4.md)** - Core principles

## License

MIT License - See LICENSE file

## Disclaimer

This tool is for educational and personal use only. Using real-time assistance tools may violate online poker site Terms of Service. Use responsibly.

---

**Status**: Week 1 - Core Infrastructure (In Progress)
**Version**: 0.1.0-alpha
