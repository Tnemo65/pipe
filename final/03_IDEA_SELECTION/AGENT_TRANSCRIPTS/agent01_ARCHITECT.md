# ARCHITECT Agent Report: Context-Aware Upgrade Evaluation

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Phase**: Step 3B — Architect (Context-Aware Deconstruction & Upgrade Scoring)
**Date**: April 22, 2026
**Agent**: ARCHITECT
**Input**: Orchestrator's critical code finding — ContextAware-DQ already has partial context-aware infrastructure
**Output**: `final/AGENT_TRANSCRIPTS_03B/agent01_ARCHITECT.md`

---

## Executive Summary

**Central Finding**: The context-aware upgrade is NOT about building context-awareness from scratch. The ContextAware-DQ codebase already contains a complete context-aware infrastructure: `ContextAwareAdaptiveThresholdEngine` (5-level hierarchical fallback), `ContextRegistry` (5D context extraction), `ExternalContext` (Dey 2001 formal 4D model), and `AdaptiveThresholdEngine` (Shannon entropy + bootstrap CI). What is MISSING is the **integration** of this infrastructure into the TQS layer and the rules engine.

**Key Numbers**:
- ContextAware-DQ currently scores **9/12** on the thesis title fit
- IDEA-NEW-2 alone scores **1/3** on Context-Aware dimension
- IDEA-NEW-2 + IDEA-05 (Contextual Calibration) together score **3/3** on Context-Aware
- Upgrade target: **12/12** — fully realize the "Context-Aware Framework" promise

**Path to 12/12**: IDEA-NEW-2 (TQS integration) + IDEA-05 (Contextual Calibration) + integration engineering = 12/12. The TQS layer decomposes quality scores by context cell. The contextual calibration connects adaptive thresholds to rules. The framework is context-aware at every layer.

---

## Context-Aware Decomposition (5 Dimensions)

### Dimension 1: TEMPORAL CONTEXT

**What it means**: Time-of-day, day-of-week, and derived temporal properties that affect what "valid" data looks like. Rush hour taxi trips have different fare distributions than late-night trips. A trip at 3 AM that would be suspicious at noon is normal.

**Examples**:
- Hour of day (0-23)
- Day of week (Mon-Sun)
- Is weekend (Sat/Sun flag)
- Is rush hour (7-10 AM or 4-7 PM on weekdays)
- Is late night (10 PM - 5 AM)
- Is holiday (NYC TLC has holiday surcharges)
- Time category (morning/afternoon/evening/night buckets)

**IDEA-NEW-2 (TQS Integration)**: PARTIAL. T-Assess provides quality dimensions but does NOT decompose scores by temporal context by default. The integration could include temporal context decomposition as a feature. T-Assess's statistical approach computes quality scores globally; decomposition by time-of-day would require aggregating violations within temporal cells.

**IDEA-05 (Contextual Calibration)**: YES. Contextual calibration is fundamentally about temporal context. The method explicitly calibrates thresholds by temporal context cells (rush hour vs. late night vs. weekend). This is the primary contribution of IDEA-05.

**ContextAware-DQ Existing Code**: YES — already implemented. `ExternalContext` in `base.py` (lines 17-100) extracts: `when_hour`, `when_day`, `is_rush_hour`, `is_late_night`, `is_weekend`, `is_holiday`. `ContextDimension.temporal()` in `context_registry.py` (lines 111-153) extracts: `hour_of_day`, `day_of_week`, `is_weekend`, `time_category`, `is_rush_hour`. SEM rules (`semantic.py`) already use these: `FareRangeRule` applies multipliers (1.3x rush hour, 0.7x late night, 1.15x weekend, 1.5x holiday). `TripDurationSanityRule` expands max duration by 1.5x during rush hour and 1.2x on weekends. `AverageSpeedSanityRule` adjusts max speed by +15 mph at night and -5 mph during rush hour.

**Gap**: Temporal context extraction exists AND is used by rules, but thresholds are NOT context-adaptive (they use hardcoded multipliers, not data-driven contextual thresholds from `ContextAwareAdaptiveThresholdEngine`).

---

### Dimension 2: SPATIAL CONTEXT

**What it means**: Geographic location and its derived properties. Midtown Manhattan trips have different fare distributions than airport trips or outer borough trips. A $50 fare is suspicious in the outer boroughs but normal at JFK.

**Examples**:
- Zone (263 NYC TLC zones, e.g., "Midtown Center", "JFK Airport")
- Borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island, EWR)
- Zone category (midtown, airport, manhattan_other, outer)
- Latitude/longitude bounds
- Route characteristics (highway vs. urban, express vs. local)

**IDEA-NEW-2 (TQS Integration)**: PARTIAL. T-Assess computes trajectory-level quality scores. Spatial decomposition would require aggregating violations by spatial cells. The current TQS approach does not inherently decompose by zone; the integration could add spatial cell decomposition as a feature.

**IDEA-05 (Contextual Calibration)**: YES. Spatial context is a primary dimension of contextual calibration. Thresholds for `fare_amount` should differ by zone category (midtown vs. airport vs. outer). IDEA-05's calibration method explicitly uses spatial context cells.

**ContextAware-DQ Existing Code**: YES — partially implemented. `ContextDimension.spatial()` in `context_registry.py` (lines 155-189) extracts: `zone` (zone name), `borough`, `zone_category` (midtown/airport/manhattan_other/outer). The `zone_map` parameter enables mapping location IDs to zone names and boroughs. `ContextKey` hierarchy levels 0-2 include spatial dimensions: L0 = (hour, zone_category, weekend), L1 = (hour_bucket, zone_category, weekend), L2 = (hour_bucket, borough, weekend). `ContextAwareAdaptiveThresholdEngine` maintains separate threshold buffers per context key including spatial dimensions.

**Gap**: `ContextRegistry` can extract spatial context, and `ContextAwareAdaptiveThresholdEngine` can store per-spatial-context thresholds, but NO rules currently USE these adaptive spatial thresholds. All spatial context in rules is through hardcoded zone category strings, not adaptive data-driven thresholds.

---

### Dimension 3: OPERATIONAL CONTEXT

**What it means**: The operational characteristics of the trip or vehicle that affect what "valid" means. Yellow taxis, green taxis, and FHV (ride-hailing) have different fare structures and trip patterns. Passenger count affects fare合理性. Airport trips have surcharges.

**Examples**:
- Vehicle type (yellow taxi, green taxi, FHV)
- Payment type (card vs. cash — card payments are more reliable)
- Passenger count (1-9, affects fare calculation)
- Trip distance (long trips have different fare ranges)
- Trip type (airport, street hail, dispatch)

**IDEA-NEW-2 (TQS Integration)**: NO. T-Assess trajectory quality scoring does not inherently incorporate operational context dimensions. The quality dimensions (validity, completeness, consistency, fairness) are computed across all data, not disaggregated by vehicle type or payment method.

**IDEA-05 (Contextual Calibration)**: PARTIAL. IDEA-05 focuses on temporal and spatial calibration. Operational context (vehicle type, passenger load) is less central to the method as described.

**ContextAware-DQ Existing Code**: PARTIAL. `ContextDimension.entity()` in `context_registry.py` (lines 210-224) extracts: `entity_type` (nyc_taxi, gtfs_vehicle), `payment_type`. However, NO rules currently use operational context for adaptive threshold adjustment. Rules use operational fields directly (e.g., `trip_distance` in `FareRangeRule` for distance-based fare scaling) but not as context dimensions for threshold adaptation.

**Gap**: Operational context extraction exists in the registry but is NOT used by any rules for adaptive thresholding. The `payment_type` field is extracted but never used in any rule evaluation.

---

### Dimension 4: EXTERNAL CONTEXT

**What it means**: Context from outside the data stream itself — weather, traffic incidents, special events (NYC Marathon, New Year's Eve), construction, transit disruptions. These external factors affect what "valid" data looks like. A 2-hour trip during the NYC Marathon is plausible; the same trip at normal times is suspicious.

**Examples**:
- Weather conditions (rain, snow — affects traffic and trip duration)
- Traffic incidents (accidents, construction)
- Special events (NYC Marathon, Macy's Thanksgiving Parade, New Year's Eve)
- Road closures or transit disruptions
- Surge pricing periods

**IDEA-NEW-2 (TQS Integration)**: NO. T-Assess does not incorporate external context signals. Quality scores are computed from data characteristics alone, not from external event calendars or weather APIs.

**IDEA-05 (Contextual Calibration)**: NO. The method as described uses only temporal and spatial context dimensions. External context (weather, events) would require API integration and is outside the scope of threshold calibration.

**ContextAware-DQ Existing Code**: PARTIAL. `ExternalContext` in `base.py` includes `is_holiday` (boolean), but this is derived from the event timestamp itself, not from an external calendar or weather API. `FareRangeRule` uses `is_holiday` to expand fare bounds (0.8x min, 1.5x max). However, there is NO integration with external event calendars, weather APIs, or traffic feeds.

**Gap**: External context is the most underdeveloped dimension. Only `is_holiday` is supported, and it is hardcoded (derived from the event timestamp, not from an external calendar). Weather, traffic, and special events are not modeled at all.

---

### Dimension 5: DATA CHARACTERISTICS CONTEXT

**What it means**: Properties of the data stream itself that affect validation strategy. Update frequency (30s for GTFS-RT vs. trip-level for NYC TLC), sample rate, sensor quality, data lineage (replay vs. live), and source reliability all affect how rules should be applied.

**Examples**:
- Source type (replay vs. live stream)
- Update frequency (30s GTFS-RT, trip-level NYC TLC)
- Sample rate variability
- Sensor quality indicators
- Data freshness (how old is this record?)
- Kafka offset / batch ID for deduplication confidence

**IDEA-NEW-2 (TQS Integration)**: PARTIAL. T-Assess computes quality scores for trajectory data. Data characteristics (update frequency, sample rate) affect trajectory completeness and could be incorporated into quality scoring. The integration could include data characteristics as a quality dimension.

**IDEA-05 (Contextual Calibration)**: NO. Data characteristics context is orthogonal to temporal/spatial calibration. Not part of the method.

**ContextAware-DQ Existing Code**: YES — implemented. `ContextDimension.source()` in `context_registry.py` (lines 191-208) extracts: `source_id`, `source_type`, `is_replay`. CRS003 (`evaluate_duplicate_event` in `cross_record.py`, lines 304-311) explicitly suppresses duplicate detection for replay streams (`if lineage.get("is_replay", False): return None`). The `ContextAwareDuplicateAdjudicator` uses `source_id`, `batch_id`, and `kafka_offset` for duplicate confidence scoring. Policy context (`ContextDimension.policy()`, lines 226-240) extracts `contract_tier` and `owner` from event metadata.

**Gap**: Data characteristics context is well-implemented for lineage tracking and duplicate detection, but NOT used for adaptive thresholding. The `source_type` and `is_replay` flags affect rule behavior (suppressing CRS003 for replay), but do not affect threshold values.

---

## Existing Ideas Context-Aware Scoring

### Scoring Table

| Dimension | IDEA-NEW-2 (TQS) | IDEA-05 (Contextual) | IDEA-02 (Physics) | IDEA-07 (Benchmark) |
|-----------|:-----------------:|:--------------------:|:-----------------:|:-------------------:|
| **D1: Temporal** | PARTIAL | **YES** | PARTIAL | NO |
| **D2: Spatial** | PARTIAL | **YES** | PARTIAL | NO |
| **D3: Operational** | NO | PARTIAL | **YES** | NO |
| **D4: External** | NO | NO | NO | NO |
| **D5: Data Char** | PARTIAL | NO | NO | NO |
| **Context-Aware Score** | **1/5** | **2.5/5** | **1.5/5** | **0/5** |

### Detailed Scoring Rationale

**IDEA-NEW-2 (TQS Integration)** — 1/5 = PARTIAL
- Temporal: PARTIAL. T-Assess computes quality scores but does not decompose by time-of-day by default. Integration could add temporal cell decomposition.
- Spatial: PARTIAL. Same — T-Assess computes trajectory-level scores, spatial decomposition requires integration design decision.
- Operational: NO. Vehicle type, payment type, passenger count are not quality dimensions in T-Assess.
- External: NO. Weather, traffic, special events are not incorporated.
- Data Char: PARTIAL. Data lineage (replay vs. live) affects quality interpretation but is not a quality dimension.

**IDEA-05 (Contextual Calibration)** — 2.5/5 = YES/PARTIAL
- Temporal: YES. Core contribution — calibrates thresholds by temporal context cells (rush hour, late night, weekend).
- Spatial: YES. Primary dimension — calibrates by zone category (midtown, airport, outer).
- Operational: PARTIAL. Vehicle type and passenger count are not primary calibration dimensions but could be added.
- External: NO. No external event/weather integration.
- Data Char: NO. Not part of the method.

**IDEA-02 (Physics-Constrained Calibration)** — 1.5/5 = PARTIAL
- Temporal: PARTIAL. Physics constraints are time-invariant (no vehicle exceeds 200 km/h regardless of time), but threshold calibration could use temporal context for finer-grained bounds.
- Spatial: PARTIAL. Physics constraints are location-dependent (highway speeds differ from urban speeds), spatial context could refine physics bounds.
- Operational: YES. Physics constraints are fundamentally about operational context — speed limits, acceleration profiles, passenger load affects vehicle dynamics.
- External: NO. Weather affects physics (rain reduces traction, affects braking distance) but is not part of the method.
- Data Char: NO. Not part of the method.

**IDEA-07 (Benchmark)** — 0/5 = NO
- A benchmark evaluates framework performance. It is orthogonal to context-awareness. The benchmark could MEASURE context-aware performance, but the idea itself does not ADD context-awareness.

---

## What ContextAware-DQ Already Has

The orchestrator's critical finding changes everything: context-aware infrastructure is NOT a gap to be filled — it is infrastructure to be INTEGRATED.

### Infrastructure Layer 1: `ContextAwareAdaptiveThresholdEngine` (`context_adaptive.py`)

**What it does**: Stores rolling statistics per (field, context_key) instead of globally. Maintains separate P10/P90/etc. thresholds for each context cell. Supports 5-level hierarchical fallback (L0 most specific → L4 global).

**Hierarchy levels** (from `ContextKey.from_dict()`, `context_registry.py` lines 34-94):
```
L0: (hour, zone_category, weekend)    → e.g., "hour_10_midtown_weekday"   [most specific]
L1: (hour_bucket, zone_category, weekend) → e.g., "morning_midtown_weekday"
L2: (hour_bucket, borough, weekend)  → e.g., "morning_Manhattan_weekday"
L3: (time_category)                   → e.g., "morning"                   [most general, non-spatial]
L4: global                           → "global"                          [fallback]
```

**Key method**: `get_threshold_with_fallback(field, percentile, event)` returns `{"value": 45.5, "level": 0, "context_key": "hour_10_midtown_weekday"}`. Tries L0 first; if insufficient samples (< min_sample_size=100), falls back to L1, L2, L3, L4.

**What it already does**: Computes P10, P25, P50, P75, P90, P95, P99, mean, std, min, max per context cell. Updates ALL hierarchy levels per event (line 111: `for level in range(5)`).

**What it does NOT do**: It is never called by any rule. Rules use `ctx.historical_stats` from the non-context-aware `AdaptiveThresholdEngine`, not from this engine.

### Infrastructure Layer 2: `ContextRegistry` (`context_registry.py`)

**What it does**: Extracts 5D context from events. Provides `resolve(event) → dict` and `match_key(context, level) → str`.

**Dimensions extracted**:
1. Temporal: `hour_of_day`, `day_of_week`, `is_weekend`, `time_category`, `is_rush_hour`
2. Spatial: `zone`, `borough`, `zone_category`
3. Source: `source_id`, `source_type`, `is_replay`
4. Entity: `entity_type`, `payment_type`
5. Policy: `contract_tier`, `owner`

**What it already does**: Hierarchical key generation at 5 levels. YAML-based zone mapping. Temporal/rush-hour/late-night detection.

**What it does NOT do**: It is never instantiated by the pipeline. Rules never call `ContextRegistry.resolve(event)`.

### Infrastructure Layer 3: `ExternalContext` (`base.py`, lines 17-100)

**What it does**: Formal 4D context model (Dey 2001 / Serra 2022). Dimensions: WHO (consumer), WHAT (entity), WHEN (temporal), WHERE (spatial). Embedded in `RuleContext.external_context`.

**What it already does**: Auto-detection from event timestamp (`from_event()` classmethod): `when_hour`, `when_day`, `is_rush_hour`, `is_late_night`, `is_weekend`, `is_holiday`. Spatial from event (`where_region`, `where_zone`).

**What it does NOT do**: `RuleContext.external_context` is set by the pipeline but rules that USE it (only `semantic.py` rules) use hardcoded multipliers instead of adaptive thresholds from `ContextAwareAdaptiveThresholdEngine`.

### Infrastructure Layer 4: `AdaptiveThresholdEngine` (`adaptive.py`)

**What it does**: Global rolling statistics (non-context-aware). Bootstrap CI on P10/P90 (NG-36). Shannon entropy for drift detection (NG-35).

**What it already does**: Computes 13 statistics per field. Supports human overrides. LRU eviction of idle fields. Entropy-based early warning.

**What it does NOT do**: It is context-agnostic. All thresholds are global per field, not per context cell.

### Infrastructure Layer 5: Rule-Level Context Usage (`semantic.py`)

**What exists**: `FareRangeRule` uses `ctx.get_external("is_rush_hour")`, `is_late_night`, `is_weekend`, `is_holiday` to apply HARDCODED multipliers to thresholds (1.3x rush hour, 0.7x late night, 1.15x weekend, 0.8x/1.5x holiday). `TripDurationSanityRule` uses `is_rush_hour` and `is_weekend` for hardcoded duration multipliers (1.5x rush hour, 1.2x weekend). `AverageSpeedSanityRule` uses `is_rush_hour` and `is_late_night` for hardcoded speed adjustments (+15 mph night, -5 mph rush hour).

**The gap**: Rules ACCESS context but do not USE `ContextAwareAdaptiveThresholdEngine`. They apply hardcoded multipliers instead of data-driven contextual thresholds. The difference: hardcoded multipliers are static; adaptive contextual thresholds learn from data within each context cell.

### Infrastructure Summary Table

| Component | Status | Used by Rules? | Used by Pipeline? |
|-----------|:------:|:--------------:|:-----------------:|
| `ContextAwareAdaptiveThresholdEngine` | IMPLEMENTED | **NO** | NO |
| `ContextRegistry` | IMPLEMENTED | **NO** | NO |
| `ExternalContext` (Dey 2001) | IMPLEMENTED | PARTIAL (semantic.py only) | YES |
| `AdaptiveThresholdEngine` (entropy/CI) | IMPLEMENTED | YES (but context-agnostic) | YES |
| `ContextDimension.temporal()` | IMPLEMENTED | **NO** | NO |
| `ContextDimension.spatial()` | IMPLEMENTED | **NO** | NO |
| `ContextDimension.source()` | IMPLEMENTED | YES (CRS003 only) | YES |
| `ContextDimension.entity()` | IMPLEMENTED | **NO** | NO |
| `ContextDimension.policy()` | IMPLEMENTED | **NO** | NO |

---

## What Is Missing

### Gap 1: Context-Aware Thresholds Not Integrated into Rules

**Problem**: `ContextAwareAdaptiveThresholdEngine` is implemented but never called. Rules use `ctx.historical_stats` from the non-context-aware engine.

**Impact**: All adaptive thresholds are global. A $50 fare is evaluated against the global P90 across all NYC TLC data, not against the P90 for (rush_hour, midtown, weekday) specifically.

**Evidence**: `semantic.py` line 67-77: `fare_stats = ctx.historical_stats.get("fare_amount", {})`. This dict comes from `AdaptiveThresholdEngine.get_stats()`, not from `ContextAwareAdaptiveThresholdEngine.get_threshold_with_fallback()`. The `RuleContext` is constructed with `historical_stats: dict[str, dict]` (a flat global dict), not with a `ContextAwareAdaptiveThresholdEngine` instance.

**Required fix**: Pass `ContextAwareAdaptiveThresholdEngine` (or a wrapper) to `RuleContext`. Modify semantic rules to call `engine.get_threshold_with_fallback(field, percentile, event)` instead of reading from `ctx.historical_stats`.

### Gap 2: TQS Layer Does Not Decompose Scores by Context Cell

**Problem**: T-Assess computes trajectory quality scores at the trajectory level. IDEA-NEW-2 proposes mapping rule violations to quality dimensions, but does not specify decomposition by context cell.

**Impact**: Quality scores are not explainable by context. A low quality score could be explained by "rush hour in midtown has high violation rates" or "weekend outer borough data is noisier." Without context decomposition, the score cannot distinguish these.

**Required fix**: TQS integration must aggregate violations within context cells. The quality score per trajectory should be annotated with the context key (e.g., "rush_hour_midtown_weekday"). The evaluation should report TQS degradation curves per context cell.

### Gap 3: No Context-Aware Quality Reporting

**Problem**: Violations are reported individually with context metadata (e.g., `is_rush_hour: True`), but there is no aggregate quality reporting by context.

**Impact**: Operators cannot answer "Why is quality low right now?" The answer requires aggregating violations by context cell and comparing to expected rates.

**Required fix**: Add a quality reporting layer that computes violation rates per context cell (using the same hierarchy as `ContextAwareAdaptiveThresholdEngine`). Compare current violation rates to historical rates for the same context cell. Report anomalous context cells.

### Gap 4: Context Registry Not Instantiated by Pipeline

**Problem**: `ContextRegistry` is implemented but never used. The pipeline constructs `ExternalContext` from event metadata directly, bypassing the full 5D context extraction.

**Impact**: `where_region`, `where_zone`, `data_steward`, `consumer_profile`, `use_case`, `pipeline_stage`, `pipeline_id` are all set to "unknown" defaults. Only temporal context is auto-detected from the event timestamp.

**Required fix**: Instantiate `ContextRegistry` in the pipeline. Call `registry.resolve(event)` to populate full 5D context. Pass to `RuleContext.external_context`.

### Gap 5: No External Context Integration

**Problem**: External context (weather, traffic, special events) is not modeled at all.

**Impact**: During the NYC Marathon or heavy rain, data quality degrades for legitimate reasons. Without external context, the system cannot distinguish "data quality problem" from "data quality reflects real-world conditions."

**Required fix**: Integrate external event calendar (holidays, major events) and optionally weather/traffic APIs. Map external context to threshold adjustments. This is a future enhancement, not part of the minimum viable upgrade.

---

## Updated Name Fit Scores

### Before Integration (IDEA-NEW-2 Alone)

| Component | Score | Rationale |
|-----------|:-----:|-----------|
| Streaming | 3/3 | T-Assess + ContextAware-DQ both process streaming data. Closed-loop monitoring pipeline. |
| Data Quality | 3/3 | SYN/SEM/CRS rules detect violations. TQS aggregates violations into quality scores. |
| Framework | 2/3 | TQS layer + ContextAware-DQ rules + dimension mapper = framework. But context-awareness is absent. |
| Context-Aware | 1/3 | T-Assess computes quality scores but does NOT decompose by context. Rules use temporal context but not adaptive contextual thresholds. |
| **TOTAL** | **9/12** | |

### After Integration (IDEA-NEW-2 + IDEA-05 + Integration Engineering)

| Component | Before | After | Evidence |
|-----------|:------:|:-----:|----------|
| Streaming | 3/3 | 3/3 | Unchanged — both systems are streaming-native |
| Data Quality | 3/3 | 3/3 | Unchanged — rules + TQS still detect and score violations |
| Framework | 2/3 | **3/3** | Context-aware threshold engine + context registry + TQS decomposition = full framework |
| Context-Aware | 1/3 | **3/3** | IDEA-05 provides contextual calibration; integration connects adaptive thresholds to rules; TQS decomposes by context cell |
| **TOTAL** | **9/12** | **12/12** | |

### Evidence for Framework Dimension Upgrade (2/3 → 3/3)

A "Framework" scores 3/3 when it has:
1. Multiple interacting components — YES. ContextAware-DQ rules + TQS aggregation + dimension mapper + confidence scorer + context-aware threshold engine + context registry.
2. Shared data models and interfaces — YES. `RuleContext`, `Violation`, `ExternalContext`, `ContextKey`, `FieldStats`.
3. Emergent properties from integration — YES. The combination detects things neither system detects alone. Context-aware thresholds learn from data within each cell. TQS explains quality degradation by context. This emergent behavior is the key research contribution.

### Evidence for Context-Aware Dimension Upgrade (1/3 → 3/3)

A "Context-Aware" scores 3/3 when:
1. Context extraction from events — YES. `ContextRegistry.resolve()` extracts 5D context (temporal, spatial, operational, external, data characteristics).
2. Context used for adaptive behavior — YES. `ContextAwareAdaptiveThresholdEngine.get_threshold_with_fallback()` provides data-driven thresholds per context cell.
3. Quality reporting by context — YES (required addition). TQS decomposition by context cell + context-aware quality reporting answers "Why is quality low?"

The integration of IDEA-NEW-2 + IDEA-05 activates all three. IDEA-05 activates (2). TQS decomposition by context cell activates (3). `ContextRegistry` provides (1).

---

## Required Additions Summary

### Minimum Viable Context-Aware Upgrade (12/12 Target)

The following additions are REQUIRED to achieve 12/12:

#### Addition 1: Connect `ContextAwareAdaptiveThresholdEngine` to Rules (P1)

**What**: Pass `ContextAwareAdaptiveThresholdEngine` instance to `RuleContext`. Modify `FareRangeRule`, `TripDurationSanityRule`, and `AverageSpeedSanityRule` to call `engine.get_threshold_with_fallback(field, percentile, event)` instead of reading from `ctx.historical_stats`.

**Effort**: ~2 days. Modify `RuleContext` dataclass to include `context_aware_engine: Optional[ContextAwareAdaptiveThresholdEngine] = None`. Add a helper method `ctx.get_contextual_threshold(field, percentile)` that delegates to the engine. Modify semantic rules to use the new method.

**Impact**: Rules now use data-driven contextual thresholds instead of hardcoded multipliers. Estimated +10-15 precision points on semantic rules (per ENHANCEMENT_ROADMAP.md T7).

#### Addition 2: TQS Decomposition by Context Cell (P1)

**What**: Extend TQS aggregation to compute quality scores per context key. The output of TQS should include: trajectory quality score + context_key + violation rate within context cell.

**Effort**: ~1 week. Modify TQS aggregation function to group violations by context cell before computing quality dimensions. Add context_key to output schema.

**Impact**: Quality scores are now explainable by context. Operators can see "midtown rush-hour quality is 0.72, outer-borough weekend quality is 0.91."

#### Addition 3: Instantiate `ContextRegistry` in Pipeline (P2)

**What**: Create `ContextRegistry` instance in `LocalPipeline` and `SparkPipeline`. Call `registry.resolve(event)` for each event. Pass resolved context to `RuleContext.external_context`.

**Effort**: ~2 days. Add registry initialization to pipeline. Add `resolve()` call in event processing loop. Update `RuleContext` construction.

**Impact**: Full 5D context (temporal, spatial, operational, external, data characteristics) is available to rules and TQS layer.

#### Addition 4: Context-Aware Quality Reporting (P2)

**What**: Add aggregate quality reporting that computes violation rates per context cell. Compare current rates to historical rates for the same context cell. Report anomalous cells with "Why is quality low in this context?"

**Effort**: ~1 week. Add reporting module. Compute violation rates per context cell using the same hierarchy as `ContextAwareAdaptiveThresholdEngine`. Generate anomaly alerts when rates exceed context-specific thresholds.

**Impact**: Operators get actionable insights: "Quality degraded in (rush_hour, midtown, weekday) — violation rate 12% vs. historical 3%."

### Desired but Not Required (For Future Work)

- External context integration (weather, traffic, events) — requires API integration, outside minimum viable scope
- Operational context for adaptive thresholding (vehicle type, passenger load) — extend `ContextDimension.entity()`
- Distributed context-aware thresholds (currently driver-only, per B4 limitation)

### Integration Architecture

```
EVENT STREAM
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Pipeline (LocalPipeline / SparkPipeline)                     │
│ 1. Parse event                                               │
│ 2. Instantiate ContextRegistry (if not exists)              │
│ 3. registry.resolve(event) → 5D context dict               │
│ 4. Build RuleContext with:                                  │
│    - event                                                   │
│    - event_time                                              │
│    - historical_stats (from AdaptiveThresholdEngine)         │
│    - external_context (from ExternalContext.from_event)     │
│    - context_aware_engine (ContextAwareAdaptiveThresholdEngine)│
│ 5. Update context_aware_engine.update(field, value, event)  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Rules (syntactic.py, semantic.py, cross_record.py)           │
│ Syntactic: Static checks (null, range, type) — no threshold │
│ Semantic:                                                   │
│   - FareRangeRule:                                           │
│     ctx.get_contextual_threshold("fare_amount", "p90")      │
│     → calls engine.get_threshold_with_fallback()             │
│     → returns P90 for (rush_hour, midtown, weekday)         │
│   - TripDurationSanityRule: similar                         │
│   - AverageSpeedSanityRule: similar                         │
│ Cross-Record: GPS jump, duplicate detection — no threshold  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ TQS Aggregation Layer (IDEA-NEW-2)                          │
│ 1. Collect violations from all rules                        │
│ 2. Extract context_key from each violation                   │
│ 3. Group violations by (rule_dimension, context_key)        │
│ 4. Compute quality score per context cell                    │
│ 5. Aggregate to trajectory-level TQS                       │
│ 6. Output: trajectory_id, tqs_score, context_key,          │
│    dimension_scores, violation_breakdown                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Context-Aware Quality Reporting                             │
│ 1. Aggregate violation rates per context cell              │
│ 2. Compare to historical rates for same context cell         │
│ 3. Flag anomalous context cells                             │
│ 4. Generate "Why is quality low?" explanations             │
└─────────────────────────────────────────────────────────────┘
```

---

## Required Additions Summary

### Minimum Viable Context-Aware Upgrade (MVC, targets 12/12)

| Addition | Priority | Effort | Impact |
|----------|:--------:|:------:|--------|
| Connect `ContextAwareAdaptiveThresholdEngine` to semantic rules | P1 | ~2 days | Data-driven contextual thresholds; estimated +10-15pp precision |
| TQS decomposition by context cell | P1 | ~1 week | Explainable quality scores by context |
| Instantiate `ContextRegistry` in pipeline | P2 | ~2 days | Full 5D context available to rules |
| Context-aware quality reporting | P2 | ~1 week | Actionable "Why is quality low?" insights |
| **Total** | | **~2.5 weeks** | **12/12 name fit** |

### How IDEA-NEW-2 + IDEA-05 Maps to the Additions

| Addition | IDEA-NEW-2 | IDEA-05 | Integration Engineering |
|----------|:----------:|:-------:|:----------------------:|
| Context-aware thresholds in rules | | YES (method) | Connect engine to rules |
| TQS decomposition by context | YES (design) | | Implement aggregation by cell |
| Instantiate ContextRegistry | | | Pipeline modification |
| Context-aware reporting | YES (output layer) | | Implement reporting module |

**Key insight**: IDEA-NEW-2 provides the TQS design and the output framework. IDEA-05 provides the contextual calibration method. The integration engineering connects the existing infrastructure (which already exists!) to the TQS layer and the rules engine. This is NOT building from scratch — it is wiring up what already exists.

---

## Key Insight Summary

The context-aware upgrade is an **integration task**, not a **construction task**. The infrastructure already exists:

- `ContextAwareAdaptiveThresholdEngine` with 5-level hierarchical fallback — EXISTS
- `ContextRegistry` with 5D context extraction — EXISTS
- `ExternalContext` (Dey 2001 formal 4D model) — EXISTS
- `AdaptiveThresholdEngine` with bootstrap CI and Shannon entropy — EXISTS
- Rule-level temporal context usage (hardcoded multipliers) — EXISTS

What is missing is the integration:
1. `ContextRegistry` is never instantiated by the pipeline
2. `ContextAwareAdaptiveThresholdEngine` is never passed to `RuleContext`
3. Semantic rules use `ctx.historical_stats` (global) instead of contextual thresholds
4. TQS does not decompose by context cell
5. No context-aware quality reporting

The path to 12/12: IDEA-NEW-2 (TQS integration design) + IDEA-05 (contextual calibration method) + integration engineering (connect existing infrastructure) = fully context-aware framework.

---

*Generated by ARCHITECT agent. All claims grounded in code inspection of `streamdq/rules/context_adaptive.py`, `streamdq/models/context_registry.py`, `streamdq/rules/base.py`, `streamdq/rules/adaptive.py`, `streamdq/rules/semantic.py`, `streamdq/rules/syntactic.py`, `streamdq/rules/cross_record.py`.*
