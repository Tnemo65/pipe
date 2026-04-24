"""
Complementarity evaluation: Conditional Coverage (CC) and Complementarity Index (CI).

Measures: P(StreamDQ catches | Existing missed)
Test: McNemar's chi-square with bootstrap CI (n=1000, per Rule EV3)
Threshold: CC >= 0.30 for "complementary" claim

Usage:
    result = run_complementarity_evaluation(
        ground_truth=[{"entity_id": "trip_001", "anomaly_type": "NEGATIVE_FARE"}, ...],
        streamdq_violations={"trip_001", "trip_042"},
        existing_violations={"trip_001", "trip_103"},
        existing_name="Great Expectations",
    )
    print(result.summary())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


def _chi2_cdf(x: float, df: int) -> float:
    """Chi-square CDF. Fallback if scipy unavailable."""
    try:
        from scipy.stats import chi2
        return chi2.cdf(x, df)
    except ImportError:
        import math
        if df == 1 and x >= 0:
            k = math.sqrt(2 * x)
            p = 0.5 * (1 + math.erf(k / math.sqrt(2)))
            return p
        raise


@dataclass
class ComplementarityResult:
    """
    Result of complementarity evaluation between StreamDQ and one existing method.

    2x2 contingency table:
                        Existing Missed   Existing Caught
    StreamDQ Caught          b                 a
    StreamDQ Missed          d                 c

    Key metrics:
    - CC (Conditional Coverage): P(StreamDQ catches | Existing missed) = b / (b + d)
    - CI (Complementarity Index): fraction of total anomalies uniquely caught = b / N
    """
    method_a: str
    """Name of method A (typically 'StreamDQ')."""

    method_b: str
    """Name of method B (e.g., 'Great Expectations')."""

    a: int = 0
    """
    Both methods caught the anomaly.
    True positives shared between A and B.
    """

    b: int = 0
    """
    StreamDQ caught it; existing missed it.
    THIS IS THE COMPLEMENTARITY CELL.
    """

    c: int = 0
    """
    Existing caught it; StreamDQ missed it.
    Indicates existing is strictly better for these cases.
    """

    d: int = 0
    """
    Both methods missed it.
    These anomalies are undetectable by either method.
    """

    n_bootstrap: int = 1000
    """Number of bootstrap iterations for CI."""

    cc_ci_lower: float = 0.0
    """95% CI lower bound for Conditional Coverage (computed after bootstrap)."""

    cc_ci_upper: float = 0.0
    """95% CI upper bound for Conditional Coverage (computed after bootstrap)."""

    cc_mean: float = 0.0
    """Bootstrap mean of Conditional Coverage."""

    _detection_matrix: list[tuple[int, int]] = field(default_factory=list, repr=False)
    """Per-anomaly (S_catches, E_catches) pairs. Set internally."""

    @property
    def n(self) -> int:
        """Total ground truth anomalies."""
        return self.a + self.b + self.c + self.d

    @property
    def conditional_coverage(self) -> float:
        """
        CC = P(StreamDQ catches | Existing missed) = b / (b + d).

        Range: [0, 1]
        CC = 0.0: StreamDQ never catches what existing misses
        CC = 0.5: Equally likely to be caught by either method alone
        CC = 1.0: StreamDQ catches everything existing misses (complete complementarity)
        """
        denom = self.b + self.d
        if denom == 0:
            return 0.0
        return self.b / denom

    @property
    def complementarity_index(self) -> float:
        """
        CI = b / N: fraction of all anomalies uniquely caught by StreamDQ.

        Range: [0, 1]
        CI = 0.17 means StreamDQ adds 17pp of recall beyond existing methods.
        """
        n_total = self.n
        if n_total == 0:
            return 0.0
        return self.b / n_total

    @property
    def streamdq_recall(self) -> float:
        """Recall of StreamDQ alone: (a + b) / N."""
        n_total = self.n
        if n_total == 0:
            return 0.0
        return (self.a + self.b) / n_total

    @property
    def existing_recall(self) -> float:
        """Recall of existing method alone: (a + c) / N."""
        n_total = self.n
        if n_total == 0:
            return 0.0
        return (self.a + self.c) / n_total

    @property
    def combined_recall(self) -> float:
        """
        Combined recall (either method catches): (a + b + c) / N.

        This is the key claim: combined > max(individual).
        """
        n_total = self.n
        if n_total == 0:
            return 0.0
        return (self.a + self.b + self.c) / n_total

    @property
    def recall_gain(self) -> float:
        """
        Recall gain from adding StreamDQ to the toolchain.
        combined_recall - max(streamdq_recall, existing_recall)
        """
        return self.combined_recall - max(self.streamdq_recall, self.existing_recall)

    def mcnemar_test(
        self, continuity_correction: bool = True
    ) -> dict[str, float | int | str]:
        """
        McNemar's test for paired nominal data (discordant pairs only).

        H0: P(A catches | B missed) = P(A misses | B caught)
            (conditional coverage is equal — no complementarity)
        H1: P(A catches | B missed) > P(A misses | B caught)
            (StreamDQ has higher conditional coverage — complementary)

        Returns dict with:
        - statistic: chi-square value
        - df: degrees of freedom (always 1)
        - p_value: one-sided p-value
        - discordant_pairs: total discordant (b + c)
        - test: test name
        """
        b_val, c_val = self.b, self.c
        n_discordant = b_val + c_val

        if n_discordant == 0:
            return {
                "statistic": 0.0,
                "df": 1,
                "p_value": 1.0,
                "discordant_pairs": 0,
                "test": "mid-P McNemar" if continuity_correction else "McNemar",
            }

        if continuity_correction:
            stat = (abs(b_val - c_val) - 1) ** 2 / n_discordant
        else:
            stat = (b_val - c_val) ** 2 / n_discordant

        p_value = 1.0 - _chi2_cdf(stat, df=1)

        return {
            "statistic": stat,
            "df": 1,
            "p_value": p_value,
            "discordant_pairs": n_discordant,
            "test": "mid-P McNemar" if continuity_correction else "McNemar",
        }

    def is_complementary(
        self,
        cc_threshold: float = 0.30,
        alpha: float = 0.05,
        require_stat_sig: bool = True,
    ) -> bool:
        """
        Determine if the combination is complementary.

        Requires BOTH:
        1. CC >= cc_threshold (practical significance: StreamDQ catches enough of what existing misses)
        2. McNemar p < alpha (statistical significance: not due to chance)
           OR require_stat_sig=False (only practical significance)

        Also requires validity condition: b + c >= 30 (per Rule EV3).
        """
        test = self.mcnemar_test()
        cc = self.conditional_coverage
        n_discordant = test["discordant_pairs"]

        if n_discordant < 30:
            return False

        practical = cc >= cc_threshold
        statistical = test["p_value"] < alpha

        if require_stat_sig:
            return practical and statistical
        else:
            return practical

    def bootstrap_cc_ci(
        self,
        detection_matrix: Optional[list[tuple[int, int]]] = None,
        n_bootstrap: int = 1000,
        ci: float = 0.95,
        seed: int = 42,
    ) -> tuple[float, float, float]:
        """
        Bootstrap confidence interval for Conditional Coverage.

        Per Rule EV3: minimum 1,000 bootstrap iterations, 95% CI.

        Args:
            detection_matrix: list of (S_catches, E_catches) per ground-truth anomaly.
                             Each entry is (1,1), (1,0), (0,1), or (0,0).
                             If None, uses internal _detection_matrix.
            n_bootstrap: bootstrap iterations (minimum 1,000 per EV3).
            ci: confidence level (default 0.95 for 95% CI).
            seed: random seed for reproducibility.

        Returns:
            (mean_cc, ci_lower, ci_upper)
        """
        if detection_matrix is None:
            detection_matrix = self._detection_matrix

        if len(detection_matrix) == 0:
            self.cc_mean = 0.0
            self.cc_ci_lower = 0.0
            self.cc_ci_upper = 0.0
            return 0.0, 0.0, 0.0

        rng = np.random.default_rng(seed)
        cc_estimates: list[float] = []

        for _ in range(n_bootstrap):
            indices = rng.integers(
                0, len(detection_matrix), size=len(detection_matrix)
            )
            b_boot = sum(
                1
                for i in indices
                if detection_matrix[i] == (1, 0)  # StreamDQ catches, existing misses
            )
            d_boot = sum(
                1
                for i in indices
                if detection_matrix[i] == (0, 0)  # both miss
            )
            denom = b_boot + d_boot
            cc_estimates.append(b_boot / denom if denom > 0 else 0.0)

        alpha = (1 - ci) / 2
        self.cc_mean = float(np.mean(cc_estimates))
        self.cc_ci_lower = float(np.percentile(cc_estimates, alpha * 100))
        self.cc_ci_upper = float(np.percentile(cc_estimates, (1 - alpha) * 100))

        return self.cc_mean, self.cc_ci_lower, self.cc_ci_upper

    def summary(
        self,
        cc_threshold: float = 0.30,
        alpha: float = 0.05,
        include_ci: bool = True,
    ) -> str:
        """
        Human-readable summary of complementarity evaluation.

        Args:
            cc_threshold: threshold for practical significance.
            alpha: significance level for statistical test.
            include_ci: include bootstrap CI in output.

        Returns:
            Formatted string summary.
        """
        test = self.mcnemar_test()
        cc = self.conditional_coverage
        ci = self.complementarity_index
        n_disc = test["discordant_pairs"]

        status = (
            "COMPLEMENTARY"
            if self.is_complementary(cc_threshold, alpha)
            else "NOT COMPLEMENTARY"
        )

        lines = [
            f"Complementarity: {self.method_a} vs. {self.method_b}",
            f"  2x2 Table (a={self.a}, b={self.b}, c={self.c}, d={self.d}, N={self.n})",
            f"  Conditional Coverage (CC): {cc:.3f} (threshold: {cc_threshold:.2f})",
            f"  Complementarity Index (CI): {ci:.3f}",
            f"  McNemar's chi2(1)={test['statistic']:.3f}, p={test['p_value']:.4f}",
            f"  Discordant pairs: {n_disc} {'(valid)' if n_disc >= 30 else '(insufficient)'}",
            f"  StreamDQ recall: {self.streamdq_recall:.3f}",
            f"  {self.method_b} recall: {self.existing_recall:.3f}",
            f"  Combined recall: {self.combined_recall:.3f}",
            f"  Recall gain: +{self.recall_gain:.3f}",
        ]

        if include_ci and self.cc_ci_lower > 0 or self.cc_ci_upper > 0:
            lines.append(
                f"  CC 95% CI (bootstrap, n={self.n_bootstrap}): "
                f"[{self.cc_ci_lower:.3f}, {self.cc_ci_upper:.3f}]"
            )

        lines.append(f"  Status: {status}")
        return "\n".join(lines)

    def to_dict(self, cc_threshold: float = 0.30) -> dict:
        """Serialize to dict for JSON export."""
        test = self.mcnemar_test()
        return {
            "method_a": self.method_a,
            "method_b": self.method_b,
            "table": {"a": self.a, "b": self.b, "c": self.c, "d": self.d, "N": self.n},
            "conditional_coverage": round(self.conditional_coverage, 4),
            "complementarity_index": round(self.complementarity_index, 4),
            "cc_ci_lower": round(self.cc_ci_lower, 4),
            "cc_ci_upper": round(self.cc_ci_upper, 4),
            "mcnemar": {
                "statistic": round(test["statistic"], 4),
                "df": test["df"],
                "p_value": round(test["p_value"], 4),
                "discordant_pairs": test["discordant_pairs"],
            },
            "recalls": {
                "streamdq": round(self.streamdq_recall, 4),
                self.method_b: round(self.existing_recall, 4),
                "combined": round(self.combined_recall, 4),
                "gain": round(self.recall_gain, 4),
            },
            "is_complementary": self.is_complementary(cc_threshold),
            "cc_threshold": cc_threshold,
        }


def run_complementarity_evaluation(
    ground_truth: list[dict],
    streamdq_violations: set[str],
    existing_violations: set[str],
    streamdq_name: str = "StreamDQ",
    existing_name: str = "Existing",
    cc_threshold: float = 0.30,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> ComplementarityResult:
    """
    Run complementarity evaluation between StreamDQ and an existing method.

    This function is the main entry point. It:
    1. Classifies each ground-truth anomaly into one of four cells (a/b/c/d)
    2. Computes CC, CI, and recall metrics
    3. Runs McNemar's test
    4. Computes bootstrap CI for CC

    Args:
        ground_truth: List of ground-truth anomaly records.
                     Each must have an 'entity_id' field matching the violation records.
        streamdq_violations: Set of entity_ids caught by StreamDQ.
        existing_violations: Set of entity_ids caught by existing method.
        streamdq_name: Display name for StreamDQ.
        existing_name: Display name for existing method.
        cc_threshold: CC threshold for "complementary" claim (default 0.30).
        n_bootstrap: Bootstrap iterations for CI (minimum 1,000 per EV3).
        seed: Random seed for bootstrap reproducibility.

    Returns:
        ComplementarityResult with all metrics and the decision.

    Example:
        >>> ground_truth = [{"entity_id": "trip_001"}, {"entity_id": "trip_002"}]
        >>> sdq_violations = {"trip_001"}
        >>> existing_violations = {"trip_002"}
        >>> result = run_complementarity_evaluation(ground_truth, sdq_violations, existing_violations)
        >>> print(result.summary())
    """
    gt_ids = {record["entity_id"] for record in ground_truth}

    a = len(streamdq_violations & existing_violations)
    b = len(streamdq_violations - existing_violations)
    c = len(existing_violations - streamdq_violations)
    d = len(gt_ids - streamdq_violations - existing_violations)

    result = ComplementarityResult(
        method_a=streamdq_name,
        method_b=existing_name,
        a=a,
        b=b,
        c=c,
        d=d,
        n_bootstrap=n_bootstrap,
    )

    detection_matrix: list[tuple[int, int]] = []
    for entity_id in gt_ids:
        s = 1 if entity_id in streamdq_violations else 0
        e = 1 if entity_id in existing_violations else 0
        detection_matrix.append((s, e))

    result._detection_matrix = detection_matrix
    result.bootstrap_cc_ci(detection_matrix, n_bootstrap, seed=seed)

    return result


def run_multi_framework_evaluation(
    ground_truth: list[dict],
    streamdq_violations: set[str],
    framework_violations: dict[str, set[str]],
    streamdq_name: str = "StreamDQ",
    cc_threshold: float = 0.30,
    n_bootstrap: int = 1000,
) -> dict[str, ComplementarityResult]:
    """
    Run complementarity evaluation against multiple existing frameworks.

    Convenience wrapper around run_complementarity_evaluation.

    Args:
        ground_truth: List of ground-truth anomaly records with 'entity_id'.
        streamdq_violations: Set of entity_ids caught by StreamDQ.
        framework_violations: Dict of {framework_name: set of entity_ids}.
        streamdq_name: Display name for StreamDQ.
        cc_threshold: CC threshold for "complementary" claim.
        n_bootstrap: Bootstrap iterations per framework.

    Returns:
        Dict of {framework_name: ComplementarityResult}.
    """
    results: dict[str, ComplementarityResult] = {}
    for framework_name, violations in framework_violations.items():
        results[framework_name] = run_complementarity_evaluation(
            ground_truth=ground_truth,
            streamdq_violations=streamdq_violations,
            existing_violations=violations,
            streamdq_name=streamdq_name,
            existing_name=framework_name,
            cc_threshold=cc_threshold,
            n_bootstrap=n_bootstrap,
        )
    return results
