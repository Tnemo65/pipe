"""
Tests for LocalPipeline with context-aware thresholds.

Validates that pipeline properly integrates ContextAwareAdaptiveThresholdEngine.
"""
import pytest
from datetime import datetime
from streamdq.pipeline.local_pipeline import LocalPipeline, NoOpViolationStore


class TestContextAwarePipeline:
    """Test LocalPipeline with context-aware threshold integration."""

    def test_pipeline_uses_context_aware_engine(self):
        """LocalPipeline initializes with ContextAwareAdaptiveThresholdEngine."""
        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="nyc_taxi"
        )

        assert pipeline._use_context_aware is True
        assert hasattr(pipeline.threshold_engine, "registry")  # Context-aware engine has registry

    def test_pipeline_processes_events_with_context(self):
        """Pipeline processes events and updates context-aware stats."""
        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="nyc_taxi"
        )

        # Process morning events
        morning_events = [
            {
                "trip_id": f"trip_{i}",
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "tpep_dropoff_datetime": "2024-01-15T10:45:00",
                "PULocationID": 161,
                "DOLocationID": 237,
                "fare_amount": 15.0 + i,
                "trip_distance": 2.0 + i * 0.1,
                "passenger_count": 1
            }
            for i in range(10)
        ]

        for event in morning_events:
            pipeline.process_event(event)

        # Verify context-aware stats stored
        # event_count = 20 (10 events * 2 fields: fare_amount, trip_distance)
        assert pipeline.threshold_engine.event_count == 20
        assert len(pipeline.threshold_engine._buffers) > 0

    def test_pipeline_backward_compatible_with_global_thresholds(self):
        """Pipeline can use global thresholds (backward compatibility)."""
        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=False,  # Use global
            entity_type="nyc_taxi"
        )

        assert pipeline._use_context_aware is False
        assert not hasattr(pipeline.threshold_engine, "registry")  # Global engine has no registry

        # Process event
        event = {
            "trip_id": "trip_001",
            "tpep_pickup_datetime": "2024-01-15T10:30:00",
            "tpep_dropoff_datetime": "2024-01-15T10:45:00",
            "PULocationID": 161,
            "DOLocationID": 237,
            "fare_amount": 15.0,
            "trip_distance": 2.0,
            "passenger_count": 1
        }

        violations = pipeline.process_event(event)
        assert isinstance(violations, list)

    def test_context_aware_pipeline_collects_context_specific_stats(self):
        """Context-aware pipeline maintains separate stats per context."""
        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="nyc_taxi"
        )

        # Process events in two different contexts
        # Morning midtown
        for i in range(10):
            event = {
                "trip_id": f"morning_{i}",
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,
                "fare_amount": 10.0 + i,
                "trip_distance": 2.0
            }
            pipeline.process_event(event)

        # Evening midtown
        for i in range(10):
            event = {
                "trip_id": f"evening_{i}",
                "tpep_pickup_datetime": "2024-01-15T20:30:00",
                "PULocationID": 161,
                "fare_amount": 30.0 + i,
                "trip_distance": 2.0
            }
            pipeline.process_event(event)

        # Should have multiple context buffers (L0-L4 for morning + L0-L4 for evening)
        # At minimum: 2 different hour contexts (hour_10 and hour_20)
        assert len(pipeline.threshold_engine._buffers) >= 2
