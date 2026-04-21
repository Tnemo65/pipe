"""
Rule registry — central registration and evaluation of all rules.
"""
from __future__ import annotations
from typing import Optional

from streamdq.rules.base import DataQualityRule, RuleContext, Violation
from streamdq.models.contract import DataContract
from streamdq.rules.syntactic import (
    CompletenessRule,
    FareAmountRangeRule,
    PickupLocationValidRule,
    TimestampNotFutureRule,
)
from streamdq.rules.semantic import FareRangeRule, TripDurationSanityRule, AverageSpeedSanityRule
from streamdq.rules.cross_record import (
    evaluate_trajectory_anomaly,
    evaluate_duplicate_event,
    reset_cross_record_state,
)
from streamdq.rules.gtfs_rules import (
    GTFSVehicleIDValidRule,
    GTFSLatLongRangeRule,
    GTFSSpeedRangeRule,
    GTFSImpossibleSpeedRule,
    GTFSStaleDataRule,
    evaluate_gtfs_trajectory_anomaly,
    evaluate_gtfs_duplicate_event,
    reset_gtfs_cross_record_state,
)


class RuleRegistry:
    """
    Central registry for all data quality rules.

    Usage:
        registry = RuleRegistry()
        registry.register(MyCustomRule())

        violations = registry.evaluate_all(ctx)
    """

    def __init__(self):
        self._stateless_rules: list[DataQualityRule] = []
        self._stateful_evaluators: list[callable] = []

    def register(self, rule: DataQualityRule):
        """Register a stateless rule (evaluates single event)."""
        self._stateless_rules.append(rule)

    def register_stateful(self, evaluator: callable):
        """
        Register a stateful evaluator (requires cross-record state).

        The evaluator must have signature:
            evaluate(event: dict, event_time: datetime) -> list[Violation]
        """
        self._stateful_evaluators.append(evaluator)

    def evaluate_all(self, ctx: RuleContext) -> list[Violation]:
        """
        Evaluate all stateless rules against the given context.

        Returns:
            List of Violations (0 or more).
        """
        violations = []
        for rule in self._stateless_rules:
            v = rule.evaluate(ctx)
            if v:
                violations.append(v)
        return violations

    def evaluate_stateful(
        self, event: dict, event_time, start_time: float = 0.0
    ) -> list[Violation]:
        """
        Evaluate all stateful rules against the given event.

        Returns:
            List of Violations (0 or more).
        """
        violations = []
        for evaluator in self._stateful_evaluators:
            result = evaluator(event, event_time, start_time)
            if result:
                if isinstance(result, list):
                    violations.extend(result)
                elif isinstance(result, Violation):
                    violations.append(result)
        return violations

    def get_all_rules(self) -> list[DataQualityRule]:
        """Get all registered stateless rules."""
        return self._stateless_rules

    def get_summary(self) -> dict:
        """Get a summary of all registered rules."""
        return {
            "stateless_rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "severity": r.severity,
                    "violation_type": r.violation_type,
                }
                for r in self._stateless_rules
            ],
            "stateful_evaluators": len(self._stateful_evaluators),
            "total_rules": len(self._stateless_rules) + len(self._stateful_evaluators),
        }

    @classmethod
    def from_contract(cls, contract: DataContract) -> "RuleRegistry":
        """
        Build rule registry filtered by contract specification.

        Contract controls which rules fire:
        - required_rules: Must be included
        - optional_rules: Included if available
        - suppressed_rules: Excluded

        If contract specifies no rules, fall back to tier-based defaults.

        Args:
            contract: DataContract with rule specifications

        Returns:
            RuleRegistry with contract-filtered rules
        """
        # Start with default registry
        registry = build_default_registry()

        # If contract specifies suppressed rules, remove them
        if contract.suppressed_rules:
            for rule_id in contract.suppressed_rules:
                registry._stateless_rules = [r for r in registry._stateless_rules if r.rule_id != rule_id]

        # If contract specifies required/optional rules, filter to those only
        if contract.required_rules or contract.optional_rules:
            allowed_rules = set(contract.required_rules) | set(contract.optional_rules)
            registry._stateless_rules = [r for r in registry._stateless_rules if r.rule_id in allowed_rules]

        return registry


def build_default_registry(entity_type: str = "nyc_taxi") -> RuleRegistry:
    """
    Build the default registry with all built-in rules.

    Args:
        entity_type: "nyc_taxi" or "gtfs_vehicle". Determines which rules are included.

    Returns:
        RuleRegistry with SYN001-003, SEM001-003, CRS001-003 registered (NYC taxi),
        or GTFSSyn001-003, GTFSSem001-002, GTFSCRS001-002 registered (GTFS).
    """
    registry = RuleRegistry()

    if entity_type == "gtfs_vehicle":
        # GTFS-specific rules
        registry.register(GTFSVehicleIDValidRule("GTFSSyn001"))
        registry.register(GTFSLatLongRangeRule("GTFSSyn002"))
        registry.register(GTFSSpeedRangeRule("GTFSSyn003"))
        registry.register(GTFSImpossibleSpeedRule("GTFSSem001"))
        registry.register(GTFSStaleDataRule("GTFSSem002"))
        registry.register_stateful(evaluate_gtfs_trajectory_anomaly)
        registry.register_stateful(evaluate_gtfs_duplicate_event)
        return registry

    # NYC Taxi rules (default)
    # ── Syntactic rules ──────────────────────────────────────────
    registry.register(CompletenessRule("SYN000"))
    registry.register(FareAmountRangeRule("SYN001"))
    registry.register(PickupLocationValidRule("SYN002"))
    registry.register(TimestampNotFutureRule("SYN003"))

    # ── Semantic rules ─────────────────────────────────────────
    registry.register(FareRangeRule("SEM001"))
    registry.register(TripDurationSanityRule("SEM002"))
    registry.register(AverageSpeedSanityRule("SEM003"))

    # ── Stateful / cross-record rules ──────────────────────────
    registry.register_stateful(evaluate_trajectory_anomaly)
    registry.register_stateful(evaluate_duplicate_event)

    return registry
