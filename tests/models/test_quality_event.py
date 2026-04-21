"""Tests for QualityEvent model and quality meta-stream."""
import pytest
from datetime import datetime, timedelta
from streamdq.models.quality_event import QualityEvent


def test_quality_event_creation():
    """Create QualityEvent with all fields."""
    event = QualityEvent(
        timestamp="2026-04-21T10:00:00",
        pipeline_id="test_pipeline",
        window_id=1,
        window_start="2026-04-21T09:55:00",
        window_end="2026-04-21T10:00:00",
        events_processed=10000,
        events_per_second=33.33,
        processing_latency_p50=15.5,
        processing_latency_p99=45.2,
        e2e_latency_p50=20.0,
        e2e_latency_p99=50.0,
        total_violations=150,
        violation_rate=0.015,
        violations_by_rule={"SYN001": 50, "SEM001": 100},
        violations_by_severity={"HIGH": 50, "MEDIUM": 100},
        violations_by_type={"SYNTACTIC": 50, "SEMANTIC": 100},
        rule_health_scores={"SYN001": 0.85, "SEM001": 0.72},
        rule_alert_counts={"SYN001": 50, "SEM001": 100},
        silent_rules=[],
        threshold_p10={"fare_amount": 5.0, "trip_distance": 0.5},
        threshold_p90={"fare_amount": 50.0, "trip_distance": 10.0},
        threshold_updates=5,
        drift_detected=False,
        drift_fields=[],
        drift_psi_scores={},
        active_contexts=15,
        context_distribution={"rush_hour": 3000, "weekend": 7000},
        processing_errors=0,
        error_types={},
    )

    assert event.pipeline_id == "test_pipeline"
    assert event.window_id == 1
    assert event.events_processed == 10000
    assert event.violation_rate == 0.015


def test_quality_event_to_json():
    """QualityEvent converts to JSON dict."""
    event = QualityEvent(
        timestamp="2026-04-21T10:00:00",
        pipeline_id="test",
        window_id=1,
        window_start="2026-04-21T09:55:00",
        window_end="2026-04-21T10:00:00",
        events_processed=1000,
        events_per_second=3.33,
        processing_latency_p50=10.0,
        processing_latency_p99=25.0,
        e2e_latency_p50=15.0,
        e2e_latency_p99=30.0,
        total_violations=10,
        violation_rate=0.01,
        violations_by_rule={},
        violations_by_severity={},
        violations_by_type={},
        rule_health_scores={},
        rule_alert_counts={},
        silent_rules=[],
        threshold_p10={},
        threshold_p90={},
        threshold_updates=0,
        drift_detected=False,
        drift_fields=[],
        drift_psi_scores={},
        active_contexts=0,
        context_distribution={},
        processing_errors=0,
        error_types={},
    )

    json_dict = event.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict["pipeline_id"] == "test"
    assert json_dict["events_processed"] == 1000


def test_quality_event_from_metrics():
    """Create QualityEvent from pipeline metrics."""
    window_start = datetime(2026, 4, 21, 9, 55)
    window_end = datetime(2026, 4, 21, 10, 0)

    metrics = {
        "total_events": 10000,
        "total_violations": 150,
        "violation_rate": 0.015,
        "by_rule": {"SYN001": 50, "SEM001": 100},
        "by_type": {"SYNTACTIC": 50, "SEMANTIC": 100},
        "by_severity": {"HIGH": 50, "MEDIUM": 100},
        "processing_latency_p50_ms": 15.5,
        "processing_latency_p99_ms": 45.2,
        "e2e_latency_p50_ms": 20.0,
        "e2e_latency_p99_ms": 50.0,
    }

    event = QualityEvent.from_metrics(
        pipeline_id="test_pipeline",
        window_id=1,
        window_start=window_start,
        window_end=window_end,
        metrics=metrics,
    )

    assert event.pipeline_id == "test_pipeline"
    assert event.window_id == 1
    assert event.events_processed == 10000
    assert event.total_violations == 150
    assert event.violation_rate == 0.015
    assert event.violations_by_rule == {"SYN001": 50, "SEM001": 100}
    assert event.processing_latency_p50 == 15.5
    assert event.events_per_second > 0  # Should compute throughput


def test_quality_event_silent_rules_detection():
    """Detect rules with zero alerts."""
    metrics = {
        "total_events": 1000,
        "total_violations": 50,
        "violation_rate": 0.05,
        "by_rule": {"SYN001": 50, "SEM001": 0, "CRS001": 0},
        "by_type": {},
        "by_severity": {},
    }

    event = QualityEvent.from_metrics(
        pipeline_id="test",
        window_id=1,
        window_start=datetime.now(),
        window_end=datetime.now() + timedelta(minutes=5),
        metrics=metrics,
    )

    assert "SEM001" in event.silent_rules
    assert "CRS001" in event.silent_rules
    assert "SYN001" not in event.silent_rules


def test_quality_event_drift_detection():
    """Track drift detection in quality event."""
    metrics = {
        "total_events": 1000,
        "total_violations": 10,
        "violation_rate": 0.01,
        "by_rule": {},
        "by_type": {},
        "by_severity": {},
        "drift_detection": {
            "drift_detected": True,
            "drift_fields": ["fare_amount", "trip_distance"],
            "psi_scores": {"fare_amount": 0.15, "trip_distance": 0.12},
        },
    }

    event = QualityEvent.from_metrics(
        pipeline_id="test",
        window_id=1,
        window_start=datetime.now(),
        window_end=datetime.now() + timedelta(minutes=5),
        metrics=metrics,
    )

    assert event.drift_detected is True
    assert event.drift_fields == ["fare_amount", "trip_distance"]
    assert event.drift_psi_scores["fare_amount"] == 0.15
