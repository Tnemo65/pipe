# ENG_FEAS Agent — Context-Aware Upgrade Evaluation

**Date**: Wednesday Apr 22, 2026
**Agent**: ENG_FEAS (Engineering Feasibility)
**Project**: ContextAware-DQ — Context-Aware Framework for Streaming Data Quality Monitoring
**Integration Target**: IDEA-NEW-2 (T-Assess × ContextAware-DQ) + IDEA-05 (Contextual Calibration)

---

## Codebase Audit Results

### What Already Exists

The ContextAware-DQ codebase has a surprisingly mature context-aware infrastructure. Here is the complete picture of what is already built:

#### 1. `streamdq/rules/context_adaptive.py` — ContextAwareAdaptiveThresholdEngine

**Purpose**: Context-keyed adaptive threshold computation with hierarchical fallback (L0-L4).

**Key capabilities**:
- Stores rolling windows of field values **per (field, context_key)** composite key, not globally
- Maintains separate statistics at all 5 hierarchy levels simultaneously (L0=most specific, L4=global)
- `update(field, value, event)` — feeds values with full context extraction
- `get_threshold_with_fallback(field, percentile, event)` — returns `{"value": X, "level": N, "context_key": "..."}` with automatic L0→L4 fallback
- `get_stats_for_context(field, context, level)` — query stats at specific hierarchy level
- `reset_context(field, context_key)` — clears state for drift-triggered recalibration
- LRU eviction with `max_contexts=200` limit to prevent state explosion
- R-type-7 percentile interpolation (fixes B8: int truncation bias)

**Status**: Fully implemented, tested in `tests/rules/test_context_adaptive.py`.

**What it does NOT do**: It does not call rules. It only computes and stores context-keyed statistics. The rules must call `get_threshold_with_fallback()` to retrieve these thresholds.

#### 2. `streamdq/models/context_registry.py` — ContextRegistry + ContextDimension

**Purpose**: 5D context extraction (temporal, entity, spatial, source, policy) from events.

**Key capabilities**:
- `ContextRegistry.resolve(event)` — returns full context dict with all 5 dimensions
- `ContextRegistry.match_key(context, level)` — generates hierarchical context key string at specified level
- `ContextDimension.temporal(event)` — extracts: `hour_of_day`, `day_of_week`, `is_weekend`, `time_category`, `is_rush_hour`
- `ContextDimension.spatial(event, zone_map)` — extracts: `zone`, `borough`, `zone_category` (midtown/airport/manhattan_other/outer)
- `ContextDimension.source(event)` — extracts: `source_id`, `source_type`, `is_replay`
- `ContextDimension.entity(event)` — extracts: `entity_type`, `payment_type`
- `ContextDimension.policy(event)` — extracts: `contract_tier`, `owner`
- `ContextKey.from_dict(context, level)` — generates key string at any level (0-4)
- 5 hierarchy levels: L0=(hour, zone_category, weekend), L1=(hour_bucket, zone_category, weekend), L2=(hour_bucket, borough, weekend), L3=(time_category), L4=(global)
- YAML config loading via `ContextRegistry.from_yaml("config/context_nyc_taxi.yaml")`
- Holiday calendar (US federal holidays 2024-2026) for `is_holiday` detection

**Status**: Fully implemented, tested in `tests/models/test_context_registry.py`.

**What it does NOT do**: It does not connect to rules or thresholds. It only extracts context.

#### 3. `streamdq/rules/adaptive.py` — AdaptiveThresholdEngine (non-context-aware)

**Purpose**: Global (non-context-aware) adaptive threshold computation with bootstrap CI and Shannon entropy.

**Key capabilities**:
- Rolling window per field (not per context)
- P10/P90/P25/P50/P75/P95/P99 percentiles
- Bootstrap CI on P10 and P90 (100 iterations, R type 7)
- Shannon entropy computation for early drift detection (NG-35)
- LRU field eviction with `idle_threshold` (NG-26)
- Human override support via `override(field, thresholds)`
- `reset_field(field)` for drift-triggered recalibration

**Status**: Fully implemented.

**Gap**: This is the **non-context-aware** version. It is used by SparkPipeline (`spark_pipeline.py` line 632) but NOT by LocalPipeline (which uses ContextAwareAdaptiveThresholdEngine instead).

#### 4. `streamdq/rules/base.py` — ExternalContext + RuleContext

**Purpose**: Formal 4D context model (who/what/when/where) embedded in RuleContext.

**Key capabilities**:
- `ExternalContext` dataclass with Dey (2001) 4D model: WHO, WHAT, WHEN, WHERE, system context
- `ExternalContext.from_event(event, event_time)` — auto-builds from event metadata
- `RuleContext.external_context` field carries ExternalContext to rules
- `RuleContext.get_external(key, default)` — dict-like access with None/dict fallback
- `Violation` dataclass with all required fields

**Status**: Fully implemented.

**Gap**: `Violation` dataclass does NOT have fields for `context_key` or `threshold_level`. These would need to be added.

#### 5. `streamdq/pipeline/local_pipeline.py` — Pipeline Integration

**Purpose**: Wires ContextAwareAdaptiveThresholdEngine into the rule evaluation loop.

**What IS wired**:
- Line 121-127: Creates `ContextAwareAdaptiveThresholdEngine` with `ContextRegistry` when `use_context_aware_thresholds=True`
- Line 138-141: Wires threshold engine to rules via `rule.threshold_engine = self.threshold_engine`
- Line 199-201: Updates context-aware engine with `self.threshold_engine.update(field, float(value), event)` (passes full event for context extraction)
- Line 208: Gets stats via `self.threshold_engine.get_all_stats()` (returns `{}` for context-aware engine — see below)
- Line 211-217: Builds `RuleContext` with `ExternalContext.from_event()` for temporal features

**What is NOT wired**:
- `get_threshold_with_fallback()` is NEVER called by rules
- `get_stats_for_context()` is NEVER called
- The `ContextAwareAdaptiveThresholdEngine.get_all_stats()` returns `{}` (empty dict, per docstring)
- Rules receive `historical_stats={}` from context-aware engine
- Rules use static fallbacks instead of context-aware thresholds

**Critical gap**: The context-aware engine is created and updated, but its thresholds are NEVER USED by rules.

---

### What Is NOT Integrated

#### Gap 1: Rules Don't Call `get_threshold_with_fallback()`

The semantic rules have the right **intention** (multipliers based on `is_rush_hour`, `is_late_night`, `is_weekend`, `is_holiday`) but use **hardcoded multipliers**, not computed thresholds:

**FareRangeRule (SEM001)** — Lines 79-101 of `semantic.py`:
```python
if is_holiday:
    fare_max *= 1.5       # hardcoded 1.5x
elif is_rush_hour:
    fare_max *= 1.3       # hardcoded 1.3x
elif is_late_night:
    fare_max *= 0.7       # hardcoded 0.7x
```

**TripDurationSanityRule (SEM002)** — Lines 179-186:
```python
if is_rush_hour:
    max_dur = max_dur * 1.5   # hardcoded 1.5x
elif is_weekend:
    max_dur = max_dur * 1.2   # hardcoded 1.2x
```

**AverageSpeedSanityRule (SEM003)** — Lines 333-341:
```python
if is_late_night:
    max_speed += 15.0     # hardcoded +15 mph
elif is_rush_hour:
    max_speed -= 5.0      # hardcoded -5 mph
```

**What should happen**: Rules should call `engine.get_threshold_with_fallback(field="fare_amount", percentile="p90", event=ctx.event)` and use the returned context-aware threshold value instead of applying hardcoded multipliers to static thresholds.

#### Gap 2: `historical_stats` Is Empty for Context-Aware Engine

In `local_pipeline.py` line 208:
```python
historical_stats = self.threshold_engine.get_all_stats()
```

For `ContextAwareAdaptiveThresholdEngine`, `get_all_stats()` returns `{}` (empty dict, by design — see docstring on line 271-281 of `context_adaptive.py`). The engine's comment explicitly says:

> "Better approach: Pass engine to RuleContext and modify rules to use `get_threshold_with_fallback()` directly."

This is the **architecturally intended path**, but it requires:
1. Passing the threshold engine reference to rules (not just `historical_stats`)
2. Modifying rules to call `get_threshold_with_fallback()` with the event

#### Gap 3: Violation Objects Lack Context Metadata

The `Violation` dataclass in `base.py` does not include fields for:
- `context_key` — which context cell triggered this violation
- `threshold_level` — which hierarchy level (L0-L4) was used
- `threshold_value` — the actual threshold used

Without this, TQS aggregation cannot compute context-decomposed quality scores (the per-context-cell TQS that IDEA-NEW-2's TQS layer needs).

#### Gap 4: Cross-Record Rules (CRS001/CRS002/CRS003) Don't Use Adaptive Thresholds

`evaluate_trajectory_anomaly()` in `cross_record.py` uses static parameters:
```python
max_speed_kmh: float = 160.0
max_stationary_jump_m: float = 100.0
```

These could be context-aware (e.g., different speed limits for highway vs. urban contexts).

#### Gap 5: TQS Layer Does Not Exist Yet

The `QualityEvent` dataclass in `models/quality_event.py` has:
- `context_distribution: Dict[str, int]` — context key → event count
- `active_contexts: int` — number of active contexts

But there is no TQS aggregation function, no dimension mapper (SYN/SEM/CRS → T-Assess dimensions), and no per-context-cell quality scoring.

#### Gap 6: SYN002 (Location Range) Has No Adaptive Threshold Path

`PickupLocationValidRule` uses a static set of valid IDs (`VALID_LOCATION_IDS = set(range(1, 264))`). This is appropriate for syntactic validation — location IDs don't vary by context. No integration needed here.

---

### How Rules Currently Get Thresholds

| Rule | Current Threshold Source | Adaptive? | Context-Aware? |
|------|------------------------|-----------|---------------|
| SYN000 (CompletenessRule) | Static required_fields list | No | No |
| SYN001 (FareAmountRangeRule) | None (null/type check only) | N/A | N/A |
| SYN002 (PickupLocationValidRule) | Static VALID_LOCATION_IDS set | No | No (correctly) |
| SYN003 (TimestampNotFutureRule) | Static future_tolerance (5 min) | No | No (correctly) |
| SEM001 (FareRangeRule) | `historical_stats["fare_amount"]["p90"] * 2.0` OR static fallback | Partial | Partial (hardcoded multipliers) |
| SEM002 (TripDurationSanityRule) | Static min/max with hardcoded multipliers | No | Partial (hardcoded multipliers) |
| SEM003 (AverageSpeedSanityRule) | Static max_speed_mph=80 with hardcoded +/- adjustments | No | Partial (hardcoded adjustments) |
| CRS001 (TrajectoryAnomaly) | Static max_speed_kmh=160 | No | No |
| CRS002 (GPS spoofing) | Static max_stationary_jump_m=100 | No | No |
| CRS003 (Duplicate) | Hash-based dedup with confidence scoring | No | No (correctly — dedup doesn't need context) |

**Summary**: Only SEM001 uses `historical_stats` (and only for P10/P90 fare thresholds). SEM002 and SEM003 have context-awareness **intent** but use hardcoded multipliers, not adaptive thresholds.

---

## Implementation Options

### Option A — MINIMAL (Connect existing components)

**Approach**: Wire ContextAwareAdaptiveThresholdEngine into rules via `get_threshold_with_fallback()`. No new classes, no new infrastructure.

**Changes required**:

1. **Pass engine reference to rules** — Modify `RuleContext` or rule constructor to carry `ContextAwareAdaptiveThresholdEngine` reference
2. **SEM001 refactor** — Replace hardcoded multipliers with `engine.get_threshold_with_fallback(field="fare_amount", percentile="p90", event=ctx.event)`
3. **SEM002 refactor** — Make `max_duration_sec` context-aware (call `get_threshold_with_fallback` for duration field if available, or derive from distance)
4. **SEM003 refactor** — Replace hardcoded speed adjustments with context-aware thresholds
5. **Add context metadata to Violation** — Extend `Violation` dataclass with `context_key: Optional[str]` and `threshold_level: Optional[int]`
6. **Fix `get_all_stats()`** — Either return context-aggregated stats from ContextAwareAdaptiveThresholdEngine, or modify rules to query the engine directly

**Estimated**: 1-2 weeks
**Risk**: LOW — modifies existing code but doesn't change architecture

**Pros**:
- Minimal changes, maximum leverage of existing infrastructure
- Properly uses `get_threshold_with_fallback()` which already handles hierarchical fallback
- Adds context metadata to Violation enables TQS layer

**Cons**:
- Rules must receive engine reference (architectural change to rule initialization)
- SEM002/SEM003 threshold derivation from context-aware stats is non-trivial (no `duration` field being tracked)

---

### Option B — INTEGRATED (Full pipeline integration)

**Approach**: Everything in Option A + extend ContextRegistry with GPS-specific context + full TQS layer.

**Changes required**:

1. All of Option A
2. **Extend ContextRegistry** with GPS/GTFS-specific context (speed bounds per zone category, route type)
3. **Context-aware CRS001/CRS002** — speed limits vary by context (highway vs. urban vs. airport)
4. **Build TQS aggregation layer** — map SYN→Validity, SEM→Accuracy, CRS→Consistency; compute weighted TQS
5. **Per-context-cell TQS** — decompose quality scores by context key
6. **TQS degradation curves** — correlate TQS drop with ground truth injection level
7. **Pre-register 3 TQS weighting variants** (per IDEA-NEW-2 requirements)

**Estimated**: 2-3 weeks
**Risk**: MEDIUM — TQS layer is largely new code; T-Assess API compatibility unknown

**Pros**:
- Complete implementation of IDEA-NEW-2
- Full closed-loop system: rules → violations → TQS → quality reports
- Context-decomposed quality scores

**Cons**:
- TQS layer requires T-Assess API audit (gate condition per orchestrator)
- TQS weighting scheme needs pre-registration (multiple comparisons risk)
- CRS001/CRS002 context-awareness adds complexity for marginal benefit

---

### Option C — LAYERED (TQS layer only, rules unchanged)

**Approach**: Keep rules as-is (static thresholds), build TQS layer that aggregates existing Violations by context.

**Changes required**:

1. **Build TQS aggregation function** — weighted sum of SYN/SEM/CRS violation rates
2. **Pre-register 3 TQS variants** — pre-register before experiments
3. **Context decomposition** — group Violations by `context_key` (computed from event metadata at TQS layer)
4. **Context metadata computation** — TQS layer extracts context from events, doesn't modify rules
5. **TQS degradation curves** — correlate with ground truth injection

**Rules stay unchanged** — static thresholds with hardcoded context multipliers remain.

**Estimated**: 1 week
**Risk**: LOW — doesn't touch rule engine

**Pros**:
- Fastest path to IDEA-NEW-2 TQS deliverables
- No rule engine modifications (zero risk of breaking existing behavior)
- Enables TQS evaluation immediately

**Cons**:
- Rules still use static thresholds — the "context-aware" part of IDEA-05 is NOT implemented
- Hardcoded multipliers in SEM001/SEM002/SEM003 remain
- Context metadata on Violations must still be added (for TQS decomposition)

---

## Recommended Path

**Option C first (Week 1), then Option A (Weeks 2-3). Total: 2-3 weeks.**

**Rationale**:
1. **Option C is the fastest path to TQS evaluation** — TQS layer doesn't need context-aware thresholds; it just needs violation counts by context cell
2. **Option A is the correct implementation of IDEA-05** — wiring ContextAwareAdaptiveThresholdEngine properly creates genuinely context-aware thresholds (not just hardcoded multipliers)
3. **Option B can be deferred** — T-Assess API audit is a gate condition; if T-Assess is incompatible, fall back to ContextAware-DQ-only TQS
4. **Option A's changes are low-risk** — the infrastructure exists, just needs wiring

**Critical path**: T-Assess API audit (must happen Week 1 in parallel). If T-Assess fails audit, Option B's TQS layer becomes custom-built, extending Option A's timeline.

---

## Integration Architecture

### Current Data Flow (Static Thresholds)

```
Event
  ↓
LocalPipeline.process_event()
  ↓
1. threshold_engine.update(field, value, event)  [ContextAware engine updated but NOT used]
  ↓
2. threshold_engine.get_all_stats() → {}         [Returns empty dict for context-aware engine]
  ↓
3. RuleContext(historical_stats={}, external_context=ExternalContext)
  ↓
4. FareRangeRule.evaluate(ctx)
     - Reads ctx.historical_stats → empty
     - Falls back to STATIC_MIN_FARE / STATIC_MAX_FARE
     - Applies hardcoded multipliers (is_rush_hour → 1.3x, etc.)
  ↓
5. Violation(rule_id, details{...}, expected{...})
  ↓
ViolationStore
```

### Upgraded Data Flow (Option A — Context-Aware Thresholds)

```
Event
  ↓
LocalPipeline.process_event()
  ↓
1. threshold_engine.update(field, value, event)  [Updates ALL hierarchy levels L0-L4]
  ↓
2. RuleContext(threshold_engine=engine, external_context=ExternalContext)
  ↓
3. FareRangeRule.evaluate(ctx)
     - threshold = ctx.threshold_engine.get_threshold_with_fallback(
         field="fare_amount", percentile="p90", event=ctx.event)
       → {"value": 42.5, "level": 0, "context_key": "hour_10_midtown_weekday"}
     - Uses context-aware p90 instead of static threshold
     - Context multiplier still applies (or could be removed)
     - threshold_source = "context_adaptive"
  ↓
4. Violation(
     rule_id="SEM001",
     details={..., "threshold_source": "context_adaptive",
              "context_key": "hour_10_midtown_weekday",
              "threshold_level": 0,
              "threshold_value": 42.5},
     ...
   )
  ↓
5. ViolationStore (with context_key in details JSON)
  ↓
6. TQS Aggregation Layer (Option B)
     - Groups Violations by context_key
     - Computes TQS per context cell: TQS_cell = f(violations_by_dimension)
     - Decomposes: TQS_total = Σ(weight_dim × TQS_dim)
```

### Option B — Full TQS Layer Flow

```
Event
  ↓
ContextRegistry.resolve(event) → 5D context dict
  ↓
ContextAwareAdaptiveThresholdEngine.get_threshold_with_fallback()
  → context_key = "hour_10_midtown_weekday"
  → threshold_value = 42.5
  → level = 0
  ↓
Rules evaluate with context-aware thresholds
  ↓
Violation with context metadata (context_key, threshold_level, threshold_value)
  ↓
ViolationStore
  ↓
TQS Aggregator (NEW)
  - Dimension mapper: SYN→Validity, SEM→Accuracy, CRS→Consistency
  - TQS_score = w_validity × V + w_accuracy × A + w_consistency × C + w_fairness × F
  - Pre-register 3 variants (equal weights, domain-weighted, severity-weighted)
  ↓
Per-Context-Cell Quality Report
  - TQS_morning_midtown = 0.92
  - TQS_evening_airport = 0.78
  - TQS_global = 0.87
  ↓
TQS Degradation Curves (against ground truth injection level)
```

---

## Technical Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| **Cold-start on sparse context cells** | HIGH | MEDIUM | Hierarchical fallback (L0→L4 already implemented). Rare contexts fall back to more populated ones. Fallback chain: L0→L1→L2→L3→L4→static_fallback. |
| **Context extraction overhead** | LOW | LOW | Lazy computation; context extracted only from existing event fields. Estimated <1ms per event. No external calls. |
| **State management explosion** | MEDIUM | HIGH | `max_contexts=200` limit + LRU eviction already in code. Context key cardinality bounded by: 24 hours × 4 zone categories × 2 (week/weekend) = 192 possible L0 keys (within limit). |
| **Breaking existing rule behavior** | MEDIUM | HIGH | Backward compatibility: if `get_threshold_with_fallback()` returns None (no stats), rules must fall back to static thresholds. Ablation test: static vs. context-aware thresholds must show measurable improvement. |
| **TQS recalculation on context change** | MEDIUM | LOW | Incremental update in violation_store. TQS layer reads from stored violations, not in-memory. |
| **T-Assess API incompatibility** | MEDIUM | HIGH | Gate condition: must audit T-Assess GitHub API within Week 1. If incompatible, fall back to custom TQS built from ContextAware-DQ violations. |
| **TQS weighting circularity** | MEDIUM | MEDIUM | Pre-register exactly 3 variants before running experiments. Report all 3. Select primary post-hoc only if all 3 are valid. Multiple comparisons correction (Bonferroni). |
| **Duplicate injection no-op (B2)** | MEDIUM | HIGH | CRS003 recall unmeasurable until B2 fixed. CRS dimension of TQS will be incomplete. B2 fix is prerequisite for Option B CRS evaluation. |
| **Processing latency hardcoded to 0 (B6)** | LOW | MEDIUM | Fixed in semantic.py rules (uses `time.perf_counter()`). Check cross_record.py still uses `start_time` parameter. |
| **foreachBatch driver bottleneck (B4)** | HIGH | HIGH | Known limitation. SparkPipeline uses `foreachBatch` — threshold engine runs on driver only. For evaluation: use LocalPipeline (in-process) to avoid bottleneck. |

---

## Already Exists vs. Needs Building

### ALREADY EXISTS (Do Not Rebuild)

| Component | File | Status |
|-----------|------|--------|
| ContextAwareAdaptiveThresholdEngine class | `streamdq/rules/context_adaptive.py` | ✅ Complete, tested |
| ContextRegistry class | `streamdq/models/context_registry.py` | ✅ Complete, tested |
| ContextDimension extractors (5D) | `streamdq/models/context_registry.py` | ✅ Complete |
| ContextKey hierarchy (L0-L4) | `streamdq/models/context_registry.py` | ✅ Complete |
| ExternalContext dataclass (Dey 2001) | `streamdq/rules/base.py` | ✅ Complete |
| AdaptiveThresholdEngine with bootstrap CI | `streamdq/rules/adaptive.py` | ✅ Complete |
| FieldStats dataclass with entropy | `streamdq/rules/adaptive.py` | ✅ Complete |
| Holiday calendar (2024-2026) | `streamdq/pipeline/local_pipeline.py` | ✅ Complete |
| LocalPipeline wiring for context-aware engine | `streamdq/pipeline/local_pipeline.py` | ✅ Partial (engine created + updated, but NOT used) |
| Violation dataclass | `streamdq/rules/base.py` | ✅ Complete (needs extension for context metadata) |
| Tests for context_adaptive | `tests/rules/test_context_adaptive.py` | ✅ Complete |
| Tests for context_registry | `tests/models/test_context_registry.py` | ✅ Complete |
| Tests for semantic context-awareness | `tests/rules/test_sem_context_aware.py` | ✅ Partial (tests engine, not rules) |
| QualityEvent with context_distribution | `streamdq/models/quality_event.py` | ✅ Partial (tracks context metrics) |

### NEEDS BUILDING (The Actual Integration Work)

#### Option A — MINIMAL (Connect existing components)

| Task | File | Effort | Notes |
|------|------|--------|-------|
| Pass threshold_engine reference to rules | `local_pipeline.py`, `base.py` | 1 day | Modify rule constructor or RuleContext |
| Refactor SEM001 to use `get_threshold_with_fallback()` | `streamdq/rules/semantic.py` | 2 days | Replace hardcoded multipliers with context-aware P90 |
| Refactor SEM002 to use context-aware duration thresholds | `streamdq/rules/semantic.py` | 2 days | Track `trip_duration` in context-aware engine; derive from distance/speed context |
| Refactor SEM003 to use context-aware speed thresholds | `streamdq/rules/semantic.py` | 1 day | Similar pattern to SEM001 |
| Add context metadata to Violation | `streamdq/rules/base.py` | 1 day | Add `context_key`, `threshold_level`, `threshold_value` fields |
| Fix `get_all_stats()` for context-aware engine | `streamdq/rules/context_adaptive.py` | 1 day | Return context-aggregated stats OR document rules must use `get_threshold_with_fallback()` directly |
| Add unit tests for context-aware rule evaluation | `tests/rules/test_sem_context_aware.py` | 1 day | Expand existing tests |
| **Total Option A** | | **~9 days (1.5-2 weeks)** | |

#### Option B — INTEGRATED (Full TQS Layer)

| Task | File | Effort | Notes |
|------|------|--------|-------|
| All of Option A | | ~9 days | |
| Audit T-Assess GitHub API | External | 2-3 days | Gate condition; if fails, build custom TQS |
| Build TQS aggregation function | `streamdq/evaluation/tqs.py` (new) | 3 days | Dimension mapper: SYN→Validity, SEM→Accuracy, CRS→Consistency |
| Pre-register 3 TQS weighting variants | `config/tqs_variants.yaml` (new) | 1 day | Document exact formulas before experiments |
| Per-context-cell TQS decomposition | `streamdq/evaluation/tqs.py` | 2 days | Group violations by context_key; compute TQS per cell |
| Context-aware CRS001/CRS002 | `streamdq/rules/cross_record.py` | 2 days | Speed limits vary by zone category (optional) |
| TQS degradation curve visualization | `scripts/tqs_evaluation.py` (new) | 2 days | Correlation with ground truth injection level |
| Integration tests for TQS layer | `tests/evaluation/test_tqs.py` (new) | 2 days | |
| Fix B2 (CRS003 duplicate injection) | `streamdq/producers/` | 2-3 days | Prerequisite for CRS dimension TQS |
| **Total Option B (without B2)** | | **~21 days (4+ weeks)** | |
| **Total Option B (with B2)** | | **~23-26 days (4.5-5 weeks)** | |

#### Option C — LAYERED (TQS only, rules unchanged)

| Task | File | Effort | Notes |
|------|------|--------|-------|
| Build TQS aggregation function | `streamdq/evaluation/tqs.py` (new) | 3 days | Custom (not T-Assess) |
| Pre-register 3 TQS weighting variants | `config/tqs_variants.yaml` (new) | 1 day | |
| Compute context from events at TQS layer | `streamdq/evaluation/tqs.py` | 1 day | Re-use ContextRegistry |
| Per-context-cell TQS | `streamdq/evaluation/tqs.py` | 2 days | Group stored violations by context |
| Add minimal context metadata to Violation | `streamdq/rules/base.py` | 1 day | |
| TQS degradation curves | `scripts/tqs_evaluation.py` (new) | 2 days | |
| Integration tests | `tests/evaluation/test_tqs.py` (new) | 1 day | |
| **Total Option C** | | **~11 days (2 weeks)** | |

---

## Engineering Timeline

### Recommended: Option C (Week 1) → Option A (Weeks 2-3)

```
Week 1: Option C — TQS Layer (rules unchanged)
├── Day 1-2: Audit T-Assess GitHub API
│   └── If incompatible → build custom TQS from ContextAware-DQ violations
├── Day 2-4: Build TQS aggregation function
│   ├── Dimension mapper: SYN→Validity, SEM→Accuracy, CRS→Consistency
│   └── 3 pre-registered weighting variants
├── Day 4-5: Per-context-cell TQS decomposition
│   ├── ContextRegistry.resolve() from stored events
│   └── Group Violations by context_key
└── Day 5: TQS degradation curve prototype
    └── Correlation with ground truth injection

Week 2: Option A — Rule Integration (context-aware thresholds)
├── Day 1-2: Pass threshold_engine to rules via RuleContext
│   └── Modify rule constructor OR add engine to RuleContext
├── Day 2-4: Refactor SEM001/SEM002/SEM003
│   ├── SEM001: get_threshold_with_fallback(field="fare_amount", percentile="p90")
│   ├── SEM002: context-aware duration thresholds (track trip_duration field)
│   └── SEM003: context-aware speed thresholds
├── Day 4-5: Add context metadata to Violation
│   ├── context_key, threshold_level, threshold_value fields
│   └── Update ViolationStore schema
└── Day 5: Unit tests for context-aware rule evaluation

Week 3: Option A — Polish + Integration
├── Day 1-2: Fix get_all_stats() gap
│   └── Document: rules must use get_threshold_with_fallback() directly
├── Day 2-3: Integration tests (LocalPipeline end-to-end)
├── Day 3-4: Fix B2 (CRS003 duplicate injection) if needed for CRS TQS
└── Day 5: Documentation + reproducibility doc
    └── How to run: context-aware evaluation with TQS
```

### Contingency: If T-Assess API Incompatible

```
Week 1: Option C with custom TQS (no T-Assess)
├── Day 1: T-Assess audit → INCOMPATIBLE
├── Day 2-3: Design custom TQS from ContextAware-DQ violations
└── Day 3-5: Build custom TQS aggregation

Week 2-3: Option A (unchanged)

Week 4: Evaluation + TQS validation
├── Run ablation: static vs. context-aware thresholds
├── Compute TQS degradation curves
└── Pre-register TQS weighting variants
```

### Gate Conditions (Must Resolve Before Week 2)

1. **T-Assess API audit (Day 1-2)**: If incompatible, build custom TQS. This determines whether Option B is viable.
2. **B2 fix (CRS003 duplicate injection, 2-3 days)**: Required before CRS dimension TQS is meaningful. Can run in parallel with Option C Week 1.
3. **TQS weighting pre-registration (Day 1)**: Define 3 exact variants before running any experiments. Document in `config/tqs_variants.yaml`.

---

## Summary

The ContextAware-DQ codebase has a mature, well-tested context-aware infrastructure that is **created and updated but never used**. The gap is purely integration — wiring `ContextAwareAdaptiveThresholdEngine.get_threshold_with_fallback()` into semantic rules and adding context metadata to Violations.

**Estimated effort**: 2-3 weeks for full IDEA-05 integration (Option A), with 1 week for TQS layer (Option C) that can run in parallel.

**Critical risks**: T-Assess API compatibility (gate condition), B2 CRS003 fix (prerequisite for CRS TQS), and cold-start on sparse context cells (mitigated by hierarchical fallback).

**Deliverables after Option C + Option A**:
1. SEM001/SEM002/SEM003 using context-aware thresholds from `ContextAwareAdaptiveThresholdEngine`
2. Violations with `context_key`, `threshold_level`, `threshold_value` metadata
3. Per-context-cell TQS decomposition
4. TQS degradation curves validated against ground truth injection
5. 3 pre-registered TQS weighting variants with reported results for all
