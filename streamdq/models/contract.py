"""
Data contract definitions for StreamDQ.

Defines formal agreements between data producers and consumers.
Certification tiers: BRONZE, SILVER, GOLD.

References:
- Data Contract Specification (databricks.com)
- dbt data contracts (docs.getdbt.com)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import yaml


class CertificationTier(Enum):
    """Data quality certification levels."""
    BRONZE = "BRONZE"   # Basic completeness and validity
    SILVER = "SILVER"   # + semantic checks and consistency
    GOLD = "GOLD"       # + adaptive thresholds and cross-record validation


@dataclass
class FieldContract:
    """Contract for a single field."""
    name: str
    data_type: str
    nullable: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[list] = None
    description: str = ""


@dataclass
class DataContract:
    """
    Formal data contract for a dataset.

    Defines:
    - Which fields are required
    - Field-level type/value constraints
    - Certification tier requirements
    - Version and owner metadata

    Usage:
        contract = DataContract(
            name="nyc_taxi_trips",
            version="1.0.0",
            tier=CertificationTier.SILVER,
            owner="data-platform-team",
            fields=[
                FieldContract("fare_amount", "float", nullable=False, min_value=0),
                FieldContract("PULocationID", "int", nullable=False),
            ],
        )
        result = contract.evaluate(violations, total_records)
        print(result.tier_achieved)  # "SILVER"
    """

    name: str
    version: str
    tier: CertificationTier
    owner: str
    fields: list[FieldContract] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""

    # Phase 3 (T9): Contract-Aware Rule Gating
    required_rules: list[str] = field(default_factory=list)
    optional_rules: list[str] = field(default_factory=list)
    suppressed_rules: list[str] = field(default_factory=list)
    sla_max_violation_rate: Optional[float] = None

    # Tier-specific thresholds (fraction of records that must pass)
    # NOTE: violation_rate <= (1 - threshold)
    # Thresholds ordered so that BRONZE is most lenient, GOLD is strictest:
    #   BRONZE: requires 85% pass rate (≤15% violations) — entry-level
    #   SILVER: requires 90% pass rate (≤10% violations) — intermediate
    #   GOLD: requires 95% pass rate (≤5% violations) — strictest
    TIER_THRESHOLDS = {
        CertificationTier.BRONZE: 0.85,
        CertificationTier.SILVER: 0.90,
        CertificationTier.GOLD: 0.95,
    }

    # Rule coverage required per tier
    TIER_RULES = {
        CertificationTier.BRONZE: {"SYN000", "SYN001", "SYN002"},
        CertificationTier.SILVER: {"SYN000", "SYN001", "SYN002", "SYN003", "SEM001"},
        CertificationTier.GOLD: {
            "SYN000", "SYN001", "SYN002", "SYN003",
            "SEM001", "SEM002", "SEM003",
            "CRS001", "CRS002", "CRS003",
        },
    }

    def __post_init__(self):
        """Validate contract fields after initialization."""
        # Validate sla_max_violation_rate range
        if self.sla_max_violation_rate is not None:
            if not (0.0 <= self.sla_max_violation_rate <= 1.0):
                raise ValueError(
                    f"sla_max_violation_rate must be in [0.0, 1.0], got {self.sla_max_violation_rate}"
                )

    def evaluate(
        self,
        violations_by_rule: dict[str, int],
        total_records: int,
    ) -> ContractEvaluationResult:
        """
        Evaluate whether data meets the contract's tier requirements.

        Args:
            violations_by_rule: Dict mapping rule_id -> violation_count
            total_records: Total number of records in the dataset

        Returns:
            ContractEvaluationResult with tier achieved and gap analysis
        """
        if total_records == 0:
            return ContractEvaluationResult(
                contract_name=self.name,
                contract_version=self.version,
                tier_achieved=None,
                tier_required=self.tier,
                total_records=0,
                total_violations=sum(violations_by_rule.values()),
                violation_rate=1.0,
                per_rule_violations=dict(violations_by_rule),
                rule_coverage={},
                tier_met=False,
                missing_rules=set(),
                gap_analysis="No records to evaluate",
            )

        total_violations = sum(violations_by_rule.values())
        violation_rate = total_violations / total_records

        # Per-rule violation rates
        per_rule_violations = {
            rule_id: count / total_records
            for rule_id, count in violations_by_rule.items()
        }

        # Check rule coverage
        rules_fired = set(violations_by_rule.keys())
        tier_required_rules = self.TIER_RULES[self.tier]
        missing_rules = tier_required_rules - rules_fired

        # Determine achieved tier using explicit order (NG-25: avoid enum order dependency)
        # Tier thresholds ordered from most lenient to strictest (BRONZE < SILVER < GOLD)
        _TIER_EVAL_ORDER = [
            (CertificationTier.BRONZE, self.TIER_THRESHOLDS[CertificationTier.BRONZE]),
            (CertificationTier.SILVER, self.TIER_THRESHOLDS[CertificationTier.SILVER]),
            (CertificationTier.GOLD, self.TIER_THRESHOLDS[CertificationTier.GOLD]),
        ]
        tier_achieved = None
        for tier, threshold in _TIER_EVAL_ORDER:
            if violation_rate <= (1 - threshold):
                tier_achieved = tier

        # Fallback: violation rate exceeds all thresholds -> lowest tier
        if tier_achieved is None:
            tier_achieved = CertificationTier.BRONZE

        # Check if required tier is met (NG-25: explicit index order)
        _TIER_INDEX = {
            CertificationTier.BRONZE: 0,
            CertificationTier.SILVER: 1,
            CertificationTier.GOLD: 2,
        }
        tier_met = _TIER_INDEX[tier_achieved] >= _TIER_INDEX[self.tier]

        gap = ""
        if not tier_met:
            gap = (
                f"Violation rate {violation_rate:.2%} exceeds "
                f"{self.tier.name} threshold "
                f"({(1-self.TIER_THRESHOLDS[self.tier]):.2%}). "
                f"Gap: {(violation_rate - (1-self.TIER_THRESHOLDS[self.tier])):.2%}"
            )

        return ContractEvaluationResult(
            contract_name=self.name,
            contract_version=self.version,
            tier_achieved=tier_achieved,
            tier_required=self.tier,
            total_records=total_records,
            total_violations=total_violations,
            violation_rate=round(violation_rate, 4),
            per_rule_violations=per_rule_violations,
            rule_coverage={
                rule_id: rule_id in rules_fired
                for rule_id in tier_required_rules
            },
            tier_met=tier_met,
            missing_rules=missing_rules,
            gap_analysis=gap,
        )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "DataContract":
        """
        Load contract from YAML file.

        YAML schema:
            name: str
            version: str
            tier: str (BRONZE, SILVER, GOLD)
            owner: str
            description: str
            required_rules: list[str]
            optional_rules: list[str]
            suppressed_rules: list[str]
            sla_max_violation_rate: float
            fields: list[dict] (FieldContract specs)

        Args:
            yaml_path: Path to YAML contract file

        Returns:
            DataContract instance
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Contract file not found: {yaml_path}")

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Parse tier enum
        tier_str = data.get("tier", "BRONZE")
        tier = CertificationTier[tier_str]

        # Parse fields
        fields = []
        for field_spec in data.get("fields", []):
            fields.append(FieldContract(
                name=field_spec["name"],
                data_type=field_spec["data_type"],
                nullable=field_spec.get("nullable", True),
                min_value=field_spec.get("min_value"),
                max_value=field_spec.get("max_value"),
                allowed_values=field_spec.get("allowed_values"),
                description=field_spec.get("description", ""),
            ))

        return cls(
            name=data["name"],
            version=data["version"],
            tier=tier,
            owner=data.get("owner", ""),
            description=data.get("description", ""),
            fields=fields,
            required_rules=data.get("required_rules", []),
            optional_rules=data.get("optional_rules", []),
            suppressed_rules=data.get("suppressed_rules", []),
            sla_max_violation_rate=data.get("sla_max_violation_rate"),
        )


@dataclass
class ContractEvaluationResult:
    """Result of a contract evaluation."""
    contract_name: str
    contract_version: str
    tier_achieved: Optional[CertificationTier]
    tier_required: CertificationTier
    total_records: int
    total_violations: int
    violation_rate: float
    per_rule_violations: dict[str, float]
    rule_coverage: dict[str, bool]
    tier_met: bool
    missing_rules: set[str]
    gap_analysis: str
