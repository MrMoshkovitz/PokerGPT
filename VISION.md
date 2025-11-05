# LLMPoker Assistant - Vision

**One-Line Mission**: Real-time poker decision co-pilot that takes full accountability for optimal GTO-grounded recommendations.

---

## What It Is

A desktop application (Mac) that watches your poker game via screen capture, analyzes game state with FastVLM vision AI, grounds decisions in GTO strategy, applies advanced reasoning via Claude Code CLI, and displays optimal actions with transparent confidence scoring in a real-time browser dashboard.

---

## What It Is Not

- ❌ Not an autonomous bot (advisory only, never executes)
- ❌ Not a training tool (focused on live decision support)
- ❌ Not multi-platform initially (Mac-first, technical debt for others)
- ❌ Not tournament-focused (cash games 8-handed Texas Hold'em)
- ❌ Not legally compliant helper (user responsibility for ToS)

---

## Core Value Proposition

**Accountability**: "Losses → blame the tool is correct and intentional"

Unlike generic poker assistants with disclaimers, LLMPoker Assistant stakes its reputation on every recommendation. If you lose following our advice, it's our fault, not yours. This forces us to ensure every recommendation is rigorously validated, deeply reasoned, and transparently explained.

---

## Technical Stack

```
Screen Capture (mss/pyautogui - Mac native)
    ↓
FastVLM-0.5B PyTorch (local vision inference)
    ↓
Game State Extraction + Validation (3-frame temporal consistency)
    ↓
GTO Strategy Cache (in-memory, O(1) lookup)
    ↓
Claude Code CLI with ultrathink (extended reasoning)
    ↓ (fallback: OpenAI API → Gemini CLI)
Browser Dashboard (FastAPI + WebSocket, localhost:8080)
    ↓
Action Recommendation (FOLD/CALL/RAISE + reasoning + confidence)
```

---

## Key Differentiators

1. **Local LLM Execution**: Claude Code CLI, not API latency
2. **Client-Agnostic**: Works with any poker software
3. **GTO-Grounded**: Not pure GPT guessing, statistical foundation
4. **Extended Reasoning**: Ultrathink mode for complex decisions
5. **Full Accountability**: Own every outcome
6. **Persistent Memory**: Player profiling database for exploitative play

---

## Success Metrics

- **Accuracy**: >90% GTO alignment
- **Speed**: <3 second latency 95th percentile
- **Reliability**: <1% crash rate per 100-hand session
- **User Trust**: Confident action-following without second-guessing

---

## Philosophy in Three Words

**Accountable. Focused. Fast.**
