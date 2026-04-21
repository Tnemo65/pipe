"""
Tests for Context Registry.

Validates 5D context model (temporal, entity, spatial, source, policy).
"""
import pytest
from datetime import datetime
from streamdq.models.context_registry import ContextDimension


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
