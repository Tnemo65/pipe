"""
Tests for AlertRouter confidence-based filtering.

Validates that violations below confidence threshold are suppressed.
"""
import pytest
from datetime import datetime
from streamdq.rules.base import Violation
from streamdq.notification.alert_router import AlertRouter


class TestAlertRouterConfidenceFiltering:
    """Test confidence threshold filtering."""

    def test_high_confidence_violation_routed(self):
        """HIGH severity with high confidence (>0.7) → routed."""
        router = AlertRouter(confidence_threshold=0.7)

        violation = Violation(
            rule_id="CRS003",
            rule_name="Duplicate detection",
            entity_id="trip_001",
            entity_type="nyc_taxi",
            severity="HIGH",
            violation_type="CROSS_RECORD",
            details={"adjudication_confidence": 0.85},
            expected={},
            record_snapshot={},
            detected_at=datetime(2024, 1, 15, 10, 0, 0),
            processing_latency_ms=5.0
        )

        should_route = router.should_route(violation)
        assert should_route is True

    def test_low_confidence_violation_suppressed(self):
        """MEDIUM severity with low confidence (≤0.7) → suppressed."""
        router = AlertRouter(confidence_threshold=0.7)

        violation = Violation(
            rule_id="CRS003",
            rule_name="Duplicate detection",
            entity_id="trip_002",
            entity_type="nyc_taxi",
            severity="MEDIUM",
            violation_type="CROSS_RECORD",
            details={"adjudication_confidence": 0.55},
            expected={},
            record_snapshot={},
            detected_at=datetime(2024, 1, 15, 10, 0, 0),
            processing_latency_ms=5.0
        )

        should_route = router.should_route(violation)
        assert should_route is False  # Suppressed by confidence threshold

    def test_violation_without_confidence_routed(self):
        """Violations without confidence field → routed (backward compat)."""
        router = AlertRouter(confidence_threshold=0.7)

        violation = Violation(
            rule_id="SEM001",
            rule_name="Fare range check",
            entity_id="trip_003",
            entity_type="nyc_taxi",
            severity="HIGH",
            violation_type="SEMANTIC",
            details={"reason": "out_of_range"},  # No adjudication_confidence
            expected={},
            record_snapshot={},
            detected_at=datetime(2024, 1, 15, 10, 0, 0),
            processing_latency_ms=5.0
        )

        should_route = router.should_route(violation)
        assert should_route is True  # Backward compat: no confidence → route
