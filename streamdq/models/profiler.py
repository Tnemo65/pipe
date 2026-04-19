"""
Data Quality Profiler — SchemaProfiler class.

Implements the "profiling" stage of the DQ process per Serra et al. (2022):
  profiling → measurement → analysis → cleaning → monitoring

SchemaProfiler runs before the monitoring pipeline starts. It computes:
- Field presence and null rates
- Data type inference
- Basic value distributions (min, max, cardinality)
- Quality issue pre-detection (constant fields, high-cardinality, etc.)

Usage:
    profiler = SchemaProfiler()
    profile = profiler.profile(dataframe)
    report = profiler.generate_report(profile)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class FieldProfile:
    """Profile for a single field."""
    name: str
    total_count: int
    null_count: int
    null_rate: float
    inferred_type: str
    unique_count: int
    cardinality: float
    # Numeric stats
    min_val: float | None = None
    max_val: float | None = None
    mean_val: float | None = None
    # String stats
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None
    # Quality flags
    is_constant: bool = False
    is_high_cardinality: bool = False
    is_low_variance: bool = False
    has_mixed_type: bool = False


@dataclass
class SchemaProfile:
    """Full dataset profile."""
    field_count: int
    total_rows: int
    timestamp: datetime = field(default_factory=datetime.now)
    fields: dict[str, FieldProfile] = field(default_factory=dict)
    overall_null_rate: float = 0.0
    quality_flags: list[str] = field(default_factory=list)


class SchemaProfiler:
    """
    Profile a dataset to understand its structure before monitoring.

    NG-30: Implements the profiling stage per Serra et al. (2022):
    "A Data Quality Taxonomy for Data Stream Processing"
    """

    HIGH_CARDINALITY_THRESHOLD = 0.5  # >50% unique = high cardinality
    LOW_VARIANCE_THRESHOLD = 0.01     # std/mean < 1% = low variance

    def profile(self, data: list[dict] | dict[str, list]) -> SchemaProfile:
        """
        Profile a dataset.

        Args:
            data: Either a list of dicts (records) or a dict of {field: [values]}

        Returns:
            SchemaProfile with per-field and overall statistics
        """
        if isinstance(data, list):
            return self._profile_records(data)
        elif isinstance(data, dict):
            first_val = next(iter(data.values()), [])
            if isinstance(first_val, list):
                return self._profile_columns(data)
        raise ValueError(
            "data must be list[dict] (records) or dict[str, list] (columns)"
        )

    def _profile_records(self, records: list[dict]) -> SchemaProfile:
        """Profile records (list of dicts)."""
        if not records:
            return SchemaProfile(field_count=0, total_rows=0)

        field_names = set()
        for r in records:
            field_names.update(r.keys())

        field_values: dict[str, list] = {f: [] for f in field_names}
        for r in records:
            for f in field_names:
                field_values[f].append(r.get(f))

        return self._profile_columns(field_values)

    def _profile_columns(self, columns: dict[str, list]) -> SchemaProfile:
        """Profile columns (dict of field -> values)."""
        n = len(next(iter(columns.values()), []))
        if n == 0:
            return SchemaProfile(field_count=len(columns), total_rows=0)

        field_profiles: dict[str, FieldProfile] = {}
        total_nulls = 0

        for field_name, values in columns.items():
            fp = self._profile_field(field_name, values, n)
            field_profiles[field_name] = fp
            total_nulls += fp.null_count

        quality_flags = self._detect_quality_issues(field_profiles)

        return SchemaProfile(
            field_count=len(columns),
            total_rows=n,
            fields=field_profiles,
            overall_null_rate=total_nulls / (len(columns) * n) if n > 0 else 0.0,
            quality_flags=quality_flags,
        )

    def _profile_field(
        self, name: str, values: list, n: int
    ) -> FieldProfile:
        """Build FieldProfile for a single field."""
        null_count = sum(1 for v in values if v is None)
        non_null = [v for v in values if v is not None]

        inferred_type = self._infer_type(non_null)
        unique_vals = set(non_null)
        unique_count = len(unique_vals)
        cardinality = unique_count / len(non_null) if non_null else 0.0

        # Numeric stats
        numeric_vals: list[float] = []
        str_vals: list[str] = []
        for v in non_null:
            try:
                numeric_vals.append(float(v))
            except (TypeError, ValueError):
                str_vals.append(str(v))

        min_val = min(numeric_vals) if numeric_vals else None
        max_val = max(numeric_vals) if numeric_vals else None
        mean_val = sum(numeric_vals) / len(numeric_vals) if numeric_vals else None

        lengths = [len(str(v)) for v in non_null]
        min_len = min(lengths) if lengths else None
        max_len = max(lengths) if lengths else None
        avg_len = sum(lengths) / len(lengths) if lengths else None

        # Quality flags
        is_constant = unique_count <= 1 and len(non_null) > 1
        is_high_cardinality = cardinality > self.HIGH_CARDINALITY_THRESHOLD

        is_low_variance = False
        if mean_val is not None and mean_val != 0:
            std = (sum((v - mean_val) ** 2 for v in numeric_vals) / len(numeric_vals)) ** 0.5
            is_low_variance = (std / abs(mean_val)) < self.LOW_VARIANCE_THRESHOLD

        has_mixed_type = len(numeric_vals) > 0 and len(str_vals) > 0

        return FieldProfile(
            name=name,
            total_count=n,
            null_count=null_count,
            null_rate=null_count / n,
            inferred_type=inferred_type,
            unique_count=unique_count,
            cardinality=cardinality,
            min_val=min_val,
            max_val=max_val,
            mean_val=mean_val,
            min_length=min_len,
            max_length=max_len,
            avg_length=avg_len,
            is_constant=is_constant,
            is_high_cardinality=is_high_cardinality,
            is_low_variance=is_low_variance,
            has_mixed_type=has_mixed_type,
        )

    @staticmethod
    def _infer_type(values: list) -> str:
        """Infer the type of a field from its values."""
        if not values:
            return "unknown"
        type_counts: dict[str, int] = {}
        for v in values:
            if isinstance(v, bool):
                t = "bool"
            elif isinstance(v, int):
                t = "int"
            elif isinstance(v, float):
                t = "float"
            else:
                t = "string"
            type_counts[t] = type_counts.get(t, 0) + 1
        dominant = max(type_counts, key=type_counts.get)
        if len(type_counts) > 1:
            return "mixed"
        return dominant

    def _detect_quality_issues(
        self, field_profiles: dict[str, FieldProfile]
    ) -> list[str]:
        """Detect overall quality issues across all fields."""
        flags: list[str] = []
        for fp in field_profiles.values():
            if fp.null_rate > 0.5:
                flags.append(f"HIGH_NULL: {fp.name} has {fp.null_rate:.1%} nulls")
            if fp.is_constant:
                flags.append(f"CONSTANT_FIELD: {fp.name} has only {fp.unique_count} unique value(s)")
            if fp.has_mixed_type:
                flags.append(f"MIXED_TYPE: {fp.name} contains mixed types")
            if fp.is_low_variance:
                flags.append(f"LOW_VARIANCE: {fp.name} has near-constant values (std/mean < 1%)")
        return flags

    def generate_report(self, profile: SchemaProfile) -> str:
        """Generate a human-readable profiling report."""
        lines = [
            "=" * 60,
            f"StreamDQ Schema Profile — {profile.timestamp.isoformat()}",
            f"{profile.total_rows:,} rows x {profile.field_count} fields",
            f"Overall null rate: {profile.overall_null_rate:.2%}",
            "=" * 60,
        ]
        if profile.quality_flags:
            lines.append("Quality Issues:")
            for flag in profile.quality_flags:
                lines.append(f"  [!] {flag}")
            lines.append("")

        lines.append("Field Profiles:")
        for name, fp in profile.fields.items():
            lines.append(f"  {name}:")
            lines.append(f"    type={fp.inferred_type}, null={fp.null_rate:.1%}, "
                         f"unique={fp.unique_count} ({fp.cardinality:.1%})")
            if fp.mean_val is not None:
                lines.append(f"    range=[{fp.min_val:.2g}, {fp.max_val:.2g}], mean={fp.mean_val:.2g}")
            elif fp.avg_length is not None:
                lines.append(f"    length=[{fp.min_length}, {fp.max_length}], avg={fp.avg_length:.1f}")

        return "\n".join(lines)
