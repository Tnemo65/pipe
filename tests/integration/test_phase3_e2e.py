"""
End-to-end integration test for Phase 3.

Validates contract gating, drift recalibration, and rule validity.
"""
import pytest
from pathlib import Path
from streamdq.pipeline.local_pipeline import LocalPipeline, NoOpViolationStore
from streamdq.models.contract import DataContract


class TestPhase3ContractGatingE2E:
    """E2E test for contract-aware rule gating."""

    def test_replay_contract_suppresses_crs003(self):
        """NYC Taxi replay contract suppresses CRS003 duplicate detection."""
        # Load replay contract
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        contract_path = PROJECT_ROOT / "config" / "contracts" / "nyc_taxi_replay.yaml"

        if not contract_path.exists():
            pytest.skip(f"Contract not found: {contract_path}")

        contract = DataContract.from_yaml(contract_path)

        # Create pipeline with contract
        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="nyc_taxi",
            contract=contract,
        )

        # Verify CRS003 not in registry
        all_rule_ids = [rule.rule_id for rule in pipeline.rule_registry.get_all_rules()]
        assert "CRS003" not in all_rule_ids

        # Process duplicate events
        event = {
            "trip_id": "trip_001",
            "PULocationID": 161,
            "DOLocationID": 237,
            "fare_amount": 15.0,
            "trip_distance": 2.0,
            "_lineage": {
                "source_id": "nyc_taxi_replay",
                "source_type": "batch_replay",
                "is_replay": True,
            }
        }

        violations1 = pipeline.process_event(event)
        violations2 = pipeline.process_event(event)

        # No CRS003 violations because rule is suppressed
        crs003_violations = [v for v in violations1 + violations2 if v.rule_id == "CRS003"]
        assert len(crs003_violations) == 0

    def test_live_contract_detects_crs003(self):
        """GTFS live contract includes CRS003 duplicate detection."""
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        contract_path = PROJECT_ROOT / "config" / "contracts" / "gtfs_live.yaml"

        if not contract_path.exists():
            pytest.skip(f"Contract not found: {contract_path}")

        contract = DataContract.from_yaml(contract_path)

        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="gtfs",
            contract=contract,
        )

        # Verify CRS003 IS in registry
        all_rule_ids = [rule.rule_id for rule in pipeline.rule_registry.get_all_rules()]
        assert "CRS003" in all_rule_ids
