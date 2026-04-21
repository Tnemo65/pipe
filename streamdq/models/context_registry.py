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
class ContextKey:
    """
    Hierarchical context key for threshold lookup.

    Hierarchy levels (for fallback):
    - Level 0: (hour, zone, weekend) — most specific
    - Level 1: (hour_bucket, zone, weekend)
    - Level 2: (hour_bucket, borough, weekend)
    - Level 3: (time_category)
    - Level 4: global
    """
    key_string: str
    level: int
    confidence: float  # 1.0 at level 0, decreases with fallback

    @classmethod
    def from_dict(cls, context: dict, level: int = 0) -> "ContextKey":
        """
        Generate context key at specified hierarchy level.

        Args:
            context: Context dict with dimensions
            level: Hierarchy level (0-4)

        Returns:
            ContextKey with key_string at specified level
        """
        if level == 4:
            # Global fallback
            return cls(key_string="global", level=4, confidence=0.5)

        parts = []

        # Temporal dimension
        hour = context.get("hour_of_day", 12)
        is_weekend = context.get("is_weekend", False)

        if level == 0:
            # Level 0: exact hour
            parts.append(f"hour_{hour}")
        elif level in (1, 2, 3):
            # Level 1+: hour bucket
            if 6 <= hour < 12:
                parts.append("morning")
            elif 12 <= hour < 18:
                parts.append("afternoon")
            elif 18 <= hour < 22:
                parts.append("evening")
            else:
                parts.append("night")

        # Spatial dimension
        if level == 0:
            # Level 0: zone category
            zone_cat = context.get("zone_category", "unknown")
            parts.append(zone_cat)
        elif level == 1:
            # Level 1: zone category (same as level 0)
            zone_cat = context.get("zone_category", "unknown")
            parts.append(zone_cat)
        elif level == 2:
            # Level 2: borough
            borough = context.get("borough", "unknown")
            parts.append(borough)
        # Level 3+: no spatial dimension

        # Weekend flag (level 0-2)
        if level <= 2:
            parts.append("weekend" if is_weekend else "weekday")

        key_string = "_".join(parts)

        # Confidence decreases with fallback level
        confidence = 1.0 - (level * 0.1)

        return cls(key_string=key_string, level=level, confidence=confidence)


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


class ContextRegistry:
    """
    Registry for context extraction and matching.

    Responsibilities:
    1. Load context dimension definitions from YAML
    2. Extract 5D context from events
    3. Generate hierarchical context keys for threshold lookup
    """

    def __init__(self, zone_map: Optional[dict] = None):
        """
        Initialize context registry.

        Args:
            zone_map: Mapping of location_id -> (zone_name, borough)
        """
        self.zone_map = zone_map or {}

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "ContextRegistry":
        """
        Load context registry from YAML config.

        Args:
            yaml_path: Path to YAML file with zone mappings

        Returns:
            ContextRegistry instance
        """
        try:
            with open(yaml_path) as f:
                config = yaml.safe_load(f)

            # Extract zone map
            zone_map = {}
            for entry in config.get("zones", []):
                location_id = entry["location_id"]
                zone_map[location_id] = (entry["zone_name"], entry["borough"])

            return cls(zone_map=zone_map)
        except FileNotFoundError:
            # Fallback to empty registry if config not found
            return cls(zone_map={})

    def resolve(self, event: dict) -> dict:
        """
        Extract full 5D context from event.

        Args:
            event: Event dict

        Returns:
            Context dict with all dimensions
        """
        context = {}

        # Extract each dimension
        context.update(ContextDimension.temporal(event))
        context.update(ContextDimension.spatial(event, zone_map=self.zone_map))
        context.update(ContextDimension.source(event))
        context.update(ContextDimension.entity(event))
        context.update(ContextDimension.policy(event))

        return context

    def match_key(self, context: dict, level: int = 0) -> str:
        """
        Generate context key string at specified hierarchy level.

        Args:
            context: Context dict from resolve()
            level: Hierarchy level (0-4)

        Returns:
            Context key string for threshold lookup
        """
        key = ContextKey.from_dict(context, level=level)
        return key.key_string
