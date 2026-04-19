"""
Adaptive threshold engine.

Computes statistical thresholds from rolling window of data values.
No ML — pure statistics (P10/P90, mean/std).
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class FieldStats:
    """Statistics for a single field."""
    count: int
    min_val: float
    max_val: float
    mean: float
    std: float
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    # NG-36: Uncertainty quantification (bootstrap CI on percentiles)
    p10_ci_lower: float = 0.0
    p10_ci_upper: float = 0.0
    p90_ci_lower: float = 0.0
    p90_ci_upper: float = 0.0
    # NG-35: Shannon entropy of distribution
    entropy: float = 0.0


class AdaptiveThresholdEngine:
    """
    Compute adaptive thresholds from historical data distribution.

    For each field, maintains a rolling buffer and computes:
    - P10, P25, P50, P75, P90, P95, P99 percentiles
    - Mean, Std, Min, Max

    Thresholds are recalculated every N events (configurable).
    Human can override thresholds via config (useful for known limits).

    Usage:
        engine = AdaptiveThresholdEngine(window_size=10_000, recompute_every=1_000)

        # Feed values as they arrive
        for event in events:
            fare = event.get("fare_amount")
            if fare is not None:
                engine.update("fare_amount", float(fare))

        # Rules query stats
        stats = engine.get_stats("fare_amount")
        p90 = stats["p90"]  # Use for adaptive threshold
    """

    def __init__(
        self,
        window_size: int = 10_000,
        recompute_every: int = 1_000,
        min_sample_size: int = 100,
        max_fields: int = 50,
        idle_threshold: int = 50_000,
    ):
        self.window_size = window_size
        self.recompute_every = recompute_every
        self.min_sample_size = min_sample_size
        self.max_fields = max_fields
        self.idle_threshold = idle_threshold  # evict fields not updated in this many events

        # Rolling buffers: {field_name: [values]}
        self._buffers: dict[str, list[float]] = {}
        self._event_count = 0
        self._last_recompute = 0

        # NG-26: Track last update event count per field for LRU eviction
        self._last_update: dict[str, int] = {}

        # Human overrides: {field_name: {threshold_name: value}}
        self._overrides: dict[str, dict] = {}

        # Cached computed stats: {field_name: FieldStats}
        self._stats: dict[str, FieldStats] = {}

        # Entropy baseline for early drift detection (NG-35)
        # Per Xiong et al. (2026): entropy increases before distribution shifts
        self._entropy_baseline: dict[str, float] = {}
        self._entropy_change_threshold: float = 0.20  # 20% entropy increase triggers warning

    def update(self, field: str, value: float) -> dict | None:
        """
        Add a value to the rolling window for this field.

        Returns a dict with entropy warning if entropy increased significantly:
            {"entropy_warning": True, "field": "...", "old_entropy": 2.1, "new_entropy": 2.8}
        Returns None if no entropy warning.
        """
        # NG-26: Enforce max_fields limit via LRU eviction
        if field not in self._buffers and len(self._buffers) >= self.max_fields:
            # Evict least-recently-used field (lowest last-update count)
            evict_field = min(self._last_update, key=self._last_update.get)
            del self._buffers[evict_field]
            self._stats.pop(evict_field, None)
            self._entropy_baseline.pop(evict_field, None)
            self._last_update.pop(evict_field, None)

        if field not in self._buffers:
            self._buffers[field] = []
        self._buffers[field].append(value)
        self._last_update[field] = self._event_count
        if len(self._buffers[field]) > self.window_size:
            self._buffers[field].pop(0)
        self._event_count += 1

        # Evict idle fields (NG-26): fields not updated for idle_threshold events
        if len(self._buffers) > self.max_fields // 2:
            cutoff = self._event_count - self.idle_threshold
            idle = [f for f, c in list(self._last_update.items()) if c < cutoff]
            for f in idle:
                self._buffers.pop(f, None)
                self._stats.pop(f, None)
                self._entropy_baseline.pop(f, None)
                self._last_update.pop(f, None)

        # Entropy-based early warning (NG-35)
        entropy_warning = None
        current_entropy = self._compute_shannon_entropy(self._buffers[field])
        if current_entropy > 0 and field in self._entropy_baseline:
            baseline_entropy = self._entropy_baseline[field]
            if baseline_entropy > 0:
                change = abs(current_entropy - baseline_entropy) / baseline_entropy
                if change > self._entropy_change_threshold:
                    entropy_warning = {
                        "field": field,
                        "baseline_entropy": round(baseline_entropy, 4),
                        "current_entropy": round(current_entropy, 4),
                        "change_pct": round(change * 100, 1),
                    }
                    # Update baseline
                    self._entropy_baseline[field] = current_entropy
        elif field not in self._entropy_baseline:
            # Initialize baseline
            self._entropy_baseline[field] = current_entropy

        if self._event_count - self._last_recompute >= self.recompute_every:
            self._recompute()

        return entropy_warning

    @staticmethod
    def _percentile(sorted_vals: list[float], p: float) -> float:
        """
        Compute percentile using linear interpolation (R type 7).

        Fixes B8: int() truncation caused downward bias for small windows.
        For p=0.10 with n=100: idx=9.9 -> interpolate between indices 9 and 10.
        """
        n = len(sorted_vals)
        if n == 0:
            return 0.0
        idx = (n - 1) * p
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])

    def _recompute(self):
        """Recompute stats for all fields. Adds entropy (NG-35) and bootstrap CI (NG-36)."""
        for field, values in self._buffers.items():
            if len(values) < self.min_sample_size:
                continue

            sorted_vals = sorted(values)
            n = len(sorted_vals)

            # Bootstrap CI for P10 and P90 (NG-36)
            # Only compute if we have enough samples (n >= 30)
            if n >= 30:
                import random as _random
                _random.seed(42)
                n_bootstrap = 100
                p10_estimates = []
                p90_estimates = []
                for _ in range(n_bootstrap):
                    boot = _random.choices(values, k=n)
                    sorted_boot = sorted(boot)
                    p10_estimates.append(self._percentile(sorted_boot, 0.10))
                    p90_estimates.append(self._percentile(sorted_boot, 0.90))
                p10_estimates.sort()
                p90_estimates.sort()
                ci_lo = int(n_bootstrap * 0.025)
                ci_hi = int(n_bootstrap * 0.975)
                p10_ci = (p10_estimates[ci_lo], p10_estimates[ci_hi])
                p90_ci = (p90_estimates[ci_lo], p90_estimates[ci_hi])
            else:
                p10_ci = (0.0, 0.0)
                p90_ci = (0.0, 0.0)

            # Shannon entropy (NG-35)
            entropy = self._compute_shannon_entropy(values)
            # Update entropy baseline
            if field in self._entropy_baseline:
                self._entropy_baseline[field] = entropy
            else:
                self._entropy_baseline[field] = entropy

            self._stats[field] = FieldStats(
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
                p10_ci_lower=round(p10_ci[0], 4),
                p10_ci_upper=round(p10_ci[1], 4),
                p90_ci_lower=round(p90_ci[0], 4),
                p90_ci_upper=round(p90_ci[1], 4),
                entropy=round(entropy, 4),
            )
        self._last_recompute = self._event_count

    @staticmethod
    def _std(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5

    def _compute_shannon_entropy(self, values: list[float]) -> float:
        """
        Compute Shannon entropy of binned distribution.

        Per Xiong et al. (2026), entropy increases before distribution shifts —
        this can serve as an early warning signal for concept drift.
        Uses 10 equal-width bins. Returns 0.0 if insufficient data.
        """
        if len(values) < 10:
            return 0.0
        min_v, max_v = min(values), max(values)
        if min_v == max_v:
            return 0.0
        bins = 10
        bucket_size = (max_v - min_v) / bins
        counts = [0] * bins
        for v in values:
            idx = min(int((v - min_v) / bucket_size), bins - 1)
            counts[idx] += 1
        total = len(values)
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)
        return entropy

    def get_stats(self, field: str) -> dict:
        """
        Get computed stats for a field as a dict.

        Returns empty dict if not enough data yet.
        Includes override values with 'override_' prefix.
        """
        if field in self._overrides:
            override_data = {f"override_{k}": v for k, v in self._overrides[field].items()}
            base = self._stats.get(field)
            if base:
                base_dict = {
                    "count": base.count,
                    "min": base.min_val,
                    "max": base.max_val,
                    "mean": base.mean,
                    "std": base.std,
                    "p10": base.p10,
                    "p10_ci_lower": base.p10_ci_lower,
                    "p10_ci_upper": base.p10_ci_upper,
                    "p25": base.p25,
                    "p50": base.p50,
                    "p75": base.p75,
                    "p90": base.p90,
                    "p90_ci_lower": base.p90_ci_lower,
                    "p90_ci_upper": base.p90_ci_upper,
                    "p95": base.p95,
                    "p99": base.p99,
                    "entropy": base.entropy,
                    "entropy_baseline": self._entropy_baseline.get(field, 0.0),
                    "_source": "override",
                }
                base_dict.update(override_data)
                return base_dict
            return {**override_data, "_source": "override"}

        base = self._stats.get(field)
        if not base:
            return {}
        return {
            "count": base.count,
            "min": base.min_val,
            "max": base.max_val,
            "mean": base.mean,
            "std": base.std,
            "p10": base.p10,
            "p10_ci_lower": base.p10_ci_lower,
            "p10_ci_upper": base.p10_ci_upper,
            "p25": base.p25,
            "p50": base.p50,
            "p75": base.p75,
            "p90": base.p90,
            "p90_ci_lower": base.p90_ci_lower,
            "p90_ci_upper": base.p90_ci_upper,
            "p95": base.p95,
            "p99": base.p99,
            "entropy": base.entropy,
            "entropy_baseline": self._entropy_baseline.get(field, 0.0),
            "_source": "computed",
        }

    def get_all_stats(self) -> dict:
        """Get stats for all fields that have been updated."""
        result = {}
        for field in self._buffers:
            result[field] = self.get_stats(field)
        return result

    def override(self, field: str, thresholds: dict):
        """
        Set human override for specific field thresholds.

        Override values take precedence over computed stats.
        Useful for known business limits that shouldn't change.
        """
        self._overrides[field] = thresholds

    def clear_overrides(self):
        """Remove all human overrides."""
        self._overrides.clear()

    def reset_field(self, field: str) -> None:
        """
        Clear rolling buffer for a field, forcing fresh recompute.

        Called by drift detector when concept drift is detected (PSI >= 0.2).
        Clears the buffer so next values start building a new baseline.
        """
        if field in self._buffers:
            self._buffers[field] = []
        if field in self._stats:
            del self._stats[field]
        self._event_count = 0
        self._last_recompute = 0

    @property
    def event_count(self) -> int:
        return self._event_count
