"""
Rule Validity Gate (Phase 3 T10).

Validates rules before production deployment by running them on historical data
and measuring:
- FPR (False Positive Rate): violations / total events (conservative: assumes all are FP if no ground truth)
- Precision: TP / (TP + FP) (only measurable with ground truth)
- Recall: TP / (TP + FN) (only measurable with ground truth)
- Coverage: violations / total events (% of data the rule applies to)

Rules are promoted to production if:
- FPR < fpr_threshold (default: 0.10)
- Precision > precision_threshold (default: 0.50) — only if ground truth provided
- Coverage > coverage_threshold (default: 0.01)
- Historical data size >= min_events (default: 100)

References:
- ENHANCEMENT_ROADMAP.md section 6.2.3 (T10: Rule Validity Gate)
- Phase 3 (Days 12-15): Before promoting a rule to production, validate on historical data.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from streamdq.rules.base import DataQualityRule, RuleContext, ExternalContext
from streamdq.rules.adaptive import AdaptiveThresholdEngine


@dataclass
class RuleValidationResult:
    """
    Result of validating a rule on historical data.

    Attributes:
        rule_id: The rule being validated
        fpr: False positive rate (violations / total_events) if no ground truth
        precision: TP / (TP + FP) — only meaningful with ground truth
        recall: TP / (TP + FN) — only meaningful with ground truth
        coverage: violations / total_events (% of data the rule applies to)
        total_events: Number of historical events used for validation
        violations: Number of events that triggered the rule
        accepted: Whether the rule passed validation gates
        rejection_reason: If rejected, explanation of why (e.g., "FPR exceeds threshold")
    """

    rule_id: str
    fpr: float
    precision: float
    recall: float
    coverage: float
    total_events: int
    violations: int
    accepted: bool
    rejection_reason: Optional[str] = None


class RuleValidator:
    """
    Validates rules before production deployment.

    Usage:
        validator = RuleValidator(
            fpr_threshold=0.10,
            precision_threshold=0.50,
            coverage_threshold=0.01,
            min_events=100
        )
        result = validator.validate_rule(
            rule=my_rule,
            historical_events=event_list,
            ground_truth=None  # or dict mapping event_id -> is_anomaly
        )
        if result.accepted:
            promote_to_production(my_rule)
    """

    def __init__(
        self,
        fpr_threshold: float = 0.10,
        precision_threshold: float = 0.50,
        coverage_threshold: float = 0.01,
        min_events: int = 100,
    ):
        """
        Initialize RuleValidator with thresholds.

        Args:
            fpr_threshold: Max acceptable false positive rate (default: 0.10 = 10%)
            precision_threshold: Min acceptable precision (default: 0.50 = 50%)
            coverage_threshold: Min acceptable coverage (default: 0.01 = 1%)
            min_events: Min historical events required (default: 100)
        """
        self.fpr_threshold = fpr_threshold
        self.precision_threshold = precision_threshold
        self.coverage_threshold = coverage_threshold
        self.min_events = min_events

    def validate_rule(
        self,
        rule: DataQualityRule,
        historical_events: list[dict],
        ground_truth: Optional[dict] = None,
    ) -> RuleValidationResult:
        """
        Validate a rule on historical data.

        Runs the rule on all historical events and computes metrics:
        1. Checks if sufficient historical data (>= min_events)
        2. Sets up AdaptiveThresholdEngine with historical data
        3. Evaluates rule on all events
        4. Computes FPR, precision, recall, coverage
        5. Returns acceptance decision

        Args:
            rule: DataQualityRule to validate
            historical_events: List of dicts representing historical data
            ground_truth: Optional dict mapping event_id -> is_anomaly (bool).
                         If None, assumes all violations are false positives (conservative).

        Returns:
            RuleValidationResult with acceptance decision and metrics
        """
        # 1. Check minimum events requirement
        total_events = len(historical_events)
        if total_events < self.min_events:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                fpr=0.0,
                precision=0.0,
                recall=0.0,
                coverage=0.0,
                total_events=total_events,
                violations=0,
                accepted=False,
                rejection_reason=f"Insufficient historical data: {total_events} events < {self.min_events} required",
            )

        # 2. Set up AdaptiveThresholdEngine with historical data
        engine = AdaptiveThresholdEngine(
            window_size=max(10_000, total_events),
            recompute_every=total_events,
            min_sample_size=100,
        )

        # Feed all events to the engine to build baselines
        for event in historical_events:
            # Extract numeric fields for threshold engine
            for key, value in event.items():
                try:
                    numeric_val = float(value)
                    engine.update(key, numeric_val)
                except (ValueError, TypeError):
                    # Skip non-numeric fields
                    pass

        # 3. Evaluate rule on all events
        violations = 0
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        event_time = datetime.now()
        external_context = ExternalContext()

        for event in historical_events:
            # Create rule context for this event
            ctx = RuleContext(
                event=event,
                event_time=event_time,
                historical_stats=engine._stats,  # Access computed statistics
                external_context=external_context,
            )

            # Evaluate rule
            violation = rule.evaluate(ctx)

            if violation is not None:
                violations += 1

                # If ground truth provided, categorize as TP or FP
                if ground_truth is not None:
                    event_id = event.get("id", str(event))
                    is_anomaly = ground_truth.get(event_id, False)

                    if is_anomaly:
                        true_positives += 1
                    else:
                        false_positives += 1
                else:
                    # No ground truth: assume all violations are false positives (conservative)
                    false_positives += 1

            else:
                # No violation detected
                if ground_truth is not None:
                    event_id = event.get("id", str(event))
                    is_anomaly = ground_truth.get(event_id, False)

                    if is_anomaly:
                        false_negatives += 1

        # 4. Compute metrics

        # FPR: If no ground truth, FPR = coverage (conservative: all violations are FP)
        # Otherwise, FPR = FP / (FP + TP) = FP / total_violations
        if ground_truth is None:
            # Conservative assumption: all violations are false positives
            fpr = violations / total_events if total_events > 0 else 0.0
        else:
            total_violations = true_positives + false_positives
            fpr = false_positives / total_violations if total_violations > 0 else 0.0

        # Precision: TP / (TP + FP)
        # If no ground truth, precision = 0 (we can't claim precision without labels)
        total_violations = true_positives + false_positives
        precision = (
            true_positives / total_violations if total_violations > 0 else 0.0
        )

        # Recall: TP / (TP + FN)
        total_actual_anomalies = true_positives + false_negatives
        recall = (
            true_positives / total_actual_anomalies
            if total_actual_anomalies > 0
            else 0.0
        )

        # Coverage: violations / total_events (% of data the rule applies to)
        coverage = violations / total_events if total_events > 0 else 0.0

        # 5. Decision logic: accept if all thresholds passed
        acceptance_criteria = [
            ("FPR", fpr <= self.fpr_threshold),
            ("coverage", coverage >= self.coverage_threshold),
        ]

        # Only check precision if ground truth is provided (otherwise it's always 0)
        if ground_truth is not None:
            acceptance_criteria.append(
                ("precision", precision >= self.precision_threshold)
            )

        accepted = all(passed for _, passed in acceptance_criteria)
        rejection_reason = None

        if not accepted:
            failures = [name for name, passed in acceptance_criteria if not passed]
            if "FPR" in failures:
                rejection_reason = (
                    f"FPR ({fpr:.4f}) exceeds threshold ({self.fpr_threshold:.4f})"
                )
            elif "coverage" in failures:
                rejection_reason = f"Coverage ({coverage:.4f}) below threshold ({self.coverage_threshold:.4f})"
            elif "precision" in failures:
                rejection_reason = f"Precision ({precision:.4f}) below threshold ({self.precision_threshold:.4f})"
            else:
                rejection_reason = f"Failed criteria: {', '.join(failures)}"

        return RuleValidationResult(
            rule_id=rule.rule_id,
            fpr=fpr,
            precision=precision,
            recall=recall,
            coverage=coverage,
            total_events=total_events,
            violations=violations,
            accepted=accepted,
            rejection_reason=rejection_reason,
        )
