# LLMPoker Assistant - Implementation Instructions

**Version**: 1.0
**Target**: Developers ready to implement the system
**Time Estimate**: 7 weeks (one developer, full-time)

---

## Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/MrMoshkovitz/PokerGPT.git
cd PokerGPT

# 2. Create Python environment
python3.10 -m venv venv
source venv/bin/activate  # On Mac/Linux

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Download FastVLM model
python scripts/download_fastvlm.py

# 5. Download GTO data
python scripts/download_gto_data.py

# 6. Configure environment
cp .env.example .env
# Edit .env with your OpenAI/Gemini API keys (for fallback)

# 7. Run application
python src/main.py
```

---

## Prerequisites

### System Requirements
- **OS**: macOS 12.0+ (Monterey or later)
- **CPU**: M1/M2 recommended (x86_64 also supported)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 2GB for models + data
- **Python**: 3.10 or 3.11

### Required Tools
- **Python 3.10+**: `brew install python@3.10`
- **Claude Code CLI**: Install from https://github.com/anthropics/claude-code
- **Git**: Pre-installed on macOS
- **Homebrew**: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Optional Tools
- **OpenAI API Key**: For fallback (https://platform.openai.com/api-keys)
- **Gemini API Key**: For fallback (https://aistudio.google.com/app/apikey)

---

## Implementation Roadmap (7 Weeks)

### Week 1: Core Infrastructure

#### Day 1-2: Project Setup
```bash
# Create project structure
mkdir -p src/{capture,vision,gto,llm,state,persistence,api,ui/static,utils,models}
mkdir -p tests data/{gto,models,database} logs config

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;

# Initialize git
git init
echo "venv/\n*.pyc\n__pycache__/\ndata/\nlogs/\n.env" > .gitignore

# Create requirements.txt (see Dependencies section below)
```

#### Day 3-4: Screen Capture Module
**File**: `src/capture/screen_capture.py`

**Implementation Steps**:
1. Install mss: `pip install mss pillow`
2. Implement `ScreenCapture` class:
   - `__init__(region)`: Store capture region
   - `check_for_changes()`: Quick diff check (100ms)
   - `capture_frame()`: Full screenshot capture
   - `_calculate_diff()`: Pixel difference ratio

**Testing**:
```python
# tests/test_screen_capture.py
def test_capture():
    region = {"left": 0, "top": 0, "width": 800, "height": 600}
    capture = ScreenCapture(region)
    frame = capture.capture_frame()
    assert frame.size == (800, 600)
```

#### Day 5: Region Selector UI
**File**: `src/capture/region_selector.py`

**Implementation Steps**:
1. Create tkinter overlay for drag-to-select
2. Return region coordinates: `{"left": x, "top": y, "width": w, "height": h}`
3. Save to config file for persistence

**Manual Test**:
```bash
python -c "from src.capture.region_selector import RegionSelector; print(RegionSelector().select_region())"
```

---

### Week 2: Vision Module

#### Day 1-3: FastVLM Integration
**File**: `src/vision/fastvlm_inference.py`

**Implementation Steps**:
1. Download FastVLM-0.5B model:
```python
# scripts/download_fastvlm.py
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="apple/fastvlm-0.5b-stage3",
    local_dir="data/models/fastvlm-0.5b"
)
```

2. Load model in `FastVLMInference` class:
```python
from llava.model.builder import load_pretrained_model

self.tokenizer, self.model, self.image_processor, _ = load_pretrained_model(
    model_path="data/models/fastvlm-0.5b",
    model_base=None,
    model_name="fastvlm-0.5b"
)
```

3. Implement `extract_game_state(image)`:
   - Construct vision prompt (see IMPLEMENTATION.md)
   - Run inference
   - Parse JSON response

**Testing**:
```python
# tests/test_vision.py
def test_vision_extraction():
    vision = FastVLMInference("data/models/fastvlm-0.5b")

    # Load test screenshot (poker table)
    image = Image.open("tests/fixtures/poker_screenshot.png")

    state = vision.extract_game_state(image)

    assert "hole_cards" in state
    assert len(state["hole_cards"]) == 2
    assert "confidence" in state
```

#### Day 4-5: Confidence Validation
**File**: `src/vision/confidence_validator.py`

**Implementation Steps**:
1. Implement 3-frame buffer:
```python
self.state_buffer: List[Dict] = []

def validate(self, game_state):
    self.state_buffer.append(game_state)
    if len(self.state_buffer) > 3:
        self.state_buffer.pop(0)

    consistency = self._check_consistency()
    aggregate_conf = self._aggregate_confidence(game_state)
    final_conf = aggregate_conf * consistency

    return final_conf >= self.threshold, final_conf
```

2. Implement consistency checks:
   - Hole cards shouldn't change mid-hand
   - Board should only add cards (flop → turn → river)
   - Pot should only increase
   - Stacks should only decrease

**Testing**:
```python
# tests/test_confidence.py
def test_temporal_consistency():
    validator = ConfidenceValidator()

    # Frame 1: Preflop
    state1 = {"hole_cards": ["Ah", "Kd"], "board": [], "pot": 50}
    is_conf, conf = validator.validate(state1)

    # Frame 2: Flop (consistent)
    state2 = {"hole_cards": ["Ah", "Kd"], "board": ["Qh", "Js", "10c"], "pot": 150}
    is_conf, conf = validator.validate(state2)
    assert is_conf

    # Frame 3: Inconsistent (hole cards changed - error)
    state3 = {"hole_cards": ["2h", "3d"], "board": ["Qh", "Js", "10c"], "pot": 150}
    is_conf, conf = validator.validate(state3)
    assert not is_conf
```

---

### Week 3: GTO Engine

#### Day 1-2: GTO Data Acquisition
**File**: `scripts/download_gto_data.py`

**Data Sources** (Open Source):
1. **GTOBase**: Free preflop ranges (https://gtobase.com/)
2. **GTOwizard Free Tier**: Limited postflop data
3. **GTO+ Community**: Open-source ranges

**Format**: Convert to Python dictionaries, save as pickle:
```python
# Example structure
preflop_ranges = {
    "BTN": {
        "AhAs": {"action": "RAISE", "sizing": 3.0},  # 3bb
        "KhKs": {"action": "RAISE", "sizing": 3.0},
        "AhKd": {"action": "RAISE", "sizing": 3.0},
        # ... all hands
    },
    "CO": {...},
    # ... all positions
}

postflop_buckets = {
    ("NUTS", "WET", "DEEP"): {"action": "BET", "sizing": 0.75},  # 75% pot
    ("STRONG", "DRY", "MEDIUM"): {"action": "BET", "sizing": 0.50},
    # ... all combinations
}

import pickle
with open("data/gto/preflop_ranges.pkl", "wb") as f:
    pickle.dump(preflop_ranges, f)
```

**Manual Step**: You may need to manually scrape/compile GTO data. This is tedious but one-time.

#### Day 3-4: Strategy Cache Implementation
**File**: `src/gto/strategy_cache.py`

**Implementation Steps**:
1. Load pickle files into memory at startup
2. Implement `get_action()`:
```python
def get_action(self, position, hole_cards, board, pot, stack):
    if not board:  # Preflop
        hand_key = self._normalize_hand(hole_cards)  # "AhKd" → "AKo"
        return self.preflop_ranges[position].get(hand_key, {"action": "FOLD"})
    else:  # Postflop
        hand_strength = self._calculate_hand_strength(hole_cards, board)
        board_texture = self._classify_board_texture(board)
        spr_bucket = self._bucket_spr(stack / pot)
        key = (hand_strength, board_texture, spr_bucket)
        return self.postflop_buckets.get(key, {"action": "CHECK"})
```

3. Implement helper functions:
   - `_normalize_hand()`: Convert ["Ah", "Kd"] → "AKo"
   - `_calculate_hand_strength()`: Use `treys` library for hand evaluation
   - `_classify_board_texture()`: Count flush draws, straight draws
   - `_bucket_spr()`: Map continuous SPR to buckets (DEEP >10, MEDIUM 3-10, SHALLOW <3)

**Dependencies**:
```bash
pip install treys  # Poker hand evaluator
```

**Testing**:
```python
# tests/test_gto.py
def test_preflop_range():
    gto = GTOStrategyCache()
    gto.load_from_disk("data/gto")

    action = gto.get_action(
        position="BTN",
        hole_cards=["Ah", "As"],
        board=[],
        pot=10,
        stack=100
    )

    assert action["action"] == "RAISE"
    assert action["sizing"] > 0
```

#### Day 5: Hand Evaluator Integration
**File**: `src/gto/hand_evaluator.py`

**Implementation**:
```python
from treys import Card, Evaluator

def calculate_hand_strength(hole_cards, board):
    """
    Returns: NUTS, STRONG, MEDIUM, WEAK, BLUFF
    """
    evaluator = Evaluator()

    # Convert strings to treys format
    hole = [Card.new(c) for c in hole_cards]
    board_cards = [Card.new(c) for c in board]

    rank = evaluator.evaluate(board_cards, hole)

    # Bucket by rank (lower is better in treys)
    if rank < 500:  # Very strong
        return "NUTS"
    elif rank < 1500:
        return "STRONG"
    elif rank < 3000:
        return "MEDIUM"
    elif rank < 5000:
        return "WEAK"
    else:
        return "BLUFF"
```

---

### Week 4: LLM Integration

#### Day 1-2: Claude Code CLI Executor
**File**: `src/llm/claude_cli.py`

**Implementation Steps**:
1. Verify Claude Code CLI installed: `claude --version`
2. Implement executor:
```python
import subprocess
import json

class ClaudeCLI:
    def get_recommendation(self, prompt: str) -> Optional[Dict]:
        try:
            result = subprocess.run(
                ["claude", "-p", f"--extended-thinking {prompt}"],
                timeout=5,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logging.error(f"Claude error: {result.stderr}")
                return None

            return self._parse_response(result.stdout)

        except subprocess.TimeoutExpired:
            logging.warning("Claude timeout")
            return None
```

**Testing**:
```python
# tests/test_claude.py
def test_claude_cli():
    cli = ClaudeCLI()
    prompt = "What is 2+2? Respond in JSON: {\"answer\": <number>}"
    result = cli.get_recommendation(prompt)
    assert result["answer"] == 4
```

#### Day 3: Prompt Builder
**File**: `src/llm/prompt_builder.py`

**Implementation**:
```python
class PromptBuilder:
    @staticmethod
    def build_decision_prompt(game_state, gto_baseline, hand_history, session_stats):
        return f"""You are a professional poker advisor using GTO strategy as foundation.

**Current Decision Point:**
- Your Hand: {' '.join(game_state['hole_cards'])}
- Board: {' '.join(game_state.get('board', ['Preflop']))}
- Pot: ${game_state['pot']}
- Your Stack: ${game_state['your_stack']}
- Position: {game_state['position']}

**GTO Baseline Recommendation:**
{json.dumps(gto_baseline, indent=2)}

**Recent Hand History (last 5 hands):**
{PromptBuilder._format_history(hand_history)}

**Session Statistics:**
- Hands Played: {session_stats.get('hands_played', 0)}
- VPIP: {session_stats.get('vpip', 0):.1f}%
- Win Rate: ${session_stats.get('win_rate', 0)}/hour

**Your Task:**
Provide optimal recommendation in JSON format:
{{
    "action": "FOLD|CALL|RAISE",
    "amount": <number or null>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "alternatives": [
        {{"action": "...", "confidence": <0.0-1.0>}}
    ]
}}

Think deeply about:
1. Hand strength vs range
2. Position and initiative
3. Pot odds and implied odds
4. Board texture and equity distribution
5. Stack-to-pot ratio (SPR)

Use extended thinking to analyze this decision thoroughly.
"""
```

#### Day 4-5: Fallback Chain
**Files**:
- `src/llm/openai_fallback.py`
- `src/llm/gemini_fallback.py`

**Implementation**:
```python
# OpenAI fallback
import openai

class OpenAIFallback:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_recommendation(self, prompt: str) -> Optional[Dict]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=5
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"OpenAI fallback failed: {e}")
            return None
```

---

### Week 5: State Management & Persistence

#### Day 1-2: Database Schema
**File**: `src/persistence/database.py`

**Implementation**:
```python
import sqlite3
import aiosqlite

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_schema()

    def _create_schema(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables (see IMPLEMENTATION.md for schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                position TEXT,
                hole_cards TEXT,
                board TEXT,
                pot REAL,
                stack REAL,
                gto_action TEXT,
                llm_action TEXT,
                llm_confidence REAL,
                llm_reasoning TEXT,
                llm_provider TEXT,
                vision_confidence REAL
            )
        """)

        conn.commit()
        conn.close()

    async def log_decision(self, game_state, gto_action, recommendation):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO hands (
                    session_id, position, hole_cards, board, pot, stack,
                    gto_action, llm_action, llm_confidence, llm_reasoning, llm_provider
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                game_state['position'],
                json.dumps(game_state['hole_cards']),
                json.dumps(game_state.get('board', [])),
                game_state['pot'],
                game_state['your_stack'],
                gto_action['action'],
                recommendation['action'],
                recommendation['confidence'],
                recommendation['reasoning'],
                recommendation.get('fallback_used', 'claude_cli')
            ))
            await db.commit()
```

#### Day 3: Game State Manager
**File**: `src/state/state_manager.py`

**Implementation**: Integrate temporal buffer, confidence validator, state transitions.

#### Day 4-5: Logging Infrastructure
**File**: `src/utils/logger.py`

**Implementation**:
```python
import logging
import json
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Application logs
    app_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=100*1024*1024,  # 100MB
        backupCount=5
    )
    app_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Decision logs (JSON Lines)
    decision_handler = RotatingFileHandler(
        'logs/decisions.jsonl',
        maxBytes=100*1024*1024,
        backupCount=5
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[app_handler, logging.StreamHandler()]
    )

    # Separate logger for decisions
    decision_logger = logging.getLogger('decisions')
    decision_logger.addHandler(decision_handler)
    decision_logger.setLevel(logging.INFO)

def log_decision(game_state, recommendation, latency_ms):
    decision_logger = logging.getLogger('decisions')
    decision_logger.info(json.dumps({
        'timestamp': time.time(),
        'game_state': game_state,
        'recommendation': recommendation,
        'latency_ms': latency_ms
    }))
```

---

### Week 6: Web Server & UI

#### Day 1-2: FastAPI Server
**File**: `src/api/server.py`

**Implementation**:
```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")

# Store active WebSocket connections
connections: List[WebSocket] = []

@app.get("/")
async def root():
    with open("src/ui/static/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)

    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except Exception:
        connections.remove(websocket)

async def broadcast_update(data: dict):
    """Send update to all connected clients."""
    for ws in connections[:]:  # Copy list to avoid modification during iteration
        try:
            await ws.send_json(data)
        except Exception:
            connections.remove(ws)
```

#### Day 3-4: Browser Dashboard (HTML/CSS/JS)
**File**: `src/ui/static/index.html`

**Implementation**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>LLMPoker Assistant</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div id="app">
        <div id="game-state">
            <h2>Game State</h2>
            <div id="cards">
                <span id="hole-cards">--</span>
                <span id="board">--</span>
            </div>
            <div id="info">
                <span id="pot">Pot: $--</span>
                <span id="stack">Stack: $--</span>
                <span id="position">Position: --</span>
            </div>
        </div>

        <div id="recommendation">
            <h1 id="action">Waiting...</h1>
            <progress id="confidence" max="100" value="0"></progress>
            <p id="confidence-text">--</p>
        </div>

        <details id="reasoning">
            <summary>Reasoning</summary>
            <p id="reasoning-text">--</p>
        </details>

        <div id="status">
            <span id="provider">--</span>
            <span id="latency">--</span>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

**File**: `src/ui/static/app.js`

**Implementation**:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'game_state_update') {
        updateGameState(data.state);
    } else if (data.type === 'recommendation') {
        displayRecommendation(data);
    } else if (data.type === 'system_alert') {
        showAlert(data.message, data.level);
    }
};

function updateGameState(state) {
    document.getElementById('hole-cards').innerText = state.hole_cards.join(' ');
    document.getElementById('board').innerText = state.board.join(' ') || 'Preflop';
    document.getElementById('pot').innerText = `Pot: $${state.pot}`;
    document.getElementById('stack').innerText = `Stack: $${state.your_stack}`;
    document.getElementById('position').innerText = `Position: ${state.position}`;
}

function displayRecommendation(rec) {
    const action = document.getElementById('action');
    action.innerText = rec.action;

    // Color-code by confidence
    action.className = rec.confidence > 0.8 ? 'high-conf' :
                       rec.confidence > 0.6 ? 'med-conf' : 'low-conf';

    document.getElementById('confidence').value = rec.confidence * 100;
    document.getElementById('confidence-text').innerText = `${(rec.confidence * 100).toFixed(0)}% confident`;
    document.getElementById('reasoning-text').innerText = rec.reasoning;
    document.getElementById('provider').innerText = rec.llm_provider || 'claude_cli';
}
```

#### Day 5: Styling
**File**: `src/ui/static/style.css`

**Implementation**: Create clean, readable UI with large fonts for action, color-coded confidence.

---

### Week 7: Integration & Testing

#### Day 1-2: Main Application Loop
**File**: `src/main.py`

**Implementation**:
```python
import asyncio
from capture.screen_capture import ScreenCapture
from capture.region_selector import RegionSelector
from vision.fastvlm_inference import FastVLMInference
from vision.confidence_validator import ConfidenceValidator
from gto.strategy_cache import GTOStrategyCache
from llm.claude_cli import ClaudeCLI
from llm.openai_fallback import OpenAIFallback
from persistence.database import Database
from api.server import app, broadcast_update
import uvicorn

class LLMPokerAssistant:
    def __init__(self):
        # Initialize all components
        self.vision = FastVLMInference("data/models/fastvlm-0.5b")
        self.validator = ConfidenceValidator()
        self.gto = GTOStrategyCache()
        self.gto.load_from_disk("data/gto")
        self.llm_primary = ClaudeCLI()
        self.llm_fallback = OpenAIFallback()
        self.db = Database("data/database/poker.db")

    async def run(self):
        # Select region
        selector = RegionSelector()
        region = selector.select_region()
        self.capture = ScreenCapture(region)

        # Start API server
        asyncio.create_task(self._start_server())

        # Main loop
        while True:
            if self.capture.check_for_changes():
                await self.process_frame()
            await asyncio.sleep(0.1)

    async def process_frame(self):
        # Full pipeline (see ARCHITECTURE.md for details)
        frame = self.capture.capture_frame()
        game_state = self.vision.extract_game_state(frame)
        is_confident, confidence = self.validator.validate(game_state)

        if not is_confident:
            await broadcast_update({
                "type": "system_alert",
                "level": "warning",
                "message": f"Low confidence ({confidence:.0%})"
            })
            return

        gto_action = self.gto.get_action(...)
        recommendation = self.llm_primary.get_recommendation(...)

        if not recommendation:
            recommendation = self.llm_fallback.get_recommendation(...)

        await broadcast_update({
            "type": "recommendation",
            **recommendation
        })

        await self.db.log_decision(game_state, gto_action, recommendation)

if __name__ == "__main__":
    assistant = LLMPokerAssistant()
    asyncio.run(assistant.run())
```

#### Day 3-4: End-to-End Testing

**Test Plan**:
1. Open PokerStars/GGPoker/home game software
2. Run `python src/main.py`
3. Select poker table region
4. Play 20 hands
5. Verify:
   - Recommendations appear within 3 seconds
   - Confidence scores are reasonable
   - Reasoning makes sense
   - No crashes
   - Logs are written

**Automated Testing**:
```bash
# Unit tests
pytest tests/

# Integration test (mock game states)
python tests/test_integration.py

# Performance benchmark
python tests/benchmark.py
```

#### Day 5: Polish & Documentation
- Fix bugs found during testing
- Update README with setup instructions
- Add example screenshots
- Document known issues

---

## Configuration

### Environment Variables (.env)
```bash
# LLM API Keys (for fallback)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Application settings
LOG_LEVEL=INFO
DATABASE_PATH=data/database/poker.db
GTO_DATA_PATH=data/gto
MODEL_PATH=data/models/fastvlm-0.5b

# Performance tuning
VISION_CONFIDENCE_THRESHOLD=0.70
LLM_TIMEOUT_SECONDS=5
SCREEN_CAPTURE_INTERVAL_MS=100
```

### Config File (config/default_config.yaml)
```yaml
capture:
  check_interval_ms: 100
  diff_threshold: 0.05

vision:
  model_path: "data/models/fastvlm-0.5b"
  confidence_threshold: 0.70
  temporal_buffer_size: 3

gto:
  data_path: "data/gto"

llm:
  primary_provider: "claude_cli"
  timeout_seconds: 5
  extended_thinking: true
  fallback_chain:
    - "openai"
    - "gemini"

api:
  host: "127.0.0.1"
  port: 8080

logging:
  level: "INFO"
  log_dir: "logs"
```

---

## Dependencies (requirements.txt)

```txt
# Core
python>=3.10

# Vision & ML
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
pillow>=9.5.0
accelerate>=0.20.0

# FastVLM (from GitHub)
git+https://github.com/MrMoshkovitz/ml-fastvlm.git

# Screen capture
mss>=9.0.0
pyautogui>=0.9.54

# Web server
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
websockets>=11.0.0
python-multipart>=0.0.6

# Database
aiosqlite>=0.19.0

# LLM clients
openai>=1.0.0
google-generativeai>=0.3.0

# Poker utilities
treys>=0.1.8

# Utilities
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
numpy>=1.24.0
requests>=2.31.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.4.0
```

---

## Troubleshooting

### Issue: FastVLM inference is slow (>3 seconds)
**Solution**:
- Use smaller model variant (fastvlm-0.5b, not 1.5b/7b)
- Enable Metal acceleration on Mac: `export PYTORCH_ENABLE_MPS_FALLBACK=1`
- Reduce image resolution before inference

### Issue: Claude Code CLI not found
**Solution**:
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
# Or follow: https://github.com/anthropics/claude-code
```

### Issue: Vision can't read cards
**Solution**:
- Ensure poker client has high-contrast cards
- Increase screen resolution
- Adjust capture region to exclude overlapping UI elements
- Try different poker clients

### Issue: GTO data missing
**Solution**:
- Manually download from GTOBase/GTOwizard
- Or create simplified ranges (see Week 3, Day 1-2)
- Ping me for pre-compiled data files

### Issue: Database locked error
**Solution**:
```python
# Use WAL mode for concurrent reads/writes
conn = sqlite3.connect("poker.db")
conn.execute("PRAGMA journal_mode=WAL")
```

### Issue: WebSocket disconnects frequently
**Solution**:
- Add ping/pong heartbeat:
```javascript
setInterval(() => ws.send(JSON.stringify({type: 'ping'})), 30000);
```

---

## Performance Optimization

### If latency >3 seconds:
1. **Profile with**:
```python
import cProfile
cProfile.run('assistant.process_frame()', 'profile.stats')

import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(10)
```

2. **Common bottlenecks**:
   - FastVLM inference: Try quantization (int8/int4)
   - Screen capture: Reduce capture frequency
   - LLM timeout: Reduce from 5s to 3s

### If memory >500MB:
1. **Profile with**:
```python
import tracemalloc
tracemalloc.start()
# ... run application
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

2. **Common issues**:
   - FastVLM model not unloaded
   - Image buffers not cleared
   - GTO cache too large (reduce granularity)

---

## Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Claude Code CLI installed
- [ ] FastVLM model downloaded (~500MB)
- [ ] GTO data downloaded (~100MB)
- [ ] API keys configured (.env)
- [ ] Dependencies installed (requirements.txt)
- [ ] Database initialized (poker.db)
- [ ] Logs directory created
- [ ] First-time region selection completed
- [ ] Browser opens automatically to localhost:8080
- [ ] Test with real poker game (20 hands)
- [ ] Verify latency <3s
- [ ] Verify no crashes
- [ ] Verify logs are written

---

## Next Steps After MVP

### Phase 2: Windows/Linux Support
- Implement win32gui (Windows)
- Implement X11/Wayland (Linux)
- Cross-platform testing

### Phase 3: Tournament Mode
- Add ICM calculations
- Bubble factor adjustments
- Tournament stage detection

### Phase 4: Advanced Features
- HUD overlay (transparent window)
- Hand history export
- Player profiling dashboard

---

## Support & Resources

- **Documentation**: See ARCHITECTURE.md, PRD.md, IMPLEMENTATION.md
- **Philosophy**: See PHILOSOPHY_PHASE4.md
- **GPA Methodology**: See GPA/Grounded Progressive Architecture.md
- **FastVLM Docs**: ml-fastvlm/README.md
- **Issues**: GitHub Issues (create if blocked)

---

**Status**: Implementation instructions complete
**Estimated Effort**: 7 weeks (1 developer, full-time)
**Risk Level**: Medium (FastVLM accuracy unknown until tested)

Good luck building! 🚀
