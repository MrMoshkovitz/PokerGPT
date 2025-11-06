"""
Performance Metrics

Track and report application performance metrics.
"""

import time
from typing import Dict, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Track performance metrics."""

    def __init__(self, window_size: int = 20):
        """
        Initialize metrics tracker.

        Args:
            window_size: Number of recent measurements to keep
        """
        self.window_size = window_size

        # Latency tracking (circular buffer)
        self.vision_latency: deque = deque(maxlen=window_size)
        self.gto_latency: deque = deque(maxlen=window_size)
        self.llm_latency: deque = deque(maxlen=window_size)
        self.total_latency: deque = deque(maxlen=window_size)

        # Counters
        self.frame_count = 0
        self.decision_count = 0
        self.low_confidence_count = 0
        self.llm_fallback_count = 0

        # Timestamps
        self.session_start_time = time.time()

    def record_vision_latency(self, latency_ms: float):
        """Record vision inference latency."""
        self.vision_latency.append(latency_ms)

    def record_gto_latency(self, latency_ms: float):
        """Record GTO lookup latency."""
        self.gto_latency.append(latency_ms)

    def record_llm_latency(self, latency_ms: float):
        """Record LLM reasoning latency."""
        self.llm_latency.append(latency_ms)

    def record_total_latency(self, latency_ms: float):
        """Record total pipeline latency."""
        self.total_latency.append(latency_ms)

    def increment_frame_count(self):
        """Increment frame processed count."""
        self.frame_count += 1

    def increment_decision_count(self):
        """Increment decision made count."""
        self.decision_count += 1

    def increment_low_confidence(self):
        """Increment low confidence count."""
        self.low_confidence_count += 1

    def increment_llm_fallback(self):
        """Increment LLM fallback count."""
        self.llm_fallback_count += 1

    def get_stats(self) -> Dict:
        """
        Get current performance statistics.

        Returns:
            Dict with all metrics
        """
        def avg(values):
            return sum(values) / len(values) if values else 0

        def percentile(values, p):
            if not values:
                return 0
            sorted_vals = sorted(values)
            idx = int(len(sorted_vals) * p)
            return sorted_vals[min(idx, len(sorted_vals) - 1)]

        session_duration = time.time() - self.session_start_time

        return {
            "session_duration_sec": session_duration,
            "frames_processed": self.frame_count,
            "decisions_made": self.decision_count,
            "low_confidence_count": self.low_confidence_count,
            "llm_fallback_count": self.llm_fallback_count,
            "latency": {
                "vision": {
                    "avg_ms": avg(self.vision_latency),
                    "p95_ms": percentile(self.vision_latency, 0.95),
                },
                "gto": {
                    "avg_ms": avg(self.gto_latency),
                    "p95_ms": percentile(self.gto_latency, 0.95),
                },
                "llm": {
                    "avg_ms": avg(self.llm_latency),
                    "p95_ms": percentile(self.llm_latency, 0.95),
                },
                "total": {
                    "avg_ms": avg(self.total_latency),
                    "p95_ms": percentile(self.total_latency, 0.95),
                },
            },
        }

    def log_stats(self):
        """Log current statistics."""
        stats = self.get_stats()

        logger.info("=== Performance Metrics ===")
        logger.info(f"Session duration: {stats['session_duration_sec']:.1f}s")
        logger.info(f"Frames processed: {stats['frames_processed']}")
        logger.info(f"Decisions made: {stats['decisions_made']}")
        logger.info(f"Low confidence: {stats['low_confidence_count']}")
        logger.info(f"LLM fallbacks: {stats['llm_fallback_count']}")
        logger.info(
            f"Latency (avg): "
            f"Vision={stats['latency']['vision']['avg_ms']:.0f}ms, "
            f"GTO={stats['latency']['gto']['avg_ms']:.0f}ms, "
            f"LLM={stats['latency']['llm']['avg_ms']:.0f}ms, "
            f"Total={stats['latency']['total']['avg_ms']:.0f}ms"
        )
        logger.info(
            f"Latency (p95): "
            f"Total={stats['latency']['total']['p95_ms']:.0f}ms"
        )

    def reset(self):
        """Reset all metrics."""
        self.vision_latency.clear()
        self.gto_latency.clear()
        self.llm_latency.clear()
        self.total_latency.clear()
        self.frame_count = 0
        self.decision_count = 0
        self.low_confidence_count = 0
        self.llm_fallback_count = 0
        self.session_start_time = time.time()
