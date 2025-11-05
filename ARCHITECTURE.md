# LLMPoker Assistant - Simplified Architecture

**Version**: 1.0
**Purpose**: High-level system overview for quick understanding
**Audience**: Developers, stakeholders, future maintainers

---

## System Overview (One Sentence)

Real-time poker decision co-pilot that captures your screen, analyzes game state with vision AI, grounds decisions in GTO strategy, applies advanced LLM reasoning, and displays optimal actions in a live browser dashboard.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER'S POKER GAME                       │
│              (Any poker client - PokerStars, etc.)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    [Screen Capture]
                    (100ms diff check)
                    Only capture on 5%+ change
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    VISION MODULE                            │
│                                                             │
│  FastVLM-0.5B PyTorch                                      │
│  Extract: Hole cards, board, pot, stacks, position        │
│  Output: Game state + confidence scores (0-100%)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
                [Confidence Validation]
                3-frame temporal buffer
                Consistency check
                            ↓
                    <70% confidence?
                    /              \
                 YES               NO
                  ↓                 ↓
         [Show "UNCERTAIN"]   [Continue Pipeline]
                                    ↓
┌─────────────────────────────────────────────────────────────┐
│                    GTO ENGINE                               │
│                                                             │
│  In-Memory Cache (~100MB RAM)                              │
│  Preflop ranges by position                                │
│  Postflop buckets (hand strength × board texture × SPR)    │
│  Output: Baseline action + sizing (GTO recommendation)     │
│  Lookup time: <1ms (O(1) hash table)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  LLM REASONING LAYER                        │
│                                                             │
│  Prompt Builder:                                           │
│  ├─ Current game state                                     │
│  ├─ GTO baseline recommendation                            │
│  ├─ Hand history (last 5-10 hands)                         │
│  ├─ Session statistics (VPIP%, win rate)                   │
│  └─ Player patterns (if tracked)                           │
│                                                             │
│  Execution Chain (with 5s timeout each):                   │
│  1. Claude Code CLI (--extended-thinking)                  │
│     └─ Timeout/Error → 2. OpenAI API                       │
│                         └─ Timeout/Error → 3. Gemini CLI   │
│                                             └─ Error → GTO-only
│                                                             │
│  Output: Action + amount + confidence + reasoning          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  PERSISTENCE LAYER                          │
│                                                             │
│  SQLite Database:                                          │
│  ├─ hands: Every decision + outcome                        │
│  ├─ player_profiles: Opponent tendencies                   │
│  └─ sessions: Win/loss tracking                            │
│                                                             │
│  Logging:                                                  │
│  └─ logs/decisions.jsonl: Full audit trail                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               WEB SERVER (FastAPI)                          │
│                                                             │
│  WebSocket (ws://localhost:8080/ws)                        │
│  Sends real-time updates:                                  │
│  ├─ game_state_update                                      │
│  ├─ recommendation                                         │
│  └─ system_alert                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            BROWSER DASHBOARD (http://localhost:8080)        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  GAME STATE                                           │ │
│  │  You: A♥ K♦  |  Board: Q♥ J♠ 10♣                     │ │
│  │  Pot: $450   |  Stack: $2500 (BTN)                   │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │  ⚡ RAISE TO $900                                     │ │
│  │  Confidence: ████████░░ 87%                          │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │  Reasoning (click to expand):                        │ │
│  │  Strong draw (OESD+FD), position advantage...        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  WebSocket client receives updates every ~2-3 seconds      │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow (Step by Step)

### 1. Screen Monitoring (Continuous Loop)
```
Every 100ms:
  - Quick pixel diff check
  - If >5% change detected → Capture full screenshot
  - Else → Skip processing (save CPU)
```

### 2. Vision Extraction
```
Screenshot (PIL Image)
  ↓
FastVLM-0.5B model inference
  ↓
JSON output:
{
  "hole_cards": ["Ah", "Kd"],
  "board": ["Qh", "Js", "10c"],
  "pot": 450,
  "your_stack": 2500,
  "position": "BTN",
  "confidence": {
    "hole_cards": 0.92,
    "board": 0.88,
    "pot": 0.85,
    "stacks": 0.90
  }
}
```

### 3. Confidence Validation
```
State buffer: [frame_t-2, frame_t-1, frame_t]
  ↓
Check temporal consistency:
  - Do hole cards match across frames?
  - Does board progress logically (flop → turn → river)?
  - Does pot only increase (never decrease)?
  ↓
Aggregate confidence = avg(all element confidences) × consistency_score
  ↓
If aggregate < 70%:
  → Show "UNCERTAIN - Verify manually"
  → STOP (don't recommend)
Else:
  → Continue to GTO
```

### 4. GTO Baseline Lookup
```
Input: position="BTN", hole_cards=["Ah","Kd"], board=["Qh","Js","10c"], pot=450, stack=2500

Preflop (no board):
  lookup: gto_cache['preflop_ranges'][position][normalize_hand(hole_cards)]

Postflop (board exists):
  hand_strength = calculate_hand_strength(hole_cards, board)  # e.g., "STRONG"
  board_texture = classify_board(board)                       # e.g., "WET"
  spr = stack / pot                                           # e.g., 5.5
  lookup: gto_cache['postflop_buckets'][(hand_strength, board_texture, bucket_spr(5.5))]

Output:
{
  "action": "RAISE",
  "sizing": 337.5,  # 75% pot
  "confidence": 0.85,
  "range": "top 15%"
}
```

### 5. LLM Reasoning
```
Prompt = """
You are a professional poker advisor.

Current Situation:
- Your Hand: Ah Kd
- Board: Qh Js 10c
- Pot: $450
- Your Stack: $2500
- Position: BTN

GTO Baseline: RAISE to $337.50 (75% pot)

Recent Hand History:
- Hand #42: AsKs → RAISE → Won $320
- Hand #43: 7h6h → FOLD preflop
...

Session Statistics:
- Hands: 45
- VPIP: 22%
- Win Rate: $45/hr

Task: Provide optimal recommendation in JSON.
"""

Execute:
  try:
    subprocess.run(["claude", "-p", "--extended-thinking {prompt}"], timeout=5s)
  except TimeoutExpired:
    fallback_to_openai()

Parse response:
{
  "action": "RAISE",
  "amount": 900,
  "confidence": 0.87,
  "reasoning": "Strong draw (OESD + flush draw). GTO suggests 75% pot, but we can size up to $900 (2x pot) for better fold equity given position advantage and single opponent.",
  "alternatives": [
    {"action": "CALL", "confidence": 0.45},
    {"action": "FOLD", "confidence": 0.05}
  ]
}
```

### 6. Send to Dashboard
```
WebSocket message:
{
  "type": "recommendation",
  "action": "RAISE to $900",
  "confidence": 0.87,
  "reasoning": "Strong draw (OESD+FD)...",
  "alternatives": [...],
  "gto_baseline": "RAISE to $337.50",
  "llm_provider": "claude_cli"
}

JavaScript client receives → Updates UI in real-time
```

### 7. Log Decision
```
SQLite INSERT:
hands (
  session_id, timestamp, position, hole_cards, board, pot, stack,
  gto_action, gto_sizing, llm_action, llm_amount, llm_confidence,
  llm_reasoning, llm_provider, vision_confidence
)

JSON log (logs/decisions.jsonl):
{"timestamp": 1699200000, "game_state": {...}, "recommendation": {...}, "latency_ms": 2340}
```

---

## Component Responsibilities

### 1. Screen Capture Module
**Job**: Monitor poker window, detect changes, capture screenshots
**Tech**: `mss` library (cross-platform screen capture)
**Performance**: 100ms check interval, event-driven (80-90% CPU savings)

### 2. Vision Module
**Job**: Extract game state from screenshots
**Tech**: FastVLM-0.5B PyTorch model (~500MB)
**Performance**: <1 second inference on M1/M2 Mac

### 3. State Manager
**Job**: Validate vision confidence, filter noise
**Tech**: 3-frame temporal buffer, consistency checker
**Performance**: <10ms validation

### 4. GTO Engine
**Job**: Provide baseline strategy recommendations
**Tech**: In-memory hash tables (~100MB RAM)
**Performance**: <1ms O(1) lookups

### 5. LLM Orchestrator
**Job**: Advanced reasoning, contextual adjustments
**Tech**: Claude Code CLI (primary), OpenAI/Gemini (fallbacks)
**Performance**: <2 seconds with 5s timeout

### 6. Persistence Layer
**Job**: Store hand history, track player patterns
**Tech**: SQLite + structured JSON logging
**Performance**: Async writes, no blocking

### 7. Web Server
**Job**: Serve dashboard, push real-time updates
**Tech**: FastAPI + WebSocket
**Performance**: <10ms message delivery

### 8. Browser Dashboard
**Job**: Display recommendations to user
**Tech**: Vanilla HTML/CSS/JS (no framework bloat)
**Performance**: Real-time WebSocket client

---

## Technology Stack Summary

| Layer | Technology | Why This Choice |
|-------|-----------|-----------------|
| **Language** | Python 3.10+ | ML ecosystem, rapid development |
| **Vision** | FastVLM-0.5B PyTorch | Fastest VLM, client-agnostic |
| **Screen** | mss | Cross-platform, native APIs |
| **GTO Data** | Pickle (in-memory) | Instant O(1) lookups |
| **LLM** | Claude Code CLI | Local execution, ultrathink |
| **Fallback** | OpenAI API, Gemini CLI | Resilience chain |
| **Server** | FastAPI | Modern async Python |
| **WebSocket** | websockets | Real-time bidirectional |
| **Database** | SQLite | Zero-config, reliable |
| **Frontend** | Vanilla JS | No build step, fast |
| **Logging** | JSON Lines | Structured, parseable |

---

## Performance Characteristics

### Latency Breakdown (Target <3s Total)

| Stage | Time Budget | Actual Target |
|-------|-------------|---------------|
| Diff check | 100ms interval | N/A (background) |
| Screen capture | Variable | ~50ms |
| FastVLM inference | <1000ms | ~800ms |
| Confidence validation | <50ms | ~10ms |
| GTO lookup | <50ms | <1ms |
| LLM reasoning | <2000ms | ~1500ms |
| WebSocket send | <50ms | ~10ms |
| **TOTAL** | **<3000ms** | **~2370ms** |

### Resource Usage (Target <500MB RAM, <50% CPU)

| Component | Memory | CPU (Active) |
|-----------|--------|-------------|
| FastVLM model | ~500MB | 30-40% (inference) |
| GTO cache | ~100MB | <1% (lookup) |
| Application | ~50MB | 5-10% |
| Browser | ~100MB | <5% |
| **TOTAL** | **~750MB** | **40-55%** |

**Note**: CPU is only high during FastVLM inference (~1s). Rest of time <10%.

---

## Failure Modes & Resilience

### 1. Vision Fails (Low Confidence)
```
FastVLM extracts cards with 65% confidence
  ↓
Confidence validator: 65% < 70% threshold
  ↓
Dashboard shows: "⚠️ UNCERTAIN GAME STATE - Verify manually"
  ↓
No recommendation shown (better silent than wrong)
```

### 2. Claude CLI Timeout
```
Claude CLI takes >5 seconds
  ↓
Timeout exception caught
  ↓
Fallback to OpenAI API
  ↓
OpenAI returns in 1.2s
  ↓
Dashboard shows: "[Fallback: OpenAI]"
```

### 3. All LLMs Fail
```
Claude → Timeout
OpenAI → Error
Gemini → Error
  ↓
Return GTO baseline only
  ↓
Dashboard shows: "GTO-ONLY MODE - LLM reasoning unavailable"
  ↓
User still gets valid recommendation (GTO is good enough)
```

### 4. Screen Capture Fails
```
Poker window closed/minimized
  ↓
Screen capture returns error
  ↓
Dashboard shows: "Waiting for game state..."
  ↓
Resume when window reappears
```

### 5. Database Write Fails
```
SQLite write error (disk full, permission issue)
  ↓
Log to stderr
  ↓
Continue operation (don't block recommendations)
  ↓
Fallback to file-only logging
```

---

## Key Design Principles (From Philosophy)

### 1. Radical Accountability
- No disclaimers, own every recommendation
- <70% confidence → Don't show recommendation
- Comprehensive logging for post-session improvement

### 2. Performance as Feature
- <3s latency non-negotiable
- Event-driven capture (only process changes)
- In-memory GTO (instant lookups)

### 3. Resilient by Design
- Multi-layer fallback chain
- Graceful degradation, never crash
- Temporal consistency checks

### 4. Transparent Reasoning
- Always show confidence + reasoning
- Extended thinking (ultrathink) mode
- Full audit trail in logs

### 5. Ruthless Focus
- Texas Hold'em only
- Cash games only (MVP)
- Mac only (MVP)
- Single table only (MVP)

---

## Security & Privacy

### Data Storage
- **Local only**: All data stays on user's machine
- **No cloud sync**: SQLite database is local
- **API calls**: Only to OpenAI/Gemini (if fallback triggered)

### API Keys
- Stored in `.env` file (not committed to git)
- OpenAI API key (for fallback)
- Gemini API key (for fallback)

### Screen Capture
- User explicitly selects region at startup
- No persistent screen recording
- Only captures selected poker window

---

## Deployment Model

### Single User, Single Machine
```
Mac (user's laptop)
├─ Python app (background process)
├─ FastVLM model (loaded in RAM)
├─ GTO data (loaded in RAM)
├─ SQLite database (local disk)
├─ Web server (localhost:8080)
└─ Browser (auto-opens dashboard)
```

### No Server Infrastructure Required
- Runs entirely locally
- No deployment complexity
- No scaling concerns (single user)

---

## Future Expansion (Technical Debt)

### Phase 2: Cross-Platform
- Windows: win32gui for screen capture
- Linux: X11/Wayland APIs

### Phase 3: Tournament Support
- ICM calculations
- Bubble factor adjustments
- Tournament stage detection

### Phase 4: Multi-Table
- Multiple capture regions
- Parallel processing
- Tabbed dashboard

### Phase 5: Advanced Features
- HUD overlay (transparent window)
- Hand history export (PT4 format)
- Custom FastVLM fine-tuning

---

## Summary: How It All Fits Together

1. **User plays poker** (any client)
2. **App monitors screen** (event-driven, only on changes)
3. **FastVLM extracts state** (cards, pot, stacks)
4. **Confidence check** (<70% → UNCERTAIN, ≥70% → continue)
5. **GTO lookup** (baseline strategy, instant)
6. **Claude reasons** (context + GTO → optimal action)
7. **Dashboard displays** (action + confidence + reasoning)
8. **User decides** (follows recommendation or not)
9. **System logs** (full audit trail for improvement)

**Result**: Real-time, accountable, optimal poker decisions.

---

**Version**: 1.0
**Status**: Architecture finalized, ready for implementation
