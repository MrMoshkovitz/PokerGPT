# LLMPoker Assistant - Product Requirements Document (PRD)

**Version**: 1.0 MVP
**Platform**: macOS (12.0+)
**Game Type**: Texas Hold'em, 8-handed cash games
**Status**: Phase 5 - Boundary Setting Complete

---

## 1. Product Overview

### 1.1 Problem Statement

Poker players need real-time, optimal decision guidance during gameplay, but existing solutions are either:
- Autonomous bots (violate ToS, risky)
- Slow GTO solvers (post-game analysis only)
- Generic GPT prompting (no statistical grounding, unreliable)

### 1.2 Solution

Desktop application with local vision AI + GTO strategy + advanced LLM reasoning that provides real-time action recommendations with full accountability and transparent confidence scoring.

### 1.3 Target User

Serious cash game poker players (online or home games) on Mac who want optimal decision guidance without running complex GTO solvers mid-hand.

---

## 2. Core Features (MVP)

### 2.1 Screen Capture & Vision

**FR-101**: System shall capture selected poker window/region via native Mac APIs
- User drag-to-select region at startup
- Persist region coordinates across sessions
- Event-driven capture (only process on game state change)
- Frame rate: Check for changes every 100ms, capture on 5%+ pixel diff

**FR-102**: System shall extract game state via FastVLM-0.5B
- Hole cards (2 cards)
- Community cards (0-5 cards: flop/turn/river)
- Pot size (numeric extraction)
- Player stacks (your stack + visible opponent stacks)
- Current action state (who's turn, available actions)

**FR-103**: System shall validate vision confidence
- Per-element confidence scoring (0-100%)
- Aggregate state confidence
- 3-frame temporal consistency check
- Show "UNCERTAIN" if confidence <70%

### 2.2 GTO Strategy Engine

**FR-201**: System shall load GTO data at startup
- Download GTO dataset on first run (~100MB)
- Load into RAM as in-memory cache
- Preflop ranges by position (9 positions)
- Postflop decision buckets (hand strength × board texture × SPR)
- O(1) lookup time (<1ms)

**FR-202**: System shall provide GTO baseline recommendations
- Input: Position, hole cards, board, pot, stacks
- Output: Action (FOLD/CHECK/CALL/BET/RAISE) + sizing (% pot or exact)
- Bucketed strategy (simplified GTO, not solver-exact)

### 2.3 LLM Reasoning Layer

**FR-301**: System shall use Claude Code CLI for decision reasoning
- Execute: `claude -p "--extended-thinking <prompt>"`
- Prompt includes: game state, GTO baseline, hand history (last 5-10 hands), player patterns
- Ultrathink mode for extended reasoning
- 5-second timeout

**FR-302**: System shall implement LLM fallback chain
- Primary: Claude Code CLI
- Fallback 1: OpenAI API (if Claude timeout/error)
- Fallback 2: Gemini CLI (if OpenAI fails)
- Fallback 3: GTO baseline only (if all LLMs fail)

**FR-303**: System shall construct rich context prompts
- Current decision point (state + GTO baseline)
- Recent hand history (last 5-10 hands with outcomes)
- Session statistics (VPIP%, aggression, win rate)
- Player patterns (if tracked)
- Stack dynamics and momentum

### 2.4 Browser Dashboard (Real-time UI)

**FR-401**: System shall serve web UI on localhost:8080
- FastAPI backend with WebSocket
- Single-page HTML/CSS/JS frontend
- Auto-open browser on startup

**FR-402**: System shall display game state in real-time
- Your hole cards (graphical card images)
- Community cards (flop/turn/river)
- Pot size, your stack, position
- Vision confidence meter

**FR-403**: System shall display action recommendations
- Primary action (large, bold): "RAISE TO $450"
- Confidence score: Visual meter (0-100%)
- Reasoning explanation: Collapsible text block
- Alternative actions: Secondary options with confidence

**FR-404**: System shall show system status
- LLM provider in use (Claude/OpenAI/Gemini/GTO-only)
- Latency timer (time from action to recommendation)
- Alert messages (low confidence, fallback used, errors)

**FR-405**: Optional always-on-top floating widget
- Minimal overlay (action + confidence only)
- Can be positioned anywhere on screen
- Toggle on/off from main dashboard

### 2.5 Persistence & Memory

**FR-501**: System shall persist hand history to SQLite
- Every hand: cards, actions, pot, stacks, outcome
- Session metadata: date, duration, win/loss
- Player profiles: VPIP%, PFR%, aggression factor, showdown hands

**FR-502**: System shall use historical data in recommendations
- Include recent hand history in LLM prompt
- Track player patterns for exploitative adjustments
- Session continuity across app restarts

### 2.6 Logging & Auditability

**FR-601**: System shall log every decision
- Timestamp, game state, vision confidence
- GTO baseline, LLM provider, LLM reasoning
- Final recommendation, confidence score
- Latency breakdown (vision/GTO/LLM timings)

**FR-602**: System shall write logs to structured format
- JSON lines format (one JSON object per line)
- Rotating log files (max 100MB per file)
- Retention: Last 30 days

**FR-603**: System shall provide log viewer in UI
- Recent decisions (last 20 hands)
- Filterable by confidence, action type, outcome
- Export to CSV for analysis

---

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-101**: Total latency <3 seconds (95th percentile)
- Vision inference: <1 second
- GTO lookup: <50ms
- LLM reasoning: <2 seconds (with 5s timeout)

**NFR-102**: Memory usage <500MB during gameplay
- FastVLM model: ~500MB loaded
- GTO cache: ~100MB
- Application overhead: <100MB

**NFR-103**: CPU usage <50% on M1/M2 Macs during active gameplay

### 3.2 Reliability

**NFR-201**: Crash rate <1% per 100-hand session

**NFR-202**: Graceful degradation on component failures
- Vision fails → show "UNCERTAIN" state
- LLM fails → fallback chain → GTO-only
- Never silent failure

**NFR-203**: State recovery on app restart
- Resume session from database
- Reload last poker window region
- Reconnect WebSocket

### 3.3 Usability

**NFR-301**: First-time setup <5 minutes
- Download GTO data: <2 minutes
- Select poker window: <1 minute
- Launch dashboard: <10 seconds

**NFR-302**: Zero-configuration window tracking
- Auto-detect window movement/resize
- Persist region coordinates
- Visual feedback on region selection

### 3.4 Compatibility

**NFR-401**: macOS 12.0+ (Monterey or later)

**NFR-402**: Works with any poker client (client-agnostic vision)

**NFR-403**: Claude Code CLI installed and configured

---

## 4. Out of Scope (MVP)

### 4.1 Deferred to Future Versions

- ❌ Tournament support (ICM calculations)
- ❌ Multi-table support
- ❌ Windows/Linux support
- ❌ Omaha/PLO/other variants
- ❌ Hand history import from tracking software
- ❌ Social features (sharing, leaderboards)
- ❌ Training mode / learning features
- ❌ Mobile companion app

### 4.2 Explicitly Not Building

- ❌ Autonomous action execution (advisory only)
- ❌ Legal compliance tools (ToS warnings, site detection)
- ❌ Anti-detection evasion
- ❌ Custom FastVLM training
- ❌ Cloud sync / account system

---

## 5. User Flows

### 5.1 First-Time Setup

1. User launches app
2. System downloads GTO data (progress bar)
3. System prompts: "Select poker window region"
4. User drags to select region
5. System opens browser dashboard at localhost:8080
6. Dashboard shows: "Waiting for game state..."

### 5.2 Active Gameplay

1. Poker game deals cards
2. System detects pixel change (5%+ diff)
3. System captures screenshot
4. FastVLM extracts: hole cards, board, pot, stacks
5. System validates confidence (3-frame consistency)
6. If confidence <70%: Show "UNCERTAIN - Verify manually"
7. If confidence ≥70%:
   a. Lookup GTO baseline (O(1) cache)
   b. Construct LLM prompt (state + GTO + history)
   c. Execute Claude Code CLI with ultrathink
   d. Parse recommendation + reasoning
   e. Send to dashboard via WebSocket
8. Dashboard displays: "⚡ RAISE TO $450 [87%]"
9. User reads reasoning, makes decision
10. System logs decision (state + recommendation + outcome)

### 5.3 Low Confidence State

1. Vision extracts cards with 65% confidence
2. Dashboard shows:
   ```
   ⚠️ UNCERTAIN GAME STATE
   Vision Confidence: 65% (threshold: 70%)

   Detected: A♥ K♦ vs Q♥ J♠ 10♣
   Action: VERIFY MANUALLY
   ```
3. User confirms cards manually
4. (Future: Manual override input)

### 5.4 LLM Fallback

1. Claude Code CLI times out after 5 seconds
2. System logs: "Claude timeout, falling back to OpenAI"
3. OpenAI returns recommendation in 1.2s
4. Dashboard shows: "⚡ RAISE TO $450 [82%]"
5. UI footer shows: "[Fallback: OpenAI]"

---

## 6. Technical Architecture

### 6.1 System Components

```
┌─────────────────────────────────────────────────────┐
│  macOS Desktop Application (Python 3.10+)          │
├─────────────────────────────────────────────────────┤
│  1. Screen Capture Module (mss)                    │
│     - Event-driven capture (100ms diff checks)      │
│     - Window region tracking                        │
├─────────────────────────────────────────────────────┤
│  2. Vision Module (FastVLM-0.5B PyTorch)           │
│     - Card recognition                              │
│     - Pot/stack extraction                          │
│     - Confidence scoring                            │
├─────────────────────────────────────────────────────┤
│  3. State Manager                                   │
│     - 3-frame temporal buffer                       │
│     - Consistency validation                        │
│     - Noise filtering                               │
├─────────────────────────────────────────────────────┤
│  4. GTO Engine (In-Memory Cache)                   │
│     - Preflop ranges (10MB)                         │
│     - Postflop buckets (50MB)                       │
│     - O(1) lookup                                   │
├─────────────────────────────────────────────────────┤
│  5. LLM Orchestrator                                │
│     - Claude Code CLI (primary)                     │
│     - OpenAI API (fallback 1)                       │
│     - Gemini CLI (fallback 2)                       │
│     - Prompt construction + parsing                 │
├─────────────────────────────────────────────────────┤
│  6. Persistence Layer (SQLite)                      │
│     - Hand history                                  │
│     - Player profiles                               │
│     - Session state                                 │
├─────────────────────────────────────────────────────┤
│  7. Web Server (FastAPI + WebSocket)               │
│     - REST endpoints (status, config)               │
│     - WebSocket (real-time updates)                 │
│     - Static files (HTML/CSS/JS)                    │
├─────────────────────────────────────────────────────┤
│  8. Logging & Monitoring                            │
│     - Structured JSON logging                       │
│     - Performance metrics                           │
│     - Error tracking                                │
└─────────────────────────────────────────────────────┘
```

### 6.2 Data Flow

```
Screen → Diff Check → Capture → FastVLM → State Validation
                                             ↓
                                    Confidence Check
                                    /              \
                          <70%: UNCERTAIN      ≥70%: Continue
                                                    ↓
                                              GTO Lookup
                                                    ↓
                                         Prompt Construction
                                                    ↓
                                          Claude Code CLI
                                          (5s timeout)
                                          /            \
                                   Success          Timeout/Error
                                      ↓                  ↓
                                   Parse           Fallback LLM
                                      ↓                  ↓
                               Recommendation ← ← ← ← ← ←
                                      ↓
                              WebSocket → Dashboard
                                      ↓
                                   Log to DB
```

---

## 7. Acceptance Criteria

### 7.1 MVP Launch Checklist

- [ ] Capture poker window region on Mac
- [ ] Extract game state with FastVLM (cards, pot, stacks)
- [ ] Load GTO data into memory (<2s startup)
- [ ] Execute Claude Code CLI with ultrathink
- [ ] Fallback to OpenAI/Gemini on failure
- [ ] Display recommendations in browser dashboard
- [ ] Show confidence scores and reasoning
- [ ] Log all decisions to SQLite
- [ ] <3 second latency 95th percentile
- [ ] <1% crash rate over 100 hands
- [ ] Works with at least 3 different poker clients (PokerStars, GGPoker, home game software)

### 7.2 Quality Gates

**Gate 1: Vision Accuracy**
- >85% card recognition accuracy across 3 poker clients
- <5% false positives (detecting cards when none exist)

**Gate 2: GTO Alignment**
- >90% agreement with GTO+ solver on standard scenarios
- <10% absolute error on bet sizing

**Gate 3: Performance**
- <3s latency for 95% of decisions
- <500MB memory usage
- <50% CPU on M1/M2

**Gate 4: Reliability**
- Zero crashes in 100-hand test session
- Graceful degradation on all failure modes

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| FastVLM accuracy too low | HIGH | Multi-client testing, confidence thresholds, manual verification UI |
| Claude CLI latency spikes | MEDIUM | Timeout + fallback chain (OpenAI/Gemini) |
| GTO data licensing issues | MEDIUM | Use open-source ranges (GTOBase), cite sources |
| User blames tool for losses | HIGH | Comprehensive logging, post-session analysis, improve recommendations |
| Mac API changes break capture | LOW | Use stable mss library, version pin |

---

## 9. Success Metrics (Post-Launch)

### 9.1 Technical Metrics
- Average latency: <2 seconds
- Vision accuracy: >90%
- LLM timeout rate: <5%
- Crash rate: <0.5% per 100 hands

### 9.2 User Metrics
- Recommendation follow rate: >80% (users trust the tool)
- Session length: >50 hands average (users stay engaged)
- Win rate improvement: +5% vs baseline (users win more)

### 9.3 Quality Metrics
- GTO alignment: >92%
- User-reported accuracy issues: <10 per 1000 hands
- False positive rate: <2%

---

**Version History**:
- v1.0 (2025-11-05): Initial MVP PRD - Phase 5 Complete
