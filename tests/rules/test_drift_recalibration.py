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


class TestDriftCallback:
    """Test drift detection triggers threshold reset."""

    def test_drift_detector_calls_callback(self):
        """Drift detector calls registered callback on drift detection."""
        callback_invoked = []

        def on_drift(field, context_key, psi):
            callback_invoked.append((field, context_key, psi))

        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=100)
        detector.register_drift_callback(on_drift)

        # Set baseline
        detector.set_baseline_for_context(
            field="fare_amount",
            context_key="morning",
            stats={"p10": 10.0, "p90": 30.0, "mean": 18.0, "count": 1000},
            event_count=1000,
        )

        # Inject drift
        result = detector.check_drift_for_context(
            field="fare_amount",
            context_key="morning",
            current_stats={"p10": 25.0, "p90": 80.0, "mean": 50.0},
            event_count=1200,
        )

        assert result.drift_detected is True
        assert len(callback_invoked) == 1
        assert callback_invoked[0][0] == "fare_amount"
        assert callback_invoked[0][1] == "morning"
        assert callback_invoked[0][2] >= 0.2

    def test_multiple_callbacks_registered(self):
        """Multiple callbacks can be registered."""
        callback1_invoked = []
        callback2_invoked = []

        def callback1(field, context_key, psi):
            callback1_invoked.append(field)

        def callback2(field, context_key, psi):
            callback2_invoked.append(context_key)

        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=100)
        detector.register_drift_callback(callback1)
        detector.register_drift_callback(callback2)

        detector.set_baseline_for_context(
            field="fare_amount",
            context_key="evening",
            stats={"p10": 15.0, "p90": 50.0, "mean": 28.0, "count": 1000},
            event_count=1000,
        )

        detector.check_drift_for_context(
            field="fare_amount",
            context_key="evening",
            current_stats={"p10": 30.0, "p90": 90.0, "mean": 55.0},
            event_count=1200,
        )

        assert len(callback1_invoked) == 1
        assert len(callback2_invoked) == 1
        assert callback1_invoked[0] == "fare_amount"
        assert callback2_invoked[0] == "evening"


class TestDriftThresholdIntegration:
    """Test drift detector resets context-aware thresholds."""

    def test_drift_resets_context_thresholds(self):
        """Drift detection triggers threshold reset for specific context."""
        from streamdq.rules.context_adaptive import ContextAwareAdaptiveThresholdEngine
        from streamdq.models.context_registry import ContextRegistry
        from pathlib import Path

        # Setup context-aware engine
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        config_path = PROJECT_ROOT / "config" / "context_nyc_taxi.yaml"

        if not config_path.exists():
            pytest.skip(f"Config not found: {config_path}")

        registry = ContextRegistry.from_yaml(str(config_path))
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=1000,
        )

        # Setup drift detector
        detector = ConceptDriftDetector(psi_threshold=0.2, check_interval=100)

        # Connect drift detector to engine
        def on_drift_detected(field, context_key, psi):
            engine.reset_context(field, context_key)

        detector.register_drift_callback(on_drift_detected)

        # Populate morning context with values
        morning_event = {
            "tpep_pickup_datetime": "2024-01-15T10:00:00",
            "PULocationID": 161,
        }

        for i in range(100):
            engine.update("fare_amount", 15.0 + i * 0.1, morning_event)

        # Trigger recompute to populate stats
        engine._recompute()

        # Extract context key from an event
        context = registry.resolve(morning_event)
        context_key = registry.match_key(context, level=0)
        composite_key = engine._make_composite_key("fare_amount", context_key)

        assert composite_key in engine._buffers
        assert len(engine._buffers[composite_key]) == 100

        # Set baseline
        morning_stats = engine.get_stats_for_context("fare_amount", context, level=0)
        assert morning_stats is not None

        detector.set_baseline_for_context(
            field="fare_amount",
            context_key=context_key,
            stats={"p10": morning_stats["p10"], "p90": morning_stats["p90"], "mean": morning_stats["mean"], "count": 100},
            event_count=100,
        )

        # Trigger drift (large shift in fare)
        result = detector.check_drift_for_context(
            field="fare_amount",
            context_key=context_key,
            current_stats={"p10": 30.0, "p90": 80.0, "mean": 50.0},
            event_count=200,
        )

        assert result.drift_detected is True

        # Verify buffer was reset
        assert len(engine._buffers[composite_key]) == 0  # Reset clears buffer
