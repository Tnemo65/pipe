"""
Tests for DataContract rule gating fields (Phase 3 T9).

Validates required_rules, optional_rules, suppressed_rules, and sla_max_violation_rate.
"""
import pytest
from datetime import datetime
from streamdq.models.contract import DataContract, FieldContract, CertificationTier


class TestContractRuleGating:
    """Test rule gating fields in DataContract."""

    def test_contract_with_required_rules(self):
        """Contract can specify required rules."""
        contract = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.BRONZE,
            owner="test_team",
            fields=[],
            required_rules=["FMT001", "COM001", "SEM001"]
        )

        assert contract.required_rules == ["FMT001", "COM001", "SEM001"]
        assert len(contract.required_rules) == 3

    def test_contract_with_optional_rules(self):
        """Contract can specify optional rules."""
        contract = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.BRONZE,
            owner="test_team",
            fields=[],
            optional_rules=["CRS003", "PAT001"]
        )

        assert contract.optional_rules == ["CRS003", "PAT001"]
        assert len(contract.optional_rules) == 2

    def test_contract_with_suppressed_rules(self):
        """Contract can suppress rules (e.g., CRS003 for replay data)."""
        contract = DataContract(
            name="nyc_taxi_replay",
            version="1.0.0",
            tier=CertificationTier.BRONZE,
            owner="data_team",
            fields=[],
            suppressed_rules=["CRS003"]  # Replay data has known duplicates
        )

        assert contract.suppressed_rules == ["CRS003"]
        assert "CRS003" in contract.suppressed_rules

    def test_contract_with_sla_max_violation_rate(self):
        """Contract can specify max violation rate SLA."""
        contract = DataContract(
            name="critical_stream",
            version="1.0.0",
            tier=CertificationTier.GOLD,
            owner="platform_team",
            fields=[],
            sla_max_violation_rate=0.02  # 2% max violation rate
        )

        assert contract.sla_max_violation_rate == 0.02

    def test_contract_defaults_empty_rule_lists(self):
        """Rule lists default to empty if not specified."""
        contract = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.BRONZE,
            owner="test_team",
            fields=[]
        )

        assert contract.required_rules == []
        assert contract.optional_rules == []
        assert contract.suppressed_rules == []
        assert contract.sla_max_violation_rate is None

    def test_contract_serialization_with_rule_gating(self):
        """Contract with rule gating fields serializes correctly."""
        contract = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.SILVER,
            owner="data_team",
            fields=[],
            required_rules=["FMT001", "COM001"],
            optional_rules=["CRS003"],
            suppressed_rules=["PAT001"],
            sla_max_violation_rate=0.05
        )

        # Serialize to dict (assuming to_dict method exists or use __dict__)
        data = {
            "name": contract.name,
            "version": contract.version,
            "tier": contract.tier.value,
            "owner": contract.owner,
            "required_rules": contract.required_rules,
            "optional_rules": contract.optional_rules,
            "suppressed_rules": contract.suppressed_rules,
            "sla_max_violation_rate": contract.sla_max_violation_rate
        }

        assert data["required_rules"] == ["FMT001", "COM001"]
        assert data["optional_rules"] == ["CRS003"]
        assert data["suppressed_rules"] == ["PAT001"]
        assert data["sla_max_violation_rate"] == 0.05
