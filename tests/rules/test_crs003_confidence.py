"""
Tests for CRS003 with confidence-based adjudication.

Validates that evaluate_duplicate_event() uses ContextAwareDuplicateAdjudicator
and populates violation.details with confidence score.
"""
import pytest
from datetime import datetime, timedelta
from streamdq.rules.cross_record import evaluate_duplicate_event, CrossRecordState


class TestCRS003ConfidenceScoring:
    """Test CRS003 confidence integration."""

    def test_high_confidence_duplicate_emits_violation(self):
        """High confidence (>0.7) duplicate → HIGH severity violation."""
        state = CrossRecordState()

        event = {
            "trip_id": "trip_001",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "_lineage": {
                "source_id": "gtfs_api_ktmb",
                "source_type": "api_poll",
                "is_replay": False
            }
        }

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=2)  # Immediate duplicate

        # First event: not a duplicate
        violation1 = evaluate_duplicate_event(event, t1, dedup_state=state)
        assert violation1 is None

        # Second event: high-confidence duplicate
        violation2 = evaluate_duplicate_event(event, t2, dedup_state=state)

        assert violation2 is not None
        assert violation2.rule_id == "CRS003"
        assert violation2.severity == "HIGH"

        # Check confidence in details
        assert "adjudication_confidence" in violation2.details
        assert violation2.details["adjudication_confidence"] > 0.7
        assert "temporal_similarity" in violation2.details
        assert "source_diversity" in violation2.details
        assert "fingerprint_stability" in violation2.details

    def test_medium_confidence_duplicate_emits_advisory(self):
        """Medium confidence (0.4-0.7) → MEDIUM severity advisory."""
        state = CrossRecordState()

        event = {
            "trip_id": "trip_002",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "_lineage": {
                "source_id": "gtfs_api_ktmb",
                "source_type": "api_poll",
                "is_replay": False
            }
        }

        t1 = datetime(2024, 1, 15, 10, 0, 0)

        violation1 = evaluate_duplicate_event(event, t1, dedup_state=state)
        assert violation1 is None

        # Second occurrence from DIFFERENT source (cross-source collision)
        event2 = dict(event)
        event2["_lineage"] = {
            "source_id": "nyc_taxi_replay_001",  # Different source
            "source_type": "batch_replay",
            "is_replay": False  # Not suppressed, but different source
        }

        t2 = t1 + timedelta(seconds=2)

        violation2 = evaluate_duplicate_event(event2, t2, dedup_state=state)

        # Cross-source collision: medium confidence
        # temporal_sim = 1.0, source_diversity = 0.0, fingerprint_stability = 0.5
        # confidence = 0.5*1.0 + 0.3*0.0 + 0.2*0.5 = 0.6
        assert violation2 is not None
        assert violation2.severity == "MEDIUM"
        assert 0.4 <= violation2.details["adjudication_confidence"] <= 0.7

    def test_low_confidence_duplicate_suppressed(self):
        """Low confidence (≤0.4) → suppressed, no violation."""
        state = CrossRecordState()

        event = {
            "trip_id": "trip_003",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "_lineage": {
                "source_id": "gtfs_api_ktmb",
                "source_type": "api_poll",
                "is_replay": False
            }
        }

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        violation1 = evaluate_duplicate_event(event, t1, dedup_state=state)
        assert violation1 is None

        # Second occurrence after 200 seconds, different source
        event2 = dict(event)
        event2["_lineage"] = {
            "source_id": "nyc_taxi_replay_001",
            "source_type": "batch_replay",
            "is_replay": False
        }

        t2 = t1 + timedelta(seconds=200)

        violation2 = evaluate_duplicate_event(event2, t2, dedup_state=state)

        # Low confidence due to:
        # - Large time gap (temporal_sim ≈ 0.5)
        # - Different source (source_diversity = 0.0)
        # - Low fingerprint stability (seen 2x)
        # Expected confidence ≈ 0.5*0.5 + 0.3*0.0 + 0.2*0.5 = 0.35
        assert violation2 is None  # Suppressed

    def test_replay_duplicate_still_suppressed(self):
        """Replay duplicates (is_replay=True) still suppressed (Phase 0 behavior preserved)."""
        state = CrossRecordState()

        event = {
            "trip_id": "trip_004",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "_lineage": {
                "source_id": "nyc_taxi_replay_001",
                "source_type": "batch_replay",
                "is_replay": True,  # Replay flag
                "batch_id": "batch_001"
            }
        }

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=2)

        violation1 = evaluate_duplicate_event(event, t1, dedup_state=state)
        assert violation1 is None

        violation2 = evaluate_duplicate_event(event, t2, dedup_state=state)
        assert violation2 is None  # Suppressed by is_replay check


class TestTemporalClustering:
    """Test temporal clustering of near-duplicates."""

    def test_near_duplicate_burst_single_violation(self):
        """
        5 identical events within 10 seconds → single violation (not 5).

        Phase 1 T2: Temporal clustering reduces over-counting.
        """
        state = CrossRecordState()

        event = {
            "trip_id": "trip_cluster_001",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "_lineage": {
                "source_id": "gtfs_api_ktmb",
                "source_type": "api_poll",
                "is_replay": False
            }
        }

        t_start = datetime(2024, 1, 15, 10, 0, 0)

        violations = []

        for i in range(5):
            t = t_start + timedelta(seconds=i * 2)  # T, T+2s, T+4s, T+6s, T+8s

            violation = evaluate_duplicate_event(
                event,
                t,
                dedup_state=state,
                enable_clustering=True,  # NEW parameter
                cluster_window_seconds=10
            )

            if violation is not None:
                violations.append(violation)

        # Without clustering: 4 violations (first event not a duplicate)
        # With clustering: 1 violation (first duplicate triggers, rest clustered)
        assert len(violations) == 1, \
            f"Expected 1 clustered violation, got {len(violations)}"

        # Check cluster metadata in details
        cluster_info = violations[0].details.get("cluster_info")
        assert cluster_info is not None
        assert cluster_info["cluster_size"] == 1  # First violation in cluster
        assert "cluster_first_seen" in cluster_info

        # Verify subsequent duplicates were suppressed (cluster grew but no new violations)
        # The cluster size in violation is captured at emission time (size=1)
        # Subsequent duplicates increment internal cluster state but don't emit violations
