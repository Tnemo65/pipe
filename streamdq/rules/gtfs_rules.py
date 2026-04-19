"""
GTFS-specific data quality rules.

These rules validate GTFS Realtime VehiclePosition data (Malaysian transit).
GTFS data has different fields from NYC Taxi — it uses:
  - vehicle_id, latitude, longitude, bearing, speed, timestamp

These rules complement the NYC taxi rules (SYN001-003, SEM001-003).
They are NOT registered by default in build_default_registry() — register them
explicitly when processing GTFS streams.

Rule taxonomy:
  - GTFSSyn001-003: syntactic (format, range)
  - GTFSSem001-002: semantic (business logic)
  - GTFSCRSSyn001: cross-record (GTFS duplicate detection)
"""
from __future__ import annotations
import time
from datetime import datetime, timedelta
from typing import Optional

from streamdq.rules.base import DataQualityRule, RuleContext, Violation


# ────────────────────────────────────────────────────────────────
# GTFS Syntactic Rules
# ────────────────────────────────────────────────────────────────


class GTFSVehicleIDValidRule(DataQualityRule):
    """
    GTFSSyn001: Validate GTFS vehicle_id is non-empty.

    vehicle_id is the primary identifier for GTFS vehicles.
    Empty/null vehicle_id makes tracking impossible.

    Severity: HIGH
    """

    violation_type = "SYNTAX"

    def __init__(self, rule_id: str = "GTFSSyn001"):
        super().__init__(rule_id, "GTFS vehicle ID validity", severity="HIGH")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        vehicle_id = ctx.event.get("vehicle_id")
        if vehicle_id is None or str(vehicle_id).strip() == "":
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=str(vehicle_id) if vehicle_id else "unknown",
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "vehicle_id",
                    "value": str(vehicle_id),
                    "reason": "MISSING_OR_EMPTY",
                },
                expected={"vehicle_id": {"min_length": 1}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )
        return None


class GTFSLatLongRangeRule(DataQualityRule):
    """
    GTFSSyn002: Validate latitude and longitude are in valid ranges.

    Latitude: [-90, 90] degrees
    Longitude: [-180, 180] degrees

    Invalid coordinates indicate GPS sensor errors or data corruption.

    Severity: CRITICAL
    """

    violation_type = "SYNTAX"

    def __init__(self, rule_id: str = "GTFSSyn002"):
        super().__init__(rule_id, "GTFS lat/lon range", severity="CRITICAL")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        lat = ctx.event.get("latitude")
        lon = ctx.event.get("longitude")
        vehicle_id = str(ctx.event.get("vehicle_id", "unknown"))

        if lat is None and lon is None:
            return None  # Caught by GTFSSyn001

        if lat is not None:
            try:
                lat_f = float(lat)
                if lat_f < -90.0 or lat_f > 90.0:
                    return Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        entity_id=vehicle_id,
                        entity_type="gtfs_vehicle",
                        severity=self.severity,
                        violation_type=self.violation_type,
                        details={
                            "field": "latitude",
                            "value": lat_f,
                            "reason": "OUT_OF_RANGE",
                            "min": -90.0,
                            "max": 90.0,
                        },
                        expected={"latitude": {"min": -90.0, "max": 90.0}},
                        record_snapshot=ctx.event,
                        detected_at=ctx.event_time,
                        processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
                    )
            except (ValueError, TypeError):
                return Violation(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    entity_id=vehicle_id,
                    entity_type="gtfs_vehicle",
                    severity=self.severity,
                    violation_type=self.violation_type,
                    details={
                        "field": "latitude",
                        "value": str(lat),
                        "reason": "PARSE_ERROR",
                    },
                    expected={"latitude": "numeric"},
                    record_snapshot=ctx.event,
                    detected_at=ctx.event_time,
                    processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
                )

        if lon is not None:
            try:
                lon_f = float(lon)
                if lon_f < -180.0 or lon_f > 180.0:
                    return Violation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        entity_id=vehicle_id,
                        entity_type="gtfs_vehicle",
                        severity=self.severity,
                        violation_type=self.violation_type,
                        details={
                            "field": "longitude",
                            "value": lon_f,
                            "reason": "OUT_OF_RANGE",
                            "min": -180.0,
                            "max": 180.0,
                        },
                        expected={"longitude": {"min": -180.0, "max": 180.0}},
                        record_snapshot=ctx.event,
                        detected_at=ctx.event_time,
                        processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
                    )
            except (ValueError, TypeError):
                return Violation(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    entity_id=vehicle_id,
                    entity_type="gtfs_vehicle",
                    severity=self.severity,
                    violation_type=self.violation_type,
                    details={
                        "field": "longitude",
                        "value": str(lon),
                        "reason": "PARSE_ERROR",
                    },
                    expected={"longitude": "numeric"},
                    record_snapshot=ctx.event,
                    detected_at=ctx.event_time,
                    processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
                )

        return None


class GTFSSpeedRangeRule(DataQualityRule):
    """
    GTFSSyn003: Validate GTFS speed is in valid range.

    GTFS speed is in km/h (or m/s depending on feed).
    We accept [0, 300] km/h range — 200 km/h is physically max for any vehicle.

    Severity: HIGH
    """

    violation_type = "SYNTAX"
    MAX_SPEED_KMH = 300.0

    def __init__(self, rule_id: str = "GTFSSyn003"):
        super().__init__(rule_id, "GTFS speed range", severity="HIGH")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        speed = ctx.event.get("speed")
        vehicle_id = str(ctx.event.get("vehicle_id", "unknown"))

        if speed is None:
            return None  # Speed may be absent; no violation

        try:
            speed_f = float(speed)
        except (ValueError, TypeError):
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "speed",
                    "value": str(speed),
                    "reason": "PARSE_ERROR",
                },
                expected={"speed": "numeric"},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if speed_f < 0.0:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "speed",
                    "value": speed_f,
                    "reason": "NEGATIVE_VALUE",
                    "min": 0.0,
                },
                expected={"speed": {"min": 0.0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if speed_f > self.MAX_SPEED_KMH:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "speed",
                    "value": speed_f,
                    "reason": "EXCEEDS_MAX",
                    "max": self.MAX_SPEED_KMH,
                },
                expected={"speed": {"max": self.MAX_SPEED_KMH}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


# ────────────────────────────────────────────────────────────────
# GTFS Semantic Rules
# ────────────────────────────────────────────────────────────────


class GTFSImpossibleSpeedRule(DataQualityRule):
    """
    GTFSSem001: Speed > 200 km/h is physically impossible for transit vehicles.

    While GTFSSyn003 checks for syntactically valid speeds (0-300 km/h),
    this rule checks for semantically impossible speeds for Malaysian transit:
    - Express buses: max ~120 km/h
    - City buses: max ~80 km/h
    - 200 km/h is only possible for trains/motorcycles

    Severity: CRITICAL
    """

    violation_type = "SEMANTIC"
    IMPOSSIBLE_SPEED_KMH = 200.0

    def __init__(self, rule_id: str = "GTFSSem001"):
        super().__init__(rule_id, "GTFS impossible speed", severity="CRITICAL")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        speed = ctx.event.get("speed")
        vehicle_id = str(ctx.event.get("vehicle_id", "unknown"))

        if speed is None:
            return None

        try:
            speed_f = float(speed)
        except (ValueError, TypeError):
            return None

        if speed_f > self.IMPOSSIBLE_SPEED_KMH:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "speed",
                    "value": speed_f,
                    "reason": "IMPOSSIBLE_FOR_TRANSIT",
                    "max_reasonable_kmh": self.IMPOSSIBLE_SPEED_KMH,
                },
                expected={"speed": {"max": self.IMPOSSIBLE_SPEED_KMH}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )
        return None


class GTFSStaleDataRule(DataQualityRule):
    """
    GTFSSem002: Vehicle position older than 5 minutes is stale.

    GTFS feeds should be near-real-time. Positions older than 5 minutes
    indicate feed delay or processing lag.

    Severity: MEDIUM
    """

    violation_type = "SEMANTIC"
    MAX_AGE_SECONDS = 300  # 5 minutes

    def __init__(self, rule_id: str = "GTFSSem002"):
        super().__init__(rule_id, "GTFS stale data", severity="MEDIUM")

    def _parse_timestamp(self, ts_str) -> Optional[datetime]:
        if ts_str is None:
            return None
        try:
            if isinstance(ts_str, datetime):
                return ts_str
            return datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        ts_str = ctx.event.get("timestamp")
        vehicle_id = str(ctx.event.get("vehicle_id", "unknown"))

        if ts_str is None:
            return None

        ts = self._parse_timestamp(ts_str)
        if ts is None:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "timestamp",
                    "value": str(ts_str),
                    "reason": "PARSE_ERROR",
                },
                expected={"timestamp": "ISO 8601 datetime"},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        age_seconds = (ctx.event_time - ts).total_seconds()
        if age_seconds > self.MAX_AGE_SECONDS:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "timestamp",
                    "value": str(ts_str),
                    "age_seconds": round(age_seconds, 1),
                    "reason": "STALE_DATA",
                    "max_age_seconds": self.MAX_AGE_SECONDS,
                },
                expected={"timestamp": {"max_age_seconds": self.MAX_AGE_SECONDS}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


# ────────────────────────────────────────────────────────────────
# GTFS Cross-Record Rules
# ────────────────────────────────────────────────────────────────

# Per-vehicle state for GTFS: {vehicle_id: (lat, lon, timestamp, seq)}
_GTFS_VEHICLE_STATES: dict = {}

# Per-event dedup state for GTFS: {dedup_key: first_seen_time}
_GTFS_DEDUP_STATES: dict = {}

DEDUP_WINDOW_SECONDS = 300  # 5 minutes


def reset_gtfs_cross_record_state():
    """Reset all GTFS cross-record state (call between test runs)."""
    global _GTFS_VEHICLE_STATES, _GTFS_DEDUP_STATES
    _GTFS_VEHICLE_STATES.clear()
    _GTFS_DEDUP_STATES.clear()


def evaluate_gtfs_trajectory_anomaly(event: dict, event_time: datetime, start_time: float = 0.0):
    """
    GTFSCRS001: Detect impossible speed using GPS position jump.

    Similar to CRS001 but for GTFS vehicles. Uses bearing + speed to detect
    physically impossible movements (e.g., teleport from KL to Penang in 1 second).

    GTFS fields: vehicle_id, latitude, longitude, speed, bearing, timestamp
    """
    vehicle_id = str(event.get("vehicle_id", "unknown"))

    lat = event.get("latitude")
    lon = event.get("longitude")
    speed = event.get("speed")
    bearing = event.get("bearing")
    ts_str = event.get("timestamp")

    if lat is None or lon is None:
        return None

    try:
        lat_f = float(lat)
        lon_f = float(lon)
        speed_f = float(speed) if speed is not None else None
        ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")) if ts_str else event_time
    except (ValueError, TypeError):
        return None

    now = event_time

    # First observation for this vehicle
    if vehicle_id not in _GTFS_VEHICLE_STATES:
        _GTFS_VEHICLE_STATES[vehicle_id] = (lat_f, lon_f, ts, 1)
        return None

    prev_lat, prev_lon, prev_ts, prev_seq = _GTFS_VEHICLE_STATES[vehicle_id]
    new_seq = prev_seq + 1

    # Compute time delta
    dt = (ts - prev_ts).total_seconds()
    if dt <= 0:
        # Same or backward timestamp — check for teleport
        dist = _haversine_km(prev_lat, prev_lon, lat_f, lon_f)
        if dist > 1.0:  # > 1km jump in same/negative time
            v = Violation(
                rule_id="GTFSCRS001",
                rule_name="GTFS GPS position teleport",
                entity_id=vehicle_id,
                entity_type="gtfs_vehicle",
                severity="CRITICAL",
                violation_type="CROSS_RECORD",
                details={
                    "field": "position",
                    "jump_km": round(dist, 3),
                    "time_delta_sec": dt,
                    "reason": "GPS_TELEPORT",
                    "prev_lat": prev_lat,
                    "prev_lon": prev_lon,
                    "curr_lat": lat_f,
                    "curr_lon": lon_f,
                },
                expected={"position_jump_km": {"max": 1.0}},
                record_snapshot=event,
                detected_at=event_time,
                processing_latency_ms=(time.perf_counter() - start_time) * 1000,
            )
            _GTFS_VEHICLE_STATES[vehicle_id] = (lat_f, lon_f, ts, new_seq)
            return [v]

    # Compute speed from position jump
    dist_km = _haversine_km(prev_lat, prev_lon, lat_f, lon_f)
    dist_mph = dist_km * 0.621371
    dt_hours = dt / 3600.0

    if dt_hours > 0:
        computed_speed_mph = dist_mph / dt_hours
        computed_speed_kmh = dist_km / dt_hours
    else:
        computed_speed_kmh = 9999.0

    # GTFS max reasonable speed: 200 km/h for any transit
    GTFS_MAX_SPEED = 200.0
    GTFS_HIGH_SPEED = 120.0

    severity = None
    reason = None
    if computed_speed_kmh > GTFS_MAX_SPEED:
        severity = "CRITICAL"
        reason = "IMPOSSIBLE_SPEED"
    elif computed_speed_kmh > GTFS_HIGH_SPEED:
        severity = "HIGH"
        reason = "EXCEEDS_REASONABLE"

    if severity:
        v = Violation(
            rule_id="GTFSCRS001",
            rule_name="GTFS GPS speed anomaly",
            entity_id=vehicle_id,
            entity_type="gtfs_vehicle",
            severity=severity,
            violation_type="CROSS_RECORD",
            details={
                "field": "speed",
                "computed_speed_kmh": round(computed_speed_kmh, 1),
                "distance_km": round(dist_km, 3),
                "time_delta_sec": round(dt, 1),
                "reason": reason,
                "prev_lat": prev_lat,
                "prev_lon": prev_lon,
                "curr_lat": lat_f,
                "curr_lon": lon_f,
            },
            expected={"computed_speed_kmh": {"max": GTFS_MAX_SPEED}},
            record_snapshot=event,
            detected_at=event_time,
            processing_latency_ms=(time.perf_counter() - start_time) * 1000,
        )
        _GTFS_VEHICLE_STATES[vehicle_id] = (lat_f, lon_f, ts, new_seq)
        return [v]

    _GTFS_VEHICLE_STATES[vehicle_id] = (lat_f, lon_f, ts, new_seq)
    return None


def evaluate_gtfs_duplicate_event(event: dict, event_time: datetime, start_time: float = 0.0):
    """
    GTFSCRS002: Detect duplicate GTFS vehicle position reports.

    Uses (vehicle_id, latitude, longitude, timestamp) as dedup key.
    Duplicates within DEDUP_WINDOW_SECONDS (5 min) are flagged.
    """
    vehicle_id = str(event.get("vehicle_id", "unknown"))
    lat = event.get("latitude")
    lon = event.get("longitude")
    ts_str = event.get("timestamp")

    if not vehicle_id or lat is None or lon is None:
        return None

    dedup_key = f"{vehicle_id}:{lat}:{lon}:{ts_str}"

    if dedup_key in _GTFS_DEDUP_STATES:
        first_seen = _GTFS_DEDUP_STATES[dedup_key]
        if (event_time - first_seen).total_seconds() <= DEDUP_WINDOW_SECONDS:
            return [
                Violation(
                    rule_id="GTFSCRS002",
                    rule_name="GTFS duplicate position",
                    entity_id=vehicle_id,
                    entity_type="gtfs_vehicle",
                    severity="MEDIUM",
                    violation_type="CROSS_RECORD",
                    details={
                        "field": "position",
                        "dedup_key": dedup_key,
                        "first_seen": first_seen.isoformat(),
                        "reason": "DUPLICATE_POSITION",
                    },
                    expected={"position": "unique within window"},
                    record_snapshot=event,
                    detected_at=event_time,
                    processing_latency_ms=(time.perf_counter() - start_time) * 1000,
                )
            ]

    _GTFS_DEDUP_STATES[dedup_key] = event_time

    # Evict old dedup entries
    cutoff = event_time - timedelta(seconds=DEDUP_WINDOW_SECONDS)
    for k, t in list(_GTFS_DEDUP_STATES.items()):
        if t < cutoff:
            del _GTFS_DEDUP_STATES[k]

    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two lat/lon points in kilometers."""
    import math
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
