"""
Evaluation metrics — precision, recall, latency, rule coverage.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class AnomalyRecord:
    """A ground-truth anomaly injected into test data."""
    anomaly_type: str
    entity_index: int
    injected_at: int  # event index in stream


@dataclass
class DetectedViolation:
    """A violation detected by the pipeline."""
    rule_id: str
    anomaly_type: Optional[str]  # Which anomaly type this corresponds to
    entity_index: int
    latency_ms: float


class EvaluationMetrics:
    """
    Compute evaluation metrics for StreamDQ.

    Usage:
        eval = EvaluationMetrics()
        eval.add_injected_anomaly("fare_negative", index=42)
        eval.add_detected_violation("SYN001", entity_index=42, latency_ms=50)

        report = eval.full_report()
        print(report["precision"])
        print(report["recall_overall"])
    """

    def __init__(self, label_delay_events: int = 0):
        """
        Args:
            label_delay_events: NG-33 — events with index < label_delay_events are
                treated as "unlabeled". Violations on these entities don't count as TP.
        """
        self.injected_anomalies: list[AnomalyRecord] = []
        self.detected_violations: list[DetectedViolation] = []
        self.latencies_ms: list[float] = []
        self.label_delay_events = label_delay_events

    def add_injected_anomaly(self, anomaly_type: str, entity_index: int):
        self.injected_anomalies.append(
            AnomalyRecord(anomaly_type=anomaly_type, entity_index=entity_index, injected_at=entity_index)
        )

    def add_detected_violation(
        self,
        rule_id: str,
        entity_index: int,
        latency_ms: float,
        anomaly_type: str = None,
    ):
        self.detected_violations.append(
            DetectedViolation(
                rule_id=rule_id,
                entity_index=entity_index,
                latency_ms=latency_ms,
                anomaly_type=anomaly_type,
            )
        )
        self.latencies_ms.append(latency_ms)

    def detection_rate(self) -> dict:
        """
        For each anomaly type: detected / total injected.

        Detection = at least one violation emitted for that entity_index.
        """
        label_available_at = self.label_delay_events  # NG-33: events before this index have no GT labels
        detected_types = {}
        injected_by_type: dict = {}
        injected_indices_by_type: dict = {}

        # Index injected anomalies
        for a in self.injected_anomalies:
            atype = a.anomaly_type
            if atype not in injected_by_type:
                injected_by_type[atype] = 0
                injected_indices_by_type[atype] = set()
            injected_by_type[atype] += 1
            injected_indices_by_type[atype].add(a.entity_index)

        # Count detected per type
        detected_indices_by_type: dict = {}
        for v in self.detected_violations:
            atype = v.anomaly_type or "unknown"
            if atype not in detected_indices_by_type:
                detected_indices_by_type[atype] = set()
            detected_indices_by_type[atype].add(v.entity_index)

        # NG-33: Apply label delay — violations detected BEFORE labels are available
        # are excluded from the detected set (they're "pending", not yet attributable)
        for atype in injected_by_type:
            injected_set = injected_indices_by_type.get(atype, set())
            detected_set = detected_indices_by_type.get(atype, set())
            # Only count violations detected after labels become available
            confirmed_detected = {
                idx for idx in (injected_set & detected_set)
                if idx >= label_available_at
            }
            total = len(injected_set)
            detected_types[atype] = {
                "detected": len(confirmed_detected),
                "total": total,
                "detection_rate": len(confirmed_detected) / max(total, 1),
                # NG-33: Track unconfirmed (pending) detections in delay window
                "pending_detections": len(injected_set & detected_set) - len(confirmed_detected),
                "label_delay_events": label_available_at,
            }

        return detected_types

    def false_positive_rate(self) -> float:
        """
        False Positive Rate = FP / (FP + TN).

        FP = detected violations on clean (non-anomalous) entities.
        TN = clean entities that had no violations detected.

        Note: TN is computed over the range [0, max_entity_index] where
        max_entity_index = max(max_injected, max_detected). This is a
        simplification — in practice the evaluation run processes a known
        number of events N, so N should be passed to get accurate TN.
        """
        injected_indices = {a.entity_index for a in self.injected_anomalies}
        detected_indices = {v.entity_index for v in self.detected_violations}
        max_index = max(
            max(injected_indices, default=-1),
            max(detected_indices, default=-1),
        )

        # TP: violations on anomalous entities
        tp = sum(1 for v in self.detected_violations if v.entity_index in injected_indices)
        fp = sum(1 for v in self.detected_violations if v.entity_index not in injected_indices)

        # TN: clean entities that had no violations
        # = entities in range that are NOT injected AND NOT detected
        clean_and_passed = sum(
            1 for idx in range(max_index + 1)
            if idx not in injected_indices and idx not in detected_indices
        )
        # Also count entities that are clean but had violations — these are FPs already counted above

        return fp / max(fp + clean_and_passed, 1)

    def precision(self) -> float:
        """
        Precision = TP / (TP + FP).

        TP = detected violations where entity_index was in injected set.
        FP = detected violations where entity_index was NOT in injected set.
        """
        injected_indices = {a.entity_index for a in self.injected_anomalies}
        tp = sum(1 for v in self.detected_violations if v.entity_index in injected_indices)
        fp = sum(1 for v in self.detected_violations if v.entity_index not in injected_indices)
        return tp / max(tp + fp, 1)

    def recall_overall(self) -> float:
        """Overall recall across all anomaly types."""
        detected = self.detection_rate()
        total_detected = sum(d["detected"] for d in detected.values())
        total_injected = sum(d["total"] for d in detected.values())
        return total_detected / max(total_injected, 1)

    def latency_percentiles(self) -> dict:
        """P50, P90, P95, P99 latency."""
        if not self.latencies_ms:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
        sorted_lat = sorted(self.latencies_ms)
        n = len(sorted_lat)
        return {
            "p50_ms": sorted_lat[int(n * 0.50)],
            "p90_ms": sorted_lat[int(n * 0.90)],
            "p95_ms": sorted_lat[int(n * 0.95)],
            "p99_ms": sorted_lat[int(n * 0.99)],
        }

    def rule_coverage(self) -> dict:
        """Which rules fired, and how often?"""
        from collections import Counter
        rule_counts = Counter(v.rule_id for v in self.detected_violations)
        total = len(self.detected_violations)
        noise_rules = [
            rule_id for rule_id, count in rule_counts.items()
            if total > 0 and count / total > 0.5
        ]
        return {
            "by_rule": dict(rule_counts),
            "total_violations": total,
            "rules_with_violations": len(rule_counts),
            "noise_rules": noise_rules,
        }

    def bootstrap_ci(
        self,
        n_resamples: int = 1000,
        confidence: float = 0.95,
        seed: int = 42,
    ) -> dict:
        """
        Compute bootstrap confidence interval for precision and recall.

        Methodology: resample ENTITY INDICES (not violations), then filter
        violations to the resampled indices. This avoids biasing precision
        estimates when some entities generate multiple violations.

        Args:
            n_resamples: Number of bootstrap resamples (min 1000 per EV3).
            confidence: Confidence level (default 0.95 = 95% CI).
            seed: Random seed for reproducibility.

        Returns:
            dict with precision_ci and recall_ci, each containing
            mean, lower_bound, upper_bound, n_resamples.
        """
        import random as _random

        _random.seed(seed)

        detected_list = list(self.detected_violations)
        injected_list = list(self.injected_anomalies)

        if not detected_list or not injected_list:
            return {
                "precision_ci": {"mean": 0.0, "lower_bound": 0.0, "upper_bound": 0.0, "n_resamples": n_resamples},
                "recall_ci": {"mean": 0.0, "lower_bound": 0.0, "upper_bound": 0.0, "n_resamples": n_resamples},
            }

        # Unique entity indices
        entity_indices = sorted(set(v.entity_index for v in detected_list))
        n_entities = len(entity_indices)

        # Precompute injected set for fast lookup
        injected_set = {a.entity_index for a in injected_list}
        max_index = max(entity_indices)

        def _compute_precision(filtered_violations: list) -> float:
            tp = sum(1 for v in filtered_violations if v.entity_index in injected_set)
            fp = sum(1 for v in filtered_violations if v.entity_index not in injected_set)
            return tp / max(tp + fp, 1)

        def _compute_recall(filtered_violations: list, resampled_injected: set) -> float:
            detected_set = {v.entity_index for v in filtered_violations}
            tp = len(detected_set & resampled_injected)
            return tp / max(len(resampled_injected), 1)

        # Pre-index violations by entity
        violations_by_entity: dict = {}
        for v in detected_list:
            violations_by_entity.setdefault(v.entity_index, []).append(v)

        prec_resamples = []
        rec_resamples = []
        for _ in range(n_resamples):
            # Resample entity indices (with replacement)
            boot_indices = [_random.choice(entity_indices) for _ in range(n_entities)]
            boot_set = set(boot_indices)

            # Filter violations to resampled entities
            boot_violations = [
                v for idx in boot_indices
                for v in violations_by_entity.get(idx, [])
            ]

            # Resample injected anomalies proportionally
            boot_injected = {
                idx for idx in boot_indices
                if idx in injected_set
            }

            prec_resamples.append(_compute_precision(boot_violations))
            rec_resamples.append(_compute_recall(boot_violations, boot_injected))

        def _ci(values: list) -> dict:
            values.sort()
            alpha = 1 - confidence
            lo_idx = int(len(values) * alpha / 2)
            hi_idx = int(len(values) * (1 - alpha / 2))
            return {
                "mean": round(sum(values) / len(values), 4),
                "lower_bound": round(values[lo_idx], 4),
                "upper_bound": round(values[hi_idx], 4),
                "n_resamples": n_resamples,
            }

        return {
            "precision_ci": _ci(prec_resamples),
            "recall_ci": _ci(rec_resamples),
        }

    def full_report(self, pipeline: str = "local") -> dict:
        """Generate full evaluation report with 95% bootstrap CI for all metrics.

        Args:
            pipeline: Pipeline type used for evaluation ("local" or "spark").
                      NG-18: Report pipeline type separately per EV-PROTO3.
        """
        dr = self.detection_rate()

        # Bootstrap CI for precision and recall (entity-resampled)
        bootstrap = self.bootstrap_ci(n_resamples=1000, confidence=0.95)
        prec_ci = bootstrap["precision_ci"]
        rec_ci = bootstrap["recall_ci"]

        # Point estimates
        prec_pt = self.precision()
        rec_pt = self.recall_overall()
        f1_pt = (2 * prec_pt * rec_pt / max(prec_pt + rec_pt, 1e-9)
                  if (prec_pt + rec_pt) > 0 else 0.0)
        fpr_pt = self.false_positive_rate()

        # NG-33: Report label delay config
        label_delay_config = {
            "label_delay_events": self.label_delay_events,
            "note": "During label_delay_events window, violations on anomalous "
                    "entities are not counted as TP (simulates label delay per "
                    "Komorniczak et al. 2026).",
        }

        return {
            "pipeline": pipeline,
            "evaluation_config": label_delay_config,
            "total_events_processed": max(
                max((a.entity_index for a in self.injected_anomalies), default=0) + 1,
                max((v.entity_index for v in self.detected_violations), default=0) + 1,
            ),
            "total_anomalies_injected": len(self.injected_anomalies),
            "total_violations_detected": len(self.detected_violations),
            "precision": {
                "point_estimate": round(prec_pt, 4),
                "ci_95": [prec_ci["lower_bound"], prec_ci["upper_bound"]],
                "n_resamples": prec_ci["n_resamples"],
            },
            "recall_overall": {
                "point_estimate": round(rec_pt, 4),
                "ci_95": [rec_ci["lower_bound"], rec_ci["upper_bound"]],
                "n_resamples": rec_ci["n_resamples"],
            },
            "f1_score": {
                "point_estimate": round(f1_pt, 4),
            },
            "false_positive_rate": {
                "point_estimate": round(fpr_pt, 4),
            },
            "detection_rate_by_type": {
                k: {**v, "detection_rate": round(v["detection_rate"], 4)}
                for k, v in dr.items()
            },
            "latency": self.latency_percentiles(),
            "rule_coverage": self.rule_coverage(),
        }
