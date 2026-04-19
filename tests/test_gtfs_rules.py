"""
Unit tests for GTFS-specific data quality rules.
"""
from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from streamdq.rules.gtfs_rules import (
    GTFSVehicleIDValidRule,
    GTFSLatLongRangeRule,
    GTFSSpeedRangeRule,
    GTFSImpossibleSpeedRule,
    GTFSStaleDataRule,
    evaluate_gtfs_trajectory_anomaly,
    evaluate_gtfs_duplicate_event,
    reset_gtfs_cross_record_state,
    _haversine_km,
)
from streamdq.rules.base import RuleContext


class TestGTFSSyntacticRules:
    """Tests for GTFS syntactic rules."""

    def make_ctx(self, event: dict) -> RuleContext:
        return RuleContext(
            event=event,
            event_time=datetime.now(),
            historical_stats={},
            external_context=None,
        )

    def test_vehicle_id_valid(self):
        """Valid vehicle_id should pass."""
        rule = GTFSVehicleIDValidRule()
        ctx = self.make_ctx({"vehicle_id": "BUS-KL-001"})
        assert rule.evaluate(ctx) is None

    def test_vehicle_id_missing(self):
        """Missing vehicle_id should return violation."""
        rule = GTFSVehicleIDValidRule()
        ctx = self.make_ctx({"vehicle_id": None})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "GTFSSyn001"
        assert v.severity == "HIGH"

    def test_vehicle_id_empty_string(self):
        """Empty string vehicle_id should return violation."""
        rule = GTFSVehicleIDValidRule()
        ctx = self.make_ctx({"vehicle_id": "  "})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "MISSING_OR_EMPTY"

    def test_lat_long_valid(self):
        """Valid lat/lon should pass."""
        rule = GTFSLatLongRangeRule()
        ctx = self.make_ctx({"latitude": 3.139, "longitude": 101.687, "vehicle_id": "BUS-001"})
        assert rule.evaluate(ctx) is None

    def test_latitude_out_of_range(self):
        """Latitude > 90 should return violation."""
        rule = GTFSLatLongRangeRule()
        ctx = self.make_ctx({"latitude": 95.0, "longitude": 101.687, "vehicle_id": "BUS-001"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "GTFSSyn002"
        assert v.severity == "CRITICAL"

    def test_longitude_out_of_range(self):
        """Longitude > 180 should return violation."""
        rule = GTFSLatLongRangeRule()
        ctx = self.make_ctx({"latitude": 3.139, "longitude": 200.0, "vehicle_id": "BUS-001"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["field"] == "longitude"

    def test_speed_valid(self):
        """Valid speed should pass."""
        rule = GTFSSpeedRangeRule()
        ctx = self.make_ctx({"speed": 60.0, "vehicle_id": "BUS-001"})
        assert rule.evaluate(ctx) is None

    def test_speed_negative(self):
        """Negative speed should return violation."""
        rule = GTFSSpeedRangeRule()
        ctx = self.make_ctx({"speed": -5.0, "vehicle_id": "BUS-001"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "NEGATIVE_VALUE"

    def test_speed_exceeds_max(self):
        """Speed > 300 km/h should return violation."""
        rule = GTFSSpeedRangeRule()
        ctx = self.make_ctx({"speed": 350.0, "vehicle_id": "BUS-001"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.details["reason"] == "EXCEEDS_MAX"


class TestGTFSSemanticRules:
    """Tests for GTFS semantic rules."""

    def make_ctx(self, event: dict, event_time=None) -> RuleContext:
        return RuleContext(
            event=event,
            event_time=event_time or datetime.now(),
            historical_stats={},
            external_context=None,
        )

    def test_impossible_speed(self):
        """Speed > 200 km/h should return violation."""
        rule = GTFSImpossibleSpeedRule()
        ctx = self.make_ctx({"speed": 250.0, "vehicle_id": "BUS-001"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "GTFSSem001"
        assert v.severity == "CRITICAL"
        assert v.details["reason"] == "IMPOSSIBLE_FOR_TRANSIT"

    def test_reasonable_speed(self):
        """Speed <= 200 km/h should pass."""
        rule = GTFSImpossibleSpeedRule()
        ctx = self.make_ctx({"speed": 120.0, "vehicle_id": "BUS-001"})
        assert rule.evaluate(ctx) is None

    def test_stale_data(self):
        """Position older than 5 minutes should return violation."""
        rule = GTFSStaleDataRule()
        old_time = datetime.now() - timedelta(minutes=10)
        ctx = self.make_ctx(
            {"timestamp": old_time.isoformat(), "vehicle_id": "BUS-001"},
            event_time=datetime.now(),
        )
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "GTFSSem002"
        assert v.severity == "MEDIUM"
        assert v.details["reason"] == "STALE_DATA"

    def test_fresh_data(self):
        """Recent position should pass."""
        rule = GTFSStaleDataRule()
        recent_time = datetime.now() - timedelta(minutes=1)
        ctx = self.make_ctx(
            {"timestamp": recent_time.isoformat(), "vehicle_id": "BUS-001"},
            event_time=datetime.now(),
        )
        assert rule.evaluate(ctx) is None


class TestGTFSCrossRecordRules:
    """Tests for GTFS cross-record rules."""

    def setup_method(self):
        reset_gtfs_cross_record_state()

    def test_trajectory_teleport(self):
        """GPS teleport should be detected."""
        event1 = {
            "vehicle_id": "BUS-KL-001",
            "latitude": 3.139,  # KL
            "longitude": 101.687,
            "timestamp": datetime.now().isoformat(),
        }
        # Same timestamp but different location (teleport)
        event2 = {
            "vehicle_id": "BUS-KL-001",
            "latitude": 5.414,  # ~260 km away (Penang)
            "longitude": 100.328,
            "timestamp": datetime.now().isoformat(),
        }
        result1 = evaluate_gtfs_trajectory_anomaly(event1, datetime.now(), 0.0)
        assert result1 is None  # First observation
        result2 = evaluate_gtfs_trajectory_anomaly(event2, datetime.now(), 0.0)
        assert result2 is not None
        assert result2[0].rule_id == "GTFSCRS001"
        assert result2[0].details["reason"] == "GPS_TELEPORT"

    def test_duplicate_position(self):
        """Duplicate position reports should be detected."""
        vehicle = {
            "vehicle_id": "BUS-KL-001",
            "latitude": 3.139,
            "longitude": 101.687,
            "timestamp": datetime.now().isoformat(),
        }
        now = datetime.now()
        result1 = evaluate_gtfs_duplicate_event(vehicle, now, 0.0)
        assert result1 is None  # First occurrence
        result2 = evaluate_gtfs_duplicate_event(vehicle, now, 0.0)
        assert result2 is not None
        assert result2[0].rule_id == "GTFSCRS002"

    def test_non_duplicate_different_position(self):
        """Different position with same vehicle_id should not be duplicate."""
        vehicle1 = {
            "vehicle_id": "BUS-KL-001",
            "latitude": 3.139,
            "longitude": 101.687,
            "timestamp": datetime.now().isoformat(),
        }
        vehicle2 = {
            "vehicle_id": "BUS-KL-001",
            "latitude": 3.150,  # Slightly different
            "longitude": 101.700,
            "timestamp": datetime.now().isoformat(),
        }
        now = datetime.now()
        assert evaluate_gtfs_duplicate_event(vehicle1, now, 0.0) is None
        assert evaluate_gtfs_duplicate_event(vehicle2, now, 0.0) is None


class TestHaversineDistance:
    """Tests for haversine distance calculation."""

    def test_kl_to_ipoh(self):
        """Haversine KL to Ipoh (~175 km)."""
        dist = _haversine_km(3.139, 101.687, 4.597, 101.091)
        assert 165 < dist < 185

    def test_same_point(self):
        """Same point should be distance 0."""
        dist = _haversine_km(3.139, 101.687, 3.139, 101.687)
        assert dist == 0.0
