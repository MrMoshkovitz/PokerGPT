"""
Database Module

SQLite database for hand history, player profiles, and session tracking.
"""

import sqlite3
import aiosqlite
import os
import json
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for poker data."""

    def __init__(self, db_path: str = "data/database/poker.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._create_schema()

        logger.info(f"Database initialized: {db_path}")

    def _create_schema(self):
        """Create database schema if not exists."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hands table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                hand_number INTEGER,

                -- Game state
                position TEXT,
                hole_cards TEXT,
                board TEXT,
                pot REAL,
                stack REAL,

                -- Recommendations
                gto_action TEXT,
                gto_sizing REAL,
                gto_confidence REAL,
                llm_action TEXT,
                llm_amount REAL,
                llm_confidence REAL,
                llm_reasoning TEXT,
                llm_provider TEXT,

                -- Outcome
                action_taken TEXT,
                outcome TEXT,
                amount_won REAL,

                -- Metadata
                vision_confidence REAL,
                latency_ms INTEGER
            )
        """)

        # Player profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_profiles (
                player_id TEXT PRIMARY KEY,
                hands_observed INTEGER DEFAULT 0,
                vpip_percent REAL DEFAULT 0.0,
                pfr_percent REAL DEFAULT 0.0,
                aggression_factor REAL DEFAULT 0.0,
                showdown_hands TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                hands_played INTEGER DEFAULT 0,
                win_loss REAL DEFAULT 0.0,
                avg_latency_ms INTEGER DEFAULT 0
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hands_session ON hands(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hands_timestamp ON hands(timestamp)")

        conn.commit()
        conn.close()

        logger.info("✓ Database schema created/verified")

    async def log_decision(
        self,
        session_id: str,
        hand_number: int,
        game_state: Dict[str, Any],
        gto_action: Dict[str, Any],
        recommendation: Dict[str, Any],
        vision_confidence: float,
        latency_ms: int,
    ):
        """
        Log a poker decision to database.

        Args:
            session_id: Current session ID
            hand_number: Hand number in session
            game_state: Game state dict
            gto_action: GTO baseline
            recommendation: LLM recommendation
            vision_confidence: Vision confidence score
            latency_ms: Processing latency
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO hands (
                    session_id, hand_number, position, hole_cards, board, pot, stack,
                    gto_action, gto_sizing, gto_confidence,
                    llm_action, llm_amount, llm_confidence, llm_reasoning, llm_provider,
                    vision_confidence, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    hand_number,
                    game_state.get("position"),
                    json.dumps(game_state.get("hole_cards", [])),
                    json.dumps(game_state.get("board", [])),
                    game_state.get("pot", 0),
                    game_state.get("your_stack", 0),
                    gto_action.get("action"),
                    gto_action.get("sizing"),
                    gto_action.get("confidence"),
                    recommendation.get("action"),
                    recommendation.get("amount"),
                    recommendation.get("confidence"),
                    recommendation.get("reasoning"),
                    recommendation.get("llm_provider"),
                    vision_confidence,
                    latency_ms,
                ),
            )
            await db.commit()

        logger.debug(f"Decision logged: session={session_id}, hand={hand_number}")

    async def get_recent_hands(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent hands from current session.

        Args:
            session_id: Session ID
            limit: Number of hands to retrieve

        Returns:
            List of hand dicts
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                """
                SELECT * FROM hands
                WHERE session_id = ?
                ORDER BY hand_number DESC
                LIMIT ?
                """,
                (session_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()

                hands = []
                for row in rows:
                    hands.append(dict(row))

                return hands

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get session statistics.

        Args:
            session_id: Session ID

        Returns:
            Stats dict with hands_played, vpip, win_rate, etc.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Count hands
            async with db.execute(
                "SELECT COUNT(*) FROM hands WHERE session_id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                hands_played = row[0] if row else 0

            # Calculate VPIP (hands where not folded preflop)
            # Placeholder - would need action_taken field
            vpip = 0.0

            # Win rate
            # Placeholder - would need outcome tracking
            win_rate = 0.0

            return {
                "hands_played": hands_played,
                "vpip": vpip,
                "win_rate": win_rate,
            }

    async def create_session(self, session_id: str):
        """Create a new session record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, start_time)
                VALUES (?, ?)
                """,
                (session_id, datetime.now().isoformat()),
            )
            await db.commit()

        logger.info(f"Session created: {session_id}")

    async def end_session(self, session_id: str, win_loss: float = 0.0):
        """End a session and update stats."""
        async with aiosqlite.connect(self.db_path) as db:
            # Count hands
            async with db.execute(
                "SELECT COUNT(*) FROM hands WHERE session_id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                hands_played = row[0] if row else 0

            # Calculate average latency
            async with db.execute(
                "SELECT AVG(latency_ms) FROM hands WHERE session_id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                avg_latency = int(row[0]) if row and row[0] else 0

            # Update session
            await db.execute(
                """
                UPDATE sessions
                SET end_time = ?, hands_played = ?, win_loss = ?, avg_latency_ms = ?
                WHERE session_id = ?
                """,
                (datetime.now().isoformat(), hands_played, win_loss, avg_latency, session_id),
            )
            await db.commit()

        logger.info(f"Session ended: {session_id} ({hands_played} hands, ${win_loss:.2f})")
