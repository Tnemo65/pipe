"""
Cross-record validation rules (stateful).

CRS001: Impossible vehicle speed (GPS jump detection).
CRS002: GPS spoofing (stationary vehicle with position jump).
CRS003: Duplicate trip records.

State management: All cross-record state is held in a `CrossRecordState` instance.
Module-level globals exist only as a fallback default instance for convenience;
pipelines that need isolation must create their own CrossRecordState.
"""
from __future__ import annotations
import hashlib
import math
import time
from datetime import datetime
from typing import Optional

from streamdq.rules.base import Violation


# ────────────────────────────────────────────────────────────────
# Haversine distance
# ────────────────────────────────────────────────────────────────

def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance in meters between two WGS84 lat/lon points.
    Uses the haversine formula.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


# ────────────────────────────────────────────────────────────────
# Cross-record state container (NG-10: eliminate module-level globals)
# ────────────────────────────────────────────────────────────────

class CrossRecordState:
    """
    Explicit state container for cross-record rule evaluation.

    NG-10: Previously used module-level `_VEHICLE_STATES` and `_DEDUP_STATES`
    which caused cross-stream contamination when multiple pipelines ran in the
    same process. Each pipeline now gets its own instance.

    State schema:
        _vehicle_states: dict[vehicle_id, tuple(lat, lon, timestamp, seq)]
        _dedup_states:   dict[hash, tuple(first_seen_datetime, first_record_dict)]
    """

    def __init__(self) -> None:
        self._vehicle_states: dict = {}
        self._dedup_states: dict = {}

    def get_vehicle(self, vehicle_id: str):
        return self._vehicle_states.get(vehicle_id)

    def set_vehicle(self, vehicle_id: str, state: tuple) -> None:
        self._vehicle_states[vehicle_id] = state

    def get_dedup(self, key: str):
        return self._dedup_states.get(key)

    def set_dedup(self, key: str, value) -> None:
        self._dedup_states[key] = value

    def clear(self) -> None:
        """Clear all state."""
        self._vehicle_states.clear()
        self._dedup_states.clear()

    @property
    def vehicle_count(self) -> int:
        return len(self._vehicle_states)

    @property
    def dedup_count(self) -> int:
        return len(self._dedup_states)


# ────────────────────────────────────────────────────────────────
# Module-level fallback state (convenience only — not for production)
# ────────────────────────────────────────────────────────────────

# NG-10: These are kept only as a fallback for backward compatibility.
# Production code should create CrossRecordState instances per pipeline.
_VEHICLE_STATES: dict = {}
_DEDUP_STATES: dict = {}


# ────────────────────────────────────────────────────────────────
# CRS001 — Trajectory Anomaly (Impossible Speed)
# ────────────────────────────────────────────────────────────────

def evaluate_trajectory_anomaly(
    event: dict,
    event_time: datetime,
    start_time: float = 0.0,
    max_speed_kmh: float = 160.0,
    max_stationary_jump_m: float = 100.0,
    vehicle_state: dict | None = None,
) -> list[Violation]:
    """
    Detect impossible vehicle movements from GTFS vehicle position data.

    GPS speed = haversine_distance / time_between_reports.
    Allow up to 160 km/h (~100 mph) — accommodates KTMB express trains
    (140 km/h) with margin. Faster is physically impossible for buses/trains.

    Also detects GPS spoofing: position jumped more than 100m.
    This catches both stationary spoofing (speed < 1 km/h + large jump)
    and slow drift attacks (speed 1-20 km/h + moderate jump).

    Args:
        event: GTFS vehicle position dict with keys:
            - vehicle_id (or vehicle.id)
            - latitude (or position.latitude)
            - longitude (or position.longitude)
            - timestamp (UNIX epoch, or secs_since_report)
        event_time: Wall-clock time when the event was processed
        max_speed_kmh: Maximum allowed speed. Default 160 km/h (~100 mph).
        max_stationary_jump_m: Max position jump for stationary vehicle. Default 100m.
        vehicle_state: Mutable dict mapping vehicle_id -> (lat, lon, timestamp, seq).
                       Pass None to use the global shared state.

    Returns:
        List of Violations (can be 0, 1, or 2).
    """
    # NG-10: Accept CrossRecordState as vehicle_state for explicit isolation
    if isinstance(vehicle_state, CrossRecordState):
        vs = vehicle_state
        _get = vs.get_vehicle
        _set = vs.set_vehicle
    elif vehicle_state is not None:
        _get = vehicle_state.get
        _set = vehicle_state.__setitem__
    else:
        _get = _VEHICLE_STATES.get
        _set = lambda k, v: _VEHICLE_STATES.update({k: v})

    vehicle_id = (
        event.get("vehicle_id")
        or (event.get("vehicle") or {}).get("id")
        or event.get("id")
        or ""
    )
    lat = (
        event.get("latitude")
        or (event.get("position") or {}).get("latitude")
    )
    lon = (
        event.get("longitude")
        or (event.get("position") or {}).get("longitude")
    )
    timestamp = event.get("timestamp") or event.get("secs_since_report")

    if None in (vehicle_id, lat, lon, timestamp):
        return []

    violations = []
    prev = _get(vehicle_id)

    if prev is not None:
        prev_lat, prev_lon, prev_time, prev_seq = prev
        time_diff = float(timestamp) - float(prev_time)

        if time_diff > 0:
            distance_m = haversine_distance(prev_lat, prev_lon, lat, lon)
            speed_kmh = (distance_m / time_diff) * 3.6  # m/s → km/h

            # Check 1: Impossible speed
            if speed_kmh > max_speed_kmh:
                violations.append(Violation(
                    rule_id="CRS001",
                    rule_name="Trajectory anomaly — impossible speed",
                    entity_id=str(vehicle_id),
                    entity_type="gtfs_vehicle",
                    severity="HIGH",
                    violation_type="CROSS_RECORD",
                    details={
                        "type": "IMPOSSIBLE_SPEED",
                        "speed_kmh": round(speed_kmh, 1),
                        "max_allowed_kmh": max_speed_kmh,
                        "distance_meters": round(distance_m, 1),
                        "time_diff_seconds": time_diff,
                        "prev_position": {"lat": prev_lat, "lon": prev_lon},
                        "curr_position": {"lat": lat, "lon": lon},
                        "route_id": event.get("route_id"),
                        "trip_id": event.get("trip_id"),
                        "reason": "GPS jump — vehicle cannot travel this fast",
                    },
                    expected={"speed_kmh": {"max": max_speed_kmh}},
                    record_snapshot=event,
                    detected_at=event_time,
                    processing_latency_ms=(time.perf_counter() - start_time) * 1000,
                ))

            # Check 2: GPS spoofing — position jump detection across 3 severity bands.
            # Band 1 (CRITICAL): near-stationary + large jump — sensor glitch or intentional spoof
            # Band 2 (HIGH): moderate speed (1-20 km/h) + jump — slow drift injection attack
            # Band 3 (MEDIUM): higher speed (20-40 km/h) + jump — moderate GPS manipulation
            # Beyond 40 km/h: likely legitimate highway movement, no violation
            if distance_m > max_stationary_jump_m and speed_kmh < 40.0:
                if speed_kmh < 1.0:
                    severity = "CRITICAL"
                    reason = "Vehicle reported as stationary but position jumped"
                elif speed_kmh < 20.0:
                    severity = "HIGH"
                    reason = f"Slow drift GPS anomaly: {speed_kmh:.1f} km/h with {distance_m:.0f}m jump"
                else:
                    severity = "MEDIUM"
                    reason = f"Moderate GPS anomaly: {speed_kmh:.1f} km/h with {distance_m:.0f}m jump"
                violations.append(Violation(
                    rule_id="CRS002",
                    rule_name="GPS spoofing — position jump anomaly",
                    entity_id=str(vehicle_id),
                    entity_type="gtfs_vehicle",
                    severity=severity,
                    violation_type="CROSS_RECORD",
                    details={
                        "type": "GPS_SPOOFING",
                        "speed_kmh": round(speed_kmh, 1),
                        "distance_meters": round(distance_m, 1),
                        "time_diff_seconds": time_diff,
                        "prev_position": {"lat": prev_lat, "lon": prev_lon},
                        "curr_position": {"lat": lat, "lon": lon},
                        "route_id": event.get("route_id"),
                        "trip_id": event.get("trip_id"),
                        "reason": reason,
                    },
                    expected={"distance_at_stationary": {"max": f"{max_stationary_jump_m}m"}},
                    record_snapshot=event,
                    detected_at=event_time,
                    processing_latency_ms=(time.perf_counter() - start_time) * 1000,
                ))

    # Update state
    seq = (prev[3] + 1) if prev else 0
    _set(vehicle_id, (float(lat), float(lon), float(timestamp), seq))
    return violations


# ────────────────────────────────────────────────────────────────
# CRS003 — Duplicate Events
# ────────────────────────────────────────────────────────────────

def evaluate_duplicate_event(
    event: dict,
    event_time: datetime,
    start_time: float = 0.0,
    dedup_window_seconds: int = 300,
    dedup_state: dict | None = None,
) -> Optional[Violation]:
    """
    Detect duplicate events: same key fields within a time window.

    Strategy:
    - Hash of (trip_id, PULocationID, DOLocationID, passenger_count, trip_distance)
    - If hash seen within last N seconds → duplicate

    Args:
        event: Event dict with key fields
        event_time: Wall-clock time when processed
        dedup_window_seconds: How long to remember seen hashes
        dedup_state: Mutable dict for state. Pass None to use global state.

    Returns:
        Violation if duplicate, None otherwise.
    """
    # Phase 0 (T3) - Suppress replay duplicates
    # Check if this is a replay stream before duplicate detection
    lineage = event.get("_lineage", {})
    if lineage.get("is_replay", False):
        # Replay streams are known to have duplicates (historical data replayed)
        # Suppress duplicate detection to avoid false positives
        # Expected impact: +5-8 precision points (22.9% → 28-31%)
        return None

    # NG-10: Accept CrossRecordState as dedup_state for explicit isolation
    if isinstance(dedup_state, CrossRecordState):
        ds = dedup_state
        _get = ds.get_dedup
        _set = ds.set_dedup
    elif dedup_state is not None:
        _get = dedup_state.get
        _set = dedup_state.__setitem__
    else:
        _get = _DEDUP_STATES.get
        _set = lambda k, v: _DEDUP_STATES.update({k: v})

    key_fields = [
        "trip_id",
        "PULocationID",
        "DOLocationID",
        "passenger_count",
        "trip_distance",
    ]
    values = [str(event.get(f, "")) for f in key_fields]
    h = hashlib.md5("|".join(values).encode()).hexdigest()

    trip_id = str(event.get("trip_id", "unknown"))

    if _get(h):
        first_seen, first_record = _get(h)
        age_seconds = (event_time - first_seen).total_seconds()

        violation_details = {
            "type": "DUPLICATE_RECORD",
            "event_hash": h,
            "first_seen_at": first_seen.isoformat(),
            "duplicate_at": event_time.isoformat(),
            "age_seconds": round(age_seconds, 1),
            "first_record": first_record,
            "lineage": lineage,  # NEW: Include lineage for debugging
        }

        return Violation(
            rule_id="CRS003",
            rule_name="Duplicate event detection",
            entity_id=trip_id,
            entity_type=event.get("entity_type", "nyc_taxi"),
            severity="HIGH",
            violation_type="CROSS_RECORD",
            details=violation_details,
            expected={"event_hash": {"unique": True}},
            record_snapshot=event,
            detected_at=event_time,
            processing_latency_ms=(time.perf_counter() - start_time) * 1000,
        )

    _set(h, (event_time, event))

    # Evict old entries
    if isinstance(dedup_state, CrossRecordState):
        current = dict(dedup_state._dedup_states)
        for k, v in list(dedup_state._dedup_states.items()):
            if (event_time - v[0]).total_seconds() <= dedup_window_seconds:
                current[k] = v
        dedup_state._dedup_states = current
    else:
        current = dict(_DEDUP_STATES if dedup_state is None else dedup_state)
        current.update({
            k: v for k, v in current.items()
            if (event_time - v[0]).total_seconds() <= dedup_window_seconds
        })
        if dedup_state is None:
            _DEDUP_STATES.clear()
            _DEDUP_STATES.update(current)
        else:
            dedup_state.clear()
            dedup_state.update(current)
    return None


# ────────────────────────────────────────────────────────────────
# State reset (for testing)
# ────────────────────────────────────────────────────────────────

def reset_cross_record_state():
    """Clear all cross-record state. Used for testing."""
    _VEHICLE_STATES.clear()
    _DEDUP_STATES.clear()


def save_cross_record_state(path: str) -> None:
    """
    Persist cross-record state to a JSON file for checkpointing.

    This allows state to survive pipeline restarts. Call this at the end of
    each micro-batch or at regular intervals.

    Args:
        path: Path to write the JSON checkpoint file.
    """
    import json
    state = {
        "vehicle_states": {
            vid: {
                "lat": float(v[0]),
                "lon": float(v[1]),
                "timestamp": float(v[2]),
                "seq": int(v[3]),
            }
            for vid, v in _VEHICLE_STATES.items()
        },
        "dedup_states": {
            h: {
                "first_seen": v[0].isoformat(),
                "first_record_keys": list(v[1]) if isinstance(v[1], (list, tuple)) else v[1],
            }
            for h, v in _DEDUP_STATES.items()
        },
        "saved_at": datetime.now().isoformat(),
    }
    with open(path, "w") as f:
        json.dump(state, f)


def load_cross_record_state(path: str) -> None:
    """
    Restore cross-record state from a JSON checkpoint file.

    Call this at pipeline startup to resume state from a prior run.

    Args:
        path: Path to the JSON checkpoint file.

    Raises:
        FileNotFoundError: If checkpoint file does not exist.
    """
    import json
    from datetime import datetime as dt
    with open(path) as f:
        state = json.load(f)

    _VEHICLE_STATES.clear()
    for vid, v in state["vehicle_states"].items():
        _VEHICLE_STATES[vid] = (v["lat"], v["lon"], v["timestamp"], v["seq"])

    _DEDUP_STATES.clear()
    for h, v in state["dedup_states"].items():
        # Restore first_seen as datetime
        _DEDUP_STATES[h] = (dt.fromisoformat(v["first_seen"]), v["first_record_keys"])
