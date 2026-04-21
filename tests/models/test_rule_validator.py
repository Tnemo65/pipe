"""
Tests for RuleValidator (Phase 3 T10).

Validates rules before production deployment by measuring FPR, precision, and coverage
on historical data. Rules are accepted if FPR < threshold and precision > threshold.
"""
from __future__ import annotations
import pytest
from datetime import datetime
from typing import Optional
from streamdq.models.rule_validator import RuleValidator, RuleValidationResult
from streamdq.rules.base import DataQualityRule, RuleContext, Violation, ExternalContext
from streamdq.rules.adaptive import AdaptiveThresholdEngine


class MockWeakRule(DataQualityRule):
    """
    A rule with high false positive rate (90%).
    Violates on ~90% of events (simulates a bad rule).
    """

    def __init__(self, rule_id: str = "MOCK_WEAK"):
        super().__init__(rule_id, "Mock Weak Rule", severity="MEDIUM")
        self.violation_count = 0

    @property
    def violation_type(self) -> str:
        return "SEMANTIC"

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        """
        Always violate (simulating a rule with very high violation rate).
        This models a weak rule that triggers on 90% of events.
        """
        self.violation_count += 1
        return Violation(
            rule_id=self.rule_id,
            rule_name=self.name,
            entity_id=ctx.event.get("id", "unknown"),
            entity_type="test_event",
            severity="MEDIUM",
            violation_type=self.violation_type,
            details={"reason": "mock violation"},
            expected={},
            record_snapshot=ctx.event,
            detected_at=ctx.event_time,
            processing_latency_ms=0.0,
        )


class MockStrongRule(DataQualityRule):
    """
    A rule with low false positive rate (5%).
    Violates on only ~5% of events (simulates a good rule).
    """

    def __init__(self, rule_id: str = "MOCK_STRONG"):
        super().__init__(rule_id, "Mock Strong Rule", severity="MEDIUM")
        self.violation_count = 0
        self.event_count = 0

    @property
    def violation_type(self) -> str:
        return "SEMANTIC"

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        """
        Only violate on ~5% of events (every 20th event).
        This models a good rule with low FPR.
        """
        self.event_count += 1
        # Violate only on every 20th event (5% violation rate)
        if self.event_count % 20 == 0:
            self.violation_count += 1
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.name,
                entity_id=ctx.event.get("id", "unknown"),
                entity_type="test_event",
                severity="MEDIUM",
                violation_type=self.violation_type,
                details={"reason": "mock violation"},
                expected={},
                record_snapshot=ctx.event,
                detected_at=ctx.event_time,
                processing_latency_ms=0.0,
            )
        return None


class TestRuleValidator:
    """Test RuleValidator class."""

    def test_reject_weak_rule_high_fpr(self):
        """RuleValidator rejects weak rule with high FPR (>10%)."""
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )

        # Create mock weak rule (90% violation rate = high FPR)
        weak_rule = MockWeakRule()

        # Generate historical data (200 events)
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(200)
        ]

        # Validate the rule
        result = validator.validate_rule(
            rule=weak_rule,
            historical_events=historical_events,
            ground_truth=None  # No ground truth provided
        )

        # Assertions
        assert isinstance(result, RuleValidationResult)
        assert result.rule_id == "MOCK_WEAK"
        assert result.total_events == 200

        # With no ground truth, FPR = coverage = violations / total_events
        # MockWeakRule violates on ~200 events (100% of them)
        # So FPR should be very high (close to 1.0)
        assert result.fpr > 0.50  # High FPR
        assert result.precision == 0.0  # No ground truth = precision = 0
        assert result.coverage > 0.50  # Rule applies to >50% of events

        # Should reject because FPR > threshold
        assert result.accepted is False
        assert result.rejection_reason is not None
        assert "fpr" in result.rejection_reason.lower()

    def test_accept_strong_rule_low_fpr(self):
        """RuleValidator accepts strong rule with low FPR (<10%)."""
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )

        # Create mock strong rule (5% violation rate = low FPR)
        strong_rule = MockStrongRule()

        # Generate historical data (200 events)
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(200)
        ]

        # Validate the rule
        result = validator.validate_rule(
            rule=strong_rule,
            historical_events=historical_events,
            ground_truth=None  # No ground truth provided
        )

        # Assertions
        assert isinstance(result, RuleValidationResult)
        assert result.rule_id == "MOCK_STRONG"
        assert result.total_events == 200

        # MockStrongRule violates on ~10 events (5% = 200 / 20)
        # So FPR should be low (close to 0.05)
        assert result.fpr < 0.10  # Low FPR (passes threshold)
        assert result.precision == 0.0  # No ground truth = precision = 0
        assert result.coverage > 0.01  # Rule applies to >1% of events
        assert result.violations == 10  # Should violate on ~10 events

        # Should accept because FPR < threshold and coverage > min_coverage
        assert result.accepted is True
        assert result.rejection_reason is None

    def test_coverage_metric(self):
        """RuleValidator correctly computes coverage metric."""
        validator = RuleValidator(
            fpr_threshold=0.20,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )

        # Create strong rule with low violation rate
        strong_rule = MockStrongRule()

        # Generate historical data (500 events)
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(500)
        ]

        # Validate the rule
        result = validator.validate_rule(
            rule=strong_rule,
            historical_events=historical_events,
            ground_truth=None
        )

        # Assertions
        assert isinstance(result, RuleValidationResult)
        assert result.total_events == 500

        # Coverage = violations / total_events
        # MockStrongRule violates on ~25 events (500 / 20)
        expected_violations = 25
        expected_coverage = expected_violations / 500  # ~0.05

        assert result.violations == expected_violations
        assert 0.04 < result.coverage < 0.06  # Within margin
        assert result.coverage > 0.01  # Above minimum

    def test_min_events_requirement(self):
        """RuleValidator rejects validation if insufficient historical events."""
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )

        # Create a rule
        rule = MockWeakRule()

        # Generate only 50 events (below min_events=100)
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(50)
        ]

        # Validate the rule - should fail min_events check
        result = validator.validate_rule(
            rule=rule,
            historical_events=historical_events,
            ground_truth=None
        )

        # Assertions
        assert result.accepted is False
        assert result.rejection_reason is not None
        assert "min_events" in result.rejection_reason.lower() or "insufficient" in result.rejection_reason.lower()


class TestRuleValidationResult:
    """Test RuleValidationResult dataclass."""

    def test_validation_result_fields(self):
        """RuleValidationResult contains all required fields."""
        result = RuleValidationResult(
            rule_id="TEST_RULE",
            fpr=0.08,
            precision=0.72,
            recall=0.95,
            coverage=0.15,
            total_events=500,
            violations=75,
            accepted=True,
            rejection_reason=None
        )

        assert result.rule_id == "TEST_RULE"
        assert result.fpr == 0.08
        assert result.precision == 0.72
        assert result.recall == 0.95
        assert result.coverage == 0.15
        assert result.total_events == 500
        assert result.violations == 75
        assert result.accepted is True
        assert result.rejection_reason is None

    def test_validation_result_with_rejection_reason(self):
        """RuleValidationResult can include rejection reason."""
        result = RuleValidationResult(
            rule_id="BAD_RULE",
            fpr=0.15,
            precision=0.40,
            recall=0.85,
            coverage=0.10,
            total_events=500,
            violations=50,
            accepted=False,
            rejection_reason="FPR (0.15) exceeds threshold (0.10)"
        )

        assert result.accepted is False
        assert result.rejection_reason is not None
        assert "FPR" in result.rejection_reason


class TestRuleRegistryValidation:
    """Test RuleRegistry integration with RuleValidator (Task 3.2)."""

    def test_registry_enable_validation(self):
        """RuleRegistry.enable_validation() activates validator."""
        from streamdq.rules.registry import RuleRegistry

        registry = RuleRegistry()

        # Validator should be disabled by default
        assert registry._validator is None

        # Enable validation
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )
        registry.enable_validation(validator)

        # Validator should now be set
        assert registry._validator is not None
        assert registry._validator is validator
        assert isinstance(registry._validation_events, list)

    def test_registry_register_rule_without_validation(self):
        """RuleRegistry.register() works normally when validation disabled."""
        from streamdq.rules.registry import RuleRegistry

        registry = RuleRegistry()
        rule = MockStrongRule()

        # Should register without validation
        registry.register_rule(rule)

        # Rule should be registered
        assert len(registry._stateless_rules) == 1
        assert registry._stateless_rules[0] is rule

    def test_registry_register_rule_with_validation_accepts_good_rule(self):
        """RuleRegistry.register_rule() accepts rule when validation enabled and rule is good."""
        from streamdq.rules.registry import RuleRegistry

        registry = RuleRegistry()

        # Enable validation
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )
        registry.enable_validation(validator)

        # Create strong rule (low FPR, should pass)
        strong_rule = MockStrongRule()

        # Generate historical data
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(200)
        ]

        # Register rule with validation
        result = registry.register_rule(strong_rule, historical_events)

        # Should be accepted
        assert result.accepted is True
        assert result.rejection_reason is None

        # Rule should be registered
        assert len(registry._stateless_rules) == 1
        assert registry._stateless_rules[0] is strong_rule

        # Validation event should be recorded
        assert len(registry._validation_events) == 1
        assert registry._validation_events[0] == result

    def test_registry_register_rule_with_validation_rejects_bad_rule(self):
        """RuleRegistry.register_rule() rejects rule when validation enabled and rule is bad."""
        from streamdq.rules.registry import RuleRegistry

        registry = RuleRegistry()

        # Enable validation
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )
        registry.enable_validation(validator)

        # Create weak rule (high FPR, should fail)
        weak_rule = MockWeakRule()

        # Generate historical data
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(200)
        ]

        # Register rule with validation
        result = registry.register_rule(weak_rule, historical_events)

        # Should be rejected
        assert result.accepted is False
        assert result.rejection_reason is not None
        assert "fpr" in result.rejection_reason.lower()

        # Rule should NOT be registered
        assert len(registry._stateless_rules) == 0

        # Validation event should be recorded
        assert len(registry._validation_events) == 1
        assert registry._validation_events[0] == result

    def test_registry_validation_events_tracking(self):
        """RuleRegistry tracks all validation events."""
        from streamdq.rules.registry import RuleRegistry

        registry = RuleRegistry()

        # Enable validation
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )
        registry.enable_validation(validator)

        # Generate historical data
        historical_events = [
            {"id": f"event_{i}", "value": float(i)}
            for i in range(200)
        ]

        # Register multiple rules
        strong_rule1 = MockStrongRule(rule_id="STRONG_1")
        strong_rule2 = MockStrongRule(rule_id="STRONG_2")
        weak_rule = MockWeakRule(rule_id="WEAK_1")

        registry.register_rule(strong_rule1, historical_events)
        registry.register_rule(weak_rule, historical_events)
        registry.register_rule(strong_rule2, historical_events)

        # Should have 3 validation events
        assert len(registry._validation_events) == 3

        # Should have 2 accepted rules
        assert len(registry._stateless_rules) == 2

        # Validate event records
        assert registry._validation_events[0].rule_id == "STRONG_1"
        assert registry._validation_events[0].accepted is True

        assert registry._validation_events[1].rule_id == "WEAK_1"
        assert registry._validation_events[1].accepted is False

        assert registry._validation_events[2].rule_id == "STRONG_2"
        assert registry._validation_events[2].accepted is True
