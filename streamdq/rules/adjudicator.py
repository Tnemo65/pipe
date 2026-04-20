"""
Context-Aware Duplicate Adjudication.

Confidence-scored duplicate detection that replaces binary MD5 exact-match.
Part of Phase 1 (T1: Context-Aware Duplicate Adjudication, Day 4-13).

Confidence Formula:
  confidence = 0.5 * temporal_sim + 0.3 * source_diversity + 0.2 * fingerprint_stability

Where:
- temporal_sim: How close in time (1.0 if ≤5s, exponential decay to 0.0 at 300s)
- source_diversity: Same source/batch vs. different (1.0 same, 0.5 same source, 0.0 different)
- fingerprint_stability: Seen count (1.0 if ≥3x, 0.5 if 2x, 0.0 if 1x)

Thresholds:
- confidence > 0.7: HIGH severity violation (true duplicate)
- 0.4 < confidence ≤ 0.7: MEDIUM advisory (suspicious, not counted for precision)
- confidence ≤ 0.4: Suppress (likely false positive)

References:
- ENHANCEMENT_ROADMAP.md lines 294-322 (T1 specification)
- Dey (2001): Context taxonomy (temporal, source, entity)
- Serra et al. (2022): SLR on context-aware DQ (60-80% FP reduction via scoring)
"""
from __future__ import annotations
import math
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class DuplicateEvidence:
    """Evidence for a single fingerprint occurrence."""

    timestamp: datetime
    source_id: str
    batch_id: str | None
    kafka_offset: int | None = None

    def same_source(self, other: "DuplicateEvidence") -> bool:
        """Check if from same source."""
        return self.source_id == other.source_id

    def same_batch(self, other: "DuplicateEvidence") -> bool:
        """Check if from same batch (implies same source)."""
        return (self.source_id == other.source_id and
                self.batch_id is not None and
                self.batch_id == other.batch_id)


class ContextAwareDuplicateAdjudicator:
    """
    Stateful adjudicator for duplicate confidence scoring.

    Maintains history of fingerprint occurrences (timestamp, source, batch)
    and computes confidence scores based on temporal, source, and stability context.

    Usage:
        adjudicator = ContextAwareDuplicateAdjudicator()

        confidence = adjudicator.compute_confidence(
            fingerprint="abc123",
            timestamp=datetime.now(),
            source_id="nyc_taxi_replay_001",
            batch_id="batch_001",
            is_replay=False
        )

        if confidence > 0.7:
            # Emit HIGH violation
        elif confidence > 0.4:
            # Emit MEDIUM advisory
        else:
            # Suppress
    """

    def __init__(
        self,
        temporal_threshold_seconds: float = 5.0,
        temporal_decay_halflife: float = 300.0,
        window_seconds: int = 3600
    ):
        """
        Initialize adjudicator.

        Args:
            temporal_threshold_seconds: Events within this are considered immediate (temporal_sim = 1.0)
            temporal_decay_halflife: Time at which temporal_sim decays to 0.5
            window_seconds: How long to keep fingerprint history (for memory bounds)
        """
        self._temporal_threshold = temporal_threshold_seconds
        self._temporal_halflife = temporal_decay_halflife
        self._window_seconds = window_seconds

        # State: fingerprint → list of evidence
        self._history: dict[str, list[DuplicateEvidence]] = defaultdict(list)

    def compute_confidence(
        self,
        fingerprint: str,
        timestamp: datetime,
        source_id: str,
        batch_id: str | None = None,
        is_replay: bool = False,
        kafka_offset: int | None = None
    ) -> float:
        """
        Compute duplicate confidence for this occurrence.

        Args:
            fingerprint: MD5 hash of event key fields
            timestamp: Event arrival time
            source_id: Source identifier (e.g., "nyc_taxi_replay_001")
            batch_id: Batch identifier (None for streaming)
            is_replay: Whether this is a replay stream (from lineage metadata)
            kafka_offset: Kafka offset (for deduplication context)

        Returns:
            Confidence score 0.0-1.0
        """
        # Create evidence for current occurrence
        current = DuplicateEvidence(
            timestamp=timestamp,
            source_id=source_id,
            batch_id=batch_id,
            kafka_offset=kafka_offset
        )

        # Get historical occurrences (before adding current)
        history = self._history[fingerprint]

        # First-time occurrence: confidence = 0.0 (not a duplicate yet)
        if len(history) == 0:
            self._history[fingerprint].append(current)
            return 0.0

        # Find most recent occurrence
        most_recent = max(history, key=lambda e: e.timestamp)

        # Compute temporal similarity
        time_delta_seconds = (timestamp - most_recent.timestamp).total_seconds()
        if time_delta_seconds <= self._temporal_threshold:
            temporal_sim = 1.0
        else:
            # Exponential decay: temporal_sim = exp(-t / halflife)
            temporal_sim = math.exp(-time_delta_seconds / self._temporal_halflife)

        # Compute source diversity
        if most_recent.same_batch(current):
            source_diversity = 1.0  # Same source + batch (strongest signal)
        elif most_recent.same_source(current):
            source_diversity = 0.5  # Same source, different batch
        else:
            source_diversity = 0.0  # Different source (likely coincidence)

        # Compute fingerprint stability (seen count)
        seen_count = len(history) + 1  # +1 for current
        if seen_count >= 3:
            fingerprint_stability = 1.0  # Seen 3+ times, stable fingerprint
        elif seen_count == 2:
            fingerprint_stability = 0.5  # Seen 2x
        else:
            fingerprint_stability = 0.0  # First seen

        # Weighted confidence formula
        confidence = (
            0.5 * temporal_sim +
            0.3 * source_diversity +
            0.2 * fingerprint_stability
        )

        # Add current occurrence to history
        self._history[fingerprint].append(current)

        # Evict old entries (memory bound)
        self._evict_old_entries(timestamp)

        return min(1.0, max(0.0, confidence))  # Clamp to [0.0, 1.0]

    def _evict_old_entries(self, current_time: datetime):
        """Remove entries older than window_seconds to bound memory."""
        for fingerprint in list(self._history.keys()):
            self._history[fingerprint] = [
                e for e in self._history[fingerprint]
                if (current_time - e.timestamp).total_seconds() <= self._window_seconds
            ]
            # Remove fingerprint if no occurrences left
            if not self._history[fingerprint]:
                del self._history[fingerprint]

    def get_history_count(self, fingerprint: str) -> int:
        """Get how many times this fingerprint has been seen."""
        return len(self._history.get(fingerprint, []))

    def clear(self):
        """Clear all state (for testing)."""
        self._history.clear()
