"""
Tests for NYC Taxi replay producer lineage metadata.

Validates that nyc_taxi_replay.py attaches correct _lineage metadata.
"""
import json
import pytest
from datetime import datetime
from streamdq.producers.nyc_taxi_replay import NYCTaxiReplayProducer
from streamdq.models.lineage import LineageMetadata


class TestNYCTaxiLineageMetadata:
    """Test lineage metadata attachment."""

    def test_replay_event_has_lineage(self):
        """Replay events must have _lineage field."""
        producer = NYCTaxiReplayProducer(
            direct_mode=True,
            rate=10,
            shuffle=False,
            inject_anomalies=False
        )

        event = {
            "trip_id": "test_123",
            "fare_amount": 15.50,
            "tpep_pickup_datetime": "2024-01-15T10:00:00"
        }

        enriched = producer._enrich_with_lineage(event)

        assert "_lineage" in enriched
        assert isinstance(enriched["_lineage"], dict)

    def test_lineage_metadata_fields(self):
        """Lineage metadata has required fields."""
        producer = NYCTaxiReplayProducer(
            direct_mode=True,
            rate=10,
            shuffle=False,
            inject_anomalies=False
        )

        event = {"trip_id": "test_123", "fare_amount": 15.50}
        enriched = producer._enrich_with_lineage(event)

        lineage = enriched["_lineage"]

        assert "source_id" in lineage
        assert "source_type" in lineage
        assert "is_replay" in lineage

        assert lineage["source_type"] == "batch_replay"
        assert lineage["is_replay"] is True
        assert lineage["batch_id"] is not None

    def test_lineage_source_id_format(self):
        """source_id follows naming convention."""
        producer = NYCTaxiReplayProducer(
            direct_mode=True,
            rate=10,
            shuffle=False
        )

        event = {"trip_id": "test_123"}
        enriched = producer._enrich_with_lineage(event)

        source_id = enriched["_lineage"]["source_id"]

        assert "nyc_taxi" in source_id.lower()
        assert len(source_id) > 0

    def test_lineage_deserializable(self):
        """_lineage can be deserialized to LineageMetadata."""
        producer = NYCTaxiReplayProducer(
            direct_mode=True,
            rate=10,
            shuffle=False
        )

        event = {"trip_id": "test_123"}
        enriched = producer._enrich_with_lineage(event)

        lineage = LineageMetadata.from_dict(enriched["_lineage"])

        assert lineage.source_type == "batch_replay"
        assert lineage.is_replay is True

    def test_original_event_preserved(self):
        """Enrichment doesn't modify original event fields."""
        producer = NYCTaxiReplayProducer(direct_mode=True)

        event = {
            "trip_id": "test_123",
            "fare_amount": 15.50,
            "passenger_count": 2
        }
        original_keys = set(event.keys())

        enriched = producer._enrich_with_lineage(event)

        for key in original_keys:
            assert key in enriched
            assert enriched[key] == event[key]

        assert set(enriched.keys()) == original_keys | {"_lineage"}


class TestNYCTaxiLineageIntegration:
    """Test lineage in full emit pipeline."""

    def test_emit_attaches_lineage(self, capsys):
        """_emit() includes _lineage in output."""
        producer = NYCTaxiReplayProducer(
            direct_mode=True,
            rate=10,
            shuffle=False
        )

        event = {"trip_id": "test_123", "fare_amount": 15.50}
        producer._emit(event)

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())

        assert "_lineage" in output
        assert output["_lineage"]["is_replay"] is True

    def test_emit_preserves_kafka_arrival_ms(self, capsys):
        """kafka_arrival_ms still attached (existing behavior)."""
        producer = NYCTaxiReplayProducer(direct_mode=True)

        event = {"trip_id": "test_123"}
        producer._emit(event)

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())

        assert "kafka_arrival_ms" in output
        assert "_lineage" in output
