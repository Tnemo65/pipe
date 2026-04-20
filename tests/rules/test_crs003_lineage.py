"""
Tests for CRS003 lineage-aware duplicate detection.

Validates that CRS003 suppresses duplicates from replay streams
but still detects real duplicates from live streams.
"""
import pytest
from datetime import datetime, timedelta
from streamdq.rules.cross_record import evaluate_duplicate_event, CrossRecordState
from streamdq.models.lineage import LineageMetadata


class TestCRS003LineageAwareness:
    """Test CRS003 respects _lineage metadata."""

    def test_replay_duplicate_suppressed(self):
        """Duplicate from replay stream does NOT trigger violation."""
        state = CrossRecordState()

        event1 = {
            "trip_id": "trip_001",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "_lineage": {
                "source_id": "nyc_taxi_replay_001",
                "source_type": "batch_replay",
                "is_replay": True,
                "batch_id": "batch_001"
            }
        }

        event2 = dict(event1)

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=30)

        violation1 = evaluate_duplicate_event(event1, t1, dedup_state=state)
        assert violation1 is None

        violation2 = evaluate_duplicate_event(event2, t2, dedup_state=state)
        assert violation2 is None

    def test_live_duplicate_detected(self):
        """Duplicate from live stream DOES trigger violation."""
        state = CrossRecordState()

        event1 = {
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

        event2 = dict(event1)

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=30)

        violation1 = evaluate_duplicate_event(event1, t1, dedup_state=state)
        assert violation1 is None

        violation2 = evaluate_duplicate_event(event2, t2, dedup_state=state)
        assert violation2 is not None
        assert violation2.rule_id == "CRS003"
        assert "DUPLICATE_RECORD" in violation2.details["type"]

    def test_no_lineage_treated_as_live(self):
        """Events without _lineage are treated as live (backward compat)."""
        state = CrossRecordState()

        event1 = {
            "trip_id": "trip_003",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5
        }

        event2 = dict(event1)

        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=30)

        violation1 = evaluate_duplicate_event(event1, t1, dedup_state=state)
        assert violation1 is None

        violation2 = evaluate_duplicate_event(event2, t2, dedup_state=state)
        assert violation2 is not None
        assert violation2.rule_id == "CRS003"
