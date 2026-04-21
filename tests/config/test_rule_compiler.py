"""Tests for RuleCompiler."""
import pytest
from pathlib import Path
from streamdq.config.rule_compiler import RuleCompiler
from streamdq.rules.syntactic import FareAmountRangeRule


def test_compile_rule_basic():
    """Compile simple static threshold rule."""
    yaml_path = Path("tests/fixtures/rules/syn001.yaml")
    rule = RuleCompiler.compile_rule(yaml_path)

    assert rule.rule_id == "SYN001"
    assert isinstance(rule, FareAmountRangeRule)
    assert rule.enabled is True


def test_compile_rule_missing_required_field():
    """Missing required field raises ValueError."""
    yaml_path = Path("tests/fixtures/rules/invalid_missing_id.yaml")

    with pytest.raises(ValueError, match="Missing required fields"):
        RuleCompiler.compile_rule(yaml_path)


def test_compile_rule_unknown_type():
    """Unknown rule type raises ValueError."""
    yaml_path = Path("tests/fixtures/rules/invalid_unknown_type.yaml")

    with pytest.raises(ValueError, match="Unknown rule type"):
        RuleCompiler.compile_rule(yaml_path)
