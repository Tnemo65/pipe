"""
Tests for GTFS live producer lineage metadata.

Validates that gtfs_live.py attaches correct _lineage metadata.
"""
import json
import pytest
from streamdq.producers.gtfs_live import GTFSLiveConsumer
from streamdq.models.lineage import LineageMetadata


class TestGTFSLineageMetadata:
    """Test lineage metadata attachment."""

    def test_live_event_has_lineage(self):
        """Live events must have _lineage field."""
        consumer = GTFSLiveConsumer(
            direct_mode=True,
            agencies=["ktmb"]
        )

        vehicle = {
            "vehicle_id": "KTM_123",
            "latitude": 3.1390,
            "longitude": 101.6869,
            "_agency": "ktmb"
        }

        enriched = consumer._enrich_with_lineage(vehicle, agency="ktmb")

        assert "_lineage" in enriched
        assert isinstance(enriched["_lineage"], dict)

    def test_lineage_metadata_fields_live_stream(self):
        """Lineage metadata for live stream has correct values."""
        consumer = GTFSLiveConsumer(
            direct_mode=True,
            agencies=["ktmb"]
        )

        vehicle = {"vehicle_id": "KTM_123", "_agency": "ktmb"}
        enriched = consumer._enrich_with_lineage(vehicle, agency="ktmb")

        lineage = enriched["_lineage"]

        assert "source_id" in lineage
        assert "source_type" in lineage
        assert "is_replay" in lineage

        assert lineage["source_type"] == "api_poll"
        assert lineage["is_replay"] is False
        assert lineage["batch_id"] is None

    def test_lineage_source_id_includes_agency(self):
        """source_id includes agency name."""
        consumer = GTFSLiveConsumer(direct_mode=True)

        vehicle = {"vehicle_id": "KTM_123"}
        enriched = consumer._enrich_with_lineage(vehicle, agency="ktmb")

        source_id = enriched["_lineage"]["source_id"]

        assert "gtfs" in source_id.lower()
        assert "ktmb" in source_id.lower()

    def test_lineage_multiple_agencies(self):
        """Different agencies get different source_ids."""
        consumer = GTFSLiveConsumer(direct_mode=True)

        vehicle1 = {"vehicle_id": "KTM_123"}
        vehicle2 = {"vehicle_id": "RAPID_456"}

        enriched1 = consumer._enrich_with_lineage(vehicle1, agency="ktmb")
        enriched2 = consumer._enrich_with_lineage(vehicle2, agency="prasaranabus")

        source_id1 = enriched1["_lineage"]["source_id"]
        source_id2 = enriched2["_lineage"]["source_id"]

        assert source_id1 != source_id2
        assert "ktmb" in source_id1.lower()
        assert "prasarana" in source_id2.lower()

    def test_lineage_deserializable(self):
        """_lineage can be deserialized to LineageMetadata."""
        consumer = GTFSLiveConsumer(direct_mode=True)

        vehicle = {"vehicle_id": "KTM_123"}
        enriched = consumer._enrich_with_lineage(vehicle, agency="ktmb")

        lineage = LineageMetadata.from_dict(enriched["_lineage"])

        assert lineage.source_type == "api_poll"
        assert lineage.is_replay is False
