"""
End-to-end integration test for lineage-aware duplicate detection.

Validates full pipeline: Producer → CRS003 → Suppression
"""
import pytest
from datetime import datetime, timedelta
from streamdq.producers.nyc_taxi_replay import NYCTaxiReplayProducer
from streamdq.producers.gtfs_live import GTFSLiveConsumer
from streamdq.rules.cross_record import evaluate_duplicate_event, CrossRecordState
from streamdq.models.lineage import LineageMetadata


class TestLineageE2EReplay:
    """End-to-end test for NYC Taxi replay."""

    def test_nyc_taxi_replay_duplicate_suppressed(self):
        """Full flow: NYC Taxi replay → CRS003 → No violation."""
        producer = NYCTaxiReplayProducer(direct_mode=True, inject_anomalies=False)

        event = {
            "trip_id": "trip_e2e_001",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5,
            "fare_amount": 15.50
        }

        enriched = producer._enrich_with_lineage(event)

        assert "_lineage" in enriched
        assert enriched["_lineage"]["is_replay"] is True

        state = CrossRecordState()
        t1 = datetime(2024, 1, 15, 10, 0, 0)

        violation1 = evaluate_duplicate_event(enriched, t1, dedup_state=state)
        assert violation1 is None

        enriched2 = producer._enrich_with_lineage(event)
        t2 = t1 + timedelta(seconds=30)

        violation2 = evaluate_duplicate_event(enriched2, t2, dedup_state=state)
        assert violation2 is None

        print("✅ E2E test passed: Replay duplicates suppressed")


class TestLineageE2ELive:
    """End-to-end test for GTFS live stream."""

    def test_gtfs_live_duplicate_detected(self):
        """Full flow: GTFS live → CRS003 → Violation."""
        consumer = GTFSLiveConsumer(direct_mode=True)

        vehicle = {
            "vehicle_id": "KTM_999",
            "trip_id": "trip_ktmb_001",
            "PULocationID": 100,
            "DOLocationID": 200,
            "passenger_count": 2,
            "trip_distance": 5.0,
            "_agency": "ktmb"
        }

        enriched = consumer._enrich_with_lineage(vehicle, agency="ktmb")

        assert "_lineage" in enriched
        assert enriched["_lineage"]["is_replay"] is False

        state = CrossRecordState()
        t1 = datetime(2024, 1, 15, 10, 0, 0)

        violation1 = evaluate_duplicate_event(enriched, t1, dedup_state=state)
        assert violation1 is None

        enriched2 = consumer._enrich_with_lineage(vehicle, agency="ktmb")
        t2 = t1 + timedelta(seconds=30)

        violation2 = evaluate_duplicate_event(enriched2, t2, dedup_state=state)
        assert violation2 is not None
        assert violation2.rule_id == "CRS003"

        print("✅ E2E test passed: Live duplicates detected")


class TestLineageE2EBackwardCompat:
    """Backward compatibility tests."""

    def test_event_without_lineage_still_works(self):
        """Events without _lineage work (treated as live)."""
        event = {
            "trip_id": "trip_old_001",
            "PULocationID": 161,
            "DOLocationID": 237,
            "passenger_count": 1,
            "trip_distance": 2.5
        }

        state = CrossRecordState()
        t1 = datetime(2024, 1, 15, 10, 0, 0)
        t2 = t1 + timedelta(seconds=30)

        violation1 = evaluate_duplicate_event(event, t1, dedup_state=state)
        assert violation1 is None

        violation2 = evaluate_duplicate_event(event, t2, dedup_state=state)
        assert violation2 is not None
        assert violation2.rule_id == "CRS003"
