"""
Concept Drift Detection for streaming data quality monitoring.

Uses PSI (Population Stability Index) to detect distributional shifts
in field statistics. When PSI exceeds a threshold, the adaptive thresholds
should be recomputed from scratch.

Classification: PSI-based drift detection is UNSUPERVISED (DDu).
It requires NO ground truth labels — only raw data distributions.
Per Komorniczak et al. (2026), drift detectors are classified as:
  - DD_s (Supervised): requires labels (DDM, ADWIN)
  - DD_u (Unsupervised): data features only, no labels (PSI, statistical tests)
  - DD_p (Partially unsupervised): labels only when drift detected

PSI is a DD_u detector — it fires purely on distributional changes.

References:
- Popovici et al., "Population Stability Index", Amazon ML blog (2019)
  https://aws.amazon.com/blogs/machine-learning/
- Komorniczak et al. (2026), "Structuring Data Stream Processing Frameworks",
  Pattern Recognition — classifies PSI as unsupervised (DDu) drift detection.
- Kim et al. (2019): PSI thresholds: <0.1 stable, 0.1-0.2 moderate, >=0.2 significant
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


# PSI bucket edges: 10 equal-width buckets across [0, 1]
_PSI_BUCKETS = [i * 0.1 for i in range(11)]


@dataclass
class PSIResult:
    """Result of a PSI drift check."""
    field: str
    psi: float
    drift_detected: bool
    threshold: float
    bucket_expected: list[float]
    bucket_actual: list[float]
    recommendation: str


@dataclass
class ConceptDriftState:
    """State for drift tracking per field."""
    baseline_p10: float
    baseline_p90: float
    baseline_mean: float
    baseline_count: int
    last_psi_check: int  # event count at last check
    n_psi_alerts: int = 0


class ConceptDriftDetector:
    """
    Detect concept drift using Population Stability Index (PSI).

    PSI < 0.1  -> No significant change
    PSI 0.1-0.2 -> Moderate shift — monitor closely
    PSI >= 0.2 -> Significant shift — recompute thresholds

    Usage:
        detector = ConceptDriftDetector(psi_threshold=0.2)
        detector.set_baseline(field="fare_amount", stats={"p10": 5.0, "p90": 40.0, "mean": 15.0})
        for batch_stats in rolling_stats:
            result = detector.check_drift("fare_amount", batch_stats, event_count)
            if result.drift_detected:
                threshold_engine.reset_field("fare_amount")
    """

    PSI_LOW = 0.1      # No significant change
    PSI_MEDIUM = 0.2  # Significant shift
    PSI_VERY_HIGH = 0.25
    PSI_VIRTUAL = 0.05  # Virtual drift: precedes real drift, early warning only

    def __init__(
        self,
        psi_threshold: float = 0.2,
        min_baseline_events: int = 100,
        check_interval: int = 500,
    ):
        self.psi_threshold = psi_threshold
        self.min_baseline_events = min_baseline_events
        self.check_interval = check_interval
        self._states: dict[str, ConceptDriftState] = {}
        self._baseline_buckets: dict[str, list[float]] = {}

    def set_baseline(
        self,
        field: str,
        stats: dict,
        event_count: int,
        bucket_edges: list[float] | None = None,
    ) -> None:
        """
        Set baseline statistics for a field.

        Args:
            field: Field name (e.g. "fare_amount")
            stats: Dict with p10, p90, mean, count
            event_count: Number of events used to compute baseline
        """
        self._states[field] = ConceptDriftState(
            baseline_p10=stats.get("p10", 0.0),
            baseline_p90=stats.get("p90", 0.0),
            baseline_mean=stats.get("mean", 0.0),
            baseline_count=event_count,
            last_psi_check=event_count,
        )
        if stats.get("p10") is not None and stats.get("p90") is not None:
            self._baseline_buckets[field] = self._build_buckets(
                stats["p10"], stats["p90"], bucket_edges
            )

    def _build_buckets(
        self,
        p10: float,
        p90: float,
        custom_edges: list[float] | None = None,
    ) -> list[float]:
        """Build bucket edges from P10/P90 range."""
        if custom_edges:
            return custom_edges
        # 10 equal-width buckets from P10 to P90
        return [p10 + (p90 - p10) * i / 10 for i in range(11)]

    @staticmethod
    def _bucket_values(values: list[float], bucket_edges: list[float]) -> list[float]:
        """Compute proportion of values in each bucket."""
        n = len(values)
        if n == 0:
            return [0.0] * (len(bucket_edges) - 1)
        buckets = [0.0] * (len(bucket_edges) - 1)
        for v in values:
            for i in range(len(bucket_edges) - 1):
                if bucket_edges[i] <= v < bucket_edges[i + 1]:
                    buckets[i] += 1
                    break
                elif i == len(bucket_edges) - 2 and v >= bucket_edges[i + 1]:
                    buckets[i] += 1
        return [b / n for b in buckets]

    @staticmethod
    def _compute_psi(
        expected: list[float],
        actual: list[float],
    ) -> float:
        """
        Compute Population Stability Index.

        PSI = sum over all buckets of:
            (Actual% - Expected%) * ln(Actual% / Expected%)

        Handles 0% buckets by adding a small epsilon (0.0001).
        """
        epsilon = 1e-4
        psi = 0.0
        for exp, act in zip(expected, actual):
            exp = max(exp, epsilon)
            act = max(act, epsilon)
            psi += (act - exp) * math.log(act / exp)
        return psi

    def check_drift(
        self,
        field: str,
        current_stats: dict,
        event_count: int,
        current_values: list[float] | None = None,
    ) -> Optional[PSIResult]:
        """
        Check for drift since the last baseline.

        Args:
            field: Field name
            current_stats: Current rolling stats (must have p10, p90)
            event_count: Current total event count
            current_values: Optional raw values for per-bucket PSI

        Returns:
            PSIResult if enough events since last check, None otherwise.
        """
        if field not in self._states:
            return None

        if event_count - self._states[field].last_psi_check < self.check_interval:
            return None

        state = self._states[field]
        state.last_psi_check = event_count

        if field in self._baseline_buckets and current_values is not None:
            bucket_edges = self._build_buckets(
                current_stats.get("p10", 0),
                current_stats.get("p90", 0),
            )
            expected = self._baseline_buckets[field]
            actual = self._bucket_values(current_values, bucket_edges)
            psi = self._compute_psi(expected, actual)
        else:
            p10 = current_stats.get("p10", 0)
            p90 = current_stats.get("p90", 0)
            if p10 == p90:
                return None
            # Fallback: compare P10/P90 directly
            p10_shift = abs(p10 - state.baseline_p10) / max(state.baseline_p10, 1e-9)
            p90_shift = abs(p90 - state.baseline_p90) / max(state.baseline_p90, 1e-9)
            # Rough PSI approximation
            psi = (p10_shift + p90_shift) * 0.5

        drift_detected = psi >= self.psi_threshold

        if drift_detected:
            state.n_psi_alerts += 1

        if psi >= self.PSI_VERY_HIGH:
            recommendation = "CRITICAL: Recompute thresholds from scratch. Large distribution shift detected."
        elif psi >= self.PSI_MEDIUM:
            recommendation = "HIGH: Recompute rolling stats window. Moderate drift detected."
        elif psi >= self.PSI_LOW:
            recommendation = "MEDIUM: Monitor closely. Minor drift detected."
        elif psi >= self.PSI_VIRTUAL:
            recommendation = "LOW: Virtual drift detected. No action needed yet — monitor more frequently."
        else:
            recommendation = "OK: No significant drift. Continue monitoring."

        return PSIResult(
            field=field,
            psi=round(psi, 4),
            drift_detected=drift_detected,
            threshold=self.psi_threshold,
            bucket_expected=self._baseline_buckets.get(field, []),
            bucket_actual=[],
            recommendation=recommendation,
        )
