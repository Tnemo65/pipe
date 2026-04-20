"""
Tests for LineageMetadata model.

Validates:
- Serialization (to_dict/from_dict roundtrip)
- Defaults for missing fields
- Backward compatibility (events without _lineage)
"""
import pytest
from streamdq.models.lineage import LineageMetadata


class TestLineageMetadataSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_full_fields(self):
        """All fields serialize correctly."""
        lineage = LineageMetadata(
            source_id="test_source",
            source_type="batch_replay",
            is_replay=True,
            batch_id="batch_123",
            kafka_offset=42,
            kafka_partition=0,
            producer_timestamp="2024-01-15T10:30:00Z",
            ingestion_timestamp="2024-01-15T10:30:01Z",
            hop_count=1,
            upstream_event_ids=["evt_1", "evt_2"]
        )

        result = lineage.to_dict()

        assert result["source_id"] == "test_source"
        assert result["source_type"] == "batch_replay"
        assert result["is_replay"] is True
        assert result["batch_id"] == "batch_123"
        assert result["kafka_offset"] == 42
        assert result["kafka_partition"] == 0
        assert result["producer_timestamp"] == "2024-01-15T10:30:00Z"
        assert result["ingestion_timestamp"] == "2024-01-15T10:30:01Z"
        assert result["hop_count"] == 1
        assert result["upstream_event_ids"] == ["evt_1", "evt_2"]

    def test_to_dict_minimal_fields(self):
        """Minimal required fields serialize with defaults."""
        lineage = LineageMetadata(
            source_id="test_source",
            source_type="api_poll"
        )

        result = lineage.to_dict()

        assert result["source_id"] == "test_source"
        assert result["source_type"] == "api_poll"
        assert result["is_replay"] is False
        assert result["batch_id"] is None
        assert result["hop_count"] == 0
        assert result["upstream_event_ids"] == []

    def test_from_dict_roundtrip(self):
        """to_dict → from_dict preserves all fields."""
        original = LineageMetadata(
            source_id="test_source",
            source_type="batch_replay",
            is_replay=True,
            batch_id="batch_123",
            hop_count=2
        )

        serialized = original.to_dict()
        restored = LineageMetadata.from_dict(serialized)

        assert restored.source_id == original.source_id
        assert restored.source_type == original.source_type
        assert restored.is_replay == original.is_replay
        assert restored.batch_id == original.batch_id
        assert restored.hop_count == original.hop_count

    def test_from_dict_with_missing_fields(self):
        """Missing fields get sensible defaults."""
        partial = {
            "source_id": "test_source",
            "source_type": "api_poll",
        }

        lineage = LineageMetadata.from_dict(partial)

        assert lineage.source_id == "test_source"
        assert lineage.source_type == "api_poll"
        assert lineage.is_replay is False
        assert lineage.batch_id is None
        assert lineage.hop_count == 0
        assert lineage.upstream_event_ids == []

    def test_from_dict_empty_dict(self):
        """Empty dict returns defaults (backward compatibility)."""
        lineage = LineageMetadata.from_dict({})

        assert lineage.source_id == "unknown"
        assert lineage.source_type == "unknown"
        assert lineage.is_replay is False
        assert lineage.batch_id is None

    def test_from_event_with_lineage(self):
        """Extract _lineage from event payload."""
        event = {
            "trip_id": "12345",
            "fare_amount": 15.50,
            "_lineage": {
                "source_id": "nyc_taxi_2024_01",
                "source_type": "batch_replay",
                "is_replay": True
            }
        }

        lineage = LineageMetadata.from_event(event)

        assert lineage.source_id == "nyc_taxi_2024_01"
        assert lineage.source_type == "batch_replay"
        assert lineage.is_replay is True

    def test_from_event_without_lineage(self):
        """Event without _lineage returns defaults (backward compatibility)."""
        event = {
            "trip_id": "12345",
            "fare_amount": 15.50,
        }

        lineage = LineageMetadata.from_event(event)

        assert lineage.source_id == "unknown"
        assert lineage.source_type == "unknown"
        assert lineage.is_replay is False


class TestLineageMetadataValidation:
    """Test validation and edge cases."""

    def test_source_type_enum_values(self):
        """Document expected source_type values."""
        valid_types = ["batch_replay", "api_poll", "cdc_stream", "manual_upload"]

        for source_type in valid_types:
            lineage = LineageMetadata(
                source_id="test",
                source_type=source_type
            )
            assert lineage.source_type == source_type

    def test_replay_flag_scenarios(self):
        """is_replay=True typically paired with batch_replay source_type."""
        replay = LineageMetadata(
            source_id="historical_data",
            source_type="batch_replay",
            is_replay=True,
            batch_id="batch_001"
        )
        assert replay.is_replay is True
        assert replay.batch_id is not None

        live = LineageMetadata(
            source_id="kafka_stream",
            source_type="api_poll",
            is_replay=False
        )
        assert live.is_replay is False
        assert live.batch_id is None
