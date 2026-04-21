"""End-to-end test of YAML rules in full pipeline."""
import pytest
import pandas as pd
from pathlib import Path
from streamdq.pipeline.local_pipeline import LocalPipeline, NoOpViolationStore


def test_yaml_pipeline_e2e():
    """Full pipeline with YAML rules processes events correctly."""
    pipeline = LocalPipeline(
        violation_store=NoOpViolationStore(),
        entity_type="nyc_taxi"
    )

    # Test with synthetic events
    test_events = [
        {
            "trip_id": "test_001",
            "fare_amount": 15.50,
            "trip_distance": 2.5,
            "PULocationID": 161,
            "DOLocationID": 237,
            "tpep_pickup_datetime": "2024-01-15T10:00:00",
            "tpep_dropoff_datetime": "2024-01-15T10:15:00",
            "passenger_count": 1,
        },
        {
            "trip_id": "test_002",
            "fare_amount": None,  # Missing fare - should trigger SYN001
            "trip_distance": 1.0,
            "PULocationID": 100,
            "tpep_pickup_datetime": "2024-01-15T10:05:00",
        },
        {
            "trip_id": "test_003",
            "fare_amount": 25.00,
            "trip_distance": 3.0,
            "PULocationID": 300,  # Invalid location - should trigger SYN002
            "tpep_pickup_datetime": "2024-01-15T10:10:00",
        },
    ]

    violations = []
    for event in test_events:
        viols = pipeline.process_event(event)
        violations.extend(viols)

    # Verify basic functionality
    assert len(violations) > 0, "Should have some violations"

    # Verify YAML rules loaded
    rule_ids = [r.rule_id for r in pipeline.registry.get_all_rules()]
    assert "SYN000" in rule_ids, "SYN000 should be loaded from YAML"
    assert "SYN001" in rule_ids, "SYN001 should be loaded from YAML"
    assert "SYN002" in rule_ids, "SYN002 should be loaded from YAML"
    assert "SEM001" in rule_ids, "SEM001 should be loaded from YAML"

    # Verify stateful rules also present
    assert "CRS001" in rule_ids or "CRS003" in rule_ids, "Stateful rules should be present"

    # Verify rules actually fire
    violation_rule_ids = [v.rule_id for v in violations]
    # Should have syntactic violations from bad data
    assert any(rule_id.startswith("SYN") for rule_id in violation_rule_ids), \
        "Should have syntactic violations"


def test_yaml_pipeline_contract_filtering():
    """Contract filtering works with YAML rules."""
    from streamdq.models.contract import DataContract

    contract = DataContract.from_yaml("config/contracts/nyc_taxi_replay.yaml")

    pipeline = LocalPipeline(
        violation_store=NoOpViolationStore(),
        contract=contract,
        entity_type="nyc_taxi"
    )

    rule_ids = [r.rule_id for r in pipeline.registry.get_all_rules()]

    # CRS003 suppressed in replay contract
    assert "CRS003" not in rule_ids, "CRS003 should be suppressed by contract"

    # SYN001 required in replay contract
    assert "SYN001" in rule_ids, "SYN001 should be required by contract"


def test_yaml_gtfs_pipeline():
    """GTFS pipeline loads GTFS-specific YAML rules."""
    pipeline = LocalPipeline(
        violation_store=NoOpViolationStore(),
        entity_type="gtfs_vehicle"
    )

    rule_ids = [r.rule_id for r in pipeline.registry.get_all_rules()]

    # Verify GTFS rules loaded
    assert "GTFSSyn001" in rule_ids, "GTFSSyn001 should be loaded"
    assert "GTFSSyn002" in rule_ids, "GTFSSyn002 should be loaded"
    assert "GTFSSyn003" in rule_ids, "GTFSSyn003 should be loaded"
    assert "GTFSSem001" in rule_ids, "GTFSSem001 should be loaded"
    assert "GTFSSem002" in rule_ids, "GTFSSem002 should be loaded"

    # Verify GTFS stateful rules present
    assert "GTFSCRS001" in rule_ids or "GTFSCRS002" in rule_ids, \
        "GTFS stateful rules should be present"
