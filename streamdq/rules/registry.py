"""
Rule registry — central registration and evaluation of all rules.
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from streamdq.rules.base import DataQualityRule, RuleContext, Violation
from streamdq.models.contract import DataContract

if TYPE_CHECKING:
    from streamdq.models.rule_validator import RuleValidator, RuleValidationResult
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
        self._validator: Optional[RuleValidator] = None  # type: ignore
        self._validation_events: list[RuleValidationResult] = []  # type: ignore

    def enable_validation(self, validator: RuleValidator):  # type: ignore
        """
        Enable rule validation before registration.

        Args:
            validator: RuleValidator instance to use for validating rules before registration.
        """
        self._validator = validator

    def register(self, rule: DataQualityRule):
        """Register a stateless rule (evaluates single event)."""
        self._stateless_rules.append(rule)

    def register_rule(
        self,
        rule: DataQualityRule,
        historical_events: Optional[list[dict]] = None,
        ground_truth: Optional[dict] = None,
    ) -> RuleValidationResult:  # type: ignore
        """
        Register a stateless rule with optional validation.

        If validation is enabled, the rule is validated on historical events before registration.
        The rule is only registered if validation passes.

        Args:
            rule: DataQualityRule to register
            historical_events: Historical events for validation (required if validator enabled)
            ground_truth: Optional dict mapping event_id -> is_anomaly for ground truth validation

        Returns:
            RuleValidationResult with validation outcome and metrics.
            If validation not enabled, returns a result with accepted=True.

        Raises:
            ValueError: If validation enabled but historical_events is None
        """
        # Import at runtime to avoid circular imports
        from streamdq.models.rule_validator import RuleValidationResult

        # If validation disabled, just register and return success
        if self._validator is None:
            self._stateless_rules.append(rule)
            return RuleValidationResult(
                rule_id=rule.rule_id,
                fpr=0.0,
                precision=0.0,
                recall=0.0,
                coverage=0.0,
                total_events=0,
                violations=0,
                accepted=True,
                rejection_reason=None,
            )

        # Validation enabled: check historical_events provided
        if historical_events is None:
            raise ValueError(
                "historical_events required when validation enabled"
            )

        # Validate the rule
        result = self._validator.validate_rule(
            rule=rule,
            historical_events=historical_events,
            ground_truth=ground_truth,
        )

        # Track validation event
        self._validation_events.append(result)

        # Register rule if validation passed
        if result.accepted:
            self._stateless_rules.append(rule)

        return result

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
    Build registry with YAML rules as source of truth.

    Args:
        entity_type: "nyc_taxi" or "gtfs_vehicle". Determines which rules are included.

    Returns:
        RuleRegistry with YAML rules + stateful rules registered.

    Raises:
        FileNotFoundError: If rules directory doesn't exist
        ValueError: If YAML invalid or rule type unknown
    """
    from streamdq.config.rule_compiler import RuleCompiler

    registry = RuleRegistry()

    # Map entity_type to YAML directory name
    yaml_entity_type = "gtfs" if entity_type == "gtfs_vehicle" else entity_type

    # Load YAML rules (fail fast if missing/invalid)
    yaml_rules = RuleCompiler.load_rules(
        entity_type=yaml_entity_type,
        threshold_engine=None  # Wired by pipeline later
    )

    for rule in yaml_rules:
        registry.register(rule)

    # Stateful rules stay in Python (can't be YAML)
    if entity_type == "gtfs_vehicle":
        registry.register_stateful(evaluate_gtfs_trajectory_anomaly)
        registry.register_stateful(evaluate_gtfs_duplicate_event)
    else:
        registry.register_stateful(evaluate_trajectory_anomaly)
        registry.register_stateful(evaluate_duplicate_event)

    return registry
