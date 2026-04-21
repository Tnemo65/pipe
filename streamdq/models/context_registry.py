"""
Context Registry for StreamDQ.

Provides 5D context extraction (temporal, entity, spatial, source, policy)
for context-aware threshold adaptation.

References:
- ENHANCEMENT_ROADMAP.md: Phase 2, T6 (Formal Context Model)
- Target: Enable T7 context-keyed thresholds → +10-15 precision points
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any
import yaml


@dataclass
class ContextDimension:
    """
    Extracts a single dimension of context from an event.

    Dimensions:
    - temporal: hour_of_day, day_of_week, is_weekend, time_category, is_rush_hour
    - entity: entity_type, entity_id, payment_type
    - spatial: zone, borough, zone_category
    - source: source_id, source_type, is_replay
    - policy: contract_tier, owner, sla_targets
    """

    @staticmethod
    def temporal(event: dict) -> dict:
        """
        Extract temporal context from event.

        Args:
            event: Event dict with tpep_pickup_datetime or timestamp

        Returns:
            Dict with hour_of_day, day_of_week, is_weekend, time_category, is_rush_hour
        """
        # Parse timestamp
        ts_str = event.get("tpep_pickup_datetime") or event.get("timestamp")
        if isinstance(ts_str, str):
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        elif isinstance(ts_str, datetime):
            ts = ts_str
        else:
            # Default to now if no timestamp
            ts = datetime.now()

        hour = ts.hour
        dow = ts.weekday()  # 0=Monday, 6=Sunday

        # Time categories
        if 6 <= hour < 12:
            time_category = "morning"
        elif 12 <= hour < 18:
            time_category = "afternoon"
        elif 18 <= hour < 22:
            time_category = "evening"
        else:
            time_category = "night"

        # Rush hour: 7-10 AM or 4-7 PM on weekdays
        is_rush_hour = (dow < 5) and ((7 <= hour <= 10) or (16 <= hour <= 19))

        return {
            "hour_of_day": hour,
            "day_of_week": dow,
            "is_weekend": dow >= 5,
            "time_category": time_category,
            "is_rush_hour": is_rush_hour,
        }

    @staticmethod
    def spatial(event: dict, zone_map: Optional[dict] = None) -> dict:
        """
        Extract spatial context from event.

        Args:
            event: Event dict with PULocationID or lat/lon
            zone_map: Mapping of location_id -> (zone_name, borough)

        Returns:
            Dict with zone, borough, zone_category
        """
        location_id = event.get("PULocationID")

        if zone_map and location_id in zone_map:
            zone_name, borough = zone_map[location_id]
        else:
            zone_name = f"zone_{location_id}" if location_id else "unknown"
            borough = "unknown"

        # Zone categories (simplified)
        if "midtown" in zone_name.lower():
            zone_category = "midtown"
        elif "airport" in zone_name.lower():
            zone_category = "airport"
        elif borough == "Manhattan":
            zone_category = "manhattan_other"
        else:
            zone_category = "outer"

        return {
            "zone": zone_name,
            "borough": borough,
            "zone_category": zone_category,
        }

    @staticmethod
    def source(event: dict) -> dict:
        """
        Extract source context from event lineage.

        Args:
            event: Event dict with _lineage metadata

        Returns:
            Dict with source_id, source_type, is_replay
        """
        lineage = event.get("_lineage", {})

        return {
            "source_id": lineage.get("source_id", "unknown"),
            "source_type": lineage.get("source_type", "unknown"),
            "is_replay": lineage.get("is_replay", False),
        }

    @staticmethod
    def entity(event: dict) -> dict:
        """
        Extract entity context from event.

        Args:
            event: Event dict with entity_type, payment_type, etc.

        Returns:
            Dict with entity_type, payment_type
        """
        return {
            "entity_type": event.get("entity_type", "nyc_taxi"),
            "payment_type": event.get("payment_type", "unknown"),
        }

    @staticmethod
    def policy(event: dict) -> dict:
        """
        Extract policy context from event (placeholder for future).

        Args:
            event: Event dict with contract metadata

        Returns:
            Dict with contract_tier, owner
        """
        return {
            "contract_tier": event.get("_contract_tier", "BRONZE"),
            "owner": event.get("_owner", "unknown"),
        }
