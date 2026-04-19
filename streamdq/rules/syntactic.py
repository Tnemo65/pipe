"""
Syntactic validation rules.

SYN000: Completeness — required fields must not be NULL.
SYN001: Fare amount non-null, non-negative, numeric.
SYN002: Pickup location ID valid (1-263).
SYN003: Pickup timestamp not in the future (with 5-min tolerance).
"""
from __future__ import annotations
import math
import time
from datetime import datetime
from typing import Optional

from streamdq.rules.base import DataQualityRule, RuleContext, Violation


VALID_LOCATION_IDS = set(range(1, 264))  # NYC TLC zones 1-263


def _isnan(value) -> bool:
    """
    Check if value is NaN (handles float, numpy.floating, pandas NaT, and string "NaN").

    NG-23: Added string "NaN" handling because _serialize_event() converts pd.isna()
    to the string "NaN" instead of None, to preserve NaN detection downstream.
    """
    if value is None:
        return False
    # String "NaN" from serialized events (NG-23 fix)
    if isinstance(value, str) and value == "NaN":
        return True
    try:
        # Python float NaN
        if isinstance(value, float):
            return math.isnan(value)
        # numpy.nan and numpy.float64 etc.
        if hasattr(value, "__float__"):
            return math.isnan(float(value))
        return False
    except (TypeError, ValueError):
        return False


class CompletenessRule(DataQualityRule):
    """
    SYN000 — Completeness check.

    Validates that required fields are not NULL/missing.
    Per-record: returns a Violation for each missing required field.

    Usage:
        rule = CompletenessRule(
            rule_id="SYN000",
            required_fields=["fare_amount", "PULocationID", "tpep_pickup_datetime"],
        )
    """

    violation_type = "SYNTAX_SYN000"

    def __init__(
        self,
        rule_id: str = "SYN000",
        required_fields: list[str] | None = None,
    ):
        super().__init__(rule_id=rule_id, name="Completeness check")
        self.required_fields = required_fields or ["fare_amount", "PULocationID"]

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        event = ctx.event
        missing_fields = []
        for field in self.required_fields:
            value = event.get(field)
            if value is None or _isnan(value):
                missing_fields.append(field)

        if not missing_fields:
            return None

        return Violation(
            rule_id=self.rule_id,
            rule_name=self.name,
            entity_id=str(event.get("trip_id", event.get("vehicle_id", "unknown"))),
            entity_type=event.get("entity_type", "unknown"),
            severity="MEDIUM",
            violation_type=self.violation_type,
            details={
                "reason": "NULL",
                "missing_fields": missing_fields,
                "completeness": round(
                    1.0 - len(missing_fields) / len(self.required_fields), 4
                ),
                "total_required": len(self.required_fields),
                "n_missing": len(missing_fields),
            },
            expected={
                "required_fields": self.required_fields,
            },
            record_snapshot=event,
            detected_at=ctx.event_time,
            processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
        )


class FareAmountRangeRule(DataQualityRule):
    """
    Fare amount must be non-null, numeric, and non-negative.

    Violation types: NULL, TYPE_MISMATCH, NEGATIVE_VALUE
    Severity: HIGH
    """

    violation_type = "SYNTACTIC"

    def __init__(self, rule_id: str = "SYN001"):
        super().__init__(rule_id, "Fare amount validity", severity="HIGH")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        fare = ctx.event.get("fare_amount")
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if fare is None:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={"field": "fare_amount", "value": None, "reason": "NULL"},
                expected={"fare_amount": {"type": "number", "min": 0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if _isnan(fare):
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "fare_amount",
                    "value": str(fare),
                    "actual_type": type(fare).__name__,
                    "reason": "NAN_VALUE",
                },
                expected={"fare_amount": {"type": "number", "min": 0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if not isinstance(fare, (int, float)):
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "fare_amount",
                    "value": str(fare),
                    "actual_type": type(fare).__name__,
                    "reason": "TYPE_MISMATCH",
                },
                expected={"fare_amount": {"type": "number"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if fare < 0:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "fare_amount",
                    "value": fare,
                    "reason": "NEGATIVE_VALUE",
                },
                expected={"fare_amount": {"min": 0}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class PickupLocationValidRule(DataQualityRule):
    """
    PULocationID must be a valid NYC TLC zone (1-263).

    Violation types: NULL, TYPE_MISMATCH, OUT_OF_RANGE
    Severity: HIGH
    """

    violation_type = "SYNTACTIC"

    def __init__(self, rule_id: str = "SYN002"):
        super().__init__(rule_id, "Pickup location validity", severity="HIGH")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        location_id = ctx.event.get("PULocationID")
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if location_id is None:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={"field": "PULocationID", "value": None, "reason": "NULL"},
                expected={"PULocationID": {"range": "1-263"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        try:
            location_int = int(location_id)
        except (ValueError, TypeError):
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "PULocationID",
                    "value": str(location_id),
                    "reason": "TYPE_MISMATCH",
                },
                expected={"PULocationID": {"type": "integer", "range": "1-263"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        if location_int not in VALID_LOCATION_IDS:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": "PULocationID",
                    "value": location_int,
                    "reason": "OUT_OF_RANGE",
                },
                expected={"PULocationID": {"range": "1-263"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class TimestampNotFutureRule(DataQualityRule):
    """
    Event timestamp must not be more than N minutes in the future.

    Accounts for clock skew between systems.
    Default tolerance: 5 minutes.

    Violation types: NULL, PARSE_ERROR, FUTURE_TIMESTAMP
    Severity: HIGH
    """

    violation_type = "SYNTACTIC"

    def __init__(
        self,
        rule_id: str = "SYN003",
        field: str = "tpep_pickup_datetime",
        future_tolerance_minutes: int = 5,
    ):
        super().__init__(rule_id, "Timestamp not in future", severity="HIGH")
        self.field = field
        self.future_tolerance = future_tolerance_minutes * 60

    def _parse_timestamp(self, ts_str: str) -> Optional[float]:
        """Parse ISO8601 timestamp string to Unix epoch."""
        if ts_str is None:
            return None
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, AttributeError, TypeError):
            return None

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        ts_str = ctx.event.get(self.field)
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if ts_str is None:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={"field": self.field, "value": None, "reason": "NULL"},
                expected={self.field: {"type": "timestamp", f"max": f"now + {self.future_tolerance}s"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        ts_epoch = self._parse_timestamp(ts_str)
        if ts_epoch is None:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": self.field,
                    "value": str(ts_str),
                    "reason": "PARSE_ERROR",
                },
                expected={self.field: {"format": "ISO8601"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        future_cutoff = ctx.event_time.timestamp() + self.future_tolerance
        if ts_epoch > future_cutoff:
            offset_seconds = int(ts_epoch - future_cutoff)
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": self.field,
                    "value": ts_str,
                    "reason": "FUTURE_TIMESTAMP",
                    "offset_seconds": offset_seconds,
                },
                expected={self.field: {"max": f"now + {self.future_tolerance}s"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None
