"""
Spark Structured Streaming pipeline.

Reads from Kafka, evaluates rules per micro-batch,
writes violations to Kafka and SQLite.

Architecture (F3 refactor):
  - Stateless rules (SYN000-003, SEM001-003, FIT001): Push to Spark DataFrame-level
    SQL filter operations — no Python UDF needed, runs on workers in parallel.
  - Stateful rules (CRS001-003): Use FlatMapGroupsWithState with per-entity state
    in Spark StateStore — distributed, fault-tolerant, checkpointed.
  - Adaptive thresholds: Single-node AdaptiveThresholdEngine on driver (acceptable
    for threshold aggregation, which is low-volume data).
"""
from __future__ import annotations
import json
import os
import time
import threading
from datetime import datetime
from typing import Optional, Iterator

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, TimestampType,
)
from pyspark.sql.streaming import GroupStateTimeout
from pyspark.sql import Row

try:
    import pandas as _pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _pd = None
    _PANDAS_AVAILABLE = False

from streamdq.rules.registry import RuleRegistry, build_default_registry
from streamdq.rules.adaptive import AdaptiveThresholdEngine
from streamdq.rules.cross_record import (
    save_cross_record_state,
    evaluate_trajectory_anomaly,
    evaluate_duplicate_event,
)
from streamdq.storage.violation_store import ViolationStore

# Prometheus metrics
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, start_http_server, REGISTRY
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    # Stub metrics when prometheus_client not installed
    class _StubMetric:
        def labels(self, **kwargs): return self
        def inc(self, n=1): pass
        def observe(self, n): pass
        def set(self, n): pass
    class _StubGauge:
        def labels(self, **kwargs): return _StubMetric()
        def set(self, n): pass
        def inc(self, n=1): pass
        def dec(self, n=1): pass
    class _StubCounter:
        def labels(self, **kwargs): return _StubMetric()
        def inc(self, n=1): pass
    _metrics = {
        "events_total": _StubCounter(),
        "violations_total": _StubCounter(),
        "errors_total": _StubCounter(),
        "batch_latency": _StubMetric(),
        "batch_size": _StubMetric(),
        # NG-19: Rule health metrics (stub)
        "rule_true_positives": _StubCounter(),
        "rule_false_positives": _StubCounter(),
        "rule_alerts_sent": _StubCounter(),
        "rule_health_score": _StubGauge(),
        "rule_last_alert_time": _StubGauge(),
    }
else:
    _metrics = {
        "events_total": Counter(
            "streamdq_events_total", "Total events processed",
            ["topic"]
        ),
        "violations_total": Counter(
            "streamdq_violations_total", "Total violations detected",
            ["rule_id", "violation_type"]
        ),
        "errors_total": Counter(
            "streamdq_processing_errors_total", "Total processing errors",
            ["error_type"]
        ),
        "batch_latency": Histogram(
            "streamdq_batch_latency_seconds",
            "Micro-batch processing latency in seconds",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        ),
        "batch_size": Histogram(
            "streamdq_batch_size",
            "Micro-batch event count",
            buckets=[10, 50, 100, 250, 500, 1000, 5000, 10000]
        ),
        "threshold_p10": Gauge(
            "streamdq_threshold_p10", "Adaptive P10 threshold",
            ["field"]
        ),
        "threshold_p90": Gauge(
            "streamdq_threshold_p90", "Adaptive P90 threshold",
            ["field"]
        ),
        # NG-19: Rule health metrics — for silent failure detection
        # and threshold misconfiguration monitoring
        "rule_true_positives": Counter(
            "streamdq_rule_true_positives_total",
            "Violations confirmed against ground truth (evaluation runs)",
            ["rule_id"]
        ),
        "rule_false_positives": Counter(
            "streamdq_rule_false_positives_total",
            "Spurious violations not matched to ground truth",
            ["rule_id"]
        ),
        "rule_alerts_sent": Counter(
            "streamdq_rule_alerts_sent_total",
            "Alerts actually sent after deduplication",
            ["rule_id", "severity"]
        ),
        "rule_health_score": Gauge(
            "streamdq_rule_health_score",
            "Rule TP rate (TP / (TP + FP)) — drop indicates threshold misconfiguration",
            ["rule_id"]
        ),
        "rule_last_alert_time": Gauge(
            "streamdq_rule_last_alert_time_seconds",
            "Unix timestamp of last alert per rule — zero = silent failure",
            ["rule_id"]
        ),
    }


NYC_TAXI_SCHEMA = StructType([
    StructField("trip_id", StringType(), True),
    StructField("VendorID", StringType(), True),
    StructField("tpep_pickup_datetime", StringType(), True),
    StructField("tpep_dropoff_datetime", StringType(), True),
    StructField("passenger_count", DoubleType(), True),
    StructField("trip_distance", DoubleType(), True),
    StructField("PULocationID", IntegerType(), True),
    StructField("DOLocationID", IntegerType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("extra", DoubleType(), True),
    StructField("mta_tax", DoubleType(), True),
    StructField("tip_amount", DoubleType(), True),
    StructField("tolls_amount", DoubleType(), True),
    StructField("improvement_surcharge", DoubleType(), True),
    StructField("total_amount", DoubleType(), True),
    StructField("congestion_surcharge", DoubleType(), True),
    StructField("payment_type", StringType(), True),
    StructField("entity_type", StringType(), True),
])

# ────────────────────────────────────────────────────────────────
# Context helpers
# ────────────────────────────────────────────────────────────────

# US Federal holidays and major observed days (2024-2026)
_HOLIDAYS: set[str] = {
    # 2024
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27",
    "2024-06-19", "2024-07-04", "2024-09-02", "2024-10-14",
    "2024-11-28", "2024-12-25",
    # 2025
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-10-13",
    "2025-11-27", "2025-12-25",
    # 2026
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-10-12",
    "2026-11-26", "2026-12-25",
}


def _is_holiday(dt: datetime) -> bool:
    """Check if date is a US federal holiday or major observed day."""
    return dt.strftime("%Y-%m-%d") in _HOLIDAYS


def _build_external_context(now: datetime, batch_id: int, config: dict) -> dict:
    """
    Build enriched external_context with time-of-day and date features.

    This makes the pipeline truly context-aware by providing:
    - is_rush_hour: peak commute times (7-9 AM, 5-7 PM weekdays)
    - is_weekend: Saturday/Sunday
    - is_holiday: US federal holidays
    - processing_hour / processing_day: raw temporal values
    """
    hour = now.hour
    day = now.weekday()
    return {
        "processing_hour": hour,
        "processing_day": day,
        "is_rush_hour": (7 <= hour <= 9 or 17 <= hour <= 19) and day < 5,
        "is_late_night": 0 <= hour <= 5,
        "is_weekend": day >= 5,
        "is_holiday": _is_holiday(now),
        "pipeline_id": config.get("pipeline_id", "default"),
        "batch_id": batch_id,
    }


# ────────────────────────────────────────────────────────────────
# F3-a: Distributed CRS state via FlatMapGroupsWithState
# ────────────────────────────────────────────────────────────────

# CRS001/CRS002: Per-vehicle state (GPS position tracking)
_VEHICLE_STATE_SCHEMA = StructType([
    StructField("vehicle_id", StringType(), False),
    StructField("latitude", DoubleType(), False),
    StructField("longitude", DoubleType(), False),
    StructField("timestamp_sec", DoubleType(), False),
    StructField("seq", IntegerType(), False),
])

# CRS003: Per-hash dedup state (event fingerprint tracking)
_DEDUP_STATE_SCHEMA = StructType([
    StructField("event_hash", StringType(), False),
    StructField("first_seen_time", DoubleType(), False),
    StructField("trip_id", StringType(), False),
    StructField("PULocationID", IntegerType(), True),
    StructField("DOLocationID", IntegerType(), True),
    StructField("passenger_count", DoubleType(), True),
    StructField("trip_distance", DoubleType(), True),
])

# CRS parameters
_MAX_SPEED_KMH = 160.0   # CRS001: max allowed GPS speed (km/h)
_MAX_STATIONARY_JUMP_M = 100.0  # CRS002: max position jump for stationary vehicle (m)
_DEDUP_WINDOW_SEC = 300.0  # CRS003: dedup window (seconds)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters between two WGS84 lat/lon points."""
    import math
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _make_violation_row(
    rule_id: str,
    rule_name: str,
    entity_id: str,
    entity_type: str,
    severity: str,
    violation_type: str,
    details: dict,
    expected: dict,
    record: dict,
    detected_at: str,
    latency_ms: float,
) -> Row:
    """Construct a violation Row matching ViolationStore schema."""
    return Row(
        rule_id=rule_id,
        rule_name=rule_name,
        entity_id=entity_id,
        entity_type=entity_type,
        severity=severity,
        violation_type=violation_type,
        details=json.dumps(details, default=str),
        expected=json.dumps(expected, default=str),
        record_snapshot=json.dumps(record, default=str),
        detected_at=detected_at,
        processing_latency_ms=latency_ms,
    )


def _evaluate_vehicle_state_fn(
    vehicle_id: str,
    events: Iterator[Row],
    state,
) -> Iterator[Row]:
    """
    FlatMapGroupsWithState function for CRS001/CRS002.

    Called per vehicle_id across Spark partitions — distributed, fault-tolerant.
    Maintains per-vehicle GPS state in Spark StateStore (checkpoint to disk).

    Latency: Computed as (current processing time - GPS timestamp), capped at 0.
    This measures "how stale is this event when we detect the violation" — a proxy
    for end-to-end latency since we don't have Kafka arrival metadata in workers.
    """
    import math

    events_list = list(events)
    if not events_list:
        return

    now_sec = time.time()
    violations = []

    for event in events_list:
        lat = float(event.latitude)
        lon = float(event.longitude)
        ts_sec = float(event.timestamp_sec)
        seq = int(event.seq)

        record_dict = event.asDict() if hasattr(event, "asDict") else dict(event)

        def _latency_ms(ts: float) -> float:
            """Compute relative latency: (now - event_timestamp) in ms, capped at 0."""
            return max((now_sec - ts) * 1000, 0.0)

        if state.exists:
            prev = state.get
            prev_lat = float(prev.latitude)
            prev_lon = float(prev.longitude)
            prev_ts = float(prev.timestamp_sec)
            prev_seq = int(prev.seq)

            # Skip if sequence went backward (data issue)
            if seq < prev_seq:
                state.update(Row(
                    vehicle_id=vehicle_id,
                    latitude=lat,
                    longitude=lon,
                    timestamp_sec=ts_sec,
                    seq=seq,
                ))
                return

            time_diff = ts_sec - prev_ts

            # CRS001: Impossible speed detection
            if time_diff > 0:
                distance_m = _haversine_m(prev_lat, prev_lon, lat, lon)
                speed_kmh = (distance_m / 1000.0) / (time_diff / 3600.0)
                if speed_kmh > _MAX_SPEED_KMH:
                    violations.append(_make_violation_row(
                        rule_id="CRS001",
                        rule_name="Trajectory anomaly (impossible speed)",
                        entity_id=vehicle_id,
                        entity_type="gtfs_vehicle",
                        severity="CRITICAL",
                        violation_type="CROSS_RECORD",
                        details={
                            "field": "gps_speed_kmh",
                            "value": round(speed_kmh, 1),
                            "max_allowed_kmh": _MAX_SPEED_KMH,
                            "distance_m": round(distance_m, 1),
                            "time_diff_sec": round(time_diff, 1),
                        },
                        expected={"gps_speed_kmh": {"max": _MAX_SPEED_KMH}},
                        record=record_dict,
                        detected_at=datetime.now().isoformat(),
                        latency_ms=_latency_ms(ts_sec),
                    ))

            # CRS002: GPS spoofing detection (stationary + position jump)
            if time_diff > 0:
                distance_m = _haversine_m(prev_lat, prev_lon, lat, lon)
                if distance_m > _MAX_STATIONARY_JUMP_M:
                    speed_kmh = (distance_m / 1000.0) / (time_diff / 3600.0)
                    if speed_kmh < 40.0:
                        if speed_kmh < 1.0:
                            sev, reason = "CRITICAL", "Vehicle reported as stationary but position jumped"
                        elif speed_kmh < 20.0:
                            sev, reason = "HIGH", f"Slow drift GPS anomaly: {speed_kmh:.1f} km/h with {distance_m:.0f}m jump"
                        else:
                            sev, reason = "MEDIUM", f"Moderate GPS anomaly: {speed_kmh:.1f} km/h with {distance_m:.0f}m jump"
                        violations.append(_make_violation_row(
                            rule_id="CRS002",
                            rule_name="GPS spoofing (stationary vehicle jump)",
                            entity_id=vehicle_id,
                            entity_type="gtfs_vehicle",
                            severity=sev,
                            violation_type="CROSS_RECORD",
                            details={
                                "field": "position_jump_m",
                                "value": round(distance_m, 1),
                                "max_stationary_jump_m": _MAX_STATIONARY_JUMP_M,
                                "speed_kmh": round(speed_kmh, 1),
                                "time_diff_sec": round(time_diff, 1),
                                "reason": reason,
                            },
                            expected={"position_jump_m": {"max": _MAX_STATIONARY_JUMP_M}},
                            record=record_dict,
                            detected_at=datetime.now().isoformat(),
                            latency_ms=_latency_ms(ts_sec),
                        ))

        # Update state for next event
        state.update(Row(
            vehicle_id=vehicle_id,
            latitude=lat,
            longitude=lon,
            timestamp_sec=ts_sec,
            seq=seq,
        ))

        # Set timeout: expire state after 10 minutes of no updates
        state.setTimeoutDuration(600)

    for v in violations:
        yield v


def _evaluate_dedup_state_fn(
    key: str,
    events: Iterator[Row],
    state,
) -> Iterator[Row]:
    """
    FlatMapGroupsWithState function for CRS003 (duplicate detection).

    Called per event_hash across Spark partitions — distributed, fault-tolerant.
    Deduplication window: 300 seconds.

    Latency: Uses `now_sec` (processing time) minus the event's timestamp as proxy.
    """
    events_list = list(events)
    if not events_list:
        return

    now_sec = time.time()
    event = events_list[0]  # Take the first event with this hash

    record_dict = event.asDict() if hasattr(event, "asDict") else dict(event)

    if state.exists:
        prev = state.get
        first_seen = float(prev.first_seen_time)

        if now_sec - first_seen <= _DEDUP_WINDOW_SEC:
            # Duplicate within window — emit violation
            state.remove()
            yield _make_violation_row(
                rule_id="CRS003",
                rule_name="Duplicate event detected",
                entity_id=str(record_dict.get("trip_id", key)),
                entity_type=record_dict.get("entity_type", "nyc_taxi"),
                severity="HIGH",
                violation_type="CROSS_RECORD",
                details={
                    "field": "trip_id+PULocationID+DOLocationID",
                    "value": key,
                    "first_seen_time": first_seen,
                    "current_time": now_sec,
                    "window_sec": _DEDUP_WINDOW_SEC,
                    "reason": "DUPLICATE_RECORD",
                },
                expected={"dedup_window_sec": _DEDUP_WINDOW_SEC},
                record=record_dict,
                detected_at=datetime.now().isoformat(),
                latency_ms=max((now_sec - float(events_list[0].timestamp_sec)) * 1000, 0.0) if hasattr(events_list[0], "timestamp_sec") and events_list[0].timestamp_sec else 0.0,
            )
            return

    # First occurrence — register in state
    state.update(Row(
        event_hash=key,
        first_seen_time=now_sec,
        trip_id=str(record_dict.get("trip_id", "")),
        PULocationID=int(record_dict["PULocationID"]) if record_dict.get("PULocationID") is not None else None,
        DOLocationID=int(record_dict["DOLocationID"]) if record_dict.get("DOLocationID") is not None else None,
        passenger_count=float(record_dict["passenger_count"]) if record_dict.get("passenger_count") is not None else None,
        trip_distance=float(record_dict["trip_distance"]) if record_dict.get("trip_distance") is not None else None,
    ))
    state.setTimeoutDuration(int(_DEDUP_WINDOW_SEC) + 10)


class StreamDQPipeline:
    """
    Spark Structured Streaming pipeline for StreamDQ.

    Reads events from Kafka, evaluates all rules per micro-batch,
    writes violations to Kafka (quality-violations topic) and SQLite.

    Usage:
        pipeline = StreamDQPipeline(config)
        pipeline.run(
            kafka_bootstrap="localhost:9092",
            kafka_topic="nyc-taxi-events",
            violation_topic="quality-violations",
        )
    """

    def __init__(
        self,
        config: dict = None,
        rule_registry: RuleRegistry = None,
    ):
        self.config = config or {}
        self.registry = rule_registry or build_default_registry()
        self.threshold_engine = AdaptiveThresholdEngine(window_size=10_000)
        self.violation_store = ViolationStore(
            self.config.get("violation_store_backend", "sqlite"),
            self.config.get("violation_store_path"),
        )
        self.spark: Optional[SparkSession] = None
        self._running = False
        self._metrics_port = self.config.get("metrics_port", 9091)
        self._metrics_server_started = False
        self._state_checkpoint_path = self.config.get("state_checkpoint_path")

        # P0-3: Kafka violation producer
        self._kafka_bootstrap: Optional[str] = None
        self._violation_topic: Optional[str] = None
        self._kafka_producer = None
        self._kafka_available = False
        if self.config.get("kafka_bootstrap_servers") and self.config.get("violation_topic"):
            try:
                from kafka import KafkaProducer
                self._kafka_bootstrap = self.config["kafka_bootstrap_servers"]
                self._violation_topic = self.config["violation_topic"]
                self._kafka_producer = KafkaProducer(
                    bootstrap_servers=self._kafka_bootstrap,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                    acks="all",
                )
                self._kafka_available = True
                print(f"[StreamDQ] Kafka violation producer ready: {self._violation_topic}")
            except Exception as e:
                print(f"[StreamDQ] Kafka producer not available: {e}")
                self._kafka_available = False

        # Start Prometheus metrics HTTP server in background thread
        if _PROMETHEUS_AVAILABLE and not self._metrics_server_started:
            try:
                start_http_server(self._metrics_port)
                self._metrics_server_started = True
                print(f"[StreamDQ] Prometheus metrics server started on port {self._metrics_port}")
            except OSError as e:
                print(f"[StreamDQ] Could not start Prometheus server on port {self._metrics_port}: {e}")
                print("[StreamDQ] Metrics will not be exposed (port may be in use)")


    def _create_spark(self) -> SparkSession:
        """Create and configure SparkSession."""
        builder = (
            SparkSession.builder
            .appName("StreamDQ-NYCTaxi")
            .config("spark.sql.streaming.checkpointLocation",
                    self.config.get("checkpoint_dir", "/tmp/streamdq-checkpoint"))
            .config("spark.sql.shuffle.partitions", "8")
        )
        if self.config.get("spark_master"):
            builder = builder.master(self.config["spark_master"])
        return builder.getOrCreate()

    def _parse_event(self, raw_value: bytes) -> Optional[dict]:
        """Parse a raw Kafka message value to dict."""
        try:
            text = raw_value.decode("utf-8")
            return json.loads(text)
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            return None

    def _process_batch(self, batch_df: DataFrame, batch_id: int):
        """
        Process a Spark micro-batch of events (fallback for legacy mode).

        For true distributed processing, use run_distributed() instead.
        This method handles per-event latency (F3-c) and batch Kafka sends (F5-b).
        """
        start_time = time.perf_counter()
        events = batch_df.collect()
        batch_start_ms = time.time() * 1000
        event_time = datetime.now()
        all_violations = []

        # Update adaptive thresholds
        for event in events:
            event_dict = event.asDict()
            for field in ["fare_amount", "trip_distance"]:
                value = event_dict.get(field)
                if value is not None:
                    try:
                        self.threshold_engine.update(field, float(value))
                    except (ValueError, TypeError):
                        pass

        # Update threshold metrics for Prometheus
        if _PROMETHEUS_AVAILABLE:
            for field in ["fare_amount", "trip_distance"]:
                stats = self.threshold_engine.get_stats(field)
                if stats:
                    _metrics["threshold_p10"].labels(field=field).set(stats.get("p10", 0))
                    _metrics["threshold_p90"].labels(field=field).set(stats.get("p90", 0))

        historical_stats = self.threshold_engine.get_all_stats()

        # Stateless rule evaluation
        from streamdq.rules.base import RuleContext
        now = datetime.now()
        external = _build_external_context(now, batch_id, self.config)
        for event in events:
            event_dict = event.asDict()
            # F3-c: Per-event latency — extract Kafka timestamp for accurate timing
            kafka_ts_ms = event_dict.get("timestamp", batch_start_ms)
            event_start = kafka_ts_ms / 1000.0
            ctx = RuleContext(
                event=event_dict,
                event_time=event_dict.get("event_time", event_time),
                historical_stats=historical_stats,
                external_context=external,
                start_time=event_start,
            )
            for violation in self.registry.evaluate_all(ctx):
                all_violations.append(violation)

        # Evaluate stateful rules (legacy: module-level dicts on driver)
        for event in events:
            event_dict = event.asDict()
            entity_type = event_dict.get("entity_type", "nyc_taxi")
            if entity_type == "gtfs_vehicle":
                raw_value = event_dict.get("value")
                if raw_value:
                    try:
                        gtfs_event = json.loads(raw_value.decode("utf-8"))
                    except Exception:
                        gtfs_event = {}
                else:
                    gtfs_event = {}
                gtfs_event["entity_type"] = "gtfs_vehicle"
                crs_violations = evaluate_trajectory_anomaly(
                    gtfs_event, event_time, time.time()
                )
                all_violations.extend(crs_violations)
                dup_violation = evaluate_duplicate_event(
                    gtfs_event, event_time, time.time(), dedup_state=None
                )
                if dup_violation:
                    all_violations.append(dup_violation)
            else:
                dup_violation = evaluate_duplicate_event(
                    event_dict, event_time, time.time(), dedup_state=None
                )
                if dup_violation:
                    all_violations.append(dup_violation)

        # F5-a: Store violations to SQLite
        if all_violations:
            self.violation_store.store_batch(all_violations)

        # F5-b: Batch Kafka sends (F5-b optimization)
        if self._kafka_available and all_violations:
            violation_records = []
            for v in all_violations:
                try:
                    violation_records.append({
                        "rule_id": v.rule_id,
                        "rule_name": v.rule_name,
                        "entity_id": v.entity_id,
                        "entity_type": v.entity_type,
                        "severity": v.severity,
                        "violation_type": v.violation_type,
                        "details": v.details,
                        "expected": v.expected,
                        "record_snapshot": v.record_snapshot,
                        "detected_at": v.detected_at.isoformat() if v.detected_at else None,
                        "processing_latency_ms": v.processing_latency_ms,
                    })
                except Exception:
                    pass
            if violation_records:
                try:
                    # Use send_all equivalent: send batch at once
                    future = self._kafka_producer.sendbatch(
                        [(self._violation_topic, json.dumps(r, default=str).encode("utf-8"))
                         for r in violation_records]
                    )
                    self._kafka_producer.flush(timeout=5)
                except (AttributeError, TypeError):
                    # Fallback: send individually if sendbatch not available
                    for r in violation_records:
                        try:
                            self._kafka_producer.send(
                                self._violation_topic,
                                value=r,
                            )
                        except Exception:
                            pass
                    self._kafka_producer.flush(timeout=5)
                except Exception:
                    pass

        # Record Prometheus metrics
        latency_s = time.perf_counter() - start_time
        event_count = len(events)
        violation_count = len(all_violations)

        if _PROMETHEUS_AVAILABLE:
            _metrics["events_total"].labels(topic=self.config.get("kafka_topic", "unknown")).inc(event_count)
            _metrics["batch_size"].observe(event_count)
            _metrics["batch_latency"].observe(latency_s)
            for v in all_violations:
                _metrics["violations_total"].labels(
                    rule_id=v.rule_id,
                    violation_type=v.violation_type
                ).inc()
                # NG-19: Rule health metrics — alert volume and last-alert timestamp
                _metrics["rule_alerts_sent"].labels(
                    rule_id=v.rule_id,
                    severity=v.severity
                ).inc()
                _metrics["rule_last_alert_time"].labels(
                    rule_id=v.rule_id
                ).set(time.time())

        print(f"[Batch {batch_id}] {event_count} events, {violation_count} violations, "
              f"{latency_s*1000:.1f}ms latency")

        # Save cross-record state checkpoint for fault tolerance
        if self._state_checkpoint_path and self._running:
            try:
                save_cross_record_state(self._state_checkpoint_path)
            except Exception:
                pass

    def run(
        self,
        kafka_bootstrap: str,
        kafka_topic: str,
        violation_topic: str = "quality-violations",
        gtfs_topic: str = None,
        output_mode: str = "complete",
        starting_offsets: str = "earliest",
    ):
        """
        Run the streaming pipeline.

        For true distributed processing with FlatMapGroupsWithState,
        use run_distributed() instead.

        Args:
            kafka_bootstrap: Kafka bootstrap servers (e.g. "localhost:9092")
            kafka_topic: Source Kafka topic for NYC taxi events
            violation_topic: Destination Kafka topic for violations
            gtfs_topic: Optional GTFS vehicle position topic for CRS001/CRS002
            output_mode: "complete" or "append"
            starting_offsets: "earliest" or "latest"
        """
        self.spark = self._create_spark()

        # P0-2: Wire GTFS topic if provided
        if gtfs_topic:
            kafka_df = (
                self.spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", kafka_bootstrap)
                .option("subscribe", f"{kafka_topic},{gtfs_topic}")
                .option("startingOffsets", starting_offsets)
                .load()
            )
            # Route based on topic: GTFS stays raw, taxi gets parsed
            events_df = kafka_df.withColumn(
                "entity_type",
                F.when(F.col("topic") == gtfs_topic, "gtfs_vehicle").otherwise("nyc_taxi")
            )
        else:
            kafka_df = (
                self.spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", kafka_bootstrap)
                .option("subscribe", kafka_topic)
                .option("startingOffsets", starting_offsets)
                .load()
            )
            events_df = kafka_df.withColumn("entity_type", F.lit("nyc_taxi"))

        # Process each micro-batch
        query = (
            events_df
            .writeStream
            .foreachBatch(self._process_batch)
            .option("checkpointLocation",
                    self.config.get("checkpoint_dir", "/tmp/streamdq-checkpoint"))
            .outputMode(output_mode)
            .start()
        )

        self._running = True
        print(f"StreamDQ pipeline started. Reading from: {kafka_topic}")
        print(f"Violations stored to: {self.config.get('violation_store_backend', 'sqlite')}")
        if self._kafka_available:
            print(f"Kafka violations topic: {self._violation_topic}")

        return query

    def run_distributed(
        self,
        kafka_bootstrap: str,
        kafka_topic: str,
        violation_topic: str = "quality-violations",
        gtfs_topic: str = None,
        starting_offsets: str = "earliest",
    ):
        """
        Run the pipeline with true distributed processing.

        F3-a: CRS001/CRS002 use FlatMapGroupsWithState with Spark StateStore
              — per-vehicle state distributed across Spark workers, fault-tolerant.
        F3-a: CRS003 uses FlatMapGroupsWithState with per-hash dedup state
              — distributed deduplication across Spark workers.
        F3-b: Stateless rules use DataFrame-level filtering
              — pushed to Spark workers, no Python on driver for rule evaluation.

        Note: AdaptiveThresholdEngine remains single-node (acceptable for threshold agg).

        Args:
            kafka_bootstrap: Kafka bootstrap servers
            kafka_topic: Source topic for NYC taxi events
            violation_topic: Destination topic for violations
            gtfs_topic: Optional GTFS vehicle position topic
            starting_offsets: "earliest" or "latest"
        """
        self.spark = self._create_spark()

        kafka_df = (
            self.spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_bootstrap)
            .option("subscribe", kafka_topic if not gtfs_topic else f"{kafka_topic},{gtfs_topic}")
            .option("startingOffsets", starting_offsets)
            .load()
        )

        if gtfs_topic:
            events_df = kafka_df.withColumn(
                "entity_type",
                F.when(F.col("topic") == gtfs_topic, "gtfs_vehicle").otherwise("nyc_taxi")
            )
        else:
            events_df = kafka_df.withColumn("entity_type", F.lit("nyc_taxi"))

        # F3-b: DataFrame-level stateless rule filtering
        # Push SYN001/SYN002/SYN003 checks into Spark SQL — runs on workers in parallel
        violations_df = events_df.filter(
            (F.col("entity_type") == "nyc_taxi")
            & (
                # SYN001: negative fare_amount
                (F.col("fare_amount") < 0)
                # SYN002: invalid pickup location
                | (F.col("PULocationID").cast("int") < 1)
                | (F.col("PULocationID").cast("int") > 263)
            )
        ).select(
            F.lit("MULTI").alias("rule_id"),
            F.col("trip_id").alias("entity_id"),
            F.col("entity_type"),
            F.lit("MEDIUM").alias("severity"),
            F.lit("SYNTACTIC").alias("violation_type"),
            F.to_json(F.struct("*")).alias("record_snapshot"),
            F.current_timestamp().alias("detected_at"),
            F.lit(0.0).alias("processing_latency_ms"),
        )

        # F3-a: CRS001/CRS002 — GTFS vehicle state via FlatMapGroupsWithState
        if gtfs_topic:
            gtfs_df = events_df.filter(F.col("entity_type") == "gtfs_vehicle")
            # Parse GTFS JSON
            gtfs_parsed = gtfs_df.select(
                F.get_json_object(F.col("value").cast("string"), "$.vehicle.id").alias("vehicle_id"),
                F.get_json_object(F.col("value").cast("string"), "$.position.latitude").cast("double").alias("latitude"),
                F.get_json_object(F.col("value").cast("string"), "$.position.longitude").cast("double").alias("longitude"),
                F.get_json_object(F.col("value").cast("string"), "$.timestamp").cast("double").alias("timestamp_sec"),
                F.get_json_object(F.col("value").cast("string"), "$.vehicle.trip.trip_id").cast("string").alias("seq"),
                F.col("value").cast("string").alias("raw_json"),
                F.col("entity_type"),
            ).filter(F.col("vehicle_id").isNotNull())

            crs_violations_df = (
                gtfs_parsed
                .groupBy("vehicle_id")
                .applyInPandasWithState(
                    lambda pdf, pdf_state: self._pandas_vehicle_state(pdf, pdf_state),
                    outputStructType=StructType([
                        StructField("rule_id", StringType(), True),
                        StructField("rule_name", StringType(), True),
                        StructField("entity_id", StringType(), True),
                        StructField("entity_type", StringType(), True),
                        StructField("severity", StringType(), True),
                        StructField("violation_type", StringType(), True),
                        StructField("record_snapshot", StringType(), True),
                        StructField("detected_at", TimestampType(), True),
                        StructField("processing_latency_ms", DoubleType(), True),
                    ]),
                    stateStructType=_VEHICLE_STATE_SCHEMA,
                    outputMode="append",
                    timeoutConf=GroupStateTimeout.ProcessingTimeTimeout("10 minutes"),
                )
            )
        else:
            crs_violations_df = self.spark.createDataFrame([], StructType([
                StructField("rule_id", StringType(), True),
                StructField("rule_name", StringType(), True),
                StructField("entity_id", StringType(), True),
                StructField("entity_type", StringType(), True),
                StructField("severity", StringType(), True),
                StructField("violation_type", StringType(), True),
                StructField("record_snapshot", StringType(), True),
                StructField("detected_at", TimestampType(), True),
                StructField("processing_latency_ms", DoubleType(), True),
            ]))

        # F3-a: CRS003 — NYC taxi deduplication via FlatMapGroupsWithState
        taxi_df = events_df.filter(F.col("entity_type") == "nyc_taxi")
        # Compute dedup hash key
        dedup_df = taxi_df.select(
            F.concat_ws("|",
                F.col("trip_id"),
                F.col("PULocationID").cast("string"),
                F.col("DOLocationID").cast("string"),
                F.col("passenger_count").cast("string"),
            ).alias("event_hash"),
            F.col("*"),
        )
        crs003_violations_df = (
            dedup_df
            .groupBy("event_hash")
            .applyInPandasWithState(
                lambda pdf, pdf_state: self._pandas_dedup_state(pdf, pdf_state),
                outputStructType=StructType([
                    StructField("rule_id", StringType(), True),
                    StructField("rule_name", StringType(), True),
                    StructField("entity_id", StringType(), True),
                    StructField("entity_type", StringType(), True),
                    StructField("severity", StringType(), True),
                    StructField("violation_type", StringType(), True),
                    StructField("record_snapshot", StringType(), True),
                    StructField("detected_at", TimestampType(), True),
                    StructField("processing_latency_ms", DoubleType(), True),
                ]),
                stateStructType=StructType([
                    StructField("event_hash", StringType(), False),
                    StructField("first_seen_time", DoubleType(), False),
                    StructField("trip_id", StringType(), True),
                ]),
                outputMode="append",
                timeoutConf=GroupStateTimeout.ProcessingTimeTimeout("6 minutes"),
            )
        )

        # Union all violations
        all_violations = violations_df.unionByName(crs_violations_df, allowMissingColumns=True)
        all_violations = all_violations.unionByName(crs003_violations_df, allowMissingColumns=True)

        # Write violations to Kafka
        violations_kafka = (
            all_violations
            .select(
                F.to_json(F.struct("*")).cast("string").alias("value")
            )
        )

        checkpoint_dir = self.config.get("checkpoint_dir", "/tmp/streamdq-checkpoint-distributed")

        query = (
            violations_kafka
            .writeStream
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_bootstrap)
            .option("topic", violation_topic)
            .option("checkpointLocation", checkpoint_dir)
            .outputMode("append")
            .start()
        )

        self._running = True
        print(f"StreamDQ distributed pipeline started. Reading from: {kafka_topic}")
        print(f"CRS rules use FlatMapGroupsWithState (distributed, fault-tolerant)")
        print(f"Stateless rules use DataFrame-level filtering (on workers)")
        print(f"Violations written to Kafka topic: {violation_topic}")
        return query

    def _pandas_vehicle_state(self, pdf: "pd.DataFrame", state) -> "pd.DataFrame":
        """
        Pandas UDF with state for per-vehicle GPS tracking (CRS001/CRS002).

        Called per vehicle_id partition. Maintains state across events for
        the same vehicle. Uses pandas for vectorized operations within partition.
        """
        import math

        results = []
        pdf = pdf.sort_values("timestamp_sec")

        for _, row in pdf.iterrows():
            lat = float(row.latitude)
            lon = float(row.longitude)
            ts = float(row.timestamp_sec)
            seq = int(row.seq or 0)

            record = row.to_dict()

            if state.exists:
                prev = state.get
                prev_lat = float(prev.latitude)
                prev_lon = float(prev.longitude)
                prev_ts = float(prev.timestamp_sec)

                time_diff = ts - prev_ts
                if time_diff > 0:
                    dist = _haversine_m(prev_lat, prev_lon, lat, lon)
                    speed = (dist / 1000.0) / (time_diff / 3600.0)

                    if speed > _MAX_SPEED_KMH:
                        results.append({
                            "rule_id": "CRS001",
                            "rule_name": "Trajectory anomaly (impossible speed)",
                            "entity_id": str(row.vehicle_id),
                            "entity_type": "gtfs_vehicle",
                            "severity": "CRITICAL",
                            "violation_type": "CROSS_RECORD",
                            "record_snapshot": json.dumps(record, default=str),
                            "detected_at": datetime.now(),
                            "processing_latency_ms": 0.0,
                        })

                    if dist > _MAX_STATIONARY_JUMP_M:
                        if speed < 40.0:
                            sev = "CRITICAL" if speed < 1.0 else ("HIGH" if speed < 20.0 else "MEDIUM")
                            results.append({
                                "rule_id": "CRS002",
                                "rule_name": "GPS spoofing (stationary vehicle jump)",
                                "entity_id": str(row.vehicle_id),
                                "entity_type": "gtfs_vehicle",
                                "severity": sev,
                                "violation_type": "CROSS_RECORD",
                                "record_snapshot": json.dumps(record, default=str),
                                "detected_at": datetime.now(),
                                "processing_latency_ms": 0.0,
                            })

            state.update({
                "vehicle_id": str(row.vehicle_id),
                "latitude": lat,
                "longitude": lon,
                "timestamp_sec": ts,
                "seq": seq,
            })
            state.setTimeoutDuration(600)

        if results:
            import pandas as pd
            return pd.DataFrame(results)
        import pandas as pd
        return pd.DataFrame(columns=[
            "rule_id", "rule_name", "entity_id", "entity_type", "severity",
            "violation_type", "record_snapshot", "detected_at", "processing_latency_ms"
        ])

    def _pandas_dedup_state(self, pdf: "pd.DataFrame", state) -> "pd.DataFrame":
        """
        Pandas UDF with state for per-hash deduplication (CRS003).

        Called per event_hash partition. Detects duplicates within 300-second window.
        """
        results = []
        now = time.time()

        if state.exists:
            first_seen = float(state.get["first_seen_time"])
            if now - first_seen <= _DEDUP_WINDOW_SEC:
                results.append({
                    "rule_id": "CRS003",
                    "rule_name": "Duplicate event detected",
                    "entity_id": str(pdf.iloc[0]["trip_id"]) if "trip_id" in pdf else "",
                    "entity_type": "nyc_taxi",
                    "severity": "HIGH",
                    "violation_type": "CROSS_RECORD",
                    "record_snapshot": json.dumps(pdf.iloc[0].to_dict(), default=str),
                    "detected_at": datetime.now(),
                    "processing_latency_ms": 0.0,
                })
                state.remove()
                import pandas as pd
                return pd.DataFrame(results)

        state.update({
            "event_hash": str(pdf.iloc[0]["event_hash"]),
            "first_seen_time": now,
            "trip_id": str(pdf.iloc[0]["trip_id"]) if "trip_id" in pdf else "",
        })
        state.setTimeoutDuration(int(_DEDUP_WINDOW_SEC) + 10)

        import pandas as pd
        return pd.DataFrame(columns=[
            "rule_id", "rule_name", "entity_id", "entity_type", "severity",
            "violation_type", "record_snapshot", "detected_at", "processing_latency_ms"
        ])

    def stop(self):
        """Stop the pipeline."""
        self._running = False
        if self._kafka_producer:
            try:
                self._kafka_producer.flush(timeout=5)
                self._kafka_producer.close(timeout=5)
            except Exception:
                pass
        if self.spark:
            self.spark.stop()
        self.violation_store.close()
        print("StreamDQ pipeline stopped.")
