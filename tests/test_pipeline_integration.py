"""
Integration tests for the LocalPipeline.
"""
from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from streamdq.pipeline.local_pipeline import LocalPipeline
from streamdq.rules.registry import build_default_registry, reset_cross_record_state
from streamdq.rules.adaptive import AdaptiveThresholdEngine
from streamdq.storage.violation_store import ViolationStore


class TestLocalPipeline:
    """Integration tests for LocalPipeline."""

    def setup_method(self):
        import os, tempfile
        reset_cross_record_state()
        # Clear SQLite between tests to avoid state pollution
        tmp_path = os.path.join(tempfile.gettempdir(), "streamdq_violations.db")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except PermissionError:
                pass  # may be locked by previous test

    def test_valid_events_no_violations(self):
        """Valid events should produce no violations."""
        pipeline = LocalPipeline()
        events = [
            {
                "trip_id": f"valid-{i}",  # unique per test
                "fare_amount": 15.0,
                "PULocationID": 1,
                "tpep_pickup_datetime": (datetime.now() - timedelta(hours=1)).isoformat(),
                "tpep_dropoff_datetime": datetime.now().isoformat(),
                "trip_distance": 5.0,
            }
            for i in range(10)
        ]
        metrics = pipeline.process_events(events)
        assert metrics["total_events"] == 10
        assert metrics["total_violations"] == 0

    def test_anomaly_injection_detected(self):
        """Injected anomalies should produce violations."""
        pipeline = LocalPipeline()
        events = [
            {"trip_id": "anomaly-T1", "fare_amount": -10.0, "PULocationID": 1,
             "tpep_pickup_datetime": datetime.now().isoformat(),
             "tpep_dropoff_datetime": datetime.now().isoformat(),
             "trip_distance": 5.0},
        ]
        metrics = pipeline.process_events(events)
        assert metrics["total_violations"] >= 1
        assert "SYN001" in metrics["by_rule"]

    def test_multiple_rule_firing(self):
        """Single event can trigger multiple rules."""
        pipeline = LocalPipeline()
        events = [
            {"trip_id": "multi-T1", "fare_amount": -10.0, "PULocationID": 99999,
             "tpep_pickup_datetime": datetime.now().isoformat(),
             "tpep_dropoff_datetime": datetime.now().isoformat(),
             "trip_distance": 5.0},
        ]
        metrics = pipeline.process_events(events)
        # SYN001 (negative fare) + SYN002 (invalid location) = 2+ violations
        assert metrics["total_violations"] >= 2
        assert "SYN001" in metrics["by_rule"]
        assert "SYN002" in metrics["by_rule"]

    def test_adaptive_threshold_updates(self):
        """Adaptive threshold engine should accumulate data after enough events."""
        pipeline = LocalPipeline(adaptive_threshold_window=10_000)
        # recompute_every=1000, so need 1000 events to trigger first computation
        events = [
            {"trip_id": f"T{i}", "fare_amount": 10.0 + i, "PULocationID": 1,
             "tpep_pickup_datetime": datetime.now().isoformat(),
             "tpep_dropoff_datetime": datetime.now().isoformat(),
             "trip_distance": 5.0}
            for i in range(1_000)
        ]
        pipeline.process_events(events)
        stats = pipeline.threshold_engine.get_stats("fare_amount")
        assert "_source" in stats
        assert "p90" in stats

    def test_violations_stored(self):
        """Violations should be persisted to the store."""
        import tempfile, os, time
        # Use timestamp-based unique path to avoid cross-test pollution
        tmp_path = os.path.join(tempfile.gettempdir(), f"test_violations_{int(time.time()*1000)}.db")
        store = ViolationStore("sqlite", tmp_path)
        pipeline = LocalPipeline(violation_store=store)
        events = [
            {"trip_id": f"stored-unique-{time.time()}", "fare_amount": -99.0, "PULocationID": 1,
             "tpep_pickup_datetime": datetime.now().isoformat(),
             "tpep_dropoff_datetime": datetime.now().isoformat(),
             "trip_distance": 5.0},
        ]
        pipeline.process_events(events)
        summary = store.get_summary()
        assert summary["total"] >= 1
        store.close()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except PermissionError:
                pass

    def test_reset_clears_state(self):
        """Reset should clear all state."""
        import time
        pipeline = LocalPipeline()
        events = [
            {"trip_id": f"reset-unique-{time.time()}", "fare_amount": -77.0, "PULocationID": 1,
             "tpep_pickup_datetime": datetime.now().isoformat(),
             "tpep_dropoff_datetime": datetime.now().isoformat(),
             "trip_distance": 5.0},
        ]
        pipeline.process_events(events)
        assert pipeline._metrics["total_violations"] >= 1

        pipeline.reset()
        assert pipeline._metrics["total_violations"] == 0
        assert pipeline.threshold_engine.event_count == 0


class TestAdaptiveThresholdEngine:
    """Tests for AdaptiveThresholdEngine."""

    def test_accumulation(self):
        engine = AdaptiveThresholdEngine(window_size=1000, recompute_every=100)
        for i in range(200):
            engine.update("fare", float(i))

        stats = engine.get_stats("fare")
        assert stats["count"] == 200
        assert "p50" in stats
        assert "p90" in stats
        assert stats["p50"] == 99.5  # Linear interpolation: (99+100)/2 for n=200

    def test_rolling_window(self):
        """Buffer is capped at window_size."""
        engine = AdaptiveThresholdEngine(window_size=100, recompute_every=100)
        for i in range(200):
            engine.update("value", float(i))

        stats = engine.get_stats("value")
        assert stats["count"] == 100  # Window capped at 100

    def test_override_takes_precedence(self):
        engine = AdaptiveThresholdEngine(window_size=100)
        engine.update("fare", 50.0)
        engine.override("fare", {"p90": 100.0, "custom_threshold": 200.0})

        stats = engine.get_stats("fare")
        assert stats["override_custom_threshold"] == 200.0
        assert stats["override_p90"] == 100.0
        assert stats["_source"] == "override"

    def test_not_enough_data(self):
        engine = AdaptiveThresholdEngine(window_size=100, min_sample_size=100)
        for i in range(50):
            engine.update("fare", float(i))

        stats = engine.get_stats("fare")
        assert stats == {}  # Not enough data yet

    def test_percentile_interpolation(self):
        """B8 fix: Linear interpolation avoids downward bias."""
        engine = AdaptiveThresholdEngine(window_size=1000, recompute_every=1, min_sample_size=5)
        # Sequence 0..9 (10 values): p10=0.9, p25=2.25, p50=4.5, p75=6.75, p90=8.1
        for i in range(10):
            engine.update("val", float(i))
        stats = engine.get_stats("val")
        assert "p25" in stats, f"Stats should be computed: {stats}"
        assert stats["p25"] == 2.25, f"Expected 2.25, got {stats['p25']}"
        assert stats["p50"] == 4.5, f"Expected 4.5, got {stats['p50']}"
        assert stats["p75"] == 6.75, f"Expected 6.75, got {stats['p75']}"
        assert stats["p10"] == 0.9, f"Expected 0.9, got {stats['p10']}"
        assert stats["p90"] == 8.1, f"Expected 8.1, got {stats['p90']}"
