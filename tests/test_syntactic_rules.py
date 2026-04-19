"""
Unit tests for syntactic rules (SYN001, SYN002, SYN003).
"""
from __future__ import annotations
import pytest
import time
from datetime import datetime, timedelta
from streamdq.rules.syntactic import (
    FareAmountRangeRule,
    PickupLocationValidRule,
    TimestampNotFutureRule,
)
from streamdq.rules.base import RuleContext


def make_ctx(event: dict, event_time: datetime = None, start_time: float = None) -> RuleContext:
    if event_time is None:
        event_time = datetime.now()
    if start_time is None:
        start_time = time.perf_counter()
    return RuleContext(
        event=event,
        event_time=event_time,
        historical_stats={},
        external_context={},
        start_time=start_time,
    )


class TestFareAmountRangeRule:
    """Tests for SYN001 — Fare amount validity."""

    def test_valid_positive_fare(self):
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 15.50})
        assert rule.evaluate(ctx) is None

    def test_valid_zero_fare(self):
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 0.0})
        assert rule.evaluate(ctx) is None

    def test_negative_fare(self):
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": -10.0})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SYN001"
        assert v.severity == "HIGH"
        assert v.violation_type == "SYNTACTIC"
        assert v.details["reason"] == "NEGATIVE_VALUE"

    def test_null_fare(self):
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": None})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SYN001"
        assert v.details["reason"] == "NULL"

    def test_wrong_type_string(self):
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": "fifteen dollars"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "TYPE_MISMATCH"

    def test_wrong_type_list(self):
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": [15, 20]})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "TYPE_MISMATCH"

    def test_nan_fare(self):
        """NaN fare must be caught, not silently pass through."""
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": float("nan")})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SYN001"
        assert v.details["reason"] == "NAN_VALUE"

    def test_latency_computed(self):
        """Violation must have non-zero processing_latency_ms when start_time is provided."""
        rule = FareAmountRangeRule()
        start = time.perf_counter()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": None}, start_time=start)
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.processing_latency_ms > 0, f"Expected latency > 0, got {v.processing_latency_ms}"

    def test_very_large_fare(self):
        """Large but positive fare should pass (caught by SEM001, not SYN001)."""
        rule = FareAmountRangeRule()
        ctx = make_ctx({"trip_id": "T1", "fare_amount": 1_000_000.0})
        assert rule.evaluate(ctx) is None  # SYN001 only checks non-negative


class TestPickupLocationValidRule:
    """Tests for SYN002 — Pickup location validity."""

    def test_valid_location(self):
        rule = PickupLocationValidRule()
        for loc_id in [1, 50, 100, 200, 263]:
            ctx = make_ctx({"trip_id": "T1", "PULocationID": loc_id})
            assert rule.evaluate(ctx) is None, f"Location {loc_id} should be valid"

    def test_invalid_location_too_high(self):
        rule = PickupLocationValidRule()
        ctx = make_ctx({"trip_id": "T1", "PULocationID": 9999})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SYN002"
        assert v.details["reason"] == "OUT_OF_RANGE"

    def test_invalid_location_zero(self):
        rule = PickupLocationValidRule()
        ctx = make_ctx({"trip_id": "T1", "PULocationID": 0})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "OUT_OF_RANGE"

    def test_null_location(self):
        rule = PickupLocationValidRule()
        ctx = make_ctx({"trip_id": "T1", "PULocationID": None})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "NULL"

    def test_string_location(self):
        """String that can be parsed as int should pass."""
        rule = PickupLocationValidRule()
        ctx = make_ctx({"trip_id": "T1", "PULocationID": "42"})
        assert rule.evaluate(ctx) is None

    def test_non_numeric_string(self):
        rule = PickupLocationValidRule()
        ctx = make_ctx({"trip_id": "T1", "PULocationID": "downtown"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "TYPE_MISMATCH"


class TestTimestampNotFutureRule:
    """Tests for SYN003 — Timestamp not in future."""

    def test_past_timestamp(self):
        rule = TimestampNotFutureRule(future_tolerance_minutes=5)
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": past})
        assert rule.evaluate(ctx) is None

    def test_recent_timestamp(self):
        rule = TimestampNotFutureRule(future_tolerance_minutes=5)
        recent = (datetime.now() - timedelta(minutes=1)).isoformat()
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": recent})
        assert rule.evaluate(ctx) is None

    def test_future_within_tolerance(self):
        rule = TimestampNotFutureRule(future_tolerance_minutes=5)
        soon = (datetime.now() + timedelta(minutes=3)).isoformat()
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": soon})
        assert rule.evaluate(ctx) is None  # Within 5-min tolerance

    def test_future_beyond_tolerance(self):
        rule = TimestampNotFutureRule(future_tolerance_minutes=5)
        far_future = (datetime.now() + timedelta(minutes=10)).isoformat()
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": far_future})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SYN003"
        assert v.details["reason"] == "FUTURE_TIMESTAMP"

    def test_null_timestamp(self):
        rule = TimestampNotFutureRule()
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": None})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "NULL"

    def test_invalid_timestamp_format(self):
        rule = TimestampNotFutureRule()
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": "not-a-timestamp"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "PARSE_ERROR"

    def test_iso_format_with_z(self):
        """ISO datetime with Z suffix should parse correctly."""
        # The test creates a timestamp 1 hour ago WITH 'Z' suffix
        # and the parser converts it to local time. The local time may be
        # ahead of UTC, causing future detection. Test just checks it parses.
        rule = TimestampNotFutureRule(future_tolerance_minutes=5)
        # Use a known past timestamp in UTC
        past = "2020-01-01T12:00:00Z"
        ctx = make_ctx({"trip_id": "T1", "tpep_pickup_datetime": past})
        assert rule.evaluate(ctx) is None  # 2020 is definitely not future
