# Table Specifications

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Step**: Step 11 — Table Specifications (Revised)
**Date**: April 24, 2026
**Sources**: Steps 1–10 output documents; debate report

---

## Overview

Tables are numbered sequentially: T1–T5 (main reference tables) + T-S1 through T-S6 (experiment scenario detail tables). All tables follow publication standards: `booktabs` LaTeX package, descriptive captions, sources cited. Tier classification (Verified / Estimated / Unmeasurable) required for every data cell.

---

## T1: Data Quality Dimensions

**Chapter**: 1 (Fundamentals) — §1.2 Streaming DQ
**Status**: Ready — from Redman (1998), Otto et al.
**Type**: Reference table

|| Dimension | Symbol | Definition | Measurement | StreamDQ Coverage |
|-----------|--------|-----------|------------|-------------------|
| **Completeness** | Cn | Fraction of required fields present | `Cn = 1 - n_null_required / N_required` | SYN001 (all rules) |
| **Validity** | Vl | Values conform to schema/syntax | Range checks, type checks | SYN002 (fare ≥ 0), SYN003 (lat/lon box) |
| **Timeliness** | Tm | Data is current when accessed | `Tm = 1 - Var(Δt_inter_event) / threshold_tm` | GTFSSem002 (stale > 5 min) |
| **Consistency** | Cs | Data consistent within/across records | Physical plausibility | CRS001 (GPS speed), CRS002 (GPS jump), SEM003 (tip/fare ratio) |
| **Uniqueness** | Uv | No duplicate records | `Uv = 1 - |distinct_hashes| / N` | CRS003 (SHA256 deduplication) |

**Caption**: Table 1: Data quality dimensions from Redman (1998) and Otto et al. Each dimension maps to one or more StreamDQ rules. Measurements are computed from raw event properties only (non-circular design).

**LaTeX**:
```latex
\caption{Data quality dimensions (Redman 1998; Otto et al.) and their
  StreamDQ coverage. Measurements are computed from raw event properties only
  (non-circular design).}
\label{tab:dq-dimensions}
```

---

## T2: Context Types

**Chapter**: 2 (Architecture) — §2.4 Hierarchical Thresholds
**Status**: Ready — from FORMULATION.md §2
**Type**: Reference table

|| Dimension | Key | Example | L0 Min Samples | Dataset |
|-----------|-----|---------|:--------------:|---------|
| **Temporal (D1)** | `H{hour}_{WE|WD}` | `H10_WD` | — | Both |
| **Spatial (D2)** | `zone_category` | `midtown`, `airport`, `outer` | — | NYC TLC |
| **Operational (D3)** | `entity_type` | `taxi`, `bus` | — | Both |
| **External (D4)** | `holiday` | `NYE`, `Thanksgiving` | — | Future work |
| **Data Characteristics (D5)** | `null_rate` | `[0, 1]` | — | Both |

**L0–L5 Hierarchy**:

|| Level | Key Schema | Example | Min Samples | Est. Coverage | Data Source |
|-------|-----------|---------|:-----------:|:-------------:|------------|
| **L0** | `H{hour}_{zone_category}_{WE|WD}` | `H10_midtown_WD` | 100 | 2–5% | NYC TLC |
| **L1** | `{hour_bucket}_{zone_category}_{WE|WD}` | `morning_midtown_WD` | 50 | 5–15% | NYC TLC |
| **L2** | `{hour_bucket}_{borough}_{WE|WD}` | `morning_Manhattan_WD` | 25 | 15–30% | NYC TLC |
| **L3** | `time_category` | `morning`, `afternoon` | 10 | 30–50% | Both |
| **L4** | `global` | — | 5 | 20–40% | Both |
| **L5** | `physics` (hardcoded) | `[0.5, 100] km/h GPS` | 0 | fallback | NYC MTA Bus |

**Note**: L0–L4 are statistical (rolling P10/P90); L5 is physics-based (hardcoded). L0 coverage is 2–5% due to NYC TLC zone-hour sparsity. Coverage estimates add to >100% because events can reach multiple fallback levels.

**Caption**: Table 2: StreamDQ context decomposition (4D + external future work) and L0\u2013L5 hierarchical threshold levels. L0 provides finest-grained bounds but covers only 2\u20135% of events due to NYC TLC zone-hour sparsity.

**LaTeX**:
```latex
\caption{StreamDQ context decomposition and L0\u2013L5 threshold hierarchy.
  L0\u2013L4 are statistical (rolling P10/P90); L5 is physics-based.
  L0 covers only 2\u20135\% of events due to zone-hour sparsity.}
\label{tab:context-types}
```

---

## T3: Comparison with Existing Approaches

**Chapter**: 1 (Fundamentals) — §1.2 Streaming DQ
**Status**: Ready — from final/04_NOVELTY_CONTRIBUTION/COMPETITIVE_TABLE.md
**Type**: Comparison table

|| Feature | StreamDQ | Stream DaQ | METER | Great Expectations | Soda Core | GTFS Validator |
|---------|---------|-----------|-------|------------------|----------|--------------|
| **Engine** | Flink-native | Pathway | Flink | Batch | Batch | Batch |
| **GPS cross-record rules** | Yes (CRS001–003) | No | No | No | No | Schema only |
| **Context-aware thresholds** | L0–L5 hierarchy | Single-level rolling | Drift detection | Static | Static | Static |
| **Cross-record validation** | GPS-specific | Future work | No | No | No | No |
| **Evaluation methodology** | Ground truth + Bootstrap CI | Not specified | Not specified | Manual | Manual | Manual |
| **Real-time alerting** | Prometheus + Grafana | Not specified | Not specified | No | No | No |
| **Open source** | Yes | Yes | No | Yes | Yes | Yes |
| **Dataset scope** | NYC TLC + NYC MTA Bus | Generic | Generic | Generic | Generic | GTFS feeds |

**Caption**: Table 3: Comparison of StreamDQ with existing data quality frameworks. StreamDQ is the only framework combining Flink-native streaming, GPS cross-record validation (CRS rules), hierarchical context-aware thresholds (L0\u2013L5), and ground-truth evaluation with bootstrap CI.

**LaTeX**:
```latex
\caption{Comparison of StreamDQ with existing data quality frameworks.
  StreamDQ is the only framework combining Flink-native streaming,
  GPS cross-record validation, L0\u2013L5 hierarchical thresholds,
  and ground-truth evaluation with bootstrap CI.}
\label{tab:comparison}
```

---

## T4: Experiment Scenarios

**Chapter**: 3 (Experiments) — §3.3 Evaluation Methodology
**Status**: Ready — from STATISTICAL_PLAN.md
**Type**: Scenario reference table

### Scenario Summary

|| Scenario | Rule Tested | Anomaly Type | Injection Method | Dataset | Target Metric |
|---------|------------|-------------|----------------|---------|--------------|
| **S1** | SYN001 | Schema violation | Set field = NULL/NaN | Both | Recall ≥ 0.70 |
| **S2** | SYN001 | Completeness issue | NULL required field | Both | Recall ≥ 0.70 |
| **S3** | GTFSSem002 | Freshness issue | Set timestamp = now - (6–10 min) | NYC MTA Bus | Recall ≥ 0.70 |
| **S4** | SYN001/SEM | Volume anomaly | Burst injection (10× rate, 30s) | NYC TLC | Detection latency |
| **S5** | SEM001/SEM002/SEM003 | Business rule violation | fare > P95, dist > P95, tip > 60% fare | NYC TLC | Recall ≥ 0.70 |
| **S6** | CRS001/CRS002 | Context-dependent violation | GPS speed: 0.2 km/h + 60s; 110 km/h; GPS jump: 500m/30s | NYC MTA Bus | Precision ≥ 0.70, Recall ≥ 0.70 |

### Scenario Detail Tables

#### T-S1: Scenario 1 — Schema Violation

**Rule**: SYN001
**Anomaly**: NULL or NaN in required fields
**Injection**: For each required field, randomly set value = NULL with probability equal to injection rate
**Injection rates**: 0.5%, 1%, 2%, 5%
**Ground truth**: `anomaly_metadata{entity_index, field_name, original_value = NULL}`
**Expected**: Recall ≥ 0.70 (TIER-2)
**CI**: BCa bootstrap, 10,000 iterations

| Field | Type | Expected NULL Rate | Dataset |
|-------|------|:------------------:|---------|
| `fare_amount` | float | varies | NYC TLC |
| `trip_distance` | float | varies | NYC TLC |
| `passenger_count` | int | varies | NYC TLC |
| `lat` | float | varies | NYC MTA Bus |
| `lon` | float | varies | NYC MTA Bus |

#### T-S2: Scenario 2 — Completeness Issue

**Rule**: SYN001
**Anomaly**: Missing required fields (same as S1 technically; separate scenario for evaluation clarity)
**Injection**: Same as S1; evaluated separately for reporting
**Ground truth**: Same as S1
**Note**: S1 and S2 use the same injection mechanism; S2 is reported separately for VNU-UET clarity
**Expected**: Recall ≥ 0.70 (TIER-2)

#### T-S3: Scenario 3 — Freshness Issue

**Rule**: GTFSSem002
**Anomaly**: Position report is older than 5 minutes
**Injection**: For GPS events, set `timestamp = current_time - uniform(360, 600)` seconds
**Injection rates**: 0.5%, 1%, 2%, 5%
**Ground truth**: `anomaly_metadata{entity_index, stale_seconds = 360-600}`
**Expected**: Recall ≥ 0.70 (TIER-2)
**CI**: BCa bootstrap, 10,000 iterations

| Parameter | Value |
|-----------|-------|
| Staleness threshold | 300s (5 min) |
| Injected stale range | 360–600s (6–10 min) |
| Dataset | NYC MTA Bus GTFS-realtime |

#### T-S4: Scenario 4 — Volume Anomaly

**Rule**: SYN001 / SYN002
**Anomaly**: Burst of anomalous events (sudden spike in NULL or negative values)
**Injection**: Inject 30-second burst of 10× anomaly rate, then return to normal rate
**Injection cycles**: 0%, 1%, 2% baseline + 10× burst for 30s
**Ground truth**: `anomaly_metadata{entity_index, burst_start, burst_end}`
**Expected**: Detection latency < 60s (TIER-2)
**Note**: Volume anomaly tests the system's ability to detect sudden quality degradation, not individual event classification

| Baseline Rate | Burst Rate | Burst Duration | Detection Target |
|:------------:|:----------:|:--------------:|-----------------|
| 0.5% | 5% | 30s | Latency < 60s |
| 1% | 10% | 30s | Latency < 60s |
| 2% | 20% | 30s | Latency < 60s |

#### T-S5: Scenario 5 — Business Rule Violation

**Rules**: SEM001, SEM002, SEM003
**Anomaly**: Values outside context-aware plausibility bounds
**Injection**:
- SEM001: Set `fare_amount = P95 + uniform(0, 2×P95)` (overcharge)
- SEM002: Set `trip_distance = P95 + uniform(0, 2×P95)` (over-distance)
- SEM003: Set `tip_amount = 0.6 × fare_amount` (excessive tip)
**Injection rates**: 0.5%, 1%, 2%, 5%
**Ground truth**: `anomaly_metadata{entity_index, rule_id, injected_value}`
**Expected**: Recall ≥ 0.70 for each rule (TIER-2)
**CI**: BCa bootstrap, 10,000 iterations

| Rule | Field | Injection | Context Bound | Dataset |
|------|-------|-----------|--------------|---------|
| SEM001 | `fare_amount` | `> P95` | L0–L4 P90 threshold | NYC TLC |
| SEM002 | `trip_distance` | `> P95` | L0–L4 P90 threshold | NYC TLC |
| SEM003 | `tip_amount` | `> 50% fare` | Hardcoded ratio | NYC TLC |

#### T-S6: Scenario 6 — Context-Dependent Violation (GPS)

**Rules**: CRS001, CRS002
**Anomaly**: GPS coordinates indicating impossible or suspicious vehicle behavior
**Injection**:
- CRS001a (sustained stop): Set speed = 0.2 km/h for 3+ consecutive updates (>60s)
- CRS001b (spoofing): Set speed = 110 km/h (above highway limit)
- CRS002 (GPS jump): Inject position jump of 500m in 30s
**Injection rates**: 0.5%, 1%, 2%, 5%
**Ground truth**: `anomaly_metadata{entity_index, rule_id, injected_speed_or_jump}`
**Expected**: Precision ≥ 0.70, Recall ≥ 0.70 (TIER-2)
**CI**: BCa bootstrap, 10,000 iterations
**Note**: CRS001 uses `speed < 0.5 km/h AND Δt > 60s` to avoid false positives from GPS jitter

| Rule | Condition | Injection | GPS Error Margin | Dataset |
|------|-----------|-----------|-----------------|---------|
| CRS001a | Sustained low speed | 0.2 km/h, 3+ updates | 0.3–1.2 km/h apparent from jitter | NYC MTA Bus |
| CRS001b | GPS spoofing | 110 km/h | Above 100 km/h threshold | NYC MTA Bus |
| CRS002 | GPS jump | 500m in 30s | 400m threshold >> 10m GPS noise | NYC MTA Bus |

**CRS003 excluded**: Replay suppression gate (NG-4) blocks synthetic duplicate injection. CRS003 is reported as Tier 3\u2014Unmeasurable.

**Caption**: Table 4: Six experiment scenarios for StreamDQ evaluation. S1/S2 test SYN001 (NULL detection). S3 tests GTFSSem002 (freshness). S4 tests burst detection latency. S5 tests SEM rules (business logic). S6 tests CRS rules (GPS anomalies). All scenarios use synthetic injection with controlled rates (0.5\u20135\%) and ground-truth tracking. CRS003 is excluded (Tier 3\u2014Unmeasurable).

**LaTeX**:
```latex
\caption{Six experiment scenarios for StreamDQ evaluation. S1/S2: SYN001 NULL detection.
  S3: GTFSSem002 freshness. S4: burst anomaly detection latency.
  S5: SEM business rule violations. S6: CRS GPS anomalies.
  All use synthetic injection at 0.5\u20135\% rates with ground-truth tracking.
  CRS003 excluded (Tier 3\u2014Unmeasurable).}
\label{tab:experiment-scenarios}
```

---

## T5: Evaluation Metrics

**Chapter**: 3 (Experiments) — §3.3 Evaluation Methodology
**Status**: Ready — from STATISTICAL_PLAN.md + debate report
**Type**: Metrics reference table

### Primary Metrics

|| Metric | Definition | CI Method | Bootstrap | Target Threshold |
|--------|-----------|-----------|:---------:|-----------------|
| **Precision** | TP / (TP + FP) | BCa bootstrap | 10,000 | P > 0.70 for S1–S6 |
| **Recall** | TP / (TP + FN) | BCa bootstrap | 10,000 | R > 0.70 for S1–S6 |
| **F1 Score** | 2·P·R / (P + R) | BCa bootstrap | 10,000 | F1 > baseline for ablation |
| **ΔF1** | F1(context-aware) - F1(static) | Wilcoxon signed-rank | — | > 5pp at L0 cells |
| **P99 Latency** | 99th percentile processing time | Quantile | — | < 500ms |
| **Throughput** | Events processed per second | Mean ± SD | 3 trials | > 1,000 events/sec |

### Statistical Correction

|| Correction | Method | α (per comparison) | Families |
|-----------|-----------|:------:|:------------------:|---------|
| Family 1: Ablation | Holm-Bonferroni | α_adj | RQ1, RQ4 |
| Family 2: Correlation | Holm-Bonferroni | α_adj | RQ2, RQ3 |
| Family 3: Threshold | Holm-Bonferroni | α_adj | RQ5 (S6 precision/recall) |
| Family 4: ML | Holm-Bonferroni | α_adj | RQ6 (ML ablation) |
| **Between-family** | Bonferroni | 0.0083 | 6 RQ families |

**Note**: Total comparisons = 6 RQ × multiple scenarios × multiple rules. We use Holm-Bonferroni within families (uniformly more powerful than Bonferroni) and Bonferroni between families.

### Tier Classification for Results

|| Tier | Meaning | Reporting |
|------|---------|-----------|
| **Tier 1** | Verified (code inspection, prior work) | Report as-is |
| **Tier 2** | Estimated (benchmark required) | Report as `[TIER-2 ESTIMATED]` with 95% CI |
| **Tier 3** | Unmeasurable (known blocker) | Report as `[TIER-3 UNMEASURABLE]` with blocker ID |

**Caption**: Table 5: Evaluation metrics and statistical correction. Precision, recall, F1 use BCa bootstrap CI (10,000 iterations). Statistical tests use Holm\u2013Bonferroni within RQ families (\u03b1_adj per family) and Bonferroni between families (\u03b1=0.0083). All Tier\u20102 results reported with 95\% CI.

**LaTeX**:
```latex
\caption{Evaluation metrics and statistical correction. Precision, recall, F1 use
  BCa bootstrap CI (10,000 iterations). Statistical tests use Holm\u2013Bonferroni
  within RQ families and Bonferroni between families (\u03b1=0.0083).
  All Tier\u20102 results reported with 95\% CI.}
\label{tab:evaluation-metrics}
```

---

## T6: Benchmark Results (Placeholder — after evaluation runs)

**Chapter**: 3 (Experiments) — §3.4–§3.6 Results
**Status**: TIER-2 ESTIMATED — requires benchmark
**Type**: Results table (to be filled after evaluation runs)

### T6a: Scenario Results (All Datasets)

|| Scenario | Rule | Precision | Recall | F1 | 95% CI | n_injected |
|---------|------|:---------:|:------:|:--:|:------:|:----------:|
| S1 | SYN001 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S2 | SYN001 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S3 | GTFSSem002 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S4 | SYN001/SEM | — | — | Detection latency | [TIER-2] | [TIER-2] |
| S5 | SEM001 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S5 | SEM002 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S5 | SEM003 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S6 | CRS001 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| S6 | CRS002 | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| — | CRS003 | [TIER-3] | [TIER-3] | [TIER-3] | — | NG-4 |

### T6b: Context-Aware Ablation

|| Configuration | L0 Coverage | ΔF1 vs Static | p-value | α_adj |
|---------------|:-------------:|:-----------:|:--------------:|:-------:|:-----:|
| Static (global P10/P90) | 0% | baseline | — | — | — |
| L4 (global rolling) | ~30% | [TIER-2] | [TIER-2] | [TIER-2] | 0.0083 |
| L0–L4 (full hierarchy) | ~2–5% | [TIER-2] | [TIER-2] | [TIER-2] | 0.0083 |

### T6c: ML Ablation (Phase 3)

|| Configuration | F1 | 95% CI | ΔF1 vs Rule-Only | p-value |
|-------------|:-------------:|:------:|:-----------------:|:-------:|
| Rule-only (baseline) | [TIER-2] | [TIER-2] | — | — |
| + Bayesian Optimization | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| + Isolation Forest | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |
| Full hybrid (BO+IF) | [TIER-2] | [TIER-2] | [TIER-2] | [TIER-2] |

**Caption**: Table 6: Benchmark results (placeholder). All values are Tier 2\u2014Estimated; benchmark required. CRS003 is Tier 3\u2014Unmeasurable due to NG-4 (replay suppression gate).

**LaTeX**:
```latex
\caption{Benchmark results. All values are Tier 2\u2014Estimated; benchmark required.
  CRS003 is Tier 3\u2014Unmeasurable due to NG-4 (replay suppression gate).}
\label{tab:benchmark-results}
```

---

## Table Production Checklist

|| ID | Table | Source | LaTeX | Status |
|----|------|--------|-------|--------|--------|
|| T1 | Data Quality Dimensions | Redman 1998; FORMULATION.md | booktabs | Ready |
|| T2 | Context Types | FORMULATION.md §2 | booktabs + longtable | Ready |
|| T3 | Comparison with Existing Approaches | COMPETITIVE_TABLE.md | booktabs | Ready |
|| T4 | Experiment Scenarios (summary + T-S1 through T-S6) | STATISTICAL_PLAN.md | booktabs + longtable | Ready |
|| T5 | Evaluation Metrics | STATISTICAL_PLAN.md | booktabs | Ready |
|| T6 | Benchmark Results | (placeholder) | booktabs | TIER-2 placeholder |

**LaTeX requirements**: All tables use `booktabs` (`\toprule`, `\midrule`, `\bottomrule`). Multi-page tables use `longtable`. Consistent column alignment: `l` for text, `c` for numbers, `p{Xcm}` for wrapped text. Caption above table, source note below if needed.
