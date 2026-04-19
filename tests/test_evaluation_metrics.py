"""
Unit tests for evaluation metrics.

Tests the entity-resampled bootstrap CI methodology and all metric computations.
"""
from __future__ import annotations
import pytest
from streamdq.evaluation.metrics import EvaluationMetrics


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics."""

    def test_basic_precision_recall(self):
        eval_metrics = EvaluationMetrics()
        # Inject anomalies at indices 5, 10, 15 (fare_negative type)
        for idx in [5, 10, 15]:
            eval_metrics.add_injected_anomaly("fare_negative", idx)
        # Detect violations at indices 5, 10 (TP), 100 (FP)
        for idx in [5, 10, 100]:
            eval_metrics.add_detected_violation("SYN001", idx, 1.0, anomaly_type="fare_negative")
        # Precision = 2/3 = 0.667, Recall = 2/3 = 0.667
        assert abs(eval_metrics.precision() - 0.667) < 0.01
        assert abs(eval_metrics.recall_overall() - 0.667) < 0.01

    def test_false_positive_rate(self):
        """FPR = FP / (FP + TN)."""
        eval_metrics = EvaluationMetrics()
        # Inject anomalies at indices 0-4 (5 anomalous entities)
        for idx in range(5):
            eval_metrics.add_injected_anomaly("fare_negative", idx)
        # Detect violations at indices 0, 1 (TP) and 10, 11, 12 (FP = 3 clean entities flagged)
        for idx in [0, 1, 10, 11, 12]:
            eval_metrics.add_detected_violation("SYN001", idx, 1.0)
        # TN = entities 5-9 that passed = 5 clean entities
        # FP = 3 detected on clean entities
        # FPR = 3 / (3 + 5) = 0.375
        assert abs(eval_metrics.false_positive_rate() - 0.375) < 0.01

    def test_full_report_structure(self):
        """full_report() should include all fields: precision, recall, f1_score, FPR, CI."""
        eval_metrics = EvaluationMetrics()
        for idx in [5, 10, 15]:
            eval_metrics.add_injected_anomaly("fare_negative", idx)
        for idx in [5, 10, 100]:
            eval_metrics.add_detected_violation("SYN001", idx, 1.0)
        report = eval_metrics.full_report()
        assert "total_events_processed" in report
        assert "precision" in report
        assert "recall_overall" in report
        assert "f1_score" in report
        assert "false_positive_rate" in report
        assert isinstance(report["precision"], dict), "precision should be dict with CI"
        assert "ci_95" in report["precision"]
        assert "point_estimate" in report["precision"]

    def test_bootstrap_ci_precision_and_recall(self):
        """P1-6: Bootstrap CI should give reasonable bounds for precision and recall."""
        eval_metrics = EvaluationMetrics()
        for idx in range(10):
            eval_metrics.add_injected_anomaly("fare_negative", idx)
        for idx in range(15):
            eval_metrics.add_detected_violation("SYN001", idx, 1.0)
        result = eval_metrics.bootstrap_ci(n_resamples=100, seed=42)
        assert result["precision_ci"]["n_resamples"] == 100
        assert result["recall_ci"]["n_resamples"] == 100
        assert result["precision_ci"]["lower_bound"] <= result["precision_ci"]["mean"] <= result["precision_ci"]["upper_bound"]
        assert result["recall_ci"]["lower_bound"] <= result["recall_ci"]["mean"] <= result["recall_ci"]["upper_bound"]
        assert result["precision_ci"]["mean"] == pytest.approx(0.667, abs=0.05)

    def test_bootstrap_ci_empty(self):
        """Empty detected violations -> zero CI."""
        eval_metrics = EvaluationMetrics()
        result = eval_metrics.bootstrap_ci()
        assert result["precision_ci"]["mean"] == 0.0
        assert result["recall_ci"]["mean"] == 0.0
