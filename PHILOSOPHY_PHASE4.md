# LLMPoker Assistant - Phase 4: Philosophical Grounding

**Project**: LLMPoker Assistant
**Methodology**: Grounded Progressive Architecture (GPA)
**Phase**: 4 - Philosophical Grounding
**Date**: 2025-11-05

---

## Core Philosophy: "The Buck Stops Here"

> "Recommendations must be optimal. Losses → blame the tool is correct and intentional."

This tool takes **full responsibility** for every recommendation it makes. We are not building an experimental toy or a "learning aid with disclaimers." We are building a **trusted co-pilot** that stakes its reputation on decision quality.

---

## Guiding Principles

### 1. Radical Accountability

**Principle**: Own every outcome.

**Implications**:
- Recommendations must be rigorously validated against GTO baselines
- Extended reasoning (ultrathink mode) to ensure deep analysis
- Never show a recommendation if confidence is insufficient
- Logging everything for post-session audit and improvement
- No "trust me bro" suggestions - every action must be defensible

**Decision Filter**: Would I bet my own money on this recommendation?

---

### 2. Pragmatic Perfectionism

**Principle**: Best possible with available tools, zero compromises on accuracy.

**Implications**:
- FastVLM as-is (no custom training) but robust error handling
- Client-agnostic vision (works with any poker UI, not just PokerStars)
- Dynamic noise filtering (ignore popups/animations, focus on game state)
- Multiple LLM backends (Claude Code CLI → OpenAI → Gemini) for resilience
- In-memory GTO data (100MB RAM for instant lookups)

**Decision Filter**: Is this the highest quality achievable without over-engineering?

---

### 3. Ruthless Focus

**Principle**: Ship a focused tool that excels at one thing.

**Implications**:
- **IN SCOPE**: 8-handed Texas Hold'em cash games, Mac, single table
- **OUT OF SCOPE**: Tournaments, multi-table, learning features, legal compliance, cross-platform (initially)
- Cut features aggressively if they distract from core mission
- Defer nice-to-haves to technical debt backlog
- Performance > features (fast recommendations trump fancy UI)

**Decision Filter**: Does this directly serve real-time poker decision-making?

---

### 4. Performance as a Feature

**Principle**: Speed is correctness. Late recommendations are wrong recommendations.

**Implications**:
- Event-driven screen capture (only process when game state changes)
- O(1) GTO lookups via in-memory cache
- Local LLM execution (Claude Code CLI, not API latency)
- Aggressive timeout handling (fallback if LLM takes >5 seconds)
- Optimized for M1/M2 Macs (Metal acceleration for FastVLM)

**Decision Filter**: Will this add latency to the critical path?

---

### 5. Transparent Reasoning

**Principle**: Users must understand WHY, not just WHAT.

**Implications**:
- Every recommendation includes reasoning explanation
- Confidence scores visible (not hidden in logs)
- Extended thinking mode (ultrathink) for complex spots
- Comprehensive logging (vision → GTO → LLM → action)
- Game history context included in prompt (last 5-10 hands)

**Decision Filter**: Can the user audit this decision later?

---

### 6. Resilient by Design

**Principle**: Graceful degradation, never crash mid-hand.

**Implications**:
- Multiple LLM backends (primary + 2 fallbacks)
- Vision confidence thresholds (show "UNCERTAIN" vs bad recommendations)
- State validation (does current frame match last 3 frames?)
- Noise filtering (ignore transient UI elements)
- Retry logic with exponential backoff

**Decision Filter**: What happens when this component fails?

---

### 7. Memory is Strategy

**Principle**: Persistent player profiling and session continuity.

**Implications**:
- SQLite database for hand history and player patterns
- Session state persists across restarts
- Player tendencies tracked (VPIP%, aggression, showdown hands)
- Game history included in LLM context
- Stack dynamics and momentum tracked

**Decision Filter**: Does this information improve future decisions?

---

## Architectural Decisions from Philosophy

### Decision 1: Local LLM Execution (Claude Code CLI)

**Philosophical Alignment**: Performance as a Feature + Resilient by Design

**Architecture**:
```python
def get_llm_recommendation(game_state, gto_baseline, context):
    # Try Claude Code CLI with ultrathink
    try:
        result = subprocess.run(
            ["claude", "-p", f"--extended-thinking {construct_prompt(game_state, gto_baseline, context)}"],
            timeout=5,
            capture_output=True
        )
        return parse_claude_response(result.stdout)
    except TimeoutExpired:
        logger.warning("Claude timeout, falling back to OpenAI")
        return fallback_to_openai(game_state, gto_baseline, context)
```

**Rationale**: Local execution eliminates API latency, ultrathink ensures deep reasoning, fallbacks ensure reliability.

---

### Decision 2: Client-Agnostic Vision with FastVLM

**Philosophical Alignment**: Pragmatic Perfectionism + Ruthless Focus

**Architecture**:
- Use FastVLM-0.5B (smallest, fastest variant)
- No poker client-specific logic (no pixel coordinate hardcoding)
- Vision prompt: "Identify: hole cards, community cards, pot size, player stacks, current action"
- Confidence scoring on every extraction
- Temporal consistency check (current frame vs last 3 frames)

**Rationale**: Works with any poker software without configuration, good enough accuracy without custom training.

---

### Decision 3: In-Memory GTO Cache

**Philosophical Alignment**: Performance as a Feature + Pragmatic Perfectionism

**Architecture**:
```python
# Startup: Load GTO data into RAM
gto_cache = {
    'preflop_ranges': load_pickle('gto_preflop.pkl'),  # ~10MB
    'postflop_buckets': load_pickle('gto_postflop.pkl'),  # ~50MB
    'tournament_adjustments': load_pickle('gto_tournament.pkl')  # ~20MB
}

# Runtime: O(1) lookup
def get_gto_action(position, hand, board, pot, stack):
    return gto_cache['postflop_buckets'][hash(position, hand, board, pot, stack)]
```

**Rationale**: 100MB RAM for instant lookups is trivial, eliminates disk I/O bottleneck.

---

### Decision 4: Comprehensive Logging Pipeline

**Philosophical Alignment**: Transparent Reasoning + Radical Accountability

**Architecture**:
```python
# Log every decision with full context
logger.info({
    'timestamp': time.time(),
    'game_state': game_state,
    'vision_confidence': vision_confidence,
    'gto_baseline': gto_action,
    'llm_provider': 'claude_cli',
    'llm_reasoning': claude_reasoning,
    'final_recommendation': action,
    'confidence': confidence_score,
    'session_id': session_id,
    'hand_number': hand_number
})
```

**Rationale**: Full audit trail for debugging and post-session analysis.

---

### Decision 5: Persistent Player Database

**Philosophical Alignment**: Memory is Strategy + Radical Accountability

**Architecture**:
```sql
CREATE TABLE hands (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp DATETIME,
    position TEXT,
    hole_cards TEXT,
    board TEXT,
    action_taken TEXT,
    pot_size REAL,
    stack_size REAL,
    outcome TEXT  -- won/lost/folded
);

CREATE TABLE player_profiles (
    player_id TEXT PRIMARY KEY,
    hands_played INTEGER,
    vpip_percent REAL,
    pfr_percent REAL,
    aggression_factor REAL,
    showdown_hands TEXT  -- JSON array
);
```

**Rationale**: Historical data improves future recommendations, enables exploitative play.

---

## Trade-offs and Non-Negotiables

### ✅ Non-Negotiables (Never Compromise)

1. **Recommendation Quality**: Every action must be defensible
2. **Speed**: <3 second total latency from action to recommendation
3. **Transparency**: Always show reasoning + confidence
4. **Logging**: Every decision must be auditable
5. **Resilience**: Graceful degradation, never crash

### ⚖️ Acceptable Trade-offs

1. **Cross-Platform Support**: Mac-first, defer Windows/Linux
2. **Tournament Support**: Cash games only initially
3. **Multi-Table**: Single table focus
4. **UI Polish**: Functional > beautiful (browser UI good enough)
5. **Custom Models**: Use pre-trained FastVLM as-is

### ❌ Explicitly Out of Scope

1. **Legal Compliance**: User responsibility (no ToS warnings built-in)
2. **Learning Features**: Not a training tool
3. **Social Features**: No multiplayer, sharing, leaderboards
4. **Autonomous Play**: Advisory only, never executes actions
5. **Omaha/PLO/Short Deck**: Texas Hold'em only

---

## Philosophy in Action: Example Scenarios

### Scenario 1: Low Vision Confidence

**Situation**: FastVLM reads hole cards as "Ah Kd" with 65% confidence

**Philosophical Response** (Radical Accountability + Transparent Reasoning):
```
UI Display:
⚠️ UNCERTAIN GAME STATE
Vision Confidence: 65% (threshold: 70%)

Detected: A♥ K♦ vs Q♥ J♠ 10♣
Action: VERIFY MANUALLY

Reasoning: Card recognition below confidence threshold.
Please confirm your hole cards before acting.
```

**Rationale**: Better to ask for confirmation than give bad advice.

---

### Scenario 2: Claude CLI Timeout

**Situation**: Claude Code CLI takes >5 seconds to respond

**Philosophical Response** (Performance as a Feature + Resilient by Design):
```
[Internal Log]
Claude timeout after 5s, falling back to OpenAI API
OpenAI response in 1.2s

UI Display:
⚡ RAISE TO $450
Confidence: 82%

Reasoning: Strong top pair, position advantage.
GTO suggests 75% pot bet, adjusted for stack sizes.

[Fallback used: OpenAI]
```

**Rationale**: User sees seamless experience, logging captures fallback for analysis.

---

### Scenario 3: Uncommon Scenario (No GTO Data)

**Situation**: 4-way all-in with complex side pots

**Philosophical Response** (Pragmatic Perfectionism + Ruthless Focus):
```
UI Display:
🤔 COMPLEX SPOT
Action: CALL (pot odds)

Reasoning: Insufficient GTO data for 4-way all-in scenario.
Basic pot odds calculation: 28% equity needed, your hand ~35%.
Recommend mathematical call.

Confidence: 60% (limited by data)
```

**Rationale**: Honest about limitations, fall back to fundamentals.

---

## Success Criteria

This tool succeeds when:

1. **Accuracy**: >90% of recommendations align with GTO solver outputs
2. **Speed**: <3 second latency for 95% of decisions
3. **Reliability**: <1% crash rate over 100-hand sessions
4. **Auditability**: Every decision can be reviewed post-session
5. **User Trust**: Users confidently follow recommendations without second-guessing

---

## Anti-Patterns to Avoid

### ❌ Feature Creep
"Let's add tournament support, then multi-table, then Omaha..."
**Counter**: Ruthless Focus - Texas Hold'em cash games only.

### ❌ Defensive Disclaimers
"This is just a suggestion, not financial advice, use at your own risk..."
**Counter**: Radical Accountability - Own the recommendation or don't show it.

### ❌ Black Box Recommendations
"RAISE TO $500" with no explanation
**Counter**: Transparent Reasoning - Always show why.

### ❌ Premature Optimization
"Let's fine-tune FastVLM on poker cards for 2% accuracy gain..."
**Counter**: Pragmatic Perfectionism - Use pre-trained model, optimize elsewhere.

### ❌ Silent Failures
Vision fails, no recommendation shown, user confused
**Counter**: Resilient by Design - Show "UNCERTAIN" state, never silent fail.

---

## Philosophy Summary

**Core Identity**: Accountable, Focused, Fast, Transparent

**Mission**: Provide optimal poker decisions in real-time with full accountability.

**Values**:
1. Own every outcome (Radical Accountability)
2. Best with available tools (Pragmatic Perfectionism)
3. One thing, done well (Ruthless Focus)
4. Speed is correctness (Performance as a Feature)
5. Show your work (Transparent Reasoning)
6. Never fail silently (Resilient by Design)
7. Learn from history (Memory is Strategy)

**Boundaries**: Cash games, Texas Hold'em, Mac, single table, advisory only.

---

**Status**: Phase 4 Complete - Philosophy Established, Ready for Boundary Setting
