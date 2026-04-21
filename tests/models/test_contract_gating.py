"""
Tests for DataContract rule gating fields (Phase 3 T9).

Validates required_rules, optional_rules, suppressed_rules, and sla_max_violation_rate.
"""
import pytest
import tempfile
import yaml
from pathlib import Path
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
        """Contract with rule gating fields serializes correctly via dataclasses.asdict()."""
        from dataclasses import asdict

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

        data = asdict(contract)

        assert data["required_rules"] == ["FMT001", "COM001"]
        assert data["optional_rules"] == ["CRS003"]
        assert data["suppressed_rules"] == ["PAT001"]
        assert data["sla_max_violation_rate"] == 0.05

    def test_sla_max_violation_rate_valid_boundaries(self):
        """sla_max_violation_rate accepts 0.0 and 1.0 as valid boundary values."""
        contract_min = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.BRONZE,
            owner="test_team",
            fields=[],
            sla_max_violation_rate=0.0
        )
        assert contract_min.sla_max_violation_rate == 0.0

        contract_max = DataContract(
            name="test_stream",
            version="1.0.0",
            tier=CertificationTier.BRONZE,
            owner="test_team",
            fields=[],
            sla_max_violation_rate=1.0
        )
        assert contract_max.sla_max_violation_rate == 1.0

    def test_sla_max_violation_rate_negative_value_raises_error(self):
        """sla_max_violation_rate raises ValueError for negative values."""
        with pytest.raises(ValueError, match="sla_max_violation_rate must be in"):
            DataContract(
                name="test_stream",
                version="1.0.0",
                tier=CertificationTier.BRONZE,
                owner="test_team",
                fields=[],
                sla_max_violation_rate=-0.1
            )

    def test_sla_max_violation_rate_exceeds_one_raises_error(self):
        """sla_max_violation_rate raises ValueError when greater than 1.0."""
        with pytest.raises(ValueError, match="sla_max_violation_rate must be in"):
            DataContract(
                name="test_stream",
                version="1.0.0",
                tier=CertificationTier.BRONZE,
                owner="test_team",
                fields=[],
                sla_max_violation_rate=1.5
            )


class TestContractYAMLLoading:
    """Test loading contracts from YAML files."""

    def test_load_nyc_taxi_replay_contract(self):
        """Load NYC Taxi replay contract from YAML."""
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        yaml_path = PROJECT_ROOT / "config" / "contracts" / "nyc_taxi_replay.yaml"

        if not yaml_path.exists():
            pytest.skip(f"Contract file not found: {yaml_path}")

        contract = DataContract.from_yaml(yaml_path)

        assert contract.name == "nyc_taxi_replay"
        assert contract.version == "v1.0.0"
        assert contract.tier == CertificationTier.SILVER
        assert contract.owner == "data_platform_team"
        assert "CRS003" in contract.suppressed_rules
        assert contract.sla_max_violation_rate == 0.10

    def test_load_gtfs_live_contract(self):
        """Load GTFS live contract from YAML."""
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        yaml_path = PROJECT_ROOT / "config" / "contracts" / "gtfs_live.yaml"

        if not yaml_path.exists():
            pytest.skip(f"Contract file not found: {yaml_path}")

        contract = DataContract.from_yaml(yaml_path)

        assert contract.name == "gtfs_live"
        assert contract.tier == CertificationTier.GOLD
        assert "CRS003" in contract.required_rules
        assert "CRS003" not in contract.suppressed_rules
        assert contract.sla_max_violation_rate == 0.05

    def test_from_yaml_file_not_found(self):
        """from_yaml raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError, match="Contract file not found"):
            DataContract.from_yaml("nonexistent.yaml")

    def test_from_yaml_invalid_tier(self):
        """from_yaml raises KeyError for invalid tier values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "name": "test",
                "version": "1.0.0",
                "tier": "INVALID_TIER",
                "owner": "test"
            }, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError):
                DataContract.from_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_from_yaml_missing_required_field(self):
        """from_yaml raises KeyError for missing required fields (name, version)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "tier": "BRONZE",
                "owner": "test"
                # Missing "name" and "version"
            }, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError):
                DataContract.from_yaml(temp_path)
        finally:
            Path(temp_path).unlink()
