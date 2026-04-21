"""
YAML Rule Compiler.

Compiles YAML rule definitions into Python DataQualityRule instances.
Supports stateless rules only (SYN, SEM, GTFS syntactic/semantic).
"""
from __future__ import annotations
import yaml
import logging
from pathlib import Path

from streamdq.rules.base import DataQualityRule
from streamdq.rules.syntactic import (
    CompletenessRule,
    FareAmountRangeRule,
    PickupLocationValidRule,
    TimestampNotFutureRule,
)
from streamdq.rules.semantic import (
    FareRangeRule,
    TripDurationSanityRule,
    AverageSpeedSanityRule,
)
from streamdq.rules.gtfs_rules import (
    GTFSVehicleIDValidRule,
    GTFSLatLongRangeRule,
    GTFSSpeedRangeRule,
    GTFSImpossibleSpeedRule,
    GTFSStaleDataRule,
)

logger = logging.getLogger(__name__)


class RuleCompiler:
    """Compiles YAML rule definitions into Python rule instances."""

    # Map YAML type names to Python classes
    RULE_TYPE_MAP = {
        "CompletenessRule": CompletenessRule,
        "FareAmountRangeRule": FareAmountRangeRule,
        "PickupLocationValidRule": PickupLocationValidRule,
        "TimestampNotFutureRule": TimestampNotFutureRule,
        "FareRangeRule": FareRangeRule,
        "TripDurationSanityRule": TripDurationSanityRule,
        "AverageSpeedSanityRule": AverageSpeedSanityRule,
        "GTFSVehicleIDValidRule": GTFSVehicleIDValidRule,
        "GTFSLatLongRangeRule": GTFSLatLongRangeRule,
        "GTFSSpeedRangeRule": GTFSSpeedRangeRule,
        "GTFSImpossibleSpeedRule": GTFSImpossibleSpeedRule,
        "GTFSStaleDataRule": GTFSStaleDataRule,
    }

    @classmethod
    def load_rules(cls, entity_type: str, threshold_engine=None) -> list[DataQualityRule]:
        """
        Load all YAML rules for entity type.

        Args:
            entity_type: "nyc_taxi" or "gtfs"
            threshold_engine: AdaptiveThresholdEngine for wiring adaptive thresholds

        Returns:
            List of compiled rule instances

        Raises:
            FileNotFoundError: If rules directory doesn't exist
            ValueError: If YAML invalid or rule type unknown
        """
        rules_dir = Path(f"rules/{entity_type}")
        if not rules_dir.exists():
            raise FileNotFoundError(f"Rules directory not found: {rules_dir}")

        rules = []
        for yaml_file in sorted(rules_dir.glob("*.yaml")):
            try:
                rule = cls.compile_rule(yaml_file, threshold_engine)
                if rule.enabled:
                    rules.append(rule)
                logger.info(f"Loaded rule {rule.rule_id} from {yaml_file.name}")
            except Exception as e:
                logger.error(f"Failed to compile {yaml_file}: {e}")
                raise  # Fail fast

        return rules

    @classmethod
    def compile_rule(cls, yaml_path: Path, threshold_engine=None) -> DataQualityRule:
        """
        Compile single YAML file to rule instance.

        Args:
            yaml_path: Path to YAML file
            threshold_engine: Optional threshold engine for adaptive rules

        Returns:
            Compiled DataQualityRule instance

        Raises:
            ValueError: If required fields missing or invalid
        """
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        rule_def = data["rule"]

        # Validate required fields
        required = ["id", "name", "type", "severity"]
        missing = [f for f in required if f not in rule_def]
        if missing:
            raise ValueError(f"{yaml_path}: Missing required fields: {missing}")

        rule_type = rule_def["type"]

        # Get Python class
        rule_class = cls.RULE_TYPE_MAP.get(rule_type)
        if not rule_class:
            raise ValueError(f"{yaml_path}: Unknown rule type: {rule_type}")

        # Parse parameters
        params = cls._parse_parameters(rule_def, threshold_engine, yaml_path)

        # Instantiate rule
        rule = rule_class(rule_id=rule_def["id"], **params)
        rule.enabled = rule_def.get("enabled", True)

        return rule

    @classmethod
    def _parse_parameters(cls, rule_def: dict, threshold_engine, yaml_path: Path) -> dict:
        """Parse YAML parameters into Python kwargs."""
        params = dict(rule_def.get("parameters", {}))

        # Handle adaptive threshold wiring
        if "threshold" in params:
            threshold_cfg = params["threshold"]

            if threshold_cfg.get("type") == "adaptive":
                if threshold_engine is None:
                    raise ValueError(
                        f"{yaml_path}: Rule {rule_def['id']} requires adaptive thresholds "
                        f"but no threshold_engine provided"
                    )

                params["threshold_engine"] = threshold_engine
                params["percentile"] = threshold_cfg["percentile"]
                params["multiplier"] = threshold_cfg.get("multiplier", 1.0)
                params["fallback_value"] = threshold_cfg.get("fallback_value")

            elif threshold_cfg.get("type") == "static":
                params["static_threshold"] = threshold_cfg["fallback_value"]

            del params["threshold"]

        return params
