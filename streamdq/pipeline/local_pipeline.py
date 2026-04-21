"""
Local Python pipeline — for quick testing without Spark/Kafka.

Processes events directly from a pandas DataFrame or iterable.
Use this for unit tests, CI, and quick validation.
"""
from __future__ import annotations
import time
from datetime import datetime
from typing import Iterable, Iterator, TYPE_CHECKING

from streamdq.rules.base import RuleContext, Violation, ExternalContext
from streamdq.rules.registry import RuleRegistry, build_default_registry
from streamdq.rules.adaptive import AdaptiveThresholdEngine
from streamdq.rules.context_adaptive import ContextAwareAdaptiveThresholdEngine
from streamdq.models.context_registry import ContextRegistry
from streamdq.storage.violation_store import ViolationStore
from streamdq.notification.alert_router import AlertRouter
from streamdq.rules.cross_record import (
    evaluate_trajectory_anomaly,
    evaluate_duplicate_event,
    reset_cross_record_state,
)
from streamdq.models.profiler import SchemaProfiler, SchemaProfile

if TYPE_CHECKING:
    from streamdq.models.contract import DataContract


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


def _build_external_context(dt: datetime) -> dict:
    """
    Build enriched external_context with time-of-day and date features.

    This makes the pipeline truly context-aware:
    - is_rush_hour: peak commute times (7-9 AM, 5-7 PM weekdays)
    - is_late_night: 12-5 AM
    - is_weekend: Saturday/Sunday
    - is_holiday: US federal holidays
    """
    hour = dt.hour
    day = dt.weekday()
    return {
        "processing_hour": hour,
        "processing_day": day,
        "is_rush_hour": (7 <= hour <= 9 or 17 <= hour <= 19) and day < 5,
        "is_late_night": 0 <= hour <= 5,
        "is_weekend": day >= 5,
        "is_holiday": _is_holiday(dt),
    }


class NoOpViolationStore:
    """Store that discards all violations. Used during evaluation to avoid SQLite overhead."""
    def store(self, violation): pass
    def store_batch(self, violations): pass
    def query(self, sql, params=(), limit=1000): return []
    def count(self, where="", params=()): return 0
    def get_summary(self): return {"total": 0, "by_rule": {}, "by_severity": {}, "by_type": {}}
    def close(self): pass


class LocalPipeline:
    """
    Local (non-distributed) pipeline for testing and quick validation.

    Processes events one-by-one from an iterable, applies all rules,
    stores violations, and collects metrics.

    Usage:
        pipeline = LocalPipeline(
            rule_registry=build_default_registry(),
            violation_store=ViolationStore("sqlite"),
        )
        results = pipeline.process_events(event_iterator)

    For high-throughput evaluation, pass violation_store=NoOpViolationStore()
    to avoid SQLite commit overhead.
    """

    def __init__(
        self,
        rule_registry: RuleRegistry = None,
        violation_store: ViolationStore = None,
        adaptive_threshold_window: int = 10_000,
        entity_type: str = "nyc_taxi",
        alert_router: AlertRouter | None = None,
        use_context_aware_thresholds: bool = True,
        context_config_path: str = "config/context_nyc_taxi.yaml",
        contract: "DataContract | None" = None,
    ):
        self.entity_type = entity_type
        self._contract = contract

        # Phase 2: Context-aware adaptive thresholds
        if use_context_aware_thresholds:
            context_registry = ContextRegistry.from_yaml(context_config_path)
            self.threshold_engine = ContextAwareAdaptiveThresholdEngine(
                registry=context_registry,
                window_size=adaptive_threshold_window
            )
            self._use_context_aware = True
        else:
            self.threshold_engine = AdaptiveThresholdEngine(window_size=adaptive_threshold_window)
            self._use_context_aware = False

        # Phase 3 T9: Build registry from contract if provided
        if contract is not None:
            self.registry = RuleRegistry.from_contract(contract, entity_type=entity_type)
        else:
            self.registry = rule_registry or build_default_registry(entity_type=entity_type)

        # Use in-memory SQLite for testing, real path for production
        import tempfile, os
        if violation_store:
            self.store = violation_store
        else:
            tmp_dir = tempfile.gettempdir()
            db_path = os.path.join(tmp_dir, "streamdq_violations.db")
            self.store = ViolationStore("sqlite", db_path)
        # P1-1: AlertRouter wired into pipeline for real-time alerting
        self.alert_router = alert_router
        self._metrics = {
            "total_events": 0,
            "total_violations": 0,
            "by_rule": {},
            "by_type": {},
            "by_severity": {},
            # NG-2a: Separate processing vs end-to-end latency tracking
            # - processing_latencies: wall-clock time for rule evaluation only
            # - e2e_latencies: Kafka produce timestamp → violation stored
            "processing_latencies": [],
            "e2e_latencies": [],
        }
        # NG-30: DQ lifecycle stage tracking (profiling, measurement, analysis, monitoring)
        self.lifecycle_stage: str = "idle"
        self.profile: SchemaProfile | None = None

    def profile_dataset(self, records: list[dict]) -> SchemaProfile:
        """
        NG-30: Run profiling stage before monitoring begins.
        Per Serra et al. (2022): DQ process has 7 stages. This implements profiling.
        Run this once before process_events() to understand the dataset structure.
        """
        self.lifecycle_stage = "profiling"
        from streamdq.models.profiler import SchemaProfiler
        profiler = SchemaProfiler()
        self.profile = profiler.profile(records)
        self.lifecycle_stage = "idle"
        return self.profile

    @property
    def rule_registry(self) -> RuleRegistry:
        """Alias for self.registry (for backward compatibility and test convenience)."""
        return self.registry

    def process_event(self, event: dict) -> list[Violation]:
        """Process a single event and return violations."""
        start = time.perf_counter()
        event_time = datetime.now()
        violations = []

        # Update adaptive thresholds with entity-specific fields
        adaptive_fields = ["fare_amount", "trip_distance"] if self.entity_type == "nyc_taxi" else ["speed"]
        for field in adaptive_fields:
            value = event.get(field)
            if value is not None:
                try:
                    if self._use_context_aware:
                        # Phase 2: Context-aware update requires event for context extraction
                        self.threshold_engine.update(field, float(value), event)
                    else:
                        self.threshold_engine.update(field, float(value))
                except (ValueError, TypeError):
                    pass

        # Get historical stats
        historical_stats = self.threshold_engine.get_all_stats()

        # Build context with enriched external_context (4D model per Dey 2001 / Serra 2022)
        ctx = RuleContext(
            event=event,
            event_time=event_time,
            historical_stats=historical_stats,
            external_context=ExternalContext.from_event(event, event_time),
            start_time=start,
        )

        # Stateless rule evaluation
        for v in self.registry.evaluate_all(ctx):
            violations.append(v)

        # Stateful / cross-record evaluation
        for v in self.registry.evaluate_stateful(event, event_time, start):
            violations.append(v)

        # NG-2a: Compute E2E latency if Kafka arrival timestamp is available.
        # e2e_latency = time from Kafka produced message → violation stored.
        # When kafka_arrival_ms is absent (e.g., direct event injection), E2E
        # equals processing latency.
        kafka_arrival_ms = event.get("kafka_arrival_ms")
        if kafka_arrival_ms is not None:
            e2e_latency_ms = (time.perf_counter() * 1000) - float(kafka_arrival_ms)
        else:
            e2e_latency_ms = (time.perf_counter() - start) * 1000

        # Store violations
        if violations:
            self.store.store_batch(violations)
            for v in violations:
                self._record_violation(v)
            # P1-1: Route violations to alert channels (NG-16: deduplication built-in)
            if self.alert_router:
                self.alert_router.route_batch(violations)

        # NG-30: Track lifecycle stage transitions
        if self.lifecycle_stage == "idle":
            self.lifecycle_stage = "monitoring"

        # Record metrics — NG-2a: distinct processing vs E2E latencies
        processing_ms = (time.perf_counter() - start) * 1000
        self._metrics["total_events"] += 1
        self._metrics["processing_latencies"].append(processing_ms)
        self._metrics["e2e_latencies"].append(e2e_latency_ms)

        return violations

    def process_events(
        self, events: Iterable[dict], max_events: int = None
    ) -> dict:
        """
        Process multiple events and return metrics.

        Args:
            events: Iterable of event dicts
            max_events: Optional cap on number of events to process

        Returns:
            Metrics dict with total_events, total_violations, by_rule, etc.
        """
        count = 0
        for event in events:
            self.process_event(event)
            count += 1
            if max_events and count >= max_events:
                break
        return self.get_metrics()

    def _record_violation(self, v: Violation):
        """Record a violation in metrics."""
        self._metrics["total_violations"] += 1
        self._metrics["by_rule"][v.rule_id] = (
            self._metrics["by_rule"].get(v.rule_id, 0) + 1
        )
        self._metrics["by_type"][v.violation_type] = (
            self._metrics["by_type"].get(v.violation_type, 0) + 1
        )
        self._metrics["by_severity"][v.severity] = (
            self._metrics["by_severity"].get(v.severity, 0) + 1
        )

    def get_metrics(self) -> dict:
        """Get current metrics."""
        proc_lat = sorted(self._metrics["processing_latencies"])
        e2e_lat = sorted(self._metrics["e2e_latencies"])
        n = len(proc_lat)
        m = len(e2e_lat)
        return {
            "total_events": self._metrics["total_events"],
            "total_violations": self._metrics["total_violations"],
            "violation_rate": (
                self._metrics["total_violations"] / max(self._metrics["total_events"], 1)
            ),
            "by_rule": dict(self._metrics["by_rule"]),
            "by_type": dict(self._metrics["by_type"]),
            "by_severity": dict(self._metrics["by_severity"]),
            # NG-2a: distinct processing vs E2E latency
            "processing_latency_p50_ms": proc_lat[n // 2] if n > 0 else 0,
            "processing_latency_p99_ms": proc_lat[int(n * 0.99)] if n > 0 else 0,
            "e2e_latency_p50_ms": e2e_lat[m // 2] if m > 0 else 0,
            "e2e_latency_p99_ms": e2e_lat[int(m * 0.99)] if m > 0 else 0,
            "violation_summary": self.store.get_summary(),
        }

    def reset(self):
        """Reset all state (for testing)."""
        reset_cross_record_state()
        self.threshold_engine = AdaptiveThresholdEngine(
            window_size=10_000
        )
        self._metrics = {
            "total_events": 0,
            "total_violations": 0,
            "by_rule": {},
            "by_type": {},
            "by_severity": {},
            "processing_latencies": [],
            "e2e_latencies": [],
        }
