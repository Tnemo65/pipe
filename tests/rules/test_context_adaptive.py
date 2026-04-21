"""
Tests for Context-Aware Adaptive Threshold Engine.

Validates context-keyed statistics storage and hierarchical fallback.
"""
import pytest
from datetime import datetime
from streamdq.rules.context_adaptive import ContextAwareAdaptiveThresholdEngine
from streamdq.models.context_registry import ContextRegistry


class TestContextAwareUpdate:
    """Test context-aware update() with context extraction."""

    def test_update_with_context_extraction(self):
        """update() extracts context from event and stores stats per context."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=10
        )

        # Morning event in midtown
        event1 = {
            "tpep_pickup_datetime": "2024-01-15T10:30:00",  # Monday 10:30 AM
            "PULocationID": 161,  # Midtown Center
            "fare_amount": 15.50
        }

        engine.update(field="fare_amount", value=15.50, event=event1)

        # Verify context extracted at all 5 hierarchy levels
        assert len(engine._buffers) == 5  # L0, L1, L2, L3, L4
        context_keys = list(engine._buffers.keys())
        # All keys should contain field name
        for key in context_keys:
            assert "fare_amount" in key

    def test_update_different_contexts_separate_stats(self):
        """Different contexts store separate statistics."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=5
        )

        # Morning midtown events
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,
                "fare_amount": 15.0 + i
            }
            engine.update("fare_amount", 15.0 + i, event)

        # Evening midtown events (different time context)
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T20:30:00",
                "PULocationID": 161,
                "fare_amount": 25.0 + i
            }
            engine.update("fare_amount", 25.0 + i, event)

        # Should have 2 separate context buffers
        assert len(engine._buffers) >= 2


class TestContextAwareGetThreshold:
    """Test get_threshold_with_fallback() hierarchical lookup."""

    def test_get_threshold_level0_exact_match(self):
        """Level 0 (most specific) returns exact context match."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=5,
            recompute_every=5
        )

        # Add 10 morning midtown events
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,
                "fare_amount": 15.0 + i
            }
            engine.update("fare_amount", 15.0 + i, event)

        # Query with same context
        query_event = {
            "tpep_pickup_datetime": "2024-01-15T10:45:00",
            "PULocationID": 161
        }

        result = engine.get_threshold_with_fallback(
            field="fare_amount",
            percentile="p90",
            event=query_event
        )

        assert result is not None
        assert "value" in result
        assert result["level"] == 0  # Exact match at level 0

    def test_get_threshold_fallback_to_level1(self):
        """Falls back to level 1 when level 0 has insufficient samples."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=30,  # High threshold
            recompute_every=5
        )

        # Add only 10 events (below min_sample_size for L0)
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,
                "fare_amount": 15.0 + i
            }
            engine.update("fare_amount", 15.0 + i, event)

        # Add more events at different hours but same time bucket (morning)
        for hour in [8, 9, 11]:
            for i in range(20):
                event = {
                    "tpep_pickup_datetime": f"2024-01-15T{hour:02d}:30:00",
                    "PULocationID": 161,
                    "fare_amount": 15.0 + i
                }
                engine.update("fare_amount", 15.0 + i, event)

        # Query with original context (only 10 samples)
        query_event = {
            "tpep_pickup_datetime": "2024-01-15T10:45:00",
            "PULocationID": 161
        }

        result = engine.get_threshold_with_fallback(
            field="fare_amount",
            percentile="p90",
            event=query_event
        )

        # Should fall back to level 1 (morning bucket)
        assert result is not None
        assert result["level"] >= 1


class TestContextAwareStats:
    """Test get_stats_for_context()."""

    def test_get_stats_for_specific_context(self):
        """get_stats_for_context() returns stats for exact context."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=5,
            recompute_every=5
        )

        # Add morning midtown events
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,
                "fare_amount": 15.0 + i
            }
            engine.update("fare_amount", 15.0 + i, event)

        # Get stats for same context
        context = registry.resolve({
            "tpep_pickup_datetime": "2024-01-15T10:45:00",
            "PULocationID": 161
        })

        stats = engine.get_stats_for_context(
            field="fare_amount",
            context=context,
            level=0
        )

        assert stats is not None
        assert "p90" in stats
        assert "count" in stats
        assert stats["count"] == 10
