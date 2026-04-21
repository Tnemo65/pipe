"""
Quality Meta-Stream Event Schema.

Defines the structure of quality events emitted every 5 minutes.
These events track pipeline health, rule performance, and violation patterns.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional


@dataclass
class QualityEvent:
    """
    Quality event emitted every 5 minutes.

    Tracks:
    - Event throughput and processing latency
    - Violation patterns by rule and severity
    - Rule health (precision, alert volume)
    - Drift detection status
    - Threshold statistics
    """
    # Metadata
    timestamp: str  # ISO8601 timestamp
    pipeline_id: str  # Pipeline identifier
    window_id: int  # Incremental window counter
    window_start: str  # ISO8601 window start
    window_end: str  # ISO8601 window end

    # Throughput metrics
    events_processed: int
    events_per_second: float

    # Latency metrics (milliseconds)
    processing_latency_p50: float
    processing_latency_p99: float
    e2e_latency_p50: float
    e2e_latency_p99: float

    # Violation metrics
    total_violations: int
    violation_rate: float  # violations / events
    violations_by_rule: Dict[str, int]
    violations_by_severity: Dict[str, int]
    violations_by_type: Dict[str, int]

    # Rule health metrics
    rule_health_scores: Dict[str, float]  # rule_id -> TP/(TP+FP)
    rule_alert_counts: Dict[str, int]  # rule_id -> alert count
    silent_rules: list[str]  # Rules with 0 alerts in window

    # Adaptive threshold metrics
    threshold_p10: Dict[str, float]  # field -> P10 threshold
    threshold_p90: Dict[str, float]  # field -> P90 threshold
    threshold_updates: int  # Number of threshold updates in window

    # Drift detection
    drift_detected: bool
    drift_fields: list[str]  # Fields with detected drift
    drift_psi_scores: Dict[str, float]  # field -> PSI score

    # Context metrics
    active_contexts: int  # Number of active context keys
    context_distribution: Dict[str, int]  # context_key -> event count

    # Errors
    processing_errors: int
    error_types: Dict[str, int]

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_metrics(
        cls,
        pipeline_id: str,
        window_id: int,
        window_start: datetime,
        window_end: datetime,
        metrics: dict,
    ) -> QualityEvent:
        """
        Create QualityEvent from pipeline metrics.

        Args:
            pipeline_id: Pipeline identifier
            window_id: Window counter
            window_start: Window start timestamp
            window_end: Window end timestamp
            metrics: Metrics dict from pipeline.get_metrics()

        Returns:
            QualityEvent instance
        """
        window_duration_sec = (window_end - window_start).total_seconds()
        events_per_second = metrics["total_events"] / max(window_duration_sec, 1)

        # Extract rule health from metrics (if available)
        rule_health = {}
        rule_alerts = metrics.get("by_rule", {})
        silent_rules = [
            rule_id for rule_id, count in rule_alerts.items()
            if count == 0
        ]

        # Extract threshold stats
        threshold_stats = metrics.get("threshold_stats", {})
        threshold_p10 = {}
        threshold_p90 = {}
        for field, stats in threshold_stats.items():
            if stats:
                threshold_p10[field] = stats.get("p10", 0.0)
                threshold_p90[field] = stats.get("p90", 0.0)

        # Extract drift status
        drift_info = metrics.get("drift_detection", {})
        drift_detected = drift_info.get("drift_detected", False)
        drift_fields = drift_info.get("drift_fields", [])
        drift_psi_scores = drift_info.get("psi_scores", {})

        return cls(
            timestamp=datetime.now().isoformat(),
            pipeline_id=pipeline_id,
            window_id=window_id,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
            events_processed=metrics["total_events"],
            events_per_second=round(events_per_second, 2),
            processing_latency_p50=metrics.get("processing_latency_p50_ms", 0.0),
            processing_latency_p99=metrics.get("processing_latency_p99_ms", 0.0),
            e2e_latency_p50=metrics.get("e2e_latency_p50_ms", 0.0),
            e2e_latency_p99=metrics.get("e2e_latency_p99_ms", 0.0),
            total_violations=metrics["total_violations"],
            violation_rate=round(metrics.get("violation_rate", 0.0), 4),
            violations_by_rule=dict(metrics.get("by_rule", {})),
            violations_by_severity=dict(metrics.get("by_severity", {})),
            violations_by_type=dict(metrics.get("by_type", {})),
            rule_health_scores=rule_health,
            rule_alert_counts=rule_alerts,
            silent_rules=silent_rules,
            threshold_p10=threshold_p10,
            threshold_p90=threshold_p90,
            threshold_updates=metrics.get("threshold_updates", 0),
            drift_detected=drift_detected,
            drift_fields=drift_fields,
            drift_psi_scores=drift_psi_scores,
            active_contexts=metrics.get("active_contexts", 0),
            context_distribution=metrics.get("context_distribution", {}),
            processing_errors=metrics.get("processing_errors", 0),
            error_types=metrics.get("error_types", {}),
        )
