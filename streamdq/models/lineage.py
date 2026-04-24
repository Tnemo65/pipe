"""
Data Lineage Metadata Model.

Tracks the provenance and source context of streaming events.
Used by cross-record rules (e.g., CRS003) to distinguish replays from real duplicates.

References:
- ENHANCEMENT_ROADMAP.md: Phase 1, T3 (Source Lineage Awareness)
- Proposed impact: +5-8 precision points by suppressing known-good replays
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class LineageMetadata:
    """
    Lineage metadata for an event.

    Tracks source provenance, replay status, batch context, and Kafka metadata.
    Attached to event payload as `_lineage` dict for backward compatibility.

    Fields:
        source_id: Unique identifier for the source system/file
                   Examples: "nyc_taxi_parquet_2024_01", "gtfs_api_ktmb"
        source_type: Type of source system
                    Values: "batch_replay" | "api_poll" | "cdc_stream" | "manual_upload"
        is_replay: Whether this is a replay of historical data (not live)
        batch_id: Batch identifier for grouped events (None for streaming)
        kafka_offset: Kafka message offset (for deduplication)
        kafka_partition: Kafka partition number
        producer_timestamp: When producer created the event (ISO 8601)
        ingestion_timestamp: When event entered the pipeline (ISO 8601)
        hop_count: Number of pipeline stages traversed (starts at 0)
        upstream_event_ids: Chain of event IDs from upstream systems
        entity_index: NG-eval-01: Ground-truth index assigned by synthetic_injector.
                     Used for precision/recall matching between injected anomalies and detected violations.
                     Extracted from event and propagated to Violation.entity_index.
    """

    source_id: str
    source_type: str
    is_replay: bool = False
    batch_id: Optional[str] = None
    kafka_offset: Optional[int] = None
    kafka_partition: Optional[int] = None
    producer_timestamp: Optional[str] = None
    ingestion_timestamp: Optional[str] = None
    hop_count: int = 0
    upstream_event_ids: list[str] = field(default_factory=list)
    # NG-eval-01: Ground-truth index for precision/recall matching
    entity_index: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LineageMetadata":
        """Create from dict (from event payload). Handles missing fields gracefully."""
        return cls(
            source_id=data.get("source_id", "unknown"),
            source_type=data.get("source_type", "unknown"),
            is_replay=data.get("is_replay", False),
            batch_id=data.get("batch_id"),
            kafka_offset=data.get("kafka_offset"),
            kafka_partition=data.get("kafka_partition"),
            producer_timestamp=data.get("producer_timestamp"),
            ingestion_timestamp=data.get("ingestion_timestamp"),
            hop_count=data.get("hop_count", 0),
            upstream_event_ids=data.get("upstream_event_ids", []),
            entity_index=data.get("entity_index"),
        )

    @classmethod
    def from_event(cls, event: dict) -> "LineageMetadata":
        """Extract lineage from event payload."""
        return cls.from_dict(event.get("_lineage", {}))
