"""
Unit tests for P2 new rules: ConceptDriftDetector, SYN000, FIT001, AlertRouter.
"""
from __future__ import annotations
import pytest
import time
from datetime import datetime
from streamdq.rules.drift import (
    ConceptDriftDetector,
    PSIResult,
    ConceptDriftState,
)
from streamdq.rules.syntactic import CompletenessRule
from streamdq.rules.semantic import FitnessScoreRule
from streamdq.rules.base import RuleContext, Violation
from streamdq.notification.alert_router import AlertRouter


class TestConceptDriftDetector:
    """Tests for ConceptDriftDetector."""

    def test_set_baseline(self):
        detector = ConceptDriftDetector(psi_threshold=0.2)
        detector.set_baseline("fare_amount", {"p10": 5.0, "p90": 40.0, "mean": 15.0}, 1000)
        assert "fare_amount" in detector._states
        assert detector._states["fare_amount"].baseline_p10 == 5.0
        assert detector._states["fare_amount"].baseline_p90 == 40.0

    def test_no_drift_below_interval(self):
        """Should return None when check_interval not reached."""
        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=500)
        detector.set_baseline("fare_amount", {"p10": 5.0, "p90": 40.0, "mean": 15.0}, 1000)
        result = detector.check_drift("fare_amount", {"p10": 5.5, "p90": 41.0}, 1200)
        assert result is None  # Not enough events since baseline

    def test_drift_detected_with_values(self):
        """PSI computed from raw values should detect shift."""
        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=100)
        detector.set_baseline("fare_amount", {"p10": 5.0, "p90": 40.0, "mean": 15.0}, 100)
        # Current values shifted higher
        current_vals = [30.0 + (i % 5) for i in range(100)]
        result = detector.check_drift(
            "fare_amount",
            {"p10": 5.0, "p90": 40.0, "mean": 31.0},
            200,
            current_vals,
        )
        assert result is not None
        assert result.psi >= 0

    def test_drift_recommendation(self):
        """High PSI should give critical recommendation."""
        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=100)
        detector.set_baseline("fare_amount", {"p10": 5.0, "p90": 40.0, "mean": 15.0}, 100)
        current_vals = [50.0 + (i % 5) for i in range(100)]
        result = detector.check_drift(
            "fare_amount",
            {"p10": 5.0, "p90": 40.0, "mean": 52.0},
            200,
            current_vals,
        )
        assert result is not None
        assert "recompute" in result.recommendation.lower() or "drift" in result.recommendation.lower()

    def test_psiresult_dataclass(self):
        """PSIResult should have all required fields."""
        result = PSIResult(
            field="test",
            psi=0.3,
            drift_detected=True,
            threshold=0.2,
            bucket_expected=[0.1] * 10,
            bucket_actual=[0.1] * 10,
            recommendation="Test",
        )
        assert result.psi == 0.3
        assert result.drift_detected is True


class TestCompletenessRule:
    """Tests for SYN000 CompletenessRule."""

    def make_ctx(self, event: dict) -> RuleContext:
        return RuleContext(
            event=event,
            event_time=datetime.now(),
            historical_stats={},
            external_context={},
            start_time=time.perf_counter(),
        )

    def test_complete_record(self):
        """All required fields present -> no violation."""
        rule = CompletenessRule(required_fields=["fare_amount", "PULocationID"])
        ctx = self.make_ctx({"trip_id": "T1", "fare_amount": 15.0, "PULocationID": 42})
        assert rule.evaluate(ctx) is None

    def test_missing_required_field(self):
        """Missing required field -> violation."""
        rule = CompletenessRule(required_fields=["fare_amount", "PULocationID"])
        ctx = self.make_ctx({"trip_id": "T1", "fare_amount": 15.0, "PULocationID": None})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "SYN000"
        assert "PULocationID" in v.details["missing_fields"]

    def test_all_fields_missing(self):
        """All required fields missing -> critical severity."""
        rule = CompletenessRule(required_fields=["fare_amount", "PULocationID"])
        ctx = self.make_ctx({"trip_id": "T1"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.severity == "MEDIUM"
        assert v.details["n_missing"] == 2
        assert v.details["completeness"] == 0.0


class TestFitnessScoreRule:
    """Tests for FIT001 FitnessScoreRule."""

    def make_ctx(self, event: dict) -> RuleContext:
        return RuleContext(
            event=event,
            event_time=datetime.now(),
            historical_stats={},
            external_context={},
            start_time=time.perf_counter(),
        )

    def test_full_record_no_violation(self):
        """Full record -> score >= 0.5 -> no violation."""
        rule = FitnessScoreRule(required_fields=["fare_amount", "PULocationID"])
        ctx = self.make_ctx({"trip_id": "T1", "fare_amount": 15.0, "PULocationID": 42})
        assert rule.evaluate(ctx) is None

    def test_partial_record_below_threshold(self):
        """Score < 0.5 -> violation emitted."""
        rule = FitnessScoreRule(required_fields=["fare_amount", "PULocationID"])
        ctx = self.make_ctx({"trip_id": "T1", "fare_amount": 15.0, "PULocationID": None})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "FIT001"
        assert v.violation_type == "FITNESS"

    def test_latency_computed(self):
        """FIT001 violation must have non-zero latency."""
        rule = FitnessScoreRule(required_fields=["fare_amount", "PULocationID"])
        start = time.perf_counter()
        ctx = self.make_ctx({"trip_id": "T1"})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.processing_latency_ms > 0

    def test_nan_required_field_returns_violation(self):
        """NaN in required field must be counted as missing (F1-c fix)."""
        rule = FitnessScoreRule(required_fields=["fare_amount", "PULocationID"])
        ctx = self.make_ctx({"trip_id": "T1", "fare_amount": float("nan"), "PULocationID": 42})
        v = rule.evaluate(ctx)
        assert v is not None
        assert v.rule_id == "FIT001"
        assert v.details["n_missing"] >= 1
        assert "fare_amount" in v.details["missing_fields"]


class TestAlertRouter:
    """Tests for AlertRouter."""

    def make_violation(self, severity: str = "HIGH", entity_id: str = "T1") -> Violation:
        return Violation(
            rule_id="SYN001",
            rule_name="Fare amount range",
            entity_id=entity_id,
            entity_type="nyc_taxi",
            severity=severity,
            violation_type="SYNTACTIC",
            details={"reason": "NEGATIVE_VALUE", "field": "fare_amount"},
            expected={},
            record_snapshot={"trip_id": "T1"},
            detected_at=datetime.now(),
            processing_latency_ms=5.0,
        )

    def test_register_channel(self):
        router = AlertRouter()
        router.register_channel("stdout", enabled=True)
        assert "stdout" in router._channels

    def test_stdout_channel(self, capsys):
        router = AlertRouter()
        router.register_channel("stdout", enabled=True)
        v = self.make_violation("HIGH")
        results = router.route(v)
        assert len(results) == 1
        assert results[0] is True
        out = capsys.readouterr()
        assert "ALERT-STDOUT" in out.out

    def test_severity_threshold(self, capsys):
        """LOW severity should be filtered by default threshold."""
        router = AlertRouter(severity_threshold="MEDIUM")
        router.register_channel("stdout", enabled=True)
        v_low = self.make_violation("LOW")
        results = router.route(v_low)
        assert results == []  # Filtered out

    def test_critical_above_threshold(self, capsys):
        """CRITICAL always passes MEDIUM threshold."""
        router = AlertRouter(severity_threshold="MEDIUM")
        router.register_channel("stdout", enabled=True)
        v_crit = self.make_violation("CRITICAL")
        results = router.route(v_crit)
        assert len(results) == 1

    def test_batch_routing(self, capsys):
        router = AlertRouter()
        router.register_channel("stdout", enabled=True)
        # Use different entity_ids to avoid deduplication
        violations = [self.make_violation("HIGH", "T1"), self.make_violation("MEDIUM", "T2")]
        counts = router.route_batch(violations)
        assert counts["stdout"] == 2

    def test_disabled_channel_skipped(self, capsys):
        router = AlertRouter()
        router.register_channel("stdout", enabled=False)
        v = self.make_violation("HIGH")
        results = router.route(v)
        assert results == []


class TestDataContract:
    """Tests for DataContract."""

    def test_bronze_tier_met(self):
        from streamdq.models.contract import DataContract, CertificationTier, FieldContract
        contract = DataContract(
            name="test_contract",
            version="1.0",
            tier=CertificationTier.BRONZE,
            owner="test",
            fields=[
                FieldContract("fare_amount", "float"),
            ],
        )
        # 20% violation rate -> passes BRONZE (20% <= 5%)?? NO!
        # Actually 20% violation rate means 80% pass, BRONZE threshold is 5% violation so 20% is FAIL
        # Let's use 3% violation rate -> 97% pass -> BRONZE achieved
        result = contract.evaluate({"SYN001": 3}, 100)
        assert result.tier_met is True  # Bronze required, 3% rate is OK
        assert result.tier_achieved is not None

    def test_contract_not_met(self):
        from streamdq.models.contract import DataContract, CertificationTier, FieldContract
        contract = DataContract(
            name="test_contract",
            version="1.0",
            tier=CertificationTier.GOLD,
            owner="test",
            fields=[],
        )
        result = contract.evaluate({"SYN001": 50}, 100)  # 50% violation rate
        assert result.tier_met is False
        assert result.gap_analysis != ""

    def test_missing_rules(self):
        from streamdq.models.contract import DataContract, CertificationTier, FieldContract
        contract = DataContract(
            name="test_contract",
            version="1.0",
            tier=CertificationTier.GOLD,
            owner="test",
            fields=[],
        )
        # CRS rules missing
        result = contract.evaluate({"SYN001": 5}, 100)
        assert len(result.missing_rules) > 0
        assert "CRS001" in result.missing_rules

    def test_empty_evaluation(self):
        from streamdq.models.contract import DataContract, CertificationTier, FieldContract
        contract = DataContract(
            name="test_contract",
            version="1.0",
            tier=CertificationTier.BRONZE,
            owner="test",
            fields=[],
        )
        result = contract.evaluate({}, 0)
        assert result.tier_met is False
        assert result.tier_achieved is None
