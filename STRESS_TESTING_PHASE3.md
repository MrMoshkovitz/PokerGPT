# LLMPoker Assistant - Phase 3: Stress Testing Results

**Project**: LLMPoker Assistant
**Methodology**: Grounded Progressive Architecture (GPA)
**Phase**: 3 - Collaborative Stress Testing
**Date**: 2025-11-05

---

## Vision & State Extraction Concerns

### 1. Card Misrecognition
- FastVLM confuses similar cards (8♥ vs 8♦, J vs Q)
- Partial card visibility (overlapping UI elements)
- Different poker clients use different card graphics
- **Risk Level**: HIGH - Core functionality blocker

### 2. Dynamic UI Changes
- Pop-up notifications covering cards/pot
- Animations mid-capture (cards being dealt)
- Table resize/multi-monitor setup changes
- **Risk Level**: MEDIUM - Affects reliability

### 3. Multi-Table Confusion
- User playing multiple tables simultaneously
- Screen capture capturing wrong window
- Context mixing between tables
- **Risk Level**: LOW - MVP is single-table only

### 4. Performance Degradation
- FastVLM inference slower than expected on older CPUs
- Claude API latency spikes (>5 seconds)
- Memory leaks from continuous vision processing
- **Risk Level**: HIGH - Unusable if slow

---

## GTO & Decision Logic Concerns

### 5. GTO Data Quality
- Incomplete ranges for uncommon scenarios
- Outdated strategies (poker meta evolves)
- Licensing issues with GTO solver data
- **Risk Level**: MEDIUM - Quality depends on data source

### 6. Contextual Mismatches
- GTO assumes rational opponents (doesn't account for bad players)
- Tournament ICM calculations become complex near bubble
- Live tells/timing not captured (online-only data)
- **Risk Level**: MEDIUM - Claude reasoning should compensate

### 7. Action Timing
- Recommendation arrives too late (action already taken)
- Opponent acts before our system processes
- Time bank pressure in fast tournaments
- **Risk Level**: HIGH - Real-time requirement

---

## Claude Integration Concerns

### 8. API Reliability
- Rate limiting (too many requests during fast action)
- Network failures mid-hand
- Cost explosion (thousands of API calls per session)
- **Risk Level**: MEDIUM - Needs retry logic + cost monitoring

### 9. Context Hallucination
- Claude misinterprets game state from text description
- Overconfident recommendations based on flawed vision input
- Reasoning doesn't match actual game theory
- **Risk Level**: HIGH - Trust/safety issue

### 10. Prompt Engineering Fragility
- Prompt needs constant tuning for different scenarios
- Edge cases produce nonsensical recommendations
- Difficulty maintaining consistency across sessions
- **Risk Level**: MEDIUM - Iterative improvement needed

---

## User Experience Concerns

### 11. Trust & Verification
- User can't verify if recommendation is actually optimal
- Blind following leads to losses → blame the tool
- No way to audit decision quality post-session
- **Risk Level**: MEDIUM - Confidence scoring helps

### 12. Learning Interference
- User becomes dependent, stops learning strategy
- Doesn't develop poker intuition
- Can't play without the assistant anymore
- **Risk Level**: LOW - User responsibility

### 13. Legal & Ethical
- Most poker sites ban real-time assistance tools
- Using this in online poker violates ToS → account bans
- Only legal for home games / training
- **Risk Level**: CRITICAL - Must warn users prominently

---

## Technical Debt & Maintenance

### 14. Cross-Platform Compatibility
- Screen capture APIs differ (Windows/Mac/Linux)
- FastVLM performance varies by OS
- Browser rendering inconsistencies
- **Risk Level**: LOW - Start with single platform

### 15. Model Updates
- FastVLM model updates break integration
- Claude API changes require refactoring
- GTO data requires periodic refresh
- **Risk Level**: LOW - Maintenance concern, not blocker

### 16. Debugging Complexity
- Hard to reproduce specific game state bugs
- No logging of vision → decision pipeline
- User can't easily report issues with context
- **Risk Level**: MEDIUM - Need robust logging

---

## Scalability & Future Features

### 17. Player Profiling
- Tracking opponent patterns requires persistence
- Privacy concerns storing player data
- Database management complexity
- **Risk Level**: LOW - Future feature

### 18. Hand History Integration
- Exporting to tracking software (PT4, HM3)
- Parsing different poker site formats
- Replay analysis for learning
- **Risk Level**: LOW - Nice-to-have

### 19. Multi-Variant Support
- Omaha, PLO, Short Deck have different GTO
- Each variant multiplies data requirements
- UI needs to adapt per game type
- **Risk Level**: LOW - Future expansion

---

## Critical Blockers vs Manageable Risks

### 🚨 BLOCKER-LEVEL CONCERNS (Must Solve for MVP)

1. **Card Misrecognition** - Too risky without validation
   - Need confidence thresholds + manual verification UI

2. **Claude API Latency** - Unusable if >5 sec recommendations
   - Need timeout handling + cached GTO fallback

3. **Legal/ToS Violations** - Account ban risk
   - Must warn users prominently on startup

### ⚠️ MANAGEABLE RISKS (Can Address Post-MVP)

- Multi-table support (start with single table)
- Player profiling (defer to v2)
- Cross-platform (launch on Windows first)
- Hand history integration (future feature)
- Multi-variant support (Texas Hold'em only for MVP)

### ✅ ACCEPTABLE RISKS (Document & Monitor)

- Learning interference (user choice)
- GTO data quality (best-effort with available sources)
- Debugging complexity (add logging infrastructure)

---

## Additional Concerns to Consider

### Performance Under Load
- Long tournament sessions (6+ hours)
- Memory usage growth over time
- CPU thermal throttling on laptops

### Edge Cases in Game State
- All-in situations with side pots
- Split pots with identical hands
- Disconnections/reconnections mid-hand
- Tournament breaks and level changes

### UI/UX Edge Cases
- Screen resolution changes
- Dark mode vs light mode poker clients
- Non-English poker clients
- Custom card deck designs

### Data Privacy
- Storing hand histories locally
- Uploading game data to Claude API
- User session analytics

---

## User Responses to Stress Testing (Phase 3 → 4 Transition)

### Decisions Made:

1. **Card Misrecognition**: Be agnostic to poker client, do best with FastVLM as-is
2. **Dynamic UI Changes**: Address as noise, ignore if not game-related content
3. **Multi-Table**: OUT OF SCOPE
4. **Performance/API**: **CRITICAL CORRECTION - Using Claude Code CLI (`claude -p ...`), NOT Claude API**
5. **GTO Data Quality**: OUT OF SCOPE
6. **Contextual Mismatches**: OUT OF SCOPE
7. **Action Timing**: Do as fast and efficient as possible
8. **API Reliability**: Fallback to OpenAI API or Gemini CLI
9. **Context Hallucination**: Use ultrathink mode, ensure reasoning is smarter and thinking harder
10. **Prompt Engineering**: Focus on REGULAR GAMES (cash), same prompt with game history context
11. **Trust & Verification**: Recommendations MUST be optimal - "losses → blame the tool" is correct and intentional
12. **Learning Interference**: OUT OF SCOPE
13. **Legal/Ethical**: OUT OF SCOPE
14. **Cross-Platform**: Start with Mac, rest is technical debt
15. **Model Updates**: Technical debt
16. **Debugging**: Add logging ALL OVER the app
17. **Player Profiling**: IMPLEMENT PERSISTENCY
18. **Hand History Integration**: (No response - future consideration)
19. **Multi-Variant**: OUT OF SCOPE (Texas Hold'em only)

### Architectural Implications:

**🔥 CRITICAL CHANGE**: Local LLM Execution via CLI
- Claude Code CLI (`claude -p "prompt"`)
- OpenAI API fallback
- Gemini CLI fallback
- Extended reasoning mode (ultrathink)
- **No API latency concerns** - local execution!

**Focus**: Cash Games (8-handed Texas Hold'em)
**Platform**: Mac-first (Windows/Linux = technical debt)
**Logging**: Comprehensive across entire pipeline
**Persistence**: Player profiling database

---

**Status**: Phase 3 Complete with User Decisions - Moving to Phase 4 (Philosophical Grounding)
