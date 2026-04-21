"""
Tests for contract-aware rule registry.

Validates that RuleRegistry can filter rules based on contract specification.
"""
import pytest
from pathlib import Path
from streamdq.rules.registry import RuleRegistry
from streamdq.models.contract import DataContract, CertificationTier


class TestRuleRegistryFromContract:
    """Test contract-based registry construction."""

    def test_from_contract_suppresses_rules(self):
        """Registry built from contract suppresses specified rules."""
        # First verify CRS003 is in default registry
        from streamdq.rules.registry import build_default_registry
        default_registry = build_default_registry()
        default_rule_ids = [r.rule_id for r in default_registry.get_all_rules()]
        assert "CRS003" in default_rule_ids, "CRS003 should be in default registry"

        # Now build with contract that suppresses CRS003
        contract = DataContract(
            name="test_replay",
            version="1.0.0",
            tier=CertificationTier.SILVER,
            owner="team",
            fields=[],
            suppressed_rules=["CRS003"],
        )

        registry = RuleRegistry.from_contract(contract)

        # CRS003 should not be in registry
        all_rule_ids = [rule.rule_id for rule in registry.get_all_rules()]
        assert "CRS003" not in all_rule_ids

    def test_from_contract_includes_required_rules(self):
        """Registry includes all required rules."""
        contract = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.SILVER,
            owner="team",
            fields=[],
            required_rules=["SYN001", "SYN002", "SEM001"],
        )

        registry = RuleRegistry.from_contract(contract)

        all_rule_ids = [rule.rule_id for rule in registry.get_all_rules()]
        assert "SYN001" in all_rule_ids
        assert "SYN002" in all_rule_ids
        assert "SEM001" in all_rule_ids

    def test_from_contract_with_yaml_file(self):
        """Registry can be built from YAML contract file."""
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        yaml_path = PROJECT_ROOT / "config" / "contracts" / "nyc_taxi_replay.yaml"

        if not yaml_path.exists():
            pytest.skip(f"Contract file not found: {yaml_path}")

        contract = DataContract.from_yaml(yaml_path)
        registry = RuleRegistry.from_contract(contract)

        all_rule_ids = [rule.rule_id for rule in registry.get_all_rules()]

        # CRS003 should be suppressed
        assert "CRS003" not in all_rule_ids

        # Required rules should be present
        assert "SYN001" in all_rule_ids
        assert "SEM001" in all_rule_ids
