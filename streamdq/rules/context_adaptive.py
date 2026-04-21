"""
Context-Aware Adaptive Threshold Engine.

Extends AdaptiveThresholdEngine with context-keyed statistics.
Instead of global P10/P90 thresholds, maintains separate thresholds
per context (e.g., morning vs evening, midtown vs airport).

References:
- ENHANCEMENT_ROADMAP.md: Phase 2, T7 (Context-Conditioned Thresholds)
- Target: +10-15 precision points via context-aware thresholds
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional

from streamdq.models.context_registry import ContextRegistry
from streamdq.rules.adaptive import FieldStats


class ContextAwareAdaptiveThresholdEngine:
    """
    Context-aware version of AdaptiveThresholdEngine.

    Key differences from base engine:
    1. Statistics stored per (field, context_key) instead of just field
    2. Accepts ContextRegistry for context extraction
    3. Hierarchical fallback: L0 (most specific) → L4 (global)

    Usage:
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")
        engine = ContextAwareAdaptiveThresholdEngine(
            registry=registry,
            window_size=10_000,
            recompute_every=1_000
        )

        # Feed events with context
        for event in events:
            fare = event.get("fare_amount")
            if fare is not None:
                engine.update("fare_amount", float(fare), event)

        # Query with fallback
        result = engine.get_threshold_with_fallback(
            field="fare_amount",
            percentile="p90",
            event=query_event
        )
        # Returns: {"value": 45.5, "level": 0, "context_key": "hour_10_midtown_weekday"}
    """

    def __init__(
        self,
        registry: ContextRegistry,
        window_size: int = 10_000,
        recompute_every: int = 1_000,
        min_sample_size: int = 100,
        max_contexts: int = 200,
    ):
        """
        Initialize context-aware adaptive threshold engine.

        Args:
            registry: ContextRegistry for extracting event context
            window_size: Max values per context buffer
            recompute_every: Recompute stats every N events
            min_sample_size: Minimum samples required for valid stats
            max_contexts: Maximum number of context buffers to maintain
        """
        self.registry = registry
        self.window_size = window_size
        self.recompute_every = recompute_every
        self.min_sample_size = min_sample_size
        self.max_contexts = max_contexts

        # Context-keyed buffers: {composite_key: [values]}
        # composite_key format: "field__context_key" (e.g., "fare_amount__hour_10_midtown_weekday")
        self._buffers: dict[str, list[float]] = {}

        # Cached stats: {composite_key: FieldStats}
        self._stats: dict[str, FieldStats] = {}

        # Event counter for recompute trigger
        self._event_count = 0
        self._last_recompute = 0

        # Track last update for LRU eviction
        self._last_update: dict[str, int] = {}

    def _make_composite_key(self, field: str, context_key: str) -> str:
        """Create composite key for field + context."""
        return f"{field}__{context_key}"

    def update(self, field: str, value: float, event: dict) -> None:
        """
        Add value to rolling window for this field in its context.

        Updates ALL hierarchy levels (0-4) to support fallback.
        This ensures statistics are available at all granularities.

        Args:
            field: Field name (e.g., "fare_amount")
            value: Field value
            event: Full event dict for context extraction
        """
        # Extract context from event
        context = self.registry.resolve(event)

        # Update all hierarchy levels (0-4) to support fallback
        for level in range(5):
            context_key = self.registry.match_key(context, level=level)
            composite_key = self._make_composite_key(field, context_key)

            # LRU eviction if max contexts exceeded
            if composite_key not in self._buffers and len(self._buffers) >= self.max_contexts:
                evict_key = min(self._last_update, key=self._last_update.get)
                del self._buffers[evict_key]
                self._stats.pop(evict_key, None)
                self._last_update.pop(evict_key, None)

            # Initialize buffer if needed
            if composite_key not in self._buffers:
                self._buffers[composite_key] = []

            # Add value to buffer
            self._buffers[composite_key].append(value)
            self._last_update[composite_key] = self._event_count

            # Maintain window size
            if len(self._buffers[composite_key]) > self.window_size:
                self._buffers[composite_key].pop(0)

        self._event_count += 1

        # Trigger recompute if needed
        if self._event_count - self._last_recompute >= self.recompute_every:
            self._recompute()

    @staticmethod
    def _percentile(sorted_vals: list[float], p: float) -> float:
        """Compute percentile using linear interpolation (R type 7)."""
        n = len(sorted_vals)
        if n == 0:
            return 0.0
        idx = (n - 1) * p
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])

    @staticmethod
    def _std(values: list[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5

    def _recompute(self):
        """Recompute stats for all context buffers."""
        for composite_key, values in self._buffers.items():
            if len(values) < self.min_sample_size:
                continue

            sorted_vals = sorted(values)
            n = len(sorted_vals)

            self._stats[composite_key] = FieldStats(
                count=n,
                min_val=sorted_vals[0],
                max_val=sorted_vals[-1],
                mean=sum(values) / n,
                std=self._std(values),
                p10=self._percentile(sorted_vals, 0.10),
                p25=self._percentile(sorted_vals, 0.25),
                p50=self._percentile(sorted_vals, 0.50),
                p75=self._percentile(sorted_vals, 0.75),
                p90=self._percentile(sorted_vals, 0.90),
                p95=self._percentile(sorted_vals, 0.95),
                p99=self._percentile(sorted_vals, 0.99),
            )

        self._last_recompute = self._event_count

    def get_stats_for_context(
        self,
        field: str,
        context: dict,
        level: int = 0
    ) -> Optional[dict]:
        """
        Get statistics for a specific field and context at given level.

        Args:
            field: Field name
            context: Context dict (from registry.resolve())
            level: Hierarchy level (0-4)

        Returns:
            Dict with stats or None if insufficient data
        """
        context_key = self.registry.match_key(context, level=level)
        composite_key = self._make_composite_key(field, context_key)

        stats = self._stats.get(composite_key)
        if not stats:
            return None

        return {
            "count": stats.count,
            "min": stats.min_val,
            "max": stats.max_val,
            "mean": stats.mean,
            "std": stats.std,
            "p10": stats.p10,
            "p25": stats.p25,
            "p50": stats.p50,
            "p75": stats.p75,
            "p90": stats.p90,
            "p95": stats.p95,
            "p99": stats.p99,
        }

    def get_threshold_with_fallback(
        self,
        field: str,
        percentile: str,
        event: dict,
        max_level: int = 4
    ) -> Optional[dict]:
        """
        Get threshold with hierarchical fallback.

        Tries levels in order: L0 (most specific) → L4 (global).
        Returns first level with sufficient samples.

        Args:
            field: Field name (e.g., "fare_amount")
            percentile: Percentile name (e.g., "p90")
            event: Event dict for context extraction
            max_level: Maximum fallback level (default 4 = global)

        Returns:
            Dict with value, level, context_key, or None if no valid stats
            Example: {"value": 45.5, "level": 0, "context_key": "hour_10_midtown_weekday"}
        """
        context = self.registry.resolve(event)

        for level in range(max_level + 1):
            context_key = self.registry.match_key(context, level=level)
            composite_key = self._make_composite_key(field, context_key)

            stats = self._stats.get(composite_key)
            if stats and stats.count >= self.min_sample_size:
                # Found valid stats at this level
                value = getattr(stats, percentile, None)
                if value is not None:
                    return {
                        "value": value,
                        "level": level,
                        "context_key": context_key,
                        "count": stats.count,
                    }

        # No valid stats at any level
        return None

    @property
    def event_count(self) -> int:
        """Total events processed."""
        return self._event_count
