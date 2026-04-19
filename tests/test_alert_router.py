"""
Unit tests for AlertRouter — deduplication, severity threshold, channels.
"""
from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from streamdq.notification.alert_router import (
    AlertRouter,
    AlertChannel,
    StdoutChannel,
    Alert,
)
from streamdq.rules.base import Violation


def make_violation(rule_id="SYN001", entity_id="123", severity="HIGH") -> Violation:
    """Create a minimal violation for testing."""
    return Violation(
        rule_id=rule_id,
        rule_name="Test Rule",
        entity_id=entity_id,
        entity_type="nyc_taxi",
        severity=severity,
        violation_type="SYNTAX",
        details={},
        expected={},
        record_snapshot={},
        detected_at=datetime.now(),
        processing_latency_ms=1.0,
    )


class TestAlertRouterDeduplication:
    """NG-16: Tests for alert deduplication."""

    def setup_method(self):
        self.router = AlertRouter(severity_threshold="MEDIUM", dedup_window_seconds=300)
        self.router.register_channel("stdout", enabled=True)

    def test_first_violation_not_deduplicated(self):
        """First occurrence of a violation should be sent."""
        v = make_violation(rule_id="SYN001", entity_id="123")
        results = self.router.route(v)
        assert len(results) == 1
        assert results[0] is True

    def test_duplicate_within_window_suppressed(self):
        """Same (rule_id, entity_id) within dedup window should be suppressed."""
        v1 = make_violation(rule_id="SYN001", entity_id="123")
        v2 = make_violation(rule_id="SYN001", entity_id="123")

        self.router.route(v1)
        results = self.router.route(v2)

        # Should be suppressed (empty results = not sent)
        assert results == []

    def test_different_entity_not_deduplicated(self):
        """Different entity_id should not be deduplicated."""
        v1 = make_violation(rule_id="SYN001", entity_id="123")
        v2 = make_violation(rule_id="SYN001", entity_id="456")

        self.router.route(v1)
        results = self.router.route(v2)

        assert len(results) == 1

    def test_different_rule_not_deduplicated(self):
        """Different rule_id should not be deduplicated."""
        v1 = make_violation(rule_id="SYN001", entity_id="123")
        v2 = make_violation(rule_id="SYN002", entity_id="123")

        self.router.route(v1)
        results = self.router.route(v2)

        assert len(results) == 1

    def test_different_entity_type_not_deduplicated(self):
        """Different entity_type should not be deduplicated."""
        v1 = make_violation(rule_id="SYN001", entity_id="123")
        v1.entity_type = "nyc_taxi"
        v2 = make_violation(rule_id="SYN001", entity_id="123")
        v2.entity_type = "gtfs_vehicle"

        self.router.route(v1)
        results = self.router.route(v2)

        assert len(results) == 1

    def test_below_severity_threshold_not_routed(self):
        """LOW severity violation should not be routed when threshold is MEDIUM."""
        self.router = AlertRouter(severity_threshold="MEDIUM")
        self.router.register_channel("stdout", enabled=True)
        v = make_violation(severity="LOW")
        results = self.router.route(v)
        assert results == []

    def test_at_severity_threshold_routed(self):
        """MEDIUM severity violation should be routed when threshold is MEDIUM."""
        v = make_violation(severity="MEDIUM")
        results = self.router.route(v)
        assert len(results) == 1


class TestAlertRouterBatch:
    """Tests for route_batch() with deduplication."""

    def setup_method(self):
        self.router = AlertRouter(dedup_window_seconds=300)
        self.router.register_channel("stdout", enabled=True)

    def test_batch_routes_all_non_duplicates(self):
        """route_batch() should route all non-duplicate violations."""
        violations = [
            make_violation(rule_id="SYN001", entity_id=str(i))
            for i in range(5)
        ]
        counts = self.router.route_batch(violations)
        assert counts["stdout"] == 5

    def test_batch_deduplicates(self):
        """route_batch() should deduplicate within the batch."""
        violations = [
            make_violation(rule_id="SYN001", entity_id="123"),
            make_violation(rule_id="SYN001", entity_id="123"),
            make_violation(rule_id="SYN001", entity_id="123"),
        ]
        counts = self.router.route_batch(violations)
        # Only first should be routed, others suppressed
        assert counts["stdout"] == 1
