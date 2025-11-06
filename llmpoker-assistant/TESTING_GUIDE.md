# LLMPoker Assistant - Testing Guide
## Zynga Poker (Facebook) Validation

This guide provides step-by-step instructions for testing the LLMPoker Assistant in a clean sandbox environment using Facebook's Zynga Poker as the poker client.

---

## 1. Pre-Testing Setup

### 1.1 Environment Preparation
```bash
cd /Users/gmoshkov/Professional/Code/PrivateGM/PokerGPT/llmpoker-assistant

# Create fresh virtual environment (Python 3.12)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Model Downloads
```bash
# Download FastVLM-0.5B model (first run only)
python -c "from transformers import AutoModel; AutoModel.from_pretrained('apple/fastvlm-0.5b')"
```

### 1.3 Configuration Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings:
# - Add OPENAI_API_KEY if available
# - Verify CLAUDE_CLI_PATH points to your claude executable
# - Set LOG_LEVEL=DEBUG for testing
```

### 1.4 LLM Availability Check
```bash
# Test Claude Code CLI
which claude
claude --version

# Test fallbacks (optional)
python -c "import openai; print('OpenAI SDK available')"
```

---

## 2. Zynga Poker Specific Considerations

### 2.1 Expected Challenges
- **Stylized Graphics**: Zynga uses cartoon-style cards (not photorealistic)
- **Expected Accuracy**: 70-85% vision confidence (vs 90%+ with realistic graphics)
- **UI Overlays**: Pop-ups, animations, chat bubbles may interfere
- **Position Detection**: May be inaccurate without dealer button tracking

### 2.2 Zynga Setup
1. Open Facebook in browser
2. Navigate to Zynga Poker app
3. Join a Texas Hold'em cash game (NOT tournament for first test)
4. Use full-screen mode (F11) to maximize consistency
5. Disable chat/notifications to reduce visual noise

---

## 3. Testing Process

### Phase 1: Launch Zynga Poker
```bash
# 1. Open browser and load Zynga Poker
# 2. Sit at a Texas Hold'em table (8-handed or 6-handed)
# 3. Wait for a hand to start (you need to see cards)
# 4. Position window so game table is clearly visible
```

### Phase 2: Start LLMPoker Assistant
```bash
cd /Users/gmoshkov/Professional/Code/PrivateGM/PokerGPT/llmpoker-assistant
source venv/bin/activate
./run.sh
```

**Expected Output:**
```
[INFO] LLMPoker Assistant v1.0 starting...
[INFO] FastVLM model loaded: apple/fastvlm-0.5b
[INFO] GTO strategy cache initialized (1326 preflop ranges)
[INFO] Web server started at http://localhost:8080
[INFO] Claude CLI detected at: /usr/local/bin/claude
[INFO] Launching region selector...
```

### Phase 3: Region Selection
1. **Tkinter window will appear** with your full screen visible
2. **Click and drag** to select the poker table area
3. **Include**: Player cards, community cards, pot, bet amounts
4. **Exclude**: Chat, menus, browser chrome
5. **Press ENTER** to confirm selection
6. **Press ESC** to cancel and retry

**Tip**: Select slightly larger area to avoid cropping important info

### Phase 4: Live Testing
1. **Open dashboard**: Navigate to `http://localhost:8080` in browser
2. **Monitor real-time updates**: Dashboard should show game state
3. **Play a hand**: Take actions in Zynga and observe recommendations
4. **Check logs**: Watch terminal for vision extraction and LLM calls

---

## 4. Test Scenarios

### Scenario 1: Preflop Decision
**Setup:**
- You are dealt pocket cards (e.g., A♠ K♦)
- Action is on you (or approaching)

**Expected Behavior:**
1. Vision extracts: `hole_cards: ["As", "Kd"]`, position, stack
2. GTO cache lookup returns: "RAISE 3BB" with 85% frequency
3. LLM provides: "Raise to 300. AKo is a premium hand, build pot in position"
4. Dashboard shows: GREEN confidence (>80%), action recommendation

**Success Criteria:**
- Vision confidence ≥75%
- Correct card detection
- GTO recommendation appears within 2 seconds
- LLM reasoning is coherent

---

### Scenario 2: Postflop Decision
**Setup:**
- Flop is dealt (e.g., K♥ 9♣ 2♦)
- Opponent bets, action on you

**Expected Behavior:**
1. Vision extracts: Board cards, pot size, bet amount
2. GTO suggests: "CALL" (top pair, good kicker)
3. LLM adds: "Call the bet. You have top pair with strong kicker. Be cautious if turn brings straight/flush draw"
4. Dashboard updates with postflop context

**Success Criteria:**
- Board detection accuracy ≥70%
- Pot odds calculated correctly
- Recommendation aligns with GTO baseline

---

### Scenario 3: Low Confidence Situation
**Setup:**
- Hand is partially obscured (animation, overlay)
- Vision confidence drops below 75%

**Expected Behavior:**
1. Vision reports: `confidence: 0.68` (below threshold)
2. System waits for next frame (does NOT make recommendation)
3. Dashboard shows: YELLOW warning "Low confidence, waiting..."
4. Terminal logs: `[WARN] Confidence 68% below threshold, buffering...`

**Success Criteria:**
- No recommendation made with low confidence
- System waits for 3-frame consensus
- Dashboard clearly indicates waiting state

---

### Scenario 4: LLM Fallback Chain
**Setup:**
- Simulate Claude CLI failure (rename `claude` binary temporarily)

**Expected Behavior:**
1. Claude CLI times out or errors
2. System falls back to OpenAI API (if configured)
3. If OpenAI fails → Gemini fallback
4. If all fail → GTO-only recommendation
5. Terminal logs: `[WARN] Claude CLI failed, trying OpenAI...`

**Success Criteria:**
- System does NOT crash
- Fallback happens within 5 seconds
- User still receives recommendation (even if GTO-only)

---

## 5. Monitoring Dashboard

### 5.1 Dashboard Panels
Open `http://localhost:8080` and verify:

**Game State Panel:**
- Shows current hand (e.g., "A♠ K♦")
- Board cards (if postflop)
- Pot size and stack size
- Current position

**Recommendation Panel:**
- Primary action (FOLD/CALL/RAISE)
- Confidence badge (GREEN >80%, YELLOW 60-80%, RED <60%)
- LLM reasoning text
- GTO baseline reference

**Performance Metrics:**
- Latency graph (should be <3s for p95)
- Confidence trend line
- LLM provider status (Claude/OpenAI/Gemini/GTO-only)

**Recent Hands:**
- Last 5 decisions with outcomes
- Click to view full hand history

### 5.2 Log Monitoring
```bash
# Terminal 1: Main application logs
tail -f logs/app.log

# Terminal 2: Decision logs (JSONL)
tail -f logs/decisions.jsonl | jq .

# Terminal 3: FastAPI server logs
# (already displayed in main terminal)
```

**Key Log Events:**
- `[CAPTURE] Screen changed (hash diff: 12%)` → Capture triggered
- `[VISION] Extracted game state: confidence=0.89` → Vision successful
- `[GTO] Cache hit: AKo_BTN_preflop` → GTO lookup
- `[LLM] Claude CLI response in 1.2s` → LLM success
- `[STATE] Hand #42 completed, saved to DB` → Persistence

---

## 6. Expected Issues & Solutions

### Issue 1: Vision Confidence Always Low (<60%)
**Cause**: Zynga's stylized cards not well-represented in FastVLM training data

**Solutions:**
- Increase screen capture resolution in config
- Adjust confidence threshold to 65% (edit `src/vision/confidence_validator.py`)
- Use full-screen mode in Zynga
- Disable Zynga animations (settings)

**Workaround**: If vision consistently fails, system will fall back to GTO-only mode

---

### Issue 2: Claude CLI Not Found
**Symptom**: `[ERROR] Claude CLI not available at /usr/local/bin/claude`

**Solutions:**
```bash
# Find claude binary
which claude

# Update .env file
CLAUDE_CLI_PATH=/path/to/claude

# Or install Claude Code CLI
# (follow https://docs.claude.com/claude-code)
```

**Workaround**: System will use OpenAI or Gemini fallback

---

### Issue 3: Region Selector Window Not Appearing
**Cause**: Tkinter issues on macOS with virtual environments

**Solutions:**
```bash
# Install python-tk
brew install python-tk

# Or use system Python for region selector only
/usr/bin/python3 src/capture/region_selector.py
```

---

### Issue 4: WebSocket Connection Failed
**Symptom**: Dashboard shows "Connecting..." indefinitely

**Solutions:**
```bash
# Check if port 8080 is available
lsof -i :8080

# Kill conflicting process
kill -9 <PID>

# Or change port in config.yaml
server:
  port: 8081
```

---

### Issue 5: High Latency (>5s)
**Cause**: Model loading, cold start, or LLM timeout

**Solutions:**
- First recommendation is always slow (model loading) - wait 30s
- Subsequent recommendations should be <3s
- If Claude CLI is slow, check `--extended-thinking` timeout
- Monitor CPU/GPU usage during inference

---

## 7. Success Criteria

### Minimum Viable (PASS):
- ✅ Application starts without crashes
- ✅ Region selector works (can capture screen)
- ✅ Vision extracts game state with ≥60% confidence
- ✅ At least one LLM provider works (Claude/OpenAI/Gemini)
- ✅ Dashboard displays recommendations in real-time
- ✅ Latency <5s (95th percentile)

### Good (EXPECTED):
- ✅ Vision confidence ≥75% on most frames
- ✅ GTO cache hits on every decision
- ✅ Claude CLI works as primary LLM
- ✅ Dashboard shows all panels correctly
- ✅ Latency <3s (95th percentile)
- ✅ No crashes over 30-minute session

### Excellent (STRETCH):
- ✅ Vision confidence ≥85% consistently
- ✅ Position detection accurate (without dealer button)
- ✅ LLM reasoning is contextually rich
- ✅ Latency <2s (95th percentile)
- ✅ All fallback chains tested and working
- ✅ Hand history persistence working

---

## 8. Debugging Tips

### Enable Verbose Logging
Edit `.env`:
```bash
LOG_LEVEL=DEBUG
FASTVLM_DEBUG=true
CAPTURE_SAVE_FRAMES=true  # Save screenshots to logs/frames/
```

### Test Individual Components
```bash
# Test screen capture only
python src/capture/screen_capture.py

# Test vision extraction
python tests/test_vision.py

# Test GTO cache
python tests/test_gto.py

# Test Claude CLI directly
claude -p "You have AK offsuit in button position. Pot is 100, opponent raised to 30. What should you do?"
```

### Inspect Database
```bash
sqlite3 data/llmpoker.db

# View recent hands
SELECT * FROM hands ORDER BY timestamp DESC LIMIT 10;

# View session stats
SELECT * FROM sessions ORDER BY start_time DESC LIMIT 5;
```

---

## 9. Test Report Template

After completing testing, document results:

```markdown
# Test Report: Zynga Poker Validation
**Date**: [DATE]
**Tester**: [YOUR NAME]
**Environment**: macOS / Python 3.10 / Claude Code CLI

## Summary
- ✅/❌ Application startup
- ✅/❌ Region selection
- ✅/❌ Vision extraction
- ✅/❌ GTO recommendations
- ✅/❌ LLM integration
- ✅/❌ Dashboard UI
- ✅/❌ Performance (<3s latency)

## Detailed Results
### Vision Accuracy
- Average confidence: X%
- Card detection rate: X/X hands
- Board detection rate: X/X flops

### LLM Performance
- Claude CLI success rate: X%
- Fallback usage: OpenAI X%, Gemini X%, GTO-only X%
- Average reasoning quality: [1-5 scale]

### Latency Metrics
- p50: Xs
- p95: Xs
- p99: Xs

## Issues Found
1. [Issue description]
   - Severity: [Critical/High/Medium/Low]
   - Workaround: [If available]

## Recommendations
- [Next steps or improvements]
```

---

## 10. Next Steps After Testing

### If Testing Passes (Minimum Viable):
1. Test with real poker client (PokerStars, GGPoker)
2. Expand GTO data with full solver ranges
3. Fine-tune FastVLM on poker-specific images
4. Add dealer button detection for accurate position

### If Testing Fails:
1. Document blocking issues in test report
2. Prioritize fixes based on severity
3. Re-run tests after fixes
4. Consider alternative vision models if FastVLM accuracy too low

### Production Readiness Checklist:
- [ ] Vision confidence >85% on realistic poker clients
- [ ] Latency <2s (p95) consistently
- [ ] 24-hour stability test (no crashes)
- [ ] Full GTO solver data integrated
- [ ] Multi-table support tested
- [ ] Tournament mode validated

---

## Contact & Support
For issues during testing:
- Check `logs/app.log` for detailed error messages
- Review architecture diagrams in `ARCHITECTURE.md`
- Consult implementation details in `IMPLEMENTATION.md`
- Reference core philosophy in `PHILOSOPHY_PHASE4.md`

**Remember**: This is an MVP test. The goal is to validate the core pipeline works end-to-end, not to achieve production-level accuracy. Focus on system stability and architectural soundness.
