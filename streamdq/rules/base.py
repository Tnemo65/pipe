"""
Base classes for StreamDQ rule engine.

DataQualityRule: Abstract base class for all rules.
RuleContext: Context passed to each rule evaluation.
Violation: A data quality violation.
ExternalContext: Formal 4D context model (who/what/when/where) per Dey 2001 / Serra 2022.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ExternalContext:
    """
    Formal 4D context model for data quality assessment.

    Derived from:
    - Dey (2001): "Understanding and Using Context" — who/what/when/where
    - Serra et al. (2022): Systematic Literature Review on Context in DQ

    Dimensions:
    - WHO (consumer): data_steward, consumer_profile, use_case
    - WHAT (data entity): entity_type (nyc_taxi, gtfs_vehicle, etc.)
    - WHEN (temporal): when_hour, when_day, is_rush_hour, is_late_night, is_weekend, is_holiday
    - WHERE (spatial): where_region, where_zone

    System context:
    - pipeline_stage: ingestion / enrichment / consumption
    - pipeline_id: identifier for this pipeline instance
    """

    # WHO (consumer/user)
    data_steward: str = "unknown"
    consumer_profile: str = "unknown"
    use_case: str = "unknown"

    # WHAT (data entity)
    entity_type: str = "unknown"

    # WHEN (temporal)
    when_hour: int = 12
    when_day: int = 0          # 0=Mon, 6=Sun
    is_rush_hour: bool = False  # 7-9 or 17-19 on weekdays
    is_late_night: bool = False  # 22-05
    is_weekend: bool = False    # Sat (5) or Sun (6)
    is_holiday: bool = False

    # WHERE (spatial)
    where_region: str = "unknown"
    where_zone: str = "unknown"

    # System context
    pipeline_stage: str = "unknown"  # ingestion | enrichment | consumption
    pipeline_id: str = "unknown"

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "data_steward": self.data_steward,
            "consumer_profile": self.consumer_profile,
            "use_case": self.use_case,
            "entity_type": self.entity_type,
            "when_hour": self.when_hour,
            "when_day": self.when_day,
            "is_rush_hour": self.is_rush_hour,
            "is_late_night": self.is_late_night,
            "is_weekend": self.is_weekend,
            "is_holiday": self.is_holiday,
            "where_region": self.where_region,
            "where_zone": self.where_zone,
            "pipeline_stage": self.pipeline_stage,
            "pipeline_id": self.pipeline_id,
        }

    @classmethod
    def from_event(cls, event: dict, event_time: datetime) -> "ExternalContext":
        """
        Build ExternalContext from event metadata.

        Detects temporal context automatically from event_time.
        Spatial and consumer context must be provided in the event dict.
        """
        hour = event_time.hour
        day = event_time.weekday()  # 0=Mon

        return cls(
            entity_type=event.get("entity_type", "unknown"),
            when_hour=hour,
            when_day=day,
            is_rush_hour=(day < 5) and (7 <= hour <= 9 or 17 <= hour <= 19),
            is_late_night=(hour >= 22 or hour < 5),
            is_weekend=(day >= 5),
            where_region=event.get("borough", "unknown"),
            where_zone=event.get("zone", "unknown"),
            pipeline_stage=event.get("pipeline_stage", "unknown"),
        )


@dataclass
class RuleContext:
    """Context passed to every rule evaluation."""

    event: dict
    """The event being evaluated."""

    event_time: datetime
    """Event timestamp (when it arrived in the pipeline)."""

    historical_stats: dict[str, dict]
    """
    Rolling statistics from AdaptiveThresholdEngine.
    Example: historical_stats["fare_amount"]["p90"] = 45.0
    """

    external_context: ExternalContext | None = None
    """
    Formal 4D context model (who/what/when/where) per Dey 2001 / Serra 2022.
    Automatically built from event metadata via ExternalContext.from_event().
    Rules access via: ctx.external_context.is_rush_hour, etc.
    If None, falls back to empty ExternalContext().
    """

    start_time: float = 0.0
    """
    Wall-clock timestamp (perf_counter) when event processing began.
    Rules use this to compute processing_latency_ms:
        latency_ms = (time.perf_counter() - ctx.start_time) * 1000
    """

    def get_external(self, key: str, default: Any = None) -> Any:
        """
        Dict-like access to external context.

        Supports both the new ExternalContext dataclass and the legacy dict format.
        Rules use this to avoid breaking when external_context is None or a dict.
        """
        if self.external_context is None:
            return default
        if isinstance(self.external_context, dict):
            return self.external_context.get(key, default)
        return getattr(self.external_context, key, default)


@dataclass
class Violation:
    """A data quality violation emitted when a rule fails."""

    rule_id: str
    rule_name: str
    entity_id: str
    entity_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    violation_type: str  # SYNTACTIC, SEMANTIC, CROSS_RECORD
    details: dict[str, Any]  # What went wrong
    expected: dict[str, Any]  # What was expected
    record_snapshot: dict[str, Any]  # Full event data
    detected_at: datetime
    processing_latency_ms: float
    # NG-eval-01: entity_index for ground-truth precision/recall matching.
    # Injected anomalies carry a unique entity_index; violations inherit it
    # so that ground_truth_tracker can match detected → injected via index join.
    entity_index: Optional[str] = None

    def with_entity_index(self, idx: Optional[str]) -> "Violation":
        """Return a copy with entity_index set. NG-eval-01."""
        self.entity_index = idx
        return self


def get_entity_index(event: dict) -> Optional[str]:
    """Extract entity_index from event lineage. NG-eval-01."""
    return event.get("_lineage", {}).get("entity_index")


def make_violation(
    event: dict,
    rule_id: str,
    rule_name: str,
    entity_id: str,
    entity_type: str,
    severity: str,
    violation_type: str,
    details: dict,
    expected: dict,
    record_snapshot: dict,
    detected_at: datetime,
    processing_latency_ms: float,
) -> Violation:
    """
    Factory for Violation with entity_index auto-extracted from event lineage.
    NG-eval-01: All violations carry entity_index for ground-truth P/R matching.
    """
    return Violation(
        rule_id=rule_id,
        rule_name=rule_name,
        entity_id=entity_id,
        entity_type=entity_type,
        severity=severity,
        violation_type=violation_type,
        details=details,
        expected=expected,
        record_snapshot=record_snapshot,
        detected_at=detected_at,
        processing_latency_ms=processing_latency_ms,
        entity_index=get_entity_index(event),
    )


class DataQualityRule(ABC):
    """
    Abstract base class for all data quality rules.

    To create a new rule:
    1. Subclass DataQualityRule
    2. Set violation_type property
    3. Implement evaluate() method
    4. Write unit tests
    5. Register in registry.py

    Example:
        class FareAmountRangeRule(DataQualityRule):
            violation_type = "SYNTACTIC"

            def __init__(self, rule_id: str = "SYN001"):
                super().__init__(rule_id, "Fare amount validity", severity="HIGH")

            def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
                fare = ctx.event.get("fare_amount")
                if fare is None:
                    return Violation(...)
                return None
    """

    def __init__(self, rule_id: str, name: str, severity: str = "MEDIUM"):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity

    @property
    @abstractmethod
    def violation_type(self) -> str:
        """
        Return violation type: SYNTACTIC, SEMANTIC, or CROSS_RECORD.
        """
        pass

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        """
        Evaluate the rule against the given context.

        Returns:
            Violation if the rule fails, None if the event passes.
        """
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.rule_id}, name={self.name})"
