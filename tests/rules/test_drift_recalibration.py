"""
Tests for drift-aware threshold recalibration.

Validates context-aware PSI tracking and threshold reset callbacks.
"""
import pytest
from streamdq.rules.drift import ConceptDriftDetector


class TestContextAwareDrift:
    """Test drift detection per (field, context_key)."""

    def test_drift_detector_tracks_per_context(self):
        """Drift detector maintains separate baselines per context."""
        detector = ConceptDriftDetector(psi_threshold=0.2)

        # Set baseline for morning context
        detector.set_baseline_for_context(
            field="fare_amount",
            context_key="morning_midtown_weekday",
            stats={"p10": 10.0, "p90": 30.0, "mean": 18.0, "count": 1000},
            event_count=1000,
        )

        # Set different baseline for evening context
        detector.set_baseline_for_context(
            field="fare_amount",
            context_key="evening_midtown_weekday",
            stats={"p10": 15.0, "p90": 50.0, "mean": 28.0, "count": 1000},
            event_count=1000,
        )

        # Verify separate baselines
        morning_state = detector.get_state_for_context("fare_amount", "morning_midtown_weekday")
        evening_state = detector.get_state_for_context("fare_amount", "evening_midtown_weekday")

        assert morning_state.baseline_mean == 18.0
        assert evening_state.baseline_mean == 28.0

    def test_drift_detected_for_specific_context(self):
        """Drift in one context doesn't affect other contexts."""
        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=100)

        # Morning baseline
        detector.set_baseline_for_context(
            field="fare_amount",
            context_key="morning",
            stats={"p10": 10.0, "p90": 30.0, "mean": 18.0, "count": 1000},
            event_count=1000,
        )

        # Evening baseline
        detector.set_baseline_for_context(
            field="fare_amount",
            context_key="evening",
            stats={"p10": 15.0, "p90": 50.0, "mean": 28.0, "count": 1000},
            event_count=1000,
        )

        # Inject drift in evening context only
        result_evening = detector.check_drift_for_context(
            field="fare_amount",
            context_key="evening",
            current_stats={"p10": 25.0, "p90": 80.0, "mean": 50.0},  # Large shift
            event_count=1200,
        )

        # Evening context has drift
        assert result_evening is not None
        assert result_evening.drift_detected is True
        assert result_evening.psi >= 0.2

        # Morning context should not have drift (no check yet)
        result_morning = detector.check_drift_for_context(
            field="fare_amount",
            context_key="morning",
            current_stats={"p10": 10.5, "p90": 31.0, "mean": 18.5},  # Small shift
            event_count=1200,
        )

        assert result_morning is not None
        assert result_morning.drift_detected is False
