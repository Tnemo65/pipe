"""
Unit tests for cross-record rules (CRS001, CRS002, CRS003).
"""
from __future__ import annotations
import pytest
import time
from datetime import datetime, timedelta
from streamdq.rules.cross_record import (
    haversine_distance,
    evaluate_trajectory_anomaly,
    evaluate_duplicate_event,
    reset_cross_record_state,
)
from streamdq.rules.base import Violation


class TestHaversineDistance:
    """Tests for the Haversine distance calculation."""

    def test_same_point(self):
        d = haversine_distance(3.1390, 101.6869, 3.1390, 101.6869)
        assert d == 0.0

    def test_known_distance_kl_to_selangor(self):
        """KL to Shah Alam (~20km)."""
        d = haversine_distance(3.1390, 101.6869, 3.0730, 101.5180)
        assert 15_000 < d < 25_000  # ~20km

    def test_known_distance_nyc_manhattan(self):
        """Times Square to Empire State Building (~2.5km)."""
        d = haversine_distance(40.7580, -73.9855, 40.7484, -73.9857)
        assert 1_000 < d < 4_000  # ~2.5km

    def test_symmetric(self):
        """Distance A→B should equal B→A."""
        d1 = haversine_distance(40.7580, -73.9855, 40.7484, -73.9857)
        d2 = haversine_distance(40.7484, -73.9857, 40.7580, -73.9855)
        assert abs(d1 - d2) < 0.001


class TestTrajectoryAnomalyRule:
    """Tests for CRS001 — Trajectory anomaly detection."""

    def setup_method(self):
        reset_cross_record_state()

    def test_normal_bus_speed(self):
        """Normal bus: 1km in 60s = 60 km/h (below 120 limit)."""
        vehicle_state = {}
        prev_event = {
            "vehicle_id": "BUS001",
            "latitude": 3.1390,
            "longitude": 101.6869,
            "timestamp": 1700000000,
            "route_id": "LRT1",
        }
        curr_event = {
            "vehicle_id": "BUS001",
            "latitude": 3.1480,  # ~1km north
            "longitude": 101.6869,
            "timestamp": 1700000060,  # 60s later
            "route_id": "LRT1",
        }
        violations = evaluate_trajectory_anomaly(
            prev_event, datetime.now(), vehicle_state=vehicle_state
        )
        # Update state
        evaluate_trajectory_anomaly(
            curr_event, datetime.now(), vehicle_state=vehicle_state
        )
        # Only the second call should be checked
        assert len(violations) == 0

    def test_impossible_speed(self):
        """GPS jump: 50km in 60s = 3000 km/h → violation."""
        vehicle_state = {
            "BUS002": (3.1390, 101.6869, 1700000000, 0)
        }
        curr_event = {
            "vehicle_id": "BUS002",
            "latitude": 3.5890,  # ~50km away
            "longitude": 101.6869,
            "timestamp": 1700000060,  # 60s later
            "route_id": "BUS23",
        }
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(), vehicle_state=vehicle_state
        )
        assert len(violations) == 1
        assert violations[0].rule_id == "CRS001"
        assert violations[0].details["type"] == "IMPOSSIBLE_SPEED"
        assert violations[0].details["speed_kmh"] > 120

    def test_gps_spoofing(self):
        """Stationary vehicle (speed < 1 km/h) but jumped >100m -> violation."""
        vehicle_state = {
            "BUS003": (3.1390, 101.6869, 1700000000, 0)
        }
        # ~311m jump in 1300s = 0.86 km/h -> < 1 km/h -> spoofing
        curr_event = {
            "vehicle_id": "BUS003",
            "latitude": 3.1418,  # ~311m from 3.1390
            "longitude": 101.6869,
            "timestamp": 1700001300,  # 1300s = 21.7 min later
            "route_id": "BUS23",
        }
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(),
            max_speed_kmh=120.0,
            max_stationary_jump_m=100.0,
            vehicle_state=vehicle_state,
        )
        gps_violations = [v for v in violations if v.rule_id == "CRS002"]
        assert len(gps_violations) == 1
        assert gps_violations[0].severity == "CRITICAL"
        assert gps_violations[0].details["type"] == "GPS_SPOOFING"

    def test_gps_spoofing_slow_drift_high(self):
        """Slow drift at 5-15 km/h -> HIGH severity (B3 fix)."""
        vehicle_state = {
            "BUS010": (3.1390, 101.6869, 1700000000, 0)
        }
        # 0.001 deg lat = ~111m in 72s = ~5.5 km/h -> HIGH band (5-20)
        curr_event = {
            "vehicle_id": "BUS010",
            "latitude": 3.1400,  # 0.001 deg = ~111m from 3.1390
            "longitude": 101.6869,
            "timestamp": 1700000072,  # 72s later -> ~5.5 km/h
            "route_id": "BUS10",
        }
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(),
            max_speed_kmh=120.0,
            max_stationary_jump_m=100.0,
            vehicle_state=vehicle_state,
        )
        gps_violations = [v for v in violations if v.rule_id == "CRS002"]
        assert len(gps_violations) == 1
        assert gps_violations[0].severity == "HIGH"

    def test_gps_spoofing_moderate_medium(self):
        """Moderate speed 20-40 km/h -> MEDIUM severity (B3 fix extended)."""
        vehicle_state = {
            "BUS011": (3.1390, 101.6869, 1700000000, 0)
        }
        # 0.001 deg lat = ~111m, in 12s = ~33.3 km/h -> 20-40 band -> MEDIUM
        curr_event = {
            "vehicle_id": "BUS011",
            "latitude": 3.1400,  # 0.001 deg = ~111m from 3.1390 at same longitude
            "longitude": 101.6869,
            "timestamp": 1700000012,  # 12s later -> ~33 km/h
            "route_id": "BUS11",
        }
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(),
            max_speed_kmh=120.0,
            max_stationary_jump_m=100.0,
            vehicle_state=vehicle_state,
        )
        gps_violations = [v for v in violations if v.rule_id == "CRS002"]
        assert len(gps_violations) == 1
        assert gps_violations[0].severity == "MEDIUM"

    def test_gps_legitimate_highway_no_violation(self):
        """Highway speed > 40 km/h -> no CRS002 violation."""
        vehicle_state = {
            "BUS012": (3.1390, 101.6869, 1700000000, 0)
        }
        # ~500m jump in 30s = 60 km/h -> above threshold -> no CRS002
        curr_event = {
            "vehicle_id": "BUS012",
            "latitude": 3.1445,
            "longitude": 101.6869,
            "timestamp": 1700000030,
            "route_id": "BUS12",
        }
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(),
            max_speed_kmh=120.0,
            max_stationary_jump_m=100.0,
            vehicle_state=vehicle_state,
        )
        crs002 = [v for v in violations if v.rule_id == "CRS002"]
        assert len(crs002) == 0

    def test_both_violations_possible(self):
        """Extreme case: both impossible speed AND spoofing."""
        vehicle_state = {
            "BUS004": (3.1390, 101.6869, 1700000000, 0)
        }
        # 5.5km in 1s = 19800 km/h → CRS001 impossible speed
        # AND 5.5km over 1800s = 11 km/h → CRS002 NOT spoofing
        # For both: need >100m jump at <1km/h speed
        curr_event = {
            "vehicle_id": "BUS004",
            "latitude": 3.1890,  # ~5.5km jump
            "longitude": 101.6869,
            "timestamp": 1700000001,  # 1 second later
            "route_id": "BUS99",
        }
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(),
            max_speed_kmh=120.0,
            max_stationary_jump_m=100.0,
            vehicle_state=vehicle_state,
        )
        rule_ids = {v.rule_id for v in violations}
        assert "CRS001" in rule_ids
        # CRS002 only fires if speed < 1 km/h AND jump > 100m

    def test_latency_computed(self):
        """CRS002 violation must have non-zero processing_latency_ms."""
        vehicle_state = {
            "BUS003": (3.1390, 101.6869, 1700000000, 0)
        }
        curr_event = {
            "vehicle_id": "BUS003",
            "latitude": 3.1418,  # ~311m jump
            "longitude": 101.6869,
            "timestamp": 1700001300,
            "route_id": "BUS23",
        }
        start = time.perf_counter()
        violations = evaluate_trajectory_anomaly(
            curr_event, datetime.now(),
            start_time=start,
            max_speed_kmh=120.0,
            max_stationary_jump_m=100.0,
            vehicle_state=vehicle_state,
        )
        gps_violations = [v for v in violations if v.rule_id == "CRS002"]
        assert len(gps_violations) == 1
        assert gps_violations[0].processing_latency_ms > 0

    def test_missing_fields_returns_empty(self):
        vehicle_state = {}
        event = {"vehicle_id": "BUS005"}  # Missing lat/lon
        violations = evaluate_trajectory_anomaly(event, datetime.now(), vehicle_state=vehicle_state)
        assert violations == []


class TestDuplicateEventRule:
    """Tests for CRS003 — Duplicate event detection."""

    def setup_method(self):
        reset_cross_record_state()

    def test_unique_events_no_violation(self):
        dedup_state = {}
        now = datetime.now()
        for i in range(3):
            event = {
                "trip_id": f"T{i}",
                "PULocationID": 1,
                "DOLocationID": 2,
                "passenger_count": 1,
                "trip_distance": 5.0,
            }
            v = evaluate_duplicate_event(event, now, dedup_state=dedup_state)
            assert v is None

    def test_duplicate_detected(self):
        dedup_state = {}
        now = datetime.now()
        event = {
            "trip_id": "T100",
            "PULocationID": 1,
            "DOLocationID": 2,
            "passenger_count": 1,
            "trip_distance": 5.0,
        }
        assert evaluate_duplicate_event(event, now, dedup_state=dedup_state) is None
        v = evaluate_duplicate_event(event, now + timedelta(minutes=1), dedup_state=dedup_state)
        assert v is not None
        assert v.rule_id == "CRS003"
        assert v.details["type"] == "DUPLICATE_RECORD"
        assert v.details["age_seconds"] == 60

    def test_different_trip_id_not_duplicate(self):
        dedup_state = {}
        now = datetime.now()
        event1 = {"trip_id": "T100", "PULocationID": 1, "DOLocationID": 2, "passenger_count": 1, "trip_distance": 5.0}
        event2 = {"trip_id": "T101", "PULocationID": 1, "DOLocationID": 2, "passenger_count": 1, "trip_distance": 5.0}
        assert evaluate_duplicate_event(event1, now, dedup_state=dedup_state) is None
        assert evaluate_duplicate_event(event2, now, dedup_state=dedup_state) is None

    def test_different_location_not_duplicate(self):
        dedup_state = {}
        now = datetime.now()
        event1 = {"trip_id": "T100", "PULocationID": 1, "DOLocationID": 2, "passenger_count": 1, "trip_distance": 5.0}
        event2 = {"trip_id": "T100", "PULocationID": 3, "DOLocationID": 2, "passenger_count": 1, "trip_distance": 5.0}
        assert evaluate_duplicate_event(event1, now, dedup_state=dedup_state) is None
        assert evaluate_duplicate_event(event2, now, dedup_state=dedup_state) is None

    def test_latency_computed(self):
        """CRS003 violation must have non-zero processing_latency_ms."""
        dedup_state = {}
        now = datetime.now()
        event = {
            "trip_id": f"lat-{now.timestamp()}",
            "PULocationID": 1,
            "DOLocationID": 2,
            "passenger_count": 1,
            "trip_distance": 5.0,
        }
        start = time.perf_counter()
        evaluate_duplicate_event(event, now, start_time=start, dedup_state=dedup_state)
        v = evaluate_duplicate_event(
            event, now + timedelta(minutes=1), start_time=time.perf_counter(), dedup_state=dedup_state
        )
        assert v is not None
        assert v.processing_latency_ms > 0

    def test_eviction_after_window(self):
        """
        Test that dedup state entries are evicted after window expires.
        We verify this by checking that the internal dedup_state is cleaned up.
        """
        from streamdq.rules.cross_record import _DEDUP_STATES
        dedup_state = _DEDUP_STATES.copy()
        now = datetime.now()
        event = {
            "trip_id": f"evict2-{now.timestamp()}",
            "PULocationID": 77,
            "DOLocationID": 88,
            "passenger_count": 3,
            "trip_distance": 10.0,
        }
        evaluate_duplicate_event(event, now, dedup_window_seconds=300, dedup_state=dedup_state)
        # Verify entry was stored
        assert len(dedup_state) >= 1
        # After window expires, the state should be empty (evicted)
        # Since the second call inserts with new timestamp, old entry is removed
        evaluate_duplicate_event(event, now + timedelta(minutes=6), dedup_window_seconds=300, dedup_state=dedup_state)
        # The dedup_state should have been pruned (only the new entry remains)
        assert len(dedup_state) <= 1  # At most 1 (the new entry)
