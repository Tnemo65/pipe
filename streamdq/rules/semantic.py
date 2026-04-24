"""
Semantic validation rules.

SEM001: Fare within contextually reasonable range (adaptive).
SEM002: Trip duration between 1 minute and 24 hours.
SEM003: Average speed between 0 and 80 mph.
FIT001: Fitness for purpose — overall data quality score per record.
"""
from __future__ import annotations
import time
from datetime import datetime
from typing import Optional

from streamdq.rules.base import DataQualityRule, RuleContext, Violation, get_entity_index, make_violation
from streamdq.rules.syntactic import _isnan


class FareRangeRule(DataQualityRule):
    """
    Fare amount must be within contextually reasonable bounds.

    Uses adaptive threshold from historical_stats if available:
    - Min = P10 (or fallback to NYC flag drop minimum $2.50)
    - Max = P90 * 2 (or fallback to $500)

    Severity: MEDIUM
    """

    violation_type = "SEMANTIC"

    # Static fallbacks derived from TLC data analysis
    STATIC_MIN_FARE = 2.5   # NYC flag drop minimum
    STATIC_MAX_FARE = 500.0  # Reasonable max for non-airport trips

    def __init__(self, rule_id: str = "SEM001"):
        super().__init__(rule_id, "Fare range check", severity="MEDIUM")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        fare = ctx.event.get("fare_amount")
        if fare is None:
            return None  # Caught by SYN001

        if _isnan(fare):
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=str(ctx.event.get("trip_id", "unknown")),
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "fare_amount",
                    "value": str(fare),
                    "actual_type": type(fare).__name__,
                    "reason": "NAN_VALUE",
                },
                expected={"fare_amount": {"min": 0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        trip_distance = ctx.event.get("trip_distance", 0) or 0
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        # Get adaptive thresholds from historical stats
        stats = ctx.historical_stats
        fare_stats = stats.get("fare_amount", {})

        if "p10" in fare_stats and "p90" in fare_stats:
            fare_min = fare_stats["p10"]
            fare_max = fare_stats["p90"] * 2.0
            threshold_source = "adaptive"
        else:
            fare_min = self.STATIC_MIN_FARE
            fare_max = self.STATIC_MAX_FARE
            threshold_source = "static_fallback"

        # Context-aware time-of-day adjustments (F2-b: makes context-aware claim REAL)
        is_rush_hour = ctx.get_external("is_rush_hour", False)
        is_late_night = ctx.get_external("is_late_night", False)
        is_weekend = ctx.get_external("is_weekend", False)
        is_holiday = ctx.get_external("is_holiday", False)

        if is_holiday:
            # Airport/surge trips spike on holidays — expand both min and max
            fare_min *= 0.8
            fare_max *= 1.5
        elif is_rush_hour:
            # Rush hour: demand surge, higher fare expectations
            fare_max *= 1.3
        elif is_late_night:
            # Late night: fewer trips, potentially lower fares but also surcharges
            fare_max *= 0.7
        elif is_weekend:
            # Weekend: different trip distribution (more leisure, less commute)
            fare_max *= 1.15

        # Contextual adjustment: very long trips justify higher fares
        if trip_distance > 20:
            fare_max = fare_max * (1 + (trip_distance - 20) * 0.05)

        if fare < fare_min or fare > fare_max:
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "fare_amount",
                    "value": fare,
                    "reason": "OUT_OF_CONTEXTUAL_RANGE",
                    "fare_min": fare_min,
                    "fare_max": fare_max,
                    "threshold_source": threshold_source,
                    "trip_distance": trip_distance,
                    "is_rush_hour": is_rush_hour,
                    "is_late_night": is_late_night,
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                },
                expected={"fare_amount": {"min": fare_min, "max": fare_max}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class TripDurationSanityRule(DataQualityRule):
    """
    Trip duration must be between 1 minute and 24 hours.

    Trips outside this range are almost certainly data errors
    (system glitch, timezone misparse, or sensor malfunction).

    Severity: HIGH
    """

    violation_type = "SEMANTIC"

    def __init__(
        self,
        rule_id: str = "SEM002",
        min_duration_minutes: int = 1,
        max_duration_hours: int = 24,
    ):
        super().__init__(rule_id, "Trip duration sanity", severity="HIGH")
        self.min_duration_sec = min_duration_minutes * 60
        self.max_duration_sec = max_duration_hours * 3600

    def _compute_duration(self, pickup: datetime, dropoff: datetime) -> float:
        return (dropoff - pickup).total_seconds()

    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        if ts_str is None:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError, TypeError):
            return None

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        pickup_str = ctx.event.get("tpep_pickup_datetime")
        dropoff_str = ctx.event.get("tpep_dropoff_datetime")
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        pickup = self._parse_timestamp(pickup_str)
        dropoff = self._parse_timestamp(dropoff_str)

        if pickup is None or dropoff is None:
            return None  # Caught by SYN003 (timestamp parse)

        duration_sec = self._compute_duration(pickup, dropoff)

        # Context-aware max duration: rush hour traffic extends expected trip time
        is_rush_hour = ctx.get_external("is_rush_hour", False)
        is_weekend = ctx.get_external("is_weekend", False)
        max_dur = self.max_duration_sec
        if is_rush_hour:
            max_dur = max_dur * 1.5  # Rush hour: traffic extends duration
        elif is_weekend:
            max_dur = max_dur * 1.2   # Weekend: different trip patterns

        if duration_sec < self.min_duration_sec:
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "trip_duration",
                    "value_seconds": duration_sec,
                    "value_minutes": round(duration_sec / 60, 1),
                    "reason": "TOO_SHORT",
                    "min_allowed_seconds": self.min_duration_sec,
                    "pickup": pickup_str,
                    "dropoff": dropoff_str,
                },
                expected={"duration_seconds": {"min": self.min_duration_sec}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if duration_sec > max_dur:
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "trip_duration",
                    "value_seconds": duration_sec,
                    "value_hours": round(duration_sec / 3600, 1),
                    "reason": "TOO_LONG",
                    "max_allowed_seconds": max_dur,
                    "is_rush_hour": is_rush_hour,
                    "is_weekend": is_weekend,
                    "pickup": pickup_str,
                    "dropoff": dropoff_str,
                },
                expected={"duration_seconds": {"max": max_dur}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class AverageSpeedSanityRule(DataQualityRule):
    """
    Average trip speed must be between 0 and 80 mph.

    NYC max urban speed ~25mph, highway ~65mph.
    We allow up to 80mph to account for express routes.
    Speed = distance / duration.

    Severity: MEDIUM
    """

    violation_type = "SEMANTIC"

    def __init__(
        self,
        rule_id: str = "SEM003",
        min_speed_mph: float = 0.0,
        max_speed_mph: float = 80.0,
    ):
        super().__init__(rule_id, "Average speed sanity", severity="MEDIUM")
        self.min_speed_mph = min_speed_mph
        self.max_speed_mph = max_speed_mph
        self.min_duration_sec = 60  # Need at least 1 min to compute meaningful speed

    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        if ts_str is None:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError, TypeError):
            return None

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        trip_distance = ctx.event.get("trip_distance")
        pickup_str = ctx.event.get("tpep_pickup_datetime")
        dropoff_str = ctx.event.get("tpep_dropoff_datetime")
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if not (trip_distance is not None and pickup_str and dropoff_str):
            return None

        # Guard against NaN values (SYN001 handles None; NaN needs explicit check)
        if _isnan(trip_distance):
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "trip_distance",
                    "value": str(trip_distance),
                    "actual_type": type(trip_distance).__name__,
                    "reason": "NAN_VALUE",
                },
                expected={"trip_distance": {"min": 0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        pickup = self._parse_timestamp(pickup_str)
        dropoff = self._parse_timestamp(dropoff_str)
        if pickup is None or dropoff is None:
            return None

        duration_sec = (dropoff - pickup).total_seconds()
        if duration_sec < self.min_duration_sec:
            return None  # Duration too short — caught by SEM002

        if trip_distance <= 0:
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "trip_distance",
                    "value": trip_distance,
                    "reason": "ZERO_OR_NEGATIVE_DISTANCE",
                },
                expected={"trip_distance": {"min": 0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        hours = duration_sec / 3600.0
        avg_speed_mph = trip_distance / hours if hours > 0 else float("inf")

        # Context-aware max speed: highway speeds at night are higher
        is_rush_hour = ctx.get_external("is_rush_hour", False)
        is_late_night = ctx.get_external("is_late_night", False)
        max_speed = self.max_speed_mph
        if is_late_night:
            # Highway speeds at night (no traffic, open roads)
            max_speed += 15.0
        elif is_rush_hour:
            # Slower speeds during rush hour (traffic)
            max_speed -= 5.0

        if avg_speed_mph > max_speed:
            return make_violation(
                ctx.event,
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "average_speed_mph",
                    "value": round(avg_speed_mph, 1),
                    "trip_distance_miles": trip_distance,
                    "duration_minutes": round(duration_sec / 60, 1),
                    "reason": "EXCEEDS_MAX_SPEED",
                    "max_allowed_mph": max_speed,
                    "is_rush_hour": is_rush_hour,
                    "is_late_night": is_late_night,
                },
                expected={"average_speed_mph": {"max": max_speed}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


# IBM's 7 data quality dimensions mapped to StreamDQ rule coverage:
# Completeness  -> SYN000 (CompletenessRule)
# Uniqueness    -> CRS003 (duplicate detection)
# Validity      -> SYN001-003 (syntactic)
# Timeliness    -> SYN003 (timestamp not future)
# Accuracy      -> SEM001-003 (semantic)
# Consistency   -> CRS001-002 (GPS consistency)


class FitnessScoreRule(DataQualityRule):
    """
    FIT001 — Fitness for Purpose score (completeness-based).

    Computes a completeness score (0-1) per record: the fraction of required
    fields that are present and non-NaN.

    NOTE: This is a COMPLETENESS-ONLY score. The docstring previously claimed
    this was a composite of completeness + validity + contextual reasonableness,
    but that would require running other rules as sub-checks and aggregating
    their pass rates, which is architecturally complex. The current
    implementation focuses purely on field-level completeness as a lightweight
    fitness indicator.

    Score bands:
        1.0       -> All required fields present and non-NaN
        0.50-0.99 -> Some fields missing or NaN
        0.00-0.49 -> Majority of required fields missing or NaN (VIOLATION)

    Violations are emitted only when score < 0.5 (majority of required fields
    missing), since that threshold clearly indicates poor fitness.
    """

    violation_type = "FITNESS"

    def __init__(
        self,
        rule_id: str = "FIT001",
        required_fields: list[str] | None = None,
    ):
        super().__init__(rule_id=rule_id, name="Fitness for purpose score")
        self.required_fields = required_fields or ["fare_amount", "PULocationID"]

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        event = ctx.event
        total_fields = max(len(self.required_fields), 1)
        missing = sum(
            1 for f in self.required_fields
            if event.get(f) is None or _isnan(event.get(f))
        )
        completeness = 1.0 - missing / total_fields
        score = completeness

        if score > 0.5:
            return None

        severity = "HIGH" if score < 0.25 else "MEDIUM"

        return make_violation(
            event,
            rule_id=self.rule_id,
            rule_name=self.name,
            entity_id=str(event.get("trip_id", event.get("vehicle_id", "unknown"))),
            entity_type=event.get("entity_type", "unknown"),
            severity=severity,
            violation_type=self.violation_type,
            details={
                "score": round(score, 4),
                "completeness": round(completeness, 4),
                "n_missing": missing,
                "missing_fields": [
                    f for f in self.required_fields
                    if event.get(f) is None or _isnan(event.get(f))
                ],
            },
            expected={"min_fitness_score": 0.5},
            record_snapshot=event,
            detected_at=ctx.event_time,
            processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
        )
