"""Test YAML rules produce identical output to Python rules."""
import pytest
from pathlib import Path
from streamdq.config.rule_compiler import RuleCompiler
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
from streamdq.rules.base import RuleContext
from datetime import datetime


@pytest.mark.parametrize("rule_id,python_class,yaml_file", [
    ("SYN001", FareAmountRangeRule, "rules/nyc_taxi/syn001-fare-amount-range.yaml"),
    ("SYN002", PickupLocationValidRule, "rules/nyc_taxi/syn002-pickup-location-valid.yaml"),
    ("SYN003", TimestampNotFutureRule, "rules/nyc_taxi/syn003-timestamp-not-future.yaml"),
    ("SEM001", FareRangeRule, "rules/nyc_taxi/sem001-fare-range.yaml"),
    ("SEM002", TripDurationSanityRule, "rules/nyc_taxi/sem002-trip-duration-sanity.yaml"),
    ("SEM003", AverageSpeedSanityRule, "rules/nyc_taxi/sem003-average-speed-sanity.yaml"),
])
def test_rule_equivalence(rule_id, python_class, yaml_file):
    """YAML rule output matches Python rule output."""
    python_rule = python_class(rule_id)
    yaml_rule = RuleCompiler.compile_rule(Path(yaml_file))

    test_events = [
        {"fare_amount": 15.50, "trip_distance": 2.5, "trip_id": "test_1",
         "tpep_pickup_datetime": "2024-01-15T10:00:00", "PULocationID": 161},
        {"fare_amount": None, "trip_distance": 0.0, "trip_id": "test_2",
         "tpep_pickup_datetime": "2024-01-15T10:00:00", "PULocationID": None},
        {"fare_amount": -5.0, "trip_distance": 1.0, "trip_id": "test_3",
         "tpep_pickup_datetime": "2024-01-15T10:00:00", "PULocationID": 300},
        {"fare_amount": 1000.0, "trip_distance": 50.0, "trip_id": "test_4",
         "tpep_pickup_datetime": "2024-01-15T10:00:00", "PULocationID": 161},
    ]

    for event in test_events:
        ctx = RuleContext(
            event=event,
            event_time=datetime.now(),
            historical_stats={},
            external_context=None,
            start_time=0.0
        )

        python_result = python_rule.evaluate(ctx)
        yaml_result = yaml_rule.evaluate(ctx)

        # Both None or both Violations
        assert (python_result is None) == (yaml_result is None), \
            f"Mismatch for event {event}: Python={python_result}, YAML={yaml_result}"

        if python_result:
            assert python_result.rule_id == yaml_result.rule_id
            assert python_result.severity == yaml_result.severity


def test_completeness_rule_equivalence():
    """Completeness rule with parameters."""
    python_rule = CompletenessRule("SYN000", required_fields=["fare_amount", "PULocationID", "tpep_pickup_datetime"])
    yaml_rule = RuleCompiler.compile_rule(Path("rules/nyc_taxi/syn000-completeness.yaml"))

    test_events = [
        {"fare_amount": 15.50, "PULocationID": 161, "tpep_pickup_datetime": "2024-01-15T10:00:00", "trip_id": "t1"},
        {"fare_amount": None, "PULocationID": 161, "tpep_pickup_datetime": "2024-01-15T10:00:00", "trip_id": "t2"},
        {"PULocationID": 161, "trip_id": "t3"},
    ]

    for event in test_events:
        ctx = RuleContext(
            event=event,
            event_time=datetime.now(),
            historical_stats={},
            external_context=None,
            start_time=0.0
        )

        python_result = python_rule.evaluate(ctx)
        yaml_result = yaml_rule.evaluate(ctx)

        assert (python_result is None) == (yaml_result is None)
        if python_result:
            assert python_result.rule_id == yaml_result.rule_id
