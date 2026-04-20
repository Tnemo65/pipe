"""
Referential Integrity and Conformity validation rules.

REF001: Referential integrity — foreign key validation (e.g., PULocationID exists in zones table).
REF002: Cardinality validation — related record counts (e.g., 1 trip = 1 payment).
REF003: Orphan record detection — records without required parent.

CON001: Format conformity — field format validation (phone, email, UUID).
CON002: Precision validation — decimal precision checks (GPS coordinates).
CON003: Enumeration conformity — field must be in allowed set.
"""
from __future__ import annotations
import re
import time
from typing import Optional, Set
from datetime import datetime

from streamdq.rules.base import DataQualityRule, RuleContext, Violation


class ReferentialIntegrityRule(DataQualityRule):
    """
    REF001 — Referential integrity check.

    Validates that foreign key values exist in a reference dataset.
    Examples:
    - PULocationID must exist in NYC TLC zones table
    - vendor_id must be in [1, 2, 3, 4] (Creative, VeriFone, CMT, DDS)
    - payment_type must be in [1, 2, 3, 4, 5, 6] (CRD, CSH, NOC, DIS, UNK, VOU)

    Severity: MEDIUM (data is syntactically valid but semantically orphaned)
    """

    violation_type = "REFERENTIAL_INTEGRITY"

    def __init__(
        self,
        rule_id: str = "REF001",
        field: str = "PULocationID",
        reference_set: Set[int] | None = None,
    ):
        super().__init__(rule_id, f"Referential integrity — {field}", severity="MEDIUM")
        self.field = field

        # Default reference sets for common NYC Taxi fields
        if reference_set is None:
            if field == "PULocationID" or field == "DOLocationID":
                # NYC TLC zones 1-263
                self.reference_set = set(range(1, 264))
            elif field == "VendorID":
                # Known NYC taxi vendors
                self.reference_set = {1, 2, 3, 4}
            elif field == "payment_type":
                # Payment types: 1=Credit, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided
                self.reference_set = {1, 2, 3, 4, 5, 6}
            elif field == "RatecodeID":
                # Rate codes: 1=Standard, 2=JFK, 3=Newark, 4=Nassau/Westchester, 5=Negotiated, 6=Group
                self.reference_set = {1, 2, 3, 4, 5, 6}
            else:
                self.reference_set = set()
        else:
            self.reference_set = reference_set

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        value = ctx.event.get(self.field)
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if value is None:
            return None  # Caught by SYN000 (completeness)

        # Convert to int for numeric fields
        try:
            if isinstance(value, str):
                value = int(value)
        except (ValueError, TypeError):
            pass

        if value not in self.reference_set:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": self.field,
                    "value": value,
                    "reason": "FOREIGN_KEY_NOT_FOUND",
                    "reference_set_size": len(self.reference_set),
                    "sample_valid_values": list(self.reference_set)[:10],
                },
                expected={self.field: {"in": "reference_set"}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class FormatConformityRule(DataQualityRule):
    """
    CON001 — Format conformity check.

    Validates that field values conform to expected formats using regex patterns.
    Examples:
    - trip_id must be UUID format (8-4-4-4-12 hex digits)
    - phone_number must be E.164 format (+1234567890)
    - email must be valid email format (user@domain.com)

    Severity: MEDIUM (data is present but malformed)
    """

    violation_type = "CONFORMITY"

    # Common regex patterns
    PATTERNS = {
        "uuid": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE),
        "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        "phone_e164": re.compile(r"^\+[1-9]\d{1,14}$"),
        "iso8601": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),
        "hex_color": re.compile(r"^#[0-9a-f]{6}$", re.IGNORECASE),
        "ipv4": re.compile(r"^(\d{1,3}\.){3}\d{1,3}$"),
    }

    def __init__(
        self,
        rule_id: str = "CON001",
        field: str = "trip_id",
        pattern_name: str = "uuid",
        custom_pattern: Optional[re.Pattern] = None,
    ):
        super().__init__(rule_id, f"Format conformity — {field}", severity="MEDIUM")
        self.field = field
        self.pattern_name = pattern_name

        if custom_pattern:
            self.pattern = custom_pattern
        elif pattern_name in self.PATTERNS:
            self.pattern = self.PATTERNS[pattern_name]
        else:
            raise ValueError(f"Unknown pattern: {pattern_name}. Use custom_pattern parameter.")

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        value = ctx.event.get(self.field)
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if value is None:
            return None  # Caught by SYN000

        value_str = str(value)

        if not self.pattern.match(value_str):
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": self.field,
                    "value": value_str[:100],  # Truncate long values
                    "reason": "FORMAT_MISMATCH",
                    "expected_format": self.pattern_name,
                    "pattern": self.pattern.pattern,
                },
                expected={self.field: {"format": self.pattern_name}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class PrecisionValidationRule(DataQualityRule):
    """
    CON002 — Precision validation.

    Validates decimal precision for numeric fields.
    Examples:
    - GPS coordinates should have exactly 6 decimal places (111m precision)
    - fare_amount should have max 2 decimal places (cents)
    - trip_distance should have max 2 decimal places

    Severity: LOW (data is accurate but imprecise)
    """

    violation_type = "CONFORMITY"

    def __init__(
        self,
        rule_id: str = "CON002",
        field: str = "pickup_latitude",
        expected_precision: int = 6,
        allow_lower_precision: bool = False,
    ):
        super().__init__(rule_id, f"Precision validation — {field}", severity="LOW")
        self.field = field
        self.expected_precision = expected_precision
        self.allow_lower_precision = allow_lower_precision

    def _get_decimal_places(self, value: float) -> int:
        """Count decimal places in a float."""
        value_str = f"{value:.20f}".rstrip('0')
        if '.' in value_str:
            return len(value_str.split('.')[1])
        return 0

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        value = ctx.event.get(self.field)
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if value is None:
            return None

        if not isinstance(value, (int, float)):
            return None  # Caught by type validation

        decimal_places = self._get_decimal_places(float(value))

        # Check precision mismatch
        violation_reason = None
        if self.allow_lower_precision:
            if decimal_places > self.expected_precision:
                violation_reason = "EXCESSIVE_PRECISION"
        else:
            if decimal_places != self.expected_precision:
                violation_reason = "PRECISION_MISMATCH"

        if violation_reason:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": self.field,
                    "value": value,
                    "actual_precision": decimal_places,
                    "expected_precision": self.expected_precision,
                    "reason": violation_reason,
                },
                expected={self.field: {"decimal_places": self.expected_precision}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class EnumerationConformityRule(DataQualityRule):
    """
    CON003 — Enumeration conformity.

    Validates that categorical fields contain only allowed values.
    Examples:
    - payment_type in ["credit_card", "cash", "no_charge"]
    - store_and_fwd_flag in ["Y", "N"]
    - trip_type in [1, 2] (street-hail vs dispatch)

    This is similar to REF001 but for enums without a separate reference table.

    Severity: MEDIUM
    """

    violation_type = "CONFORMITY"

    def __init__(
        self,
        rule_id: str = "CON003",
        field: str = "store_and_fwd_flag",
        allowed_values: Set | None = None,
    ):
        super().__init__(rule_id, f"Enumeration conformity — {field}", severity="MEDIUM")
        self.field = field

        # Default enumerations for common fields
        if allowed_values is None:
            if field == "store_and_fwd_flag":
                self.allowed_values = {"Y", "N"}
            elif field == "trip_type":
                self.allowed_values = {1, 2}  # 1=street-hail, 2=dispatch
            elif field == "passenger_count":
                self.allowed_values = set(range(0, 10))  # 0-9 passengers
            else:
                self.allowed_values = set()
        else:
            self.allowed_values = allowed_values

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        value = ctx.event.get(self.field)
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if value is None:
            return None  # Caught by completeness

        if value not in self.allowed_values:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=self.severity,
                violation_type=self.violation_type,
                details={
                    "field": self.field,
                    "value": value,
                    "reason": "INVALID_ENUM_VALUE",
                    "allowed_values": sorted(list(self.allowed_values)),
                },
                expected={self.field: {"enum": sorted(list(self.allowed_values))}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None


class TimelinessRule(DataQualityRule):
    """
    TIM001 — Timeliness / Freshness check.

    Detects late-arriving data where event_time << processing_time.
    Examples:
    - Event with pickup_time = 2023-01-01 arrives on 2023-01-05 (4 days late)
    - Real-time stream with >5 minute delay indicates pipeline backlog

    Severity: MEDIUM (operational issue, not data quality issue)
    """

    violation_type = "TIMELINESS"

    def __init__(
        self,
        rule_id: str = "TIM001",
        event_time_field: str = "tpep_pickup_datetime",
        max_delay_seconds: int = 300,  # 5 minutes
    ):
        super().__init__(rule_id, "Timeliness / Late arrival detection", severity="MEDIUM")
        self.event_time_field = event_time_field
        self.max_delay_seconds = max_delay_seconds

    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        if ts_str is None:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError, TypeError):
            return None

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        event_time_str = ctx.event.get(self.event_time_field)
        trip_id = str(ctx.event.get("trip_id", "unknown"))

        if event_time_str is None:
            return None  # Caught by completeness

        event_time = self._parse_timestamp(event_time_str)
        if event_time is None:
            return None  # Caught by timestamp parsing

        # Check if this is a replay stream (skip timeliness check)
        lineage = ctx.event.get("_lineage", {})
        if lineage.get("is_replay"):
            return None

        processing_time = ctx.event_time
        delay_seconds = (processing_time - event_time).total_seconds()

        if delay_seconds > self.max_delay_seconds:
            severity = "HIGH" if delay_seconds > 3600 else "MEDIUM"  # >1 hour = HIGH

            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=trip_id,
                entity_type=ctx.event.get("entity_type", "nyc_taxi"),
                severity=severity,
                violation_type=self.violation_type,
                details={
                    "event_time": event_time_str,
                    "processing_time": processing_time.isoformat(),
                    "delay_seconds": round(delay_seconds, 1),
                    "delay_minutes": round(delay_seconds / 60, 1),
                    "delay_hours": round(delay_seconds / 3600, 1),
                    "max_allowed_seconds": self.max_delay_seconds,
                    "reason": "LATE_ARRIVAL",
                },
                expected={"delay_seconds": {"max": self.max_delay_seconds}},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=(time.perf_counter() - ctx.start_time) * 1000,
            )

        return None
