"""
Tests for Context Registry.

Validates 5D context model (temporal, entity, spatial, source, policy).
"""
import pytest
from datetime import datetime
from streamdq.models.context_registry import ContextDimension, ContextKey, ContextRegistry


class TestContextDimension:
    """Test context dimension extraction."""

    def test_temporal_dimension_extraction(self):
        """Extract hour_of_day, day_of_week, is_weekend from timestamp."""
        event = {
            "tpep_pickup_datetime": "2024-01-15T10:30:00",  # Monday 10:30 AM
        }

        dim = ContextDimension.temporal(event)

        assert dim["hour_of_day"] == 10
        assert dim["day_of_week"] == 0  # Monday
        assert dim["is_weekend"] is False
        assert dim["time_category"] == "morning"
        assert dim["is_rush_hour"] is True  # 7-10 AM or 4-7 PM

    def test_spatial_dimension_extraction(self):
        """Extract zone, borough from pickup location."""
        event = {
            "PULocationID": 161,  # Midtown Center
        }

        # Need zone mapping table
        dim = ContextDimension.spatial(event, zone_map={161: ("Midtown Center", "Manhattan")})

        assert dim["zone"] == "Midtown Center"
        assert dim["borough"] == "Manhattan"
        assert dim["zone_category"] == "midtown"

    def test_source_dimension_extraction(self):
        """Extract source_id, source_type from lineage."""
        event = {
            "_lineage": {
                "source_id": "nyc_taxi_2024_01",
                "source_type": "batch_replay",
                "is_replay": True
            }
        }

        dim = ContextDimension.source(event)

        assert dim["source_id"] == "nyc_taxi_2024_01"
        assert dim["source_type"] == "batch_replay"
        assert dim["is_replay"] is True


class TestContextKey:
    """Test context key generation and hierarchy."""

    def test_context_key_full_specification(self):
        """Full context key includes all 5 dimensions."""
        context = {
            "hour_of_day": 10,
            "is_weekend": False,
            "zone_category": "midtown",
            "borough": "Manhattan",
            "source_type": "api_poll",
        }

        key = ContextKey.from_dict(context, level=0)

        assert key.level == 0
        assert "hour_10" in key.key_string
        assert "weekday" in key.key_string
        assert "midtown" in key.key_string

    def test_context_key_hierarchy_levels(self):
        """Context key supports 5 hierarchy levels for fallback."""
        context = {
            "hour_of_day": 10,
            "is_weekend": False,
            "zone_category": "midtown",
            "borough": "Manhattan",
        }

        # Level 0: most specific (hour, zone, weekend)
        key_l0 = ContextKey.from_dict(context, level=0)
        assert "hour_10" in key_l0.key_string
        assert "midtown" in key_l0.key_string

        # Level 1: hour bucket, zone, weekend
        key_l1 = ContextKey.from_dict(context, level=1)
        assert "morning" in key_l1.key_string  # hour 10 → morning bucket

        # Level 2: hour bucket, borough, weekend
        key_l2 = ContextKey.from_dict(context, level=2)
        assert "Manhattan" in key_l2.key_string
        assert "midtown" not in key_l2.key_string

        # Level 3: time category only
        key_l3 = ContextKey.from_dict(context, level=3)
        assert "morning" in key_l3.key_string
        assert "Manhattan" not in key_l3.key_string

        # Level 4: global (no dimensions)
        key_l4 = ContextKey.from_dict(context, level=4)
        assert key_l4.key_string == "global"


class TestContextRegistry:
    """Test context resolution from events."""

    def test_resolve_nyc_taxi_event(self):
        """Resolve NYC Taxi event to full context dict."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")

        event = {
            "tpep_pickup_datetime": "2024-01-15T10:30:00",  # Monday 10:30 AM
            "PULocationID": 161,  # Midtown
            "payment_type": "credit_card",
            "_lineage": {
                "source_id": "nyc_taxi_2024_01",
                "source_type": "batch_replay",
            }
        }

        context = registry.resolve(event)

        # Check all 5 dimensions populated
        assert "hour_of_day" in context
        assert context["hour_of_day"] == 10
        assert "zone_category" in context
        assert "source_type" in context

    def test_match_key_level0(self):
        """match_key returns level-0 context key."""
        registry = ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")

        context = {
            "hour_of_day": 10,
            "is_weekend": False,
            "zone_category": "midtown",
        }

        key = registry.match_key(context, level=0)

        assert isinstance(key, str)
        assert "hour_10" in key or "morning" in key
        assert "midtown" in key
