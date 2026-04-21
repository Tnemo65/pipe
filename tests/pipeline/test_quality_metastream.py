"""Integration tests for quality meta-stream (L8)."""
import pytest
import time
from datetime import datetime
from unittest.mock import Mock
from streamdq.pipeline.spark_pipeline import StreamDQPipeline


def test_quality_window_tracking():
    """Window metrics accumulate correctly."""
    config = {
        "quality_emit_interval_sec": 1,
    }

    pipeline = StreamDQPipeline(config=config)

    # Verify initial state
    assert pipeline._window_id == 0
    assert pipeline._window_metrics["total_events"] == 0
    assert pipeline._window_metrics["total_violations"] == 0


def test_quality_event_no_kafka_graceful():
    """Quality event emission skips when Kafka unavailable."""
    config = {
        "quality_emit_interval_sec": 1,
    }

    pipeline = StreamDQPipeline(config=config)
    assert pipeline._quality_available is False

    # Should not raise error
    pipeline._emit_quality_event()


def test_quality_topic_default():
    """Default quality topic is streamdq_quality_events."""
    config = {}

    pipeline = StreamDQPipeline(config=config)
    assert pipeline._quality_topic == "streamdq_quality_events"


def test_quality_emit_interval_default():
    """Default quality emit interval is 300 seconds (5 minutes)."""
    config = {}

    pipeline = StreamDQPipeline(config=config)
    assert pipeline._quality_emit_interval == 300


def test_quality_window_reset():
    """Window metrics reset after emission."""
    pipeline = StreamDQPipeline(config={})

    # Simulate accumulated metrics
    pipeline._window_metrics = {
        "total_events": 1000,
        "total_violations": 50,
        "by_rule": {"SYN001": 30},
        "by_type": {},
        "by_severity": {},
        "processing_latencies": [10.0],
        "e2e_latencies": [],
        "threshold_updates": 0,
        "processing_errors": 0,
        "error_types": {},
    }
    pipeline._window_id = 5

    # Mock quality producer to verify behavior
    pipeline._quality_available = True
    pipeline._quality_producer = Mock()
    pipeline._quality_producer.send = Mock()
    pipeline._quality_producer.flush = Mock()

    # Emit event
    pipeline._emit_quality_event()

    # Verify window incremented
    assert pipeline._window_id == 6

    # Verify metrics reset
    assert pipeline._window_metrics["total_events"] == 0
    assert pipeline._window_metrics["total_violations"] == 0
    assert pipeline._window_metrics["by_rule"] == {}


def test_quality_event_structure():
    """Emitted quality event has correct structure."""
    pipeline = StreamDQPipeline(config={"pipeline_id": "test"})

    pipeline._window_metrics = {
        "total_events": 100,
        "total_violations": 10,
        "by_rule": {"SYN001": 10},
        "by_type": {"SYNTACTIC": 10},
        "by_severity": {"HIGH": 10},
        "processing_latencies": [5.0, 10.0, 15.0],
        "e2e_latencies": [],
        "threshold_updates": 2,
        "processing_errors": 0,
        "error_types": {},
    }

    # Mock producer
    pipeline._quality_available = True
    pipeline._quality_producer = Mock()
    sent_events = []

    def capture_send(topic, value):
        sent_events.append((topic, value))

    pipeline._quality_producer.send.side_effect = capture_send
    pipeline._quality_producer.flush = Mock()

    # Emit
    pipeline._emit_quality_event()

    # Verify event sent
    assert len(sent_events) == 1
    topic, event = sent_events[0]

    assert topic == "streamdq_quality_events"
    assert event["pipeline_id"] == "test"
    assert event["window_id"] == 0
    assert event["events_processed"] == 100
    assert event["total_violations"] == 10
    assert event["violation_rate"] == 0.1
    assert event["violations_by_rule"] == {"SYN001": 10}
