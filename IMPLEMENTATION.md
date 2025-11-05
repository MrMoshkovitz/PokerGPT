# LLMPoker Assistant - Implementation Specification

**Version**: 1.0 MVP
**Tech Stack**: Python 3.10+, FastVLM, Claude Code CLI, FastAPI, SQLite
**Target Platform**: macOS 12.0+
**Status**: Phase 5 - Ready for Implementation

---

## 1. Project Structure

```
llmpoker-assistant/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── capture/
│   │   ├── __init__.py
│   │   ├── screen_capture.py      # Screen recording (mss)
│   │   └── region_selector.py     # UI for region selection
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── fastvlm_inference.py   # FastVLM model integration
│   │   ├── game_state_extractor.py # Parse vision output → game state
│   │   └── confidence_validator.py # 3-frame consistency checks
│   ├── gto/
│   │   ├── __init__.py
│   │   ├── data_loader.py         # Download & load GTO data
│   │   ├── strategy_cache.py      # In-memory GTO lookup
│   │   └── decision_engine.py     # GTO baseline recommendations
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── claude_cli.py          # Claude Code CLI executor
│   │   ├── openai_fallback.py     # OpenAI API fallback
│   │   ├── gemini_fallback.py     # Gemini CLI fallback
│   │   ├── prompt_builder.py      # Construct LLM prompts
│   │   └── response_parser.py     # Parse LLM responses
│   ├── state/
│   │   ├── __init__.py
│   │   ├── game_state.py          # Game state data model
│   │   ├── state_manager.py       # State buffer & validation
│   │   └── temporal_buffer.py     # 3-frame history
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite connection & schema
│   │   ├── hand_history.py        # Hand logging
│   │   └── player_profiles.py     # Player stats tracking
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py              # FastAPI server
│   │   ├── websocket.py           # WebSocket handler
│   │   └── routes.py              # REST endpoints
│   ├── ui/
│   │   ├── static/
│   │   │   ├── index.html         # Dashboard UI
│   │   │   ├── style.css          # Styling
│   │   │   └── app.js             # WebSocket client
│   │   └── templates/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py              # Structured logging
│   │   ├── config.py              # Configuration management
│   │   └── metrics.py             # Performance tracking
│   └── models/
│       ├── __init__.py
│       ├── recommendation.py      # Recommendation data model
│       └── enums.py               # Action types, positions, etc.
├── tests/
│   ├── test_vision.py
│   ├── test_gto.py
│   ├── test_llm.py
│   └── test_integration.py
├── data/
│   ├── gto/                       # GTO strategy files (downloaded)
│   ├── models/                    # FastVLM model weights
│   └── database/                  # SQLite database
├── logs/                          # Application logs
├── config/
│   └── default_config.yaml        # Default configuration
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
├── README.md                      # User documentation
└── .env.example                   # Environment variables template
```

---

## 2. Core Modules

### 2.1 Screen Capture Module

**File**: `src/capture/screen_capture.py`

```python
import mss
import numpy as np
from PIL import Image
import logging

class ScreenCapture:
    """Event-driven screen capture for poker window."""

    def __init__(self, region: dict):
        """
        Initialize screen capture.

        Args:
            region: {"left": x, "top": y, "width": w, "height": h}
        """
        self.region = region
        self.sct = mss.mss()
        self.last_frame_hash = None
        self.capture_threshold = 0.05  # 5% pixel diff

    def check_for_changes(self) -> bool:
        """Quick diff check (100ms intervals)."""
        screenshot = self.sct.grab(self.region)
        current_hash = hash(bytes(screenshot.rgb))

        if self.last_frame_hash is None:
            self.last_frame_hash = current_hash
            return True

        diff_ratio = self._calculate_diff(current_hash, self.last_frame_hash)
        self.last_frame_hash = current_hash

        return diff_ratio > self.capture_threshold

    def capture_frame(self) -> Image:
        """Capture full-resolution screenshot."""
        screenshot = self.sct.grab(self.region)
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    def _calculate_diff(self, hash1, hash2) -> float:
        """Calculate pixel difference ratio."""
        # Simplified: In production, use actual pixel comparison
        return abs(hash1 - hash2) / (2**64)  # Normalize hash diff
```

**File**: `src/capture/region_selector.py`

```python
import tkinter as tk
from typing import Dict

class RegionSelector:
    """Interactive region selection UI."""

    def select_region(self) -> Dict[str, int]:
        """
        Launch UI for user to drag-select poker window region.

        Returns:
            {"left": x, "top": y, "width": w, "height": h}
        """
        # Tkinter-based drag-to-select overlay
        # Returns coordinates of selected rectangle
        pass
```

---

### 2.2 Vision Module

**File**: `src/vision/fastvlm_inference.py`

```python
import torch
from PIL import Image
from llava.model.builder import load_pretrained_model
from llava.conversation import conv_templates
import logging

class FastVLMInference:
    """FastVLM-0.5B model for poker game state extraction."""

    def __init__(self, model_path: str):
        """Load FastVLM model."""
        self.tokenizer, self.model, self.image_processor, self.context_len = \
            load_pretrained_model(
                model_path=model_path,
                model_base=None,
                model_name="fastvlm-0.5b"
            )
        self.model.eval()

    def extract_game_state(self, image: Image) -> dict:
        """
        Extract poker game state from screenshot.

        Args:
            image: PIL Image of poker table

        Returns:
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
        """
        prompt = """Analyze this poker game screenshot and extract:
1. Your hole cards (2 cards, format: Ah, Kd)
2. Community cards (0-5 cards)
3. Pot size (numeric value)
4. Your stack size (numeric value)
5. Your position (BTN, CO, MP, UTG, SB, BB)

Respond in JSON format with confidence scores (0-1) for each element."""

        # Prepare inputs
        conv = conv_templates["qwen_2"].copy()
        conv.append_message(conv.roles[0], prompt)
        conv.append_message(conv.roles[1], None)
        prompt_formatted = conv.get_prompt()

        # Inference
        inputs = self.tokenizer([prompt_formatted], return_tensors="pt")
        image_tensor = self.image_processor.preprocess(image, return_tensors="pt")["pixel_values"]

        with torch.no_grad():
            output_ids = self.model.generate(
                inputs.input_ids,
                images=image_tensor,
                max_new_tokens=512,
                use_cache=True
            )

        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # Parse JSON response
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        """Parse FastVLM JSON response."""
        import json
        # Robust JSON extraction from LLM response
        # Handle cases where LLM wraps JSON in markdown ```json blocks
        pass
```

**File**: `src/vision/confidence_validator.py`

```python
from typing import List, Dict
import logging

class ConfidenceValidator:
    """3-frame temporal consistency validation."""

    def __init__(self, buffer_size: int = 3, threshold: float = 0.70):
        self.buffer_size = buffer_size
        self.threshold = threshold
        self.state_buffer: List[Dict] = []

    def validate(self, game_state: Dict) -> tuple[bool, float]:
        """
        Validate game state confidence.

        Returns:
            (is_confident, aggregate_confidence)
        """
        self.state_buffer.append(game_state)
        if len(self.state_buffer) > self.buffer_size:
            self.state_buffer.pop(0)

        # Check temporal consistency
        if len(self.state_buffer) < 2:
            return True, self._aggregate_confidence(game_state)

        consistency_score = self._check_consistency()
        aggregate_confidence = self._aggregate_confidence(game_state)

        # Penalize confidence if inconsistent across frames
        final_confidence = aggregate_confidence * consistency_score

        return final_confidence >= self.threshold, final_confidence

    def _check_consistency(self) -> float:
        """Check if last N frames agree on game state."""
        # Compare hole cards, board progression, pot increases
        # Penalize if cards change unexpectedly
        pass

    def _aggregate_confidence(self, state: Dict) -> float:
        """Average confidence across all elements."""
        confidences = state.get("confidence", {}).values()
        return sum(confidences) / len(confidences) if confidences else 0.0
```

---

### 2.3 GTO Engine Module

**File**: `src/gto/strategy_cache.py`

```python
import pickle
from typing import Dict, List
import logging

class GTOStrategyCache:
    """In-memory GTO strategy lookup."""

    def __init__(self):
        self.preflop_ranges: Dict = {}
        self.postflop_buckets: Dict = {}
        self.loaded = False

    def load_from_disk(self, data_path: str):
        """Load GTO data into memory (~100MB)."""
        logging.info(f"Loading GTO data from {data_path}")

        with open(f"{data_path}/preflop_ranges.pkl", "rb") as f:
            self.preflop_ranges = pickle.load(f)

        with open(f"{data_path}/postflop_buckets.pkl", "rb") as f:
            self.postflop_buckets = pickle.load(f)

        self.loaded = True
        logging.info("GTO data loaded successfully")

    def get_action(self,
                   position: str,
                   hole_cards: List[str],
                   board: List[str],
                   pot: float,
                   stack: float) -> Dict:
        """
        Get GTO baseline recommendation.

        Returns:
            {
                "action": "RAISE",
                "sizing": 450,  # exact amount or % pot
                "confidence": 0.85,
                "range": "top 15%"
            }
        """
        if not board:  # Preflop
            return self._get_preflop_action(position, hole_cards)
        else:  # Postflop
            return self._get_postflop_action(position, hole_cards, board, pot, stack)

    def _get_preflop_action(self, position: str, hole_cards: List[str]) -> Dict:
        """Preflop GTO range lookup."""
        hand_key = self._normalize_hand(hole_cards)
        range_data = self.preflop_ranges.get(position, {})
        return range_data.get(hand_key, {"action": "FOLD", "sizing": 0})

    def _get_postflop_action(self, position, hole_cards, board, pot, stack) -> Dict:
        """Postflop GTO bucket lookup."""
        # Bucket hand by strength
        hand_strength = self._calculate_hand_strength(hole_cards, board)
        board_texture = self._classify_board_texture(board)
        spr = stack / pot

        bucket_key = (hand_strength, board_texture, self._bucket_spr(spr))
        return self.postflop_buckets.get(bucket_key, {"action": "CHECK", "sizing": 0})

    def _calculate_hand_strength(self, hole_cards, board) -> str:
        """Bucket: NUTS, STRONG, MEDIUM, WEAK, BLUFF."""
        # Use poker hand evaluator (e.g., treys library)
        pass

    def _classify_board_texture(self, board) -> str:
        """Classify: WET, DRY, PAIRED, COORDINATED."""
        pass
```

---

### 2.4 LLM Orchestrator Module

**File**: `src/llm/claude_cli.py`

```python
import subprocess
import json
import logging
from typing import Dict, Optional

class ClaudeCLI:
    """Claude Code CLI executor with ultrathink."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def get_recommendation(self, prompt: str) -> Optional[Dict]:
        """
        Execute Claude Code CLI with extended thinking.

        Returns:
            {
                "action": "RAISE",
                "amount": 450,
                "confidence": 0.87,
                "reasoning": "Strong draw (OESD+FD), position advantage..."
            }
        """
        try:
            result = subprocess.run(
                ["claude", "-p", f"--extended-thinking {prompt}"],
                timeout=self.timeout,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logging.error(f"Claude CLI error: {result.stderr}")
                return None

            return self._parse_response(result.stdout)

        except subprocess.TimeoutExpired:
            logging.warning(f"Claude CLI timeout after {self.timeout}s")
            return None
        except Exception as e:
            logging.error(f"Claude CLI exception: {e}")
            return None

    def _parse_response(self, output: str) -> Dict:
        """Parse Claude CLI JSON output."""
        # Extract JSON from response (handle markdown wrappers)
        pass
```

**File**: `src/llm/prompt_builder.py`

```python
from typing import Dict, List
import json

class PromptBuilder:
    """Construct rich context prompts for LLM reasoning."""

    @staticmethod
    def build_decision_prompt(
        game_state: Dict,
        gto_baseline: Dict,
        hand_history: List[Dict],
        session_stats: Dict
    ) -> str:
        """
        Build comprehensive prompt for LLM decision-making.

        Template includes:
        - Current decision point
        - GTO baseline recommendation
        - Recent hand history (last 5-10 hands)
        - Session statistics
        - Player patterns
        """
        prompt = f"""You are a professional poker advisor. Analyze this decision point and provide optimal action.

**Current Situation:**
- Your Hand: {game_state['hole_cards']}
- Board: {game_state.get('board', 'Preflop')}
- Pot: ${game_state['pot']}
- Your Stack: ${game_state['your_stack']}
- Position: {game_state['position']}

**GTO Baseline:**
{json.dumps(gto_baseline, indent=2)}

**Recent Hand History (last 5 hands):**
{self._format_hand_history(hand_history)}

**Session Statistics:**
- Hands Played: {session_stats.get('hands_played', 0)}
- VPIP: {session_stats.get('vpip', 0)}%
- Win Rate: {session_stats.get('win_rate', 0)}/hour

**Task:**
Provide a recommendation in JSON format:
{{
    "action": "FOLD|CALL|RAISE",
    "amount": <numeric amount if RAISE>,
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
4. Opponent tendencies (if observable)
5. Stack sizes and commitment
6. Board texture and equity distribution
"""
        return prompt

    @staticmethod
    def _format_hand_history(history: List[Dict]) -> str:
        """Format recent hands for context."""
        formatted = []
        for h in history[-5:]:
            formatted.append(
                f"Hand #{h['hand_num']}: {h['hole_cards']} → {h['action']} → {h['outcome']}"
            )
        return "\n".join(formatted)
```

---

### 2.5 API Server Module

**File**: `src/api/server.py`

```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging

app = FastAPI(title="LLMPoker Assistant API")

# Mount static files (UI)
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main dashboard."""
    with open("src/ui/static/index.html") as f:
        return f.read()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()

    try:
        while True:
            # Send game state updates and recommendations
            data = await get_latest_recommendation()  # From game loop
            await websocket.send_json(data)

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

**File**: `src/ui/static/app.js`

```javascript
// WebSocket client for real-time dashboard updates

const ws = new WebSocket("ws://localhost:8080/ws");

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === "game_state_update") {
        updateGameState(data.state);
        updateConfidenceMeter(data.vision_confidence);
    } else if (data.type === "recommendation") {
        displayRecommendation(data);
    } else if (data.type === "system_alert") {
        showAlert(data.message, data.level);
    }
};

function displayRecommendation(rec) {
    document.getElementById("action").innerText = rec.action;
    document.getElementById("confidence").value = rec.confidence;
    document.getElementById("reasoning").innerText = rec.reasoning;

    // Color-code by confidence
    const actionElement = document.getElementById("action");
    if (rec.confidence > 0.8) {
        actionElement.className = "high-confidence";
    } else if (rec.confidence > 0.6) {
        actionElement.className = "medium-confidence";
    } else {
        actionElement.className = "low-confidence";
    }
}
```

---

### 2.6 Main Application Loop

**File**: `src/main.py`

```python
import asyncio
import logging
from capture.screen_capture import ScreenCapture
from vision.fastvlm_inference import FastVLMInference
from vision.confidence_validator import ConfidenceValidator
from gto.strategy_cache import GTOStrategyCache
from llm.claude_cli import ClaudeCLI
from llm.openai_fallback import OpenAIFallback
from llm.prompt_builder import PromptBuilder
from persistence.database import Database
from api.server import app
import uvicorn

class LLMPokerAssistant:
    """Main application controller."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Initialize components
        self.capture = None  # Initialized after region selection
        self.vision = FastVLMInference(model_path="data/models/fastvlm-0.5b")
        self.validator = ConfidenceValidator()
        self.gto = GTOStrategyCache()
        self.gto.load_from_disk("data/gto")
        self.llm_primary = ClaudeCLI(timeout=5)
        self.llm_fallback = OpenAIFallback()
        self.db = Database("data/database/poker.db")

    def setup_logging(self):
        """Configure structured logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/app.log'),
                logging.StreamHandler()
            ]
        )

    async def run(self):
        """Main application loop."""
        # 1. Select poker window region
        region = self.select_region()
        self.capture = ScreenCapture(region)

        # 2. Start API server (non-blocking)
        asyncio.create_task(self.start_api_server())

        # 3. Main game loop
        while True:
            if self.capture.check_for_changes():
                await self.process_frame()
            await asyncio.sleep(0.1)  # 100ms check interval

    async def process_frame(self):
        """Process single frame through entire pipeline."""
        # Capture
        frame = self.capture.capture_frame()

        # Vision
        game_state = self.vision.extract_game_state(frame)

        # Validate confidence
        is_confident, confidence = self.validator.validate(game_state)

        if not is_confident:
            self.send_to_ui({
                "type": "system_alert",
                "level": "warning",
                "message": f"Low confidence ({confidence:.0%}) - verify manually"
            })
            return

        # GTO baseline
        gto_action = self.gto.get_action(
            position=game_state['position'],
            hole_cards=game_state['hole_cards'],
            board=game_state.get('board', []),
            pot=game_state['pot'],
            stack=game_state['your_stack']
        )

        # LLM reasoning
        hand_history = self.db.get_recent_hands(limit=5)
        session_stats = self.db.get_session_stats()

        prompt = PromptBuilder.build_decision_prompt(
            game_state, gto_action, hand_history, session_stats
        )

        recommendation = self.llm_primary.get_recommendation(prompt)

        if not recommendation:  # Fallback
            self.logger.warning("Claude failed, falling back to OpenAI")
            recommendation = self.llm_fallback.get_recommendation(prompt)
            recommendation['fallback_used'] = True

        # Send to UI
        self.send_to_ui({
            "type": "recommendation",
            **recommendation
        })

        # Log decision
        self.db.log_decision(game_state, gto_action, recommendation)

    async def start_api_server(self):
        """Start FastAPI server."""
        config = uvicorn.Config(app, host="127.0.0.1", port=8080, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    assistant = LLMPokerAssistant()
    asyncio.run(assistant.run())
```

---

## 3. Database Schema

**File**: `src/persistence/database.py`

```sql
-- SQLite schema

CREATE TABLE IF NOT EXISTS hands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    hand_number INTEGER,

    -- Game state
    position TEXT,
    hole_cards TEXT,  -- JSON array
    board TEXT,       -- JSON array
    pot REAL,
    stack REAL,

    -- Recommendation
    gto_action TEXT,
    gto_sizing REAL,
    llm_action TEXT,
    llm_amount REAL,
    llm_confidence REAL,
    llm_reasoning TEXT,
    llm_provider TEXT,  -- claude/openai/gemini

    -- Outcome
    action_taken TEXT,
    outcome TEXT,  -- won/lost/folded
    amount_won REAL,

    -- Metadata
    vision_confidence REAL,
    latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS player_profiles (
    player_id TEXT PRIMARY KEY,
    hands_observed INTEGER DEFAULT 0,
    vpip_percent REAL,
    pfr_percent REAL,
    aggression_factor REAL,
    showdown_hands TEXT,  -- JSON array
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    hands_played INTEGER DEFAULT 0,
    win_loss REAL DEFAULT 0.0,
    avg_latency_ms INTEGER
);

CREATE INDEX idx_hands_session ON hands(session_id);
CREATE INDEX idx_hands_timestamp ON hands(timestamp);
```

---

## 4. Configuration

**File**: `config/default_config.yaml`

```yaml
# LLMPoker Assistant Configuration

capture:
  check_interval_ms: 100
  diff_threshold: 0.05

vision:
  model_path: "data/models/fastvlm-0.5b"
  confidence_threshold: 0.70
  temporal_buffer_size: 3

gto:
  data_path: "data/gto"
  preflop_ranges_file: "preflop_ranges.pkl"
  postflop_buckets_file: "postflop_buckets.pkl"

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

database:
  path: "data/database/poker.db"

logging:
  level: "INFO"
  log_dir: "logs"
  max_file_size_mb: 100
  retention_days: 30
```

---

## 5. Dependencies

**File**: `requirements.txt`

```
# Core
python>=3.10

# Vision
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
pillow>=9.5.0

# LLaVA / FastVLM
git+https://github.com/MrMoshkovitz/ml-fastvlm.git

# Screen capture
mss>=9.0.0
pyautogui>=0.9.54

# Web server
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
websockets>=11.0.0

# Database
aiosqlite>=0.19.0

# LLM clients
openai>=1.0.0
google-generativeai>=0.3.0

# Poker utilities
treys>=0.1.8  # Hand evaluator

# Utilities
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
numpy>=1.24.0
```

---

## 6. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [x] Project structure setup
- [ ] Screen capture module (mss integration)
- [ ] Region selector UI (tkinter)
- [ ] FastVLM model integration
- [ ] Basic vision inference
- [ ] SQLite database schema
- [ ] Structured logging

### Phase 2: GTO Engine (Week 2)
- [ ] Download open-source GTO data (GTOBase)
- [ ] Convert to pickle format
- [ ] In-memory cache implementation
- [ ] Preflop range lookup
- [ ] Postflop bucket system
- [ ] Hand strength calculator (treys)

### Phase 3: LLM Integration (Week 3)
- [ ] Claude Code CLI executor
- [ ] Prompt builder with rich context
- [ ] Response parser (JSON extraction)
- [ ] OpenAI fallback implementation
- [ ] Gemini fallback implementation
- [ ] Timeout and retry logic

### Phase 4: State Management (Week 4)
- [ ] Game state data model
- [ ] 3-frame temporal buffer
- [ ] Confidence validation
- [ ] Noise filtering logic
- [ ] State consistency checks

### Phase 5: Web UI (Week 5)
- [ ] FastAPI server setup
- [ ] WebSocket handler
- [ ] HTML/CSS dashboard
- [ ] JavaScript WebSocket client
- [ ] Real-time recommendation display
- [ ] Confidence meter UI

### Phase 6: Integration & Testing (Week 6)
- [ ] Main application loop
- [ ] Component integration
- [ ] End-to-end testing with real poker clients
- [ ] Performance benchmarking (latency, memory, CPU)
- [ ] Bug fixes and optimization

### Phase 7: Polish & Documentation (Week 7)
- [ ] User documentation (README)
- [ ] Configuration system
- [ ] Error handling improvements
- [ ] Logging enhancements
- [ ] First-time setup wizard

---

## 7. Testing Strategy

### Unit Tests
- Vision: Card recognition accuracy (mock FastVLM responses)
- GTO: Lookup correctness (known scenarios)
- LLM: Prompt construction, response parsing
- State: Temporal consistency validation

### Integration Tests
- Full pipeline: Screenshot → recommendation
- Fallback chain: Claude timeout → OpenAI
- Database: Hand logging and retrieval

### End-to-End Tests
- Run against 3 different poker clients
- 100-hand test session (no crashes)
- Latency measurement (95th percentile <3s)

### Performance Tests
- Memory usage (<500MB)
- CPU usage (<50% on M1/M2)
- GTO lookup speed (<1ms)

---

## 8. Deployment

### First-Time Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/llmpoker-assistant.git
cd llmpoker-assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download models and data
python scripts/download_assets.py

# 4. Configure environment
cp .env.example .env
# Edit .env with API keys

# 5. Run application
python src/main.py
```

### Running the Application

```bash
# Start application
python src/main.py

# Opens browser dashboard at http://localhost:8080
# 1. Select poker window region
# 2. Start playing poker
# 3. Recommendations appear in real-time
```

---

## 9. Monitoring & Observability

### Logs
- `logs/app.log`: All application logs
- `logs/decisions.jsonl`: Structured decision logs (one JSON per line)
- `logs/errors.log`: Error-level logs only

### Metrics (via dashboard)
- Average latency (last 20 decisions)
- Vision confidence trend
- LLM fallback rate
- Win/loss tracking

---

## 10. Future Enhancements (Technical Debt)

### Cross-Platform Support
- Windows: Use win32gui for window capture
- Linux: Use Xlib or Wayland APIs

### Tournament Support
- ICM calculations
- Bubble factor adjustments
- Tournament stage detection

### Multi-Table Support
- Multiple screen capture regions
- Parallel processing
- UI: Tabbed dashboard per table

### Advanced Features
- Custom FastVLM fine-tuning (poker-specific)
- HUD overlay (transparent window over poker client)
- Hand history export (PokerTracker format)
- Player profiling dashboard

---

**Status**: Phase 5 Complete - Implementation Specification Ready
**Next**: Phase 6 - Meta-Cognitive Review
