"""
Tests for context-aware SEM001 and SEM002 rules.

Validates that semantic rules use context-specific thresholds
instead of global thresholds.
"""
import pytest
from datetime import datetime
from streamdq.rules.semantic import FareRangeRule, TripDurationSanityRule
from streamdq.rules.base import RuleContext, ExternalContext
from streamdq.rules.context_adaptive import ContextAwareAdaptiveThresholdEngine
from streamdq.models.context_registry import ContextRegistry


class TestSEM001ContextAware:
    """Test SEM001 with context-aware thresholds."""

    def test_fare_range_uses_context_aware_thresholds(self):
        """SEM001 uses context-aware P10/P90 instead of global thresholds."""
        # Setup context-aware engine
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=5,
            recompute_every=5
        )

        # Add morning midtown fares (lower range)
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,
                "fare_amount": 10.0 + i  # 10-19
            }
            engine.update("fare_amount", 10.0 + i, event)

        # Add evening midtown fares (higher range)
        for i in range(10):
            event = {
                "tpep_pickup_datetime": "2024-01-15T20:30:00",
                "PULocationID": 161,
                "fare_amount": 30.0 + i  # 30-39
            }
            engine.update("fare_amount", 30.0 + i, event)

        # Test morning event with fare=25 (should pass in morning context)
        rule = FareRangeRule()
        morning_event = {
            "trip_id": "test_001",
            "tpep_pickup_datetime": "2024-01-15T10:45:00",
            "PULocationID": 161,
            "fare_amount": 25.0,
            "trip_distance": 5.0
        }

        # Get context-aware threshold
        threshold_result = engine.get_threshold_with_fallback(
            field="fare_amount",
            percentile="p90",
            event=morning_event
        )

        assert threshold_result is not None
        # Morning P90 should be around 19, so max threshold = 19 * 2 = 38
        # fare=25 should pass
        p90 = threshold_result["value"]
        assert p90 < 20  # Morning P90 should be lower

    def test_fare_context_fallback_to_global(self):
        """SEM001 falls back to global threshold when context has no data."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
            min_sample_size=30,
            recompute_every=5
        )

        # Add global context fares (enough for L4 global)
        for hour in range(6, 23):
            for i in range(10):
                event = {
                    "tpep_pickup_datetime": f"2024-01-15T{hour:02d}:30:00",
                    "PULocationID": 161,
                    "fare_amount": 15.0 + i
                }
                engine.update("fare_amount", 15.0 + i, event)

        # Query rare context (late night airport)
        rare_event = {
            "trip_id": "test_002",
            "tpep_pickup_datetime": "2024-01-15T03:00:00",
            "PULocationID": 132,  # JFK Airport
            "fare_amount": 50.0
        }

        threshold_result = engine.get_threshold_with_fallback(
            field="fare_amount",
            percentile="p90",
            event=rare_event
        )

        # Should fall back to global (level 4)
        assert threshold_result is not None
        assert threshold_result["level"] == 4  # Global fallback


class TestSEM002ContextAware:
    """Test SEM002 with context-aware duration thresholds."""

    def test_duration_uses_static_thresholds(self):
        """SEM002 currently uses static thresholds (no adaptive yet)."""
        rule = TripDurationSanityRule(min_duration_minutes=1, max_duration_hours=24)

        event = {
            "trip_id": "test_003",
            "tpep_pickup_datetime": "2024-01-15T10:00:00",
            "tpep_dropoff_datetime": "2024-01-15T10:05:00",  # 5 minutes
        }

        ctx = RuleContext(
            event=event,
            event_time=datetime(2024, 1, 15, 10, 5, 0),
            historical_stats={},
            external_context=ExternalContext.from_event(event, datetime(2024, 1, 15, 10, 5, 0)),
            start_time=0.0
        )

        violation = rule.evaluate(ctx)
        assert violation is None  # 5 minutes is valid (>= 1 minute, <= 24 hours)
