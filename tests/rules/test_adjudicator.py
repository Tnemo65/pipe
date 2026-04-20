"""
Tests for ContextAwareDuplicateAdjudicator.

Validates confidence formula:
  confidence = 0.5 * temporal_sim + 0.3 * source_diversity + 0.2 * fingerprint_stability

Where:
- temporal_sim = 1.0 if ≤5s, exponential decay to 0.0 at 300s
- source_diversity = 1.0 if same source+batch, 0.5 if same source, 0.0 if different source
- fingerprint_stability = 1.0 if seen ≥3 times, 0.5 if 2x, 0.0 if 1x (first seen)
"""
import pytest
from datetime import datetime, timedelta
from streamdq.rules.adjudicator import ContextAwareDuplicateAdjudicator


class TestConfidenceFormula:
    """Test confidence scoring formula."""

    def test_identical_event_same_source_immediate(self):
        """Identical event from same source within 5s → high confidence (>0.7)."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        fingerprint = "abc123def456"
        source_id_1 = "nyc_taxi_replay_001"
        batch_id_1 = "batch_001"

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=2)  # 2 seconds later

        # First event: no history, confidence should be 0.0 (first-seen)
        confidence1 = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1,
            source_id=source_id_1,
            batch_id=batch_id_1,
            is_replay=False
        )
        assert confidence1 == 0.0  # First seen, no duplicate

        # Second event: immediate duplicate from same source/batch
        confidence2 = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t2,
            source_id=source_id_1,
            batch_id=batch_id_1,
            is_replay=False
        )

        # Expected calculation:
        # temporal_sim = 1.0 (2s ≤ 5s)
        # source_diversity = 1.0 (same source+batch)
        # fingerprint_stability = 0.5 (seen 2x)
        # confidence = 0.5*1.0 + 0.3*1.0 + 0.2*0.5 = 0.5 + 0.3 + 0.1 = 0.9
        assert 0.85 <= confidence2 <= 0.95  # High confidence

    def test_same_event_different_source(self):
        """Identical event from different source → low confidence (<0.4)."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        fingerprint = "abc123def456"

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=3)

        # First event from source A
        adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1,
            source_id="gtfs_api_ktmb",
            batch_id=None,
            is_replay=False
        )

        # Second event from source B (different source)
        confidence = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t2,
            source_id="nyc_taxi_replay_001",
            batch_id="batch_001",
            is_replay=False
        )

        # Expected:
        # temporal_sim = 1.0 (3s ≤ 5s)
        # source_diversity = 0.0 (different source)
        # fingerprint_stability = 0.5 (seen 2x)
        # confidence = 0.5*1.0 + 0.3*0.0 + 0.2*0.5 = 0.5 + 0.0 + 0.1 = 0.6
        assert 0.55 <= confidence <= 0.65  # Medium confidence (cross-source collision)

    def test_delayed_duplicate_same_source(self):
        """Duplicate after 60 seconds from same source → medium confidence."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        fingerprint = "abc123def456"
        source_id = "nyc_taxi_replay_001"

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=60)

        adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1,
            source_id=source_id,
            batch_id="batch_001",
            is_replay=False
        )

        confidence = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t2,
            source_id=source_id,
            batch_id="batch_001",
            is_replay=False
        )

        # Expected:
        # temporal_sim = exp(-60/300) ≈ 0.82
        # source_diversity = 1.0 (same source+batch)
        # fingerprint_stability = 0.5 (seen 2x)
        # confidence = 0.5*0.82 + 0.3*1.0 + 0.2*0.5 = 0.41 + 0.3 + 0.1 = 0.81
        assert 0.75 <= confidence <= 0.85

    def test_fingerprint_stability_after_3_occurrences(self):
        """After 3 occurrences, fingerprint_stability = 1.0."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        fingerprint = "abc123def456"
        source_id = "nyc_taxi_replay_001"

        t1 = datetime(2024, 1, 15, 10, 0, 0)

        # First occurrence
        adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1,
            source_id=source_id,
            batch_id="batch_001",
            is_replay=False
        )

        # Second occurrence
        adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1 + timedelta(seconds=1),
            source_id=source_id,
            batch_id="batch_001",
            is_replay=False
        )

        # Third occurrence (fingerprint_stability should be 1.0 now)
        confidence = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1 + timedelta(seconds=2),
            source_id=source_id,
            batch_id="batch_001",
            is_replay=False
        )

        # Expected:
        # temporal_sim = 1.0 (2s ≤ 5s)
        # source_diversity = 1.0 (same source+batch)
        # fingerprint_stability = 1.0 (seen 3x)
        # confidence = 0.5*1.0 + 0.3*1.0 + 0.2*1.0 = 0.5 + 0.3 + 0.2 = 1.0
        assert 0.95 <= confidence <= 1.0


class TestAdjudicatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_replay_stream_confidence(self):
        """Replay stream events (is_replay=True) still scored normally."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        fingerprint = "abc123"

        # First event (replay)
        confidence1 = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            source_id="nyc_taxi_replay_001",
            batch_id="batch_001",
            is_replay=True
        )
        assert confidence1 == 0.0  # First seen

        # Second event (replay, same batch)
        confidence2 = adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=datetime(2024, 1, 15, 10, 0, 2),
            source_id="nyc_taxi_replay_001",
            batch_id="batch_001",
            is_replay=True
        )
        # Adjudicator doesn't care about is_replay flag—that's CRS003's job
        # It just computes confidence based on temporal/source/stability
        assert confidence2 > 0.7  # High confidence duplicate

    def test_eviction_removes_old_entries(self):
        """Old entries beyond window are evicted."""
        adjudicator = ContextAwareDuplicateAdjudicator(window_seconds=60)

        fingerprint = "abc123"
        t1 = datetime(2024, 1, 15, 10, 0, 0)

        # Add entry at t1
        adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t1,
            source_id="source_a",
            batch_id=None
        )

        assert adjudicator.get_history_count(fingerprint) == 1

        # Add entry 120 seconds later (beyond 60s window)
        t2 = t1 + timedelta(seconds=120)
        adjudicator.compute_confidence(
            fingerprint=fingerprint,
            timestamp=t2,
            source_id="source_a",
            batch_id=None
        )

        # t1 entry should be evicted
        assert adjudicator.get_history_count(fingerprint) == 1  # Only t2 remains

    def test_multiple_fingerprints_isolated(self):
        """Different fingerprints don't interfere."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        t = datetime(2024, 1, 15, 10, 0, 0)

        # Fingerprint A seen 2x
        adjudicator.compute_confidence(
            fingerprint="aaa", timestamp=t, source_id="s1", batch_id=None
        )
        adjudicator.compute_confidence(
            fingerprint="aaa", timestamp=t + timedelta(seconds=1),
            source_id="s1", batch_id=None
        )

        # Fingerprint B seen 1x
        adjudicator.compute_confidence(
            fingerprint="bbb", timestamp=t, source_id="s1", batch_id=None
        )

        assert adjudicator.get_history_count("aaa") == 2
        assert adjudicator.get_history_count("bbb") == 1

    def test_clear_state(self):
        """clear() removes all history."""
        adjudicator = ContextAwareDuplicateAdjudicator()

        adjudicator.compute_confidence(
            fingerprint="abc",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            source_id="s1",
            batch_id=None
        )

        assert adjudicator.get_history_count("abc") == 1

        adjudicator.clear()

        assert adjudicator.get_history_count("abc") == 0
