"""
Unit tests for semantic rules (SEM001, SEM002, SEM003).
"""
from __future__ import annotations
import pytest
import time
from datetime import datetime, timedelta
from streamdq.rules.semantic import (
    FareRangeRule,
    TripDurationSanityRule,
    AverageSpeedSanityRule,
)
from streamdq.rules.syntactic import _isnan
from streamdq.rules.base import RuleContext


def make_ctx(
    event: dict,
    event_time: datetime = None,
    historical_stats: dict = None,
    start_time: float = None,
    external_context: dict = None,
) -> RuleContext:
    if event_time is None:
        event_time = datetime.now()
    if start_time is None:
        start_time = time.perf_counter()
    return RuleContext(
        event=event,
        event_time=event_time,
        historical_stats=historical_stats or {},
        external_context=external_context or {},
        start_time=start_time,
    )


class TestFareRangeRule:
    """Tests for SEM001 — Fare range check."""

    def test_normal_fare_no_stats(self):
        """Without historical stats, uses static fallback bounds."""
        rule = FareRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 25.0})
        assert rule.evaluate(ctx) is None  # 2.5 < 25 < 500

    def test_fare_too_low_no_stats(self):
        rule = FareRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 1.0})  # Below 2.5
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SEM001"
        assert v.details["threshold_source"] == "static_fallback"

    def test_fare_too_high_no_stats(self):
        rule = FareRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 600.0})  # Above 500
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["threshold_source"] == "static_fallback"

    def test_fare_with_adaptive_stats(self):
        """With historical stats, uses P10-P90*2 range."""
        rule = FareRangeRule()
        stats = {"fare_amount": {"p10": 5.0, "p90": 40.0}}
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 90.0}, historical_stats=stats)
        # 40 * 2 = 80, 90 > 80 → violation
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["threshold_source"] == "adaptive"

    def test_long_trip_justifies_higher_fare(self):
        """Very long trips (distance > 20 miles) get fare multiplier."""
        rule = FareRangeRule()
        stats = {"fare_amount": {"p10": 5.0, "p90": 40.0}}
        ctx = make_ctx({
            "trip_id": "T1",
            "fare_amount": 90.0,
            "trip_distance": 30.0,  # > 20 miles
        }, historical_stats=stats)
        # Base max = 40 * 2 = 80; adjusted = 80 * (1 + (30-20)*0.05) = 80 * 1.5 = 120
        assert rule.evaluate(ctx) is None

    def test_null_fare_passes(self):
        """Null fare is caught by SYN001, not SEM001."""
        rule = FareRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": None})
        assert rule.evaluate(ctx) is None

    def test_nan_fare_returns_violation(self):
        """NaN fare must be caught by SEM001 (F1-a fix)."""
        rule = FareRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": float("nan")})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SEM001"
        assert v.details["reason"] == "NAN_VALUE"
        assert v.processing_latency_ms > 0

    def test_nan_fare_python_float_returns_violation(self):
        """Python float nan (not numpy.nan) must be caught."""
        rule = FareRangeRule()
        nan = float("nan")
        ctx = make_ctx({"trip_id": "T1", "fare_amount": nan})
        assert _isnan(nan) is True
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "NAN_VALUE"

    def test_rush_hour_expands_fare_max(self):
        """Rush hour: fare_max increases by 1.3x."""
        rule = FareRangeRule()
        ctx = make_ctx(
            {"trip_id": "T1", "fare_amount": 100.0},
            external_context={"is_rush_hour": True, "is_late_night": False,
                             "is_weekend": False, "is_holiday": False},
        )
        # Static max = 500; rush hour = 500 * 1.3 = 650; 100 < 650 → pass
        assert rule.evaluate(ctx) is None

    def test_rush_hour_expands_fare_max_adaptive(self):
        """Rush hour with adaptive stats: P90*2*1.3 should expand threshold."""
        rule = FareRangeRule()
        stats = {"fare_amount": {"p10": 5.0, "p90": 100.0}}  # max=200
        ctx = make_ctx(
            {"trip_id": "T1", "fare_amount": 290.0},  # > 200 but < 260
            historical_stats=stats,
            external_context={"is_rush_hour": True, "is_late_night": False,
                             "is_weekend": False, "is_holiday": False},
        )
        # Base max = 200; rush hour = 200 * 1.3 = 260; 290 > 260 → violation
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["threshold_source"] == "adaptive"
        assert v.details["is_rush_hour"] is True

    def test_weekend_expands_fare_max(self):
        """Weekend: fare_max increases by 1.15x."""
        rule = FareRangeRule()
        stats = {"fare_amount": {"p10": 5.0, "p90": 100.0}}  # max=200
        ctx = make_ctx(
            {"trip_id": "T1", "fare_amount": 240.0},  # > 200 but < 230
            historical_stats=stats,
            external_context={"is_rush_hour": False, "is_late_night": False,
                             "is_weekend": True, "is_holiday": False},
        )
        # Base max = 200; weekend = 200 * 1.15 = 230; 240 > 230 → violation
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["is_weekend"] is True

    def test_holiday_expands_fare_range(self):
        """Holiday: fare_min decreases 0.8x and fare_max increases 1.5x."""
        rule = FareRangeRule()
        stats = {"fare_amount": {"p10": 5.0, "p90": 100.0}}  # min=5, max=200
        ctx = make_ctx(
            {"trip_id": "T1", "fare_amount": 3.5},  # < 5*0.8=4.0
            historical_stats=stats,
            external_context={"is_rush_hour": False, "is_late_night": False,
                             "is_weekend": False, "is_holiday": True},
        )
        # min = 5 * 0.8 = 4.0; 3.5 < 4.0 → violation (below holiday min)
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["is_holiday"] is True

    def test_late_night_contracts_fare_max(self):
        """Late night: fare_max decreases by 0.7x."""
        rule = FareRangeRule()
        ctx = make_ctx(
            {"trip_id": "T1", "fare_amount": 400.0},  # > 350 but < 500
            external_context={"is_rush_hour": False, "is_late_night": True,
                             "is_weekend": False, "is_holiday": False},
        )
        # Static max = 500; late night = 500 * 0.7 = 350; 400 > 350 → violation
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["is_late_night"] is True


class TestTripDurationSanityRule:
    """Tests for SEM002 — Trip duration sanity."""

    def _make_event(self, pickup_offset_hours: float, dropoff_offset_hours: float) -> dict:
        pickup = (datetime.now() + timedelta(hours=pickup_offset_hours)).isoformat()
        dropoff = (datetime.now() + timedelta(hours=dropoff_offset_hours)).isoformat()
        return {"trip_id": "T1", "tpep_pickup_datetime": pickup, "tpep_dropoff_datetime": dropoff}

    def test_normal_duration(self):
        rule = TripDurationSanityRule()
        ctx = make_ctx(self._make_event(-2, -1))  # 1 hour trip
        assert rule.evaluate(ctx) is None

    def test_minimum_valid_duration(self):
        rule = TripDurationSanityRule()
        # 1.001 minutes = 60.06 seconds (>= 60 seconds minimum)
        ctx = make_ctx(self._make_event(-0.0167, 0))  # ~1 minute
        assert rule.evaluate(ctx) is None

    def test_duration_too_short(self):
        rule = TripDurationSanityRule()
        ctx = make_ctx(self._make_event(-0.01, 0))  # 30 seconds
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SEM002"
        assert v.details["reason"] == "TOO_SHORT"

    def test_latency_computed(self):
        """Violation must have non-zero processing_latency_ms."""
        rule = TripDurationSanityRule()
        start = time.perf_counter()
        ctx = make_ctx(self._make_event(-0.01, 0), start_time=start)
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.processing_latency_ms > 0

    def test_duration_too_long(self):
        rule = TripDurationSanityRule()
        ctx = make_ctx(self._make_event(-25, 0))  # 25 hours
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "TOO_LONG"

    def test_negative_duration(self):
        """Dropoff before pickup (dropoff_offset < pickup_offset)."""
        rule = TripDurationSanityRule()
        ctx = make_ctx(self._make_event(0, -1))  # Dropoff 1 hour BEFORE pickup
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "TOO_SHORT"

    def test_custom_duration_bounds(self):
        rule = TripDurationSanityRule(min_duration_minutes=5, max_duration_hours=2)
        ctx = make_ctx(self._make_event(-0.05, 0))  # 3 minutes
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "TOO_SHORT"


class TestAverageSpeedSanityRule:
    """Tests for SEM003 — Average speed sanity."""

    def _make_event(self, distance: float, duration_minutes: float) -> dict:
        pickup = (datetime.now() - timedelta(minutes=duration_minutes)).isoformat()
        dropoff = datetime.now().isoformat()
        return {
            "trip_id": "T1",
            "trip_distance": distance,
            "tpep_pickup_datetime": pickup,
            "tpep_dropoff_datetime": dropoff,
        }

    def test_normal_speed(self):
        """10 miles in 30 minutes = 20 mph (valid)."""
        rule = AverageSpeedSanityRule()
        ctx = make_ctx(self._make_event(10.0, 30))
        assert rule.evaluate(ctx) is None

    def test_speed_at_limit(self):
        """80 mph (max allowed) should pass."""
        rule = AverageSpeedSanityRule(max_speed_mph=80.0)
        # 80 miles in 60 minutes = 80 mph
        ctx = make_ctx(self._make_event(80.0, 60))
        assert rule.evaluate(ctx) is None

    def test_speed_too_high(self):
        """100 mph > 80 mph → violation."""
        rule = AverageSpeedSanityRule(max_speed_mph=80.0)
        # 100 miles in 60 minutes = 100 mph
        ctx = make_ctx(self._make_event(100.0, 60))
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SEM003"
        assert v.details["reason"] == "EXCEEDS_MAX_SPEED"

    def test_zero_distance(self):
        rule = AverageSpeedSanityRule()
        ctx = make_ctx(self._make_event(0, 30))
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "ZERO_OR_NEGATIVE_DISTANCE"

    def test_negative_distance(self):
        rule = AverageSpeedSanityRule()
        ctx = make_ctx(self._make_event(-5.0, 30))
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "ZERO_OR_NEGATIVE_DISTANCE"

    def test_duration_too_short_skipped(self):
        """Duration < 1 minute → checked by SEM002, SEM003 skips."""
        rule = AverageSpeedSanityRule()
        ctx = make_ctx(self._make_event(100.0, 0.5))  # 30 seconds
        assert rule.evaluate(ctx) is None  # Skipped (SEM003 returns None, SEM002 catches)

    def test_missing_fields_passes(self):
        """Missing distance → SEM003 returns None (no data to check)."""
        rule = AverageSpeedSanityRule()
        ctx = make_ctx({"trip_id": "T1"})
        assert rule.evaluate(ctx) is None

    def test_nan_distance_returns_violation(self):
        """NaN trip_distance must be caught by SEM003 (F1-b fix)."""
        rule = AverageSpeedSanityRule()
        event = {
            "trip_id": "T1",
            "trip_distance": float("nan"),
            "tpep_pickup_datetime": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "tpep_dropoff_datetime": datetime.now().isoformat(),
        }
        v = rule.evaluate(make_ctx(event))
        assert v is not None
        assert v.rule_id == "SEM003"
        assert v.details["reason"] == "NAN_VALUE"
        assert v.processing_latency_ms > 0
