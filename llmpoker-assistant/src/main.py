"""
LLMPoker Assistant - Main Application

Entry point for the poker decision co-pilot application.
"""

import asyncio
import logging
import signal
import sys
import webbrowser
from typing import Optional
import time

# Import all modules
from src.utils.logger import setup_logging
from src.utils.config import get_config
from src.utils.metrics import PerformanceMetrics

from src.capture.screen_capture import ScreenCapture
from src.capture.region_selector import RegionSelector, load_saved_region, save_region

from src.vision.fastvlm_inference import FastVLMInference

from src.gto.decision_engine import GTODecisionEngine

from src.llm.orchestrator import LLMOrchestrator

from src.state.state_manager import GameStateManager

from src.persistence.database import Database

from src.api.server import (
    app,
    send_game_state_update,
    send_recommendation,
    send_system_alert,
)

import uvicorn

logger = logging.getLogger(__name__)


class LLMPokerAssistant:
    """Main application controller."""

    def __init__(self):
        """Initialize all components."""
        # Load configuration
        self.config = get_config()

        # Setup logging
        setup_logging(
            log_dir=self.config.get("logging.log_dir", "logs"),
            log_level=self.config.get("logging.level", "INFO"),
        )

        logger.info("=" * 60)
        logger.info("LLMPoker Assistant Starting")
        logger.info("=" * 60)

        # Initialize metrics
        self.metrics = PerformanceMetrics()

        # Screen capture (initialized after region selection)
        self.capture: Optional[ScreenCapture] = None

        # Vision
        model_path = self.config.get("vision.model_path", "data/models/fastvlm-0.5b")
        logger.info(f"Loading FastVLM model from {model_path}...")
        try:
            self.vision = FastVLMInference(model_path)
            logger.info("✓ FastVLM model loaded")
        except Exception as e:
            logger.error(f"Failed to load FastVLM: {e}")
            logger.warning("Vision module disabled")
            self.vision = None

        # GTO Engine
        gto_path = self.config.get("gto.data_path", "data/gto")
        logger.info(f"Loading GTO data from {gto_path}...")
        try:
            self.gto = GTODecisionEngine(gto_path)
            logger.info("✓ GTO engine loaded")
        except Exception as e:
            logger.error(f"Failed to load GTO data: {e}")
            logger.warning("GTO engine disabled")
            self.gto = None

        # LLM Orchestrator
        timeout = self.config.get("llm.timeout_seconds", 5)
        self.llm = LLMOrchestrator(timeout=timeout)
        logger.info(f"✓ LLM orchestrator initialized")
        logger.info(f"  Providers: {self.llm.get_provider_status()}")

        # State Manager
        confidence_threshold = self.config.get("vision.confidence_threshold", 0.70)
        self.state_manager = GameStateManager(confidence_threshold=confidence_threshold)
        logger.info(f"✓ State manager initialized (threshold={confidence_threshold})")

        # Database
        db_path = self.config.get("database.path", "data/database/poker.db")
        self.db = Database(db_path)
        logger.info(f"✓ Database initialized")

        # Create session
        asyncio.run(self.db.create_session(self.state_manager.get_session_id()))

        # Running flag
        self.running = False

        logger.info("✓ All components initialized")

    async def run(self):
        """Main application loop."""
        self.running = True

        try:
            # 1. Select poker window region
            region = await self._select_region()
            if not region:
                logger.error("Region selection failed")
                return

            # 2. Initialize screen capture
            self.capture = ScreenCapture(
                region,
                diff_threshold=self.config.get("capture.diff_threshold", 0.05),
            )

            # 3. Start API server (non-blocking)
            asyncio.create_task(self._start_api_server())

            # Wait for server to start
            await asyncio.sleep(2)

            # 4. Open browser
            self._open_browser()

            # 5. Main processing loop
            await self._main_loop()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await self._shutdown()

    async def _select_region(self) -> Optional[dict]:
        """Select poker window region (load saved or prompt user)."""
        # Try to load saved region
        region = load_saved_region()

        if region:
            logger.info(f"Loaded saved region: {region}")
            # TODO: Add confirmation prompt
            return region

        # No saved region, prompt user
        logger.info("No saved region found. Launching region selector...")

        try:
            selector = RegionSelector()
            region = selector.select_region()

            # Save for next time
            save_region(region)

            return region

        except Exception as e:
            logger.error(f"Region selection error: {e}")
            return None

    async def _start_api_server(self):
        """Start FastAPI server."""
        host = self.config.get("api.host", "127.0.0.1")
        port = self.config.get("api.port", 8080)

        logger.info(f"Starting API server on {host}:{port}")

        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)

        await server.serve()

    def _open_browser(self):
        """Open browser to dashboard."""
        host = self.config.get("api.host", "127.0.0.1")
        port = self.config.get("api.port", 8080)
        url = f"http://{host}:{port}"

        logger.info(f"Opening browser to {url}")

        try:
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")
            logger.info(f"Please open manually: {url}")

    async def _main_loop(self):
        """Main processing loop."""
        logger.info("Starting main processing loop")

        check_interval = self.config.get("capture.check_interval_ms", 100) / 1000  # Convert to seconds

        while self.running:
            try:
                # Check for screen changes
                if self.capture and self.capture.check_for_changes():
                    await self._process_frame()

                # Sleep
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await send_system_alert(f"Error: {str(e)}", "error")

    async def _process_frame(self):
        """Process a single frame through the entire pipeline."""
        start_time = time.time()

        self.metrics.increment_frame_count()

        # 1. Capture frame
        frame = self.capture.capture_frame()
        if not frame:
            logger.warning("Frame capture failed")
            return

        # 2. Vision extraction
        if not self.vision:
            logger.warning("Vision module not available")
            return

        vision_start = time.time()
        vision_data = self.vision.extract_game_state(frame)
        vision_latency = (time.time() - vision_start) * 1000
        self.metrics.record_vision_latency(vision_latency)

        # 3. Validate and process state
        is_confident, confidence, game_state = self.state_manager.process_vision_output(
            vision_data
        )

        if not is_confident:
            self.metrics.increment_low_confidence()
            await send_system_alert(
                f"Low confidence ({confidence:.0%}) - verify game state", "warning"
            )
            return

        # 4. Send game state update to UI
        await send_game_state_update(vision_data, confidence)

        self.metrics.increment_decision_count()

        # 5. GTO baseline
        if not self.gto:
            logger.warning("GTO engine not available")
            return

        gto_start = time.time()
        gto_action = self.gto.get_recommendation(
            position=game_state.position,
            hole_cards=game_state.hole_cards,
            board=game_state.board,
            pot=game_state.pot,
            stack=game_state.your_stack,
        )
        gto_latency = (time.time() - gto_start) * 1000
        self.metrics.record_gto_latency(gto_latency)

        # 6. LLM reasoning
        hand_history = await self.db.get_recent_hands(
            self.state_manager.get_session_id(), limit=5
        )
        session_stats = await self.db.get_session_stats(self.state_manager.get_session_id())

        llm_start = time.time()
        recommendation = self.llm.get_recommendation(
            game_state=vision_data,
            gto_baseline=gto_action.dict(),
            hand_history=hand_history,
            session_stats=session_stats,
        )
        llm_latency = (time.time() - llm_start) * 1000
        self.metrics.record_llm_latency(llm_latency)

        if recommendation.fallback_used:
            self.metrics.increment_llm_fallback()

        # 7. Send recommendation to UI
        await send_recommendation(recommendation.dict())

        # 8. Log decision
        total_latency = int((time.time() - start_time) * 1000)
        self.metrics.record_total_latency(total_latency)

        await self.db.log_decision(
            session_id=self.state_manager.get_session_id(),
            hand_number=self.state_manager.get_hand_number(),
            game_state=vision_data,
            gto_action=gto_action.dict(),
            recommendation=recommendation.dict(),
            vision_confidence=confidence,
            latency_ms=total_latency,
        )

        logger.info(
            f"Decision #{self.state_manager.get_hand_number()}: "
            f"{recommendation.action} "
            f"[{recommendation.confidence:.0%}] "
            f"({total_latency}ms)"
        )

    async def _shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down...")

        self.running = False

        # Log final metrics
        self.metrics.log_stats()

        # End session
        if self.db and self.state_manager:
            await self.db.end_session(self.state_manager.get_session_id())

        # Close resources
        if self.capture:
            self.capture.close()

        if self.vision:
            self.vision.close()

        logger.info("Shutdown complete")


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    sys.exit(0)


def main():
    """Entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run application
    assistant = LLMPokerAssistant()

    # Run async main loop
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
