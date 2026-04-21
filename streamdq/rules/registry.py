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
        self._stateful_evaluators: dict[str, callable] = {}

    def register(self, rule: DataQualityRule):
        """Register a stateless rule (evaluates single event)."""
        self._stateless_rules.append(rule)

    def register_stateful(self, evaluator: callable):
        """
        Register a stateful evaluator (requires cross-record state).

        The evaluator must have signature:
            evaluate(event: dict, event_time: datetime) -> list[Violation]
        """
        # Store by function name for filtering
        self._stateful_evaluators[evaluator.__name__] = evaluator

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
        for evaluator in self._stateful_evaluators.values():
            result = evaluator(event, event_time, start_time)
            if result:
                if isinstance(result, list):
                    violations.extend(result)
                elif isinstance(result, Violation):
                    violations.append(result)
        return violations

    def get_all_rules(self) -> list:
        """
        Get all rules (stateless + stateful) for testing/inspection.

        Returns:
            List of all Rule objects and stateful evaluator proxies
        """
        # Return copy of stateless Rule objects
        result = list(self._stateless_rules)

        # Map function names to rule IDs
        func_name_to_rule_id = {
            "evaluate_trajectory_anomaly": "CRS001",
            "evaluate_duplicate_event": "CRS003",
            "evaluate_gtfs_trajectory_anomaly": "GTFSCRS001",
            "evaluate_gtfs_duplicate_event": "GTFSCRS002",
        }

        # Create proxy objects for stateful evaluators
        class StatefulRuleProxy:
            def __init__(self, rule_id):
                self.rule_id = rule_id

        for func_name in self._stateful_evaluators.keys():
            rule_id = func_name_to_rule_id.get(func_name)
            if rule_id:
                result.append(StatefulRuleProxy(rule_id))

        return result

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
    def from_contract(cls, contract: DataContract, entity_type: str = "nyc_taxi") -> "RuleRegistry":
        """
        Build rule registry filtered by contract specification.

        Contract controls which rules fire:
        - required_rules: Must be included
        - optional_rules: Included if available
        - suppressed_rules: Excluded

        If contract specifies no rules, fall back to tier-based defaults.

        Precedence: suppressed_rules > required/optional (suppression wins)

        Args:
            contract: DataContract with rule specifications
            entity_type: "nyc_taxi" or "gtfs_vehicle" for entity-specific rules

        Returns:
            RuleRegistry with contract-filtered rules
        """
        # Start with default registry for entity type
        registry = build_default_registry(entity_type=entity_type)

        # Map rule IDs to stateful evaluator function names
        rule_id_to_func_name = {
            "CRS001": "evaluate_trajectory_anomaly",
            "CRS003": "evaluate_duplicate_event",
            "GTFSCRS001": "evaluate_gtfs_trajectory_anomaly",
            "GTFSCRS002": "evaluate_gtfs_duplicate_event",
        }

        # If contract specifies suppressed rules, remove them from BOTH stateless and stateful
        if contract.suppressed_rules:
            suppressed_set = set(contract.suppressed_rules)

            # Filter stateless rules
            registry._stateless_rules = [r for r in registry._stateless_rules if r.rule_id not in suppressed_set]

            # Filter stateful evaluators
            for rule_id in suppressed_set:
                func_name = rule_id_to_func_name.get(rule_id)
                if func_name and func_name in registry._stateful_evaluators:
                    del registry._stateful_evaluators[func_name]

        # If contract specifies required/optional rules, filter to those only
        if contract.required_rules or contract.optional_rules:
            allowed_rules = set(contract.required_rules) | set(contract.optional_rules)

            # Filter stateless rules
            registry._stateless_rules = [r for r in registry._stateless_rules if r.rule_id in allowed_rules]

            # Filter stateful evaluators
            allowed_func_names = set()
            for rule_id in allowed_rules:
                func_name = rule_id_to_func_name.get(rule_id)
                if func_name:
                    allowed_func_names.add(func_name)

            registry._stateful_evaluators = {
                k: v for k, v in registry._stateful_evaluators.items()
                if k in allowed_func_names
            }

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
