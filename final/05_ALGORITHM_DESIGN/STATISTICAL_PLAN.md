# Statistical Evaluation Plan

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Author**: Statistical Rigor Reviewer (Agent 4)
**Date**: April 23, 2026
**Status**: Pre-Benchmark — All claims labeled Tier 2 (Estimated) or Tier 3 (Unmeasurable) until benchmark data is collected

---

## Overview

This document specifies the statistical methodology for evaluating "A Context-Aware Framework for Streaming Data Quality Monitoring." It covers hypothesis formulation with explicit null/alternative hypotheses, non-circular experimental design, confidence interval methods, power analysis with sample size justification, and reproducibility requirements. Every metric is labeled with its evidence tier. All point estimates are accompanied by 95% confidence intervals and bootstrap specifications.

**Tier classification**: Tier 1 (Verified) requires measured benchmark data. Tier 2 (Estimated) requires benchmark to confirm. Tier 3 (Unmeasurable) has documented blockers.

---

## Research Questions and Hypotheses

### RQ1: Context-aware thresholds improve F1 over static thresholds

**RQ1**: Does hierarchical context-aware threshold adaptation (L0→L5 fallback) improve detection F1 over static global thresholds?

#### Hypothesis H1-A: Context resolution improves FPR at L0 cells

**H1-A**: Events evaluated at finer-grained context levels (L0) yield lower false-positive rates than events evaluated at the global fallback level (L4).

| Field | Value |
|-------|-------|
| **H₀** | FPR(L0) ≥ FPR(L4) — context resolution provides no improvement |
| **H₁** | FPR(L0) < FPR(L4) — L0 yields strictly fewer false positives |
| **IV** | Context resolution level: `L0` vs. `L4` (global) |
| **DV** | (a) False positive rate per context cell; (b) F1 score per context cell |
| **Expected effect size** | FPR reduction of 2–5pp on L0 cells (Cohen's d ≈ 0.30 from power analysis) |
| **Statistical test** | Wilcoxon signed-rank test (paired, per cell), α = 0.01 (Bonferroni-corrected) |
| **Sample size** | ≥ 30 context cells with ≥ 100 events each |
| **Report** | Mean FPR ± 95% CI (bootstrap percentile, 1,000 iterations), Cohen's d, p-value |

**Falsification criterion**: If the lower bound of FPR(L0)'s 95% CI exceeds FPR(L4)'s point estimate, reject H1-A.

#### Hypothesis H1-B: Fallback degrades threshold specificity monotonically

**H1-B**: As the context lookup falls back from L0 to L4, threshold specificity decreases and false-negative rate increases monotonically.

| Field | Value |
|-------|-------|
| **H₀** | FNR is constant or non-monotonic across L0–L4 |
| **H₁** | FNR(L0) < FNR(L1) < FNR(L2) < FNR(L3) < FNR(L4) |
| **IV** | Fallback level: L0 → L1 → L2 → L3 → L4 |
| **DV** | Threshold specificity (ratio of cell-specific std dev to global std dev); per-level FNR |
| **Statistical test** | Friedman's test across ≥ 30 context cells; post-hoc Nemenyi test for pairwise comparisons |
| **Report** | ΔFNR per level ± 95% bootstrap CI (1,000 iterations), Friedman's χ² statistic, p-value |

**Note**: L5 (physics priors) is categorical, not statistical — excluded from monotonicity test.

#### Hypothesis H1-C: L0 coverage determines aggregate ΔF1

**H1-C**: The aggregate ΔF1 (static vs. context-aware, across all events) is proportional to the fraction of events falling into L0–L2 cells.

| Field | Value |
|-------|-------|
| **H₀** | Aggregate ΔF1 is independent of L0 coverage: ΔF1_aggregate = constant |
| **H₁** | ΔF1_aggregate > constant — higher L0 coverage yields higher aggregate ΔF1 |
| **IV** | Fraction of events at each level: f_L0, f_L1, f_L2, f_L3, f_L4 |
| **DV** | Aggregate ΔF1 across the full event stream |
| **Statistical test** | Spearman rank correlation (ρ_s) between f_L0 and ΔF1_aggregate across ablation runs |
| **Report** | ρ_s ± 95% bootstrap CI (1,000 iterations), scatter plot with regression line |

**Critical caveat**: NYC TLC has estimated L0 coverage of 0–5% (263 zones × 24h). Most events fall to L3/L4. The aggregate ΔF1 is expected to be 1–2pp (not the 5pp target which applies only to L0 cells). **Both metrics must be reported separately.**

---

### RQ2: CRS rules detect GPS anomalies with measurable precision and recall

**RQ2**: Do cross-record rules (CRS001, CRS002, CRS003) achieve measurable precision > 0.70 and recall > 0.60 on synthetically injected GPS anomalies?

#### Hypothesis H3-CRS001: GPS speed bounds detect synthetic speed violations

**H3-CRS001**: CRS001 (Haversine speed bounds [2, 120] km/h) achieves precision > 0.70 on synthetically injected GPS speed spike anomalies in NYC MTA Bus GTFS-realtime streams.

| Field | Value |
|-------|-------|
| **H₀** | P(CRS001) ≤ 0.70 |
| **H₁** | P(CRS001) > 0.70 |
| **IV** | Speed injection: synthetic GPS positions producing computed speed > 120 km/h vs. normal positions (0–80 km/h) |
| **DV** | Precision = fraction of CRS001 violations that match injected speed spikes (entity_index match) |
| **Expected effect size** | P ≈ 0.80–0.90 (hardcoded physics bounds, low false-positive risk) |
| **Statistical test** | One-sided binomial test for precision ≥ 0.70; 95% Wilson CI for precision |
| **Sample size** | ≥ 300 injected anomalies per injection rate (5%, 10%, 20%), 3 independent trials |
| **Report** | Precision point estimate + 95% Wilson CI; precision per injection rate |

#### Hypothesis H3-CRS002: GPS jump detection distinguishes real routes from spoofed positions

**H3-CRS002**: CRS002 (> 100m displacement in 30s) achieves precision > 0.70 and recall > 0.60 on synthetically injected GPS jump anomalies.

| Field | Value |
|-------|-------|
| **H₀** | P(CRS002) ≤ 0.70 OR R(CRS002) ≤ 0.60 |
| **H₁** | P(CRS002) > 0.70 AND R(CRS002) > 0.60 |
| **IV** | GPS jump injection: two positions at similar timestamps (>30s apart), separated by > 100m |
| **DV** | (a) Precision: fraction of CRS002 violations matching injected jumps; (b) Recall: fraction of injected jumps triggering CRS002 |
| **Statistical test** | TOST (two one-sided tests): precision ≥ 0.70 and recall ≥ 0.60; McNemar's test for paired comparison |
| **Sample size** | ≥ 300 injected jumps per injection rate, 3 independent trials |
| **Report** | P ± 95% CI, R ± 95% CI; per-injection-rate breakdown |

#### Hypothesis H3-CRS003: Hash-based deduplication detects injected duplicates [TIER 3 — UNMEASURABLE]

**H3-CRS003**: CRS003 recall cannot be measured until B2 (duplicate injection bug) is fixed.

| Field | Value |
|-------|-------|
| **Status** | **Tier 3 — Unmeasurable** |
| **Blocker** | B2: Duplicate injection does NOT emit both original and duplicate events. CRS003 requires two records to detect a duplicate. |
| **Required fix** | `synthetic_injector.py` must emit the original event AND the duplicate, tagged with `entity_index` and `entity_index_duplicate` |
| **After fix** | McNemar's test for paired comparison; Wilson CI for recall |

---

### RQ3: TQS reflects data quality (non-circular design)

**RQ3**: Does context-decomposed TQS correlate with an independent quality signal better than aggregate TQS?

**THE CIRCULARITY PROBLEM**: RQ3 was originally designed to measure correlation between TQS and injection rate. This is circular by construction: TQS = 1 − violation_rate, and injection_rate ∝ violation_rate. High correlation is guaranteed. The original RQ3 measures experimental self-consistency, not real quality capture.

**NON-CIRCULAR DESIGN**: The revised RQ3 measures whether TQS correlates with an **independent** quality signal — a signal computed without reference to violations or injection rate.

---

## Non-Circular TQS Validation Design

### Chosen Approach: Downstream Task Correlation (Option A — Best)

**Method**: Inject GPS violations into the GTFS-realtime stream. Compute TQS from violation patterns. Measure downstream impact on an independent task (ETA prediction accuracy). If TQS_low → ETA_error_high, the correlation is non-circular because ETA error is computed independently of violation_rate.

#### Data Requirements

| Component | Requirement |
|-----------|-------------|
| **Primary stream** | NYC MTA Bus GTFS-realtime, replayed with synthetic injection |
| **Anomaly injection** | GPS speed violations (CRS001), GPS jumps (CRS002), duplicates (CRS003 after B2 fix) |
| **Injection rates** | 0%, 5%, 10%, 20% per anomaly type, 3 trials each |
| **Independent quality signal** | ETA prediction error: compute expected arrival time using actual vehicle positions; measure deviation when positions are affected by injected violations |
| **Ground truth** | Known schedule (GTFS static) + published real-time delays from MTA API (independent source) |

#### Independent Quality Signal Definition

**ETA_error = |predicted_ETA − actual_ETA|**

- **Baseline (clean data)**: ETA_error_baseline — normal prediction error without injected anomalies
- **Affected records**: Events whose TQS < threshold (e.g., TQS < 0.90) are flagged as low-quality
- **Expected**: TQS_low events should have higher ETA_error than TQS_high events

This signal is **independent** of violation_rate because:
1. ETA_error is computed from schedule data and real position updates — not from violation counts
2. A violation does not automatically cause ETA_error — only violations that affect route computation do
3. The correlation is between **TQS pattern** and **downstream accuracy**, not between TQS and injection_rate

#### Statistical Test for Non-Circularity

| Test | Method | What It Proves |
|------|--------|---------------|
| **Primary test** | Pearson correlation: TQS_low_events → ETA_error_high | TQS predicts downstream quality degradation |
| **Null hypothesis H₀** | ρ(TQS, ETA_error) ≤ 0 — TQS is independent of downstream quality |
| **Alternative H₁** | ρ(TQS, ETA_error) > 0 — higher TQS (better quality) predicts lower ETA error |
| **Secondary test** | Spearman ρ_s(TQS_cell, ETA_error_cell) per context cell | Non-parametric correlation at cell level |
| **F-test** | R²(TQS_composite) > R²(1 − violation_rate) | TQS explains more downstream variance than raw violation rate |

#### Null Hypothesis for Non-Circularity

**H₀**: TQS is independent of downstream quality signal. Specifically:
- ρ(TQS_low_events, ETA_error) = 0, OR
- R²(TQS_composite) ≤ R²(1 − violation_rate) [TQS adds no value over simple violation rate]

**Reject H₀** if: ρ(TQS, ETA_error) > 0 AND R²(TQS_composite) > R²(simple_violation_rate) + 0.05 (minimum meaningful improvement).

#### Sample Size Calculation

| Parameter | Value | Derivation |
|-----------|-------|------------|
| Effect size | ρ ≥ 0.30 | Medium correlation; detectable with moderate sample |
| α | 0.05 | Standard significance level (corrected per comparison) |
| Power | 0.80 | Standard power threshold |
| Required sample | n ≥ 85 windows | From power analysis: r-to-z transformation, n = ((z_α + z_β) / (0.5 × ln((1+r)/(1−r))))² |
| Windows needed | ≥ 85 windows at 5-min intervals | 85 windows × 5 min = 7.1 hours of stream per trial |
| Trials | 3 independent trials | Total: 3 × 7.1 hours = 21.3 hours of replay per injection rate |
| Total (all rates) | 3 trials × 4 rates × 85 windows ≈ 1,020 window measurements | |

#### Fallback: Cross-Dataset Validation (Option C) if Downstream Task is Infeasible

If ETA prediction cannot be implemented, fall back to cross-dataset validation:

- **Compute TQS on NYC TLC** data (SYN/SEM rules, no GPS)
- **Validate against NYC Taxi & Limousine Commission public complaint data** (independent source: fare disputes, passenger complaints per zone)
- **Correlation**: If TQS_low_zones correlate with high-complaint zones, TQS captures real quality

This is weaker (observational, not causal) but still non-circular because complaint data is independent of violation tracking.

---

### Hypothesis H2-B: Per-cell TQS correlates better than aggregate TQS

**H2-B**: TQS computed per context cell shows higher correlation with downstream quality than aggregate TQS.

| Field | Value |
|-------|-------|
| **H₀** | ρ_s(per-cell TQS, downstream_quality) ≤ ρ_s(aggregate TQS, downstream_quality) |
| **H₁** | ρ_s(per-cell TQS, downstream_quality) > ρ_s(aggregate TQS, downstream_quality) |
| **Statistical test** | DeLong's test adapted for Spearman correlation (Fisher z-transformation on ρ_s); 95% bootstrap CI on Δρ_s |
| **Report** | Δρ_s ± 95% CI; per-cell vs. aggregate correlation separately |

---

### Hypothesis H2-C: TQS Variants Are Statistically Distinguishable

**H2-C**: TQS variants V1 (equal weights), V2 (domain-prioritized), V3 (consistency-prioritized) produce statistically distinguishable quality rankings.

| Field | Value |
|-------|-------|
| **H₀** | Kendall's W = 1/3 — all three variants produce the same cell ranking (equivalent) |
| **H₁** | Kendall's W > 1/3 — variants produce different rankings |
| **Statistical test** | Friedman's test across ≥ 30 context cells; post-hoc Nemenyi test for pairwise comparisons |
| **Report** | Kendall's W ± 95% bootstrap CI; which variant pairs differ significantly |

**Note**: TQS weights are design choices, not findings. The test distinguishes variants from each other, not whether any variant is "correct."

---

## Ground Truth Injection Protocol

### Anomaly Types and Injection Parameters

| Anomaly Type | Rule Triggered | Injection Method | What to Track |
|---|---|---|---|
| SYN001 null | SYN001 | Set field to NULL | entity_index, field_name, violation_rule |
| SYN001 NaN | SYN001 | Set float field to NaN | entity_index, field_name, violation_rule |
| SYN002 out-of-range | SYN002 | Set fare_amount outside L0 threshold | entity_index, injected_value, threshold_value |
| SEM001 contextual | SEM001 | Set fare_amount < rolling P10 | entity_index, injected_value, p10_value |
| CRS001 speed spike | CRS001 | Two positions 2km apart in 30s | entity_index, computed_speed, bounds |
| CRS002 GPS jump | CRS002 | Two positions > 100m same timestamp | entity_index, dist_m, time_delta_s |
| CRS003 duplicate | CRS003 | **Emit BOTH original + duplicate** | entity_index, entity_index_duplicate **[FIX B2 FIRST]** |

### What Is Tracked Per Evaluation Run

```python
evaluation_run = {
    "run_id": UUID,
    "injection_rate": float,           # 0.0, 0.05, 0.10, 0.20
    "anomaly_type": str,                # SYN001, CRS001, etc.
    "injected_events": [
        {"entity_index": int, "anomaly_type": str, "injected_value": Any}
    ],
    "detected_violations": [
        {"entity_index": int, "rule_id": str, "detected_at": timestamp_ms}
    ]
}
```

### Violation Matching Criterion

- **Match**: Detected `entity_index` == Injected `entity_index`
- **No fuzzy matching**: Exact index match only
- **Non-match**: False positive if violation detected but entity not injected; false negative if injected entity not detected

### Latency Measurement

**Latency definition**: Time from event arrival (Kafka produce timestamp) to violation stored (PostgreSQL INSERT complete).

```
processing_latency_ms = violation_stored_timestamp_ms − event_arrival_timestamp_ms
```

**NOT**: Internal processing time only (which would exclude queue/network latency). This must be measured end-to-end.

**Known limitation (B6)**: `processing_latency_ms` is currently hardcoded to 0 in the code. Must be fixed before latency evaluation.

---

## Evaluation Metrics with CI Requirements

### Metric Definitions and CI Methods

| Metric | CI Method | Bootstrap Iterations | What to Report | Formula |
|--------|:---------:|:-------------------:|----------------|---------|
| **F1 Score** | Wilson score | ≥ 1,000 | Mean ± 95% CI, per rule and aggregate | F1 = 2·P·R / (P+R) |
| **Precision** | Wilson score | ≥ 1,000 | Point estimate + 95% CI, per rule | P = TP / (TP + FP) |
| **Recall** | Wilson score | ≥ 1,000 | Point estimate + 95% CI, per rule | R = TP / (TP + FN) |
| **Violation Rate** | Clopper-Pearson | ≥ 1,000 | Rate ± 95% CI per context cell | v̂ = n_violations / N_events |
| **P99 Latency** | Percentile bootstrap | ≥ 1,000 | Median, P99, 95% CI on P99 | P99 from latency distribution |
| **Throughput** | t-test bootstrap | ≥ 1,000 | Mean ± std, 95% CI | events_per_second |
| **TQS Composite** | Percentile bootstrap | ≥ 1,000 | Mean ± 95% CI per context cell | TQS_V2 formula |
| **Spearman ρ_s** | Fisher z-transform | ≥ 1,000 | ρ_s ± 95% CI | Correlation coefficient |
| **Cohen's d** | Bootstrap | ≥ 1,000 | d ± 95% CI | Effect size for means |

### Wilson Score CI Formula

For binomial proportions (precision, recall, violation rate):

```
Wilson CI for proportion p̂ with n observations at confidence level γ:

    center = (p̂ + z²/2n) / (1 + z²/n)
    half_width = (z / (1 + z²/n)) × √(p̂(1−p̂)/n + z²/4n²)

    CI = [center − half_width, center + half_width]

where z = 1.96 for 95% CI.
```

### Bootstrap Percentile CI for P99 Latency

```
For latency distribution L with n samples:
  1. Draw n samples with replacement from L
  2. Compute P99 of the resample
  3. Repeat 1,000 times
  4. Report 2.5th and 97.5th percentiles of the 1,000 P99 values as the 95% CI
```

---

## Local vs. Distributed Benchmark Distinction

The framework has two execution modes. All results must be labeled with the mode used.

| Dimension | LocalPipeline | SparkPipeline |
|-----------|:-------------:|:------------:|
| **Architecture** | In-process Python | Apache Spark Structured Streaming |
| **State backend** | Python dict (in-memory) | RocksDB (persistent) |
| **CRS state** | In-process | Per-JVM keyed state |
| **Database** | SQLite (local file) | PostgreSQL (network) |
| **Latency floor** | ~50–200ms (no micro-batch) | 500ms (Spark micro-batch default) |
| **Throughput** | ~1,000–5,000 events/sec (SQLite-bound) | ~10,000+ events/sec (Kafka-partitioned) |
| **Evaluation mode** | Development, unit testing | Full benchmark runs |
| **Reproducibility** | High (controlled env) | Medium (cluster variance) |

**Rule**: Do NOT claim Spark-level latency/throughput numbers from LocalPipeline results. LocalPipeline results are labeled "development-mode estimates."

**Claim language**:
- LocalPipeline: "Estimated P99 latency: ~200ms (LocalPipeline, development mode)" [Tier 2]
- SparkPipeline: "P99 latency: Xms (SparkPipeline, distributed benchmark)" [Tier 1 after benchmark]

---

## Power Analysis Summary

### Power Analysis Framework

For each RQ, the power analysis provides:
- **Effect size**: Expected Δ or ρ from pilot runs or mechanistic reasoning
- **Required n**: Sample size at power = 0.80, α = 0.05 (two-sided) or α = 0.01 (Bonferroni-corrected)
- **Type II risk**: What happens if n is too small

### RQ1 Power Analysis: ΔF1 Detection

| Parameter | Value | Derivation |
|-----------|-------|------------|
| **H₀** | ΔF1 = 0 (no difference between context-aware and static) |
| **H₁** | ΔF1 ≠ 0 |
| **Effect size (L0 cells)** | Cohen's d = 0.30 | Power analysis from COMPLEXITY_ANALYSIS.md: 100 samples/cell, ΔF1 ≥ 5pp |
| **Effect size (all events)** | Cohen's d = 0.10–0.15 | Estimated: 1–2pp ΔF1 on all events |
| **α (per comparison)** | 0.01 | Bonferroni-corrected for 5 RQs (0.05/5) |
| **Power** | 0.80 | Standard threshold |
| **Required n (L0 cells, d=0.30)** | n = 140 context cells | G*Power: t-test, two-sample, α=0.01, d=0.30, power=0.80 |
| **Required n (all events, d=0.15)** | n = 700+ events | Cohen's d = 0.15 requires large samples |
| **In practice** | ≥ 30 windows × 3 trials | 90 data points; acceptable for exploratory, underpowered for confirmatory |
| **Type II risk (n=90)** | ~30–40% at d=0.15 | High risk of missing small aggregate ΔF1 |
| **Mitigation** | Report both L0-specific and aggregate ΔF1; clearly label aggregate as underpowered |

**Power curve note**: The power analysis in the hypotheses doc (COMPLEXITY_ANALYSIS.md, §L0-L5) derives min-samples from power=0.80, α=0.01, Cohen's d=0.30. These parameters apply to L0 cells specifically. Aggregate ΔF1 (all events) has a smaller effect size and requires proportionally more samples.

### RQ2 Power Analysis: CRS Precision/Recall

| Parameter | Value | Derivation |
|-----------|-------|------------|
| **H₀** | P ≤ 0.70 (precision at or below target) |
| **H₁** | P > 0.70 |
| **Effect size (expected)** | P ≈ 0.80–0.90 | Hardcoded physics bounds; high precision expected |
| **α (one-sided)** | 0.05 | Standard for one-sided superiority test |
| **Required n (P=0.80, margin=0.10)** | n = 62 injections | Binomial: P=0.80, half-width=0.10, α=0.05, power=0.80 |
| **Required n (P=0.80, margin=0.05)** | n = 246 injections | Binomial: P=0.80, half-width=0.05, α=0.05, power=0.80 |
| **Required n (P=0.80, margin=0.02)** | n = 1,536 injections | Binomial: P=0.80, half-width=0.02, α=0.05, power=0.80 |
| **Recommended n per trial** | ≥ 300 injections | Conservative: margin ≈ 0.05; sufficient for 95% Wilson CI ≈ ±5pp |
| **Type II risk (n=100)** | ~20% | May miss small precision degradation |
| **Mitigation** | 3 independent trials (total n=900); aggregate across trials |

### RQ3 Power Analysis: TQS Correlation

| Parameter | Value | Derivation |
|-----------|-------|------------|
| **H₀** | ρ(TQS, downstream_quality) = 0 |
| **H₁** | ρ(TQS, downstream_quality) > 0 |
| **Effect size** | ρ ≥ 0.30 | Medium correlation; detectable with moderate sample |
| **α** | 0.05 | Standard significance |
| **Required n (ρ=0.30)** | n = 85 windows | r-to-z: z_α=1.645, z_β=0.842, z_r=0.309, n=85 |
| **Required n (ρ=0.50)** | n = 30 windows | r-to-z: z_r=0.549, n=30 |
| **Required n (ρ=0.20)** | n = 200 windows | r-to-z: z_r=0.203, n=200 |
| **In practice (5-min windows)** | ≥ 85 windows per trial | 85 windows × 5 min = 7.1 hours; 3 trials = 21.3 hours |
| **Type II risk (n=50, ρ=0.30)** | ~40% | Moderate underpowering |
| **Type II risk (n=50, ρ=0.50)** | ~10% | Acceptable |

---

## Summary Power Analysis Table

| RQ | Metric | Effect Size | Test | α | Power | Required n | Current Plan | Status |
|----|--------|:-----------:|------|---|:-----:|:---------:|--------------|--------|
| RQ1 | ΔF1 (L0 cells) | d = 0.30 | Wilcoxon | 0.01 | 0.80 | 140 cells | ≥ 30 cells × 3 trials | **Underpowered** |
| RQ1 | ΔF1 (all events) | d = 0.10–0.15 | Wilcoxon | 0.01 | 0.80 | 700+ events | ~90 windows | **Underpowered** |
| RQ2 | CRS P/R | P ≥ 0.70 | Binomial | 0.05 | 0.80 | 246/injection | 300 × 3 trials | **Adequate** |
| RQ3 | TQS ↔ ETA error | ρ = 0.30 | Pearson | 0.05 | 0.80 | 85 windows | 85 × 3 trials | **Adequate** |
| RQ3 | TQS variants | W > 1/3 | Friedman | 0.05 | 0.80 | 30 cells | ≥ 30 cells | **Adequate** |

**Critical finding**: RQ1 is underpowered for aggregate ΔF1 detection. The 5pp target applies only to L0 cells (5% of events). Aggregate ΔF1 (1–2pp) requires n ≥ 700 — significantly more than the planned 90 windows.

---

## Reproducibility Requirements

### Code and Environment

| Component | Specification |
|-----------|---------------|
| **Framework** | `streamdq/` — see project structure |
| **Python version** | 3.10+ |
| **Key dependencies** | pyspark==3.5.0, pandas, numpy, scipy, scikit-learn |
| **Random seed** | `SEED = 42` — all random number generators seeded identically |
| **Seed logging** | Every evaluation run logs `SEED`, `run_id`, `timestamp` to `evaluation_metadata` table |
| **Container** | `Dockerfile.spark` for reproducible execution environment |

### Data

| Dataset | Source | Version | Size |
|---------|--------|---------|------|
| **NYC TLC Yellow Taxi** | TLC trip record data | January 2024 | ~3M records |
| **NYC MTA Bus GTFS-realtime** | Public GTFS-RT feed | Live replay | ~500 vehicles, 30s updates |
| **Synthetic anomalies** | `synthetic_injector.py` | Configurable | Per injection rate |

### Evaluation Protocol

```
PROTOCOL: run_evaluation.sh

1. WARMUP: 60 seconds of clean data (injection_rate = 0%) — DO NOT MEASURE
2. MEASUREMENT: 600 seconds (10 minutes) per trial — RECORD ALL METRICS
3. TRIALS: 3 independent trials per condition (injection rate, anomaly type)
4. RATES: 0%, 5%, 10%, 20% per anomaly type
5. SEED: Different seed per trial (SEED = 42 + trial_number)
6. OUTPUT: PostgreSQL violations table + metrics_summary table + Prometheus scrape
```

### Verification Checklist

- [ ] All random seeds logged with run_id
- [ ] Warmup period excluded from measurements
- [ ] Violation matching uses exact entity_index
- [ ] Latency measured end-to-end (event arrival → violation stored), not internal-only
- [ ] 95% CI reported for every metric (no point estimates alone)
- [ ] Bootstrap iterations ≥ 1,000 for all CIs
- [ ] L0-specific and aggregate ΔF1 reported separately
- [ ] LocalPipeline results labeled "development-mode estimates"
- [ ] CRS003 results labeled "UNMEASURABLE" until B2 is fixed

---

## Summary of Statistical Requirements

### Pre-Benchmark Checklist (Claims That Need Measurement)

| Requirement | Status | Blocker / Action |
|-------------|:------:|-----------------|
| **CI for all metrics** | Required | Wilson CI or percentile bootstrap; 1,000 iterations minimum |
| **Non-circular RQ3** | Required | Use downstream task correlation (ETA error) or cross-dataset validation |
| **Power analysis for RQ1** | Required | Aggregate ΔF1 is underpowered at n=90; increase to n≥700 or downgrade claim |
| **B2 fix for CRS003** | Required | Must emit both original + duplicate before CRS003 recall is measurable |
| **B6 fix for latency** | Required | `processing_latency_ms` must be measured end-to-end, not hardcoded to 0 |
| **LocalPipeline ≠ SparkPipeline** | Required | Label all latency/throughput results with execution mode |
| **L0 coverage measurement** | Required | Report actual L0 fraction, not just estimates; affects RQ1 interpretation |
| **Bootstrap iterations** | Required | ≥ 1,000 iterations for all CIs; log iteration count in output |
| **Bonferroni correction** | Required | α_adj = 0.01 for 5 RQs (0.05/5); report adjusted p-values |
| **Effect sizes** | Required | Always report Cohen's d, Kendall's W, or Spearman ρ alongside p-values |
| **Tier labels** | Required | Label every metric: Tier 1 (Verified), Tier 2 (Estimated), Tier 3 (Unmeasurable) |

### RED FLAGS — Stop if Detected

| Flag | What It Means | Required Action |
|------|--------------|----------------|
| **Any claim without CI** | Tier 2 or Tier 3 must be labeled explicitly | Add "95% CI: [lo, hi]" or "[NEEDS BENCHMARK]" |
| **RQ3 uses injection rate as ground truth** | Circular design — guaranteed high correlation | Redesign to use independent quality signal |
| **Sample size without power justification** | Underpowered → Type II error risk | Run power analysis; increase n or downgrade claim |
| **"Statistically significant" without p-value** | Claim is unsubstantiated | Report exact p-value and CI |
| **CRS003 recall reported without B2 fix** | Measurement is meaningless | Label Tier 3, document B2 blocker |
| **LocalPipeline latency claimed as Spark result** | Architecture confusion | Add "LocalPipeline (development)" label |
| **Aggregate ΔF1 claimed at 5pp without n≥700** | Claim exceeds evidence | Report L0-specific ΔF1 only; aggregate ΔF1 labeled "underpowered" |
| **P99 latency hardcoded to 0 (B6)** | Measurement is absent | Fix B6 before running latency evaluation |

---

## Evidence Tier Summary

### Tier 1 — Verified (After Benchmark)

| Metric | Requirements |
|--------|-------------|
| SYN001–003 precision/recall | Synthetic injection on NYC TLC, 95% Wilson CI, ≥ 1,000 bootstrap |
| SEM001–003 precision/recall | Synthetic injection on NYC TLC, 95% Wilson CI, ≥ 1,000 bootstrap |
| CRS001/CRS002 precision | Synthetic injection on NYC MTA Bus, 95% Wilson CI, ≥ 300 injections |
| L0 context coverage | Actual measurement from NYC TLC data (not estimate) |
| RQ1 ΔF1 (L0 cells) | Ablation study, n ≥ 140 cells, 95% bootstrap CI |
| RQ3 TQS ↔ downstream quality | Non-circular design, n ≥ 85 windows, ρ ≥ 0.30 |
| P99 latency | End-to-end measurement (not hardcoded), ≥ 1,000 samples |

### Tier 2 — Estimated (Needs Benchmark)

| Metric | Basis | Uncertainty |
|--------|:-----:|:------------:|
| RQ1 ΔF1 (all events) | Power analysis: d = 0.10–0.15 | High — underpowered at n = 90 |
| CRS001/CRS002 recall | Mechanistic: physics bounds hardcoded | Medium — depends on injection quality |
| TQS variants V1/V2/V3 ranking | T-Assess theoretical basis | Medium — weights are ad hoc |
| Throughput (LocalPipeline) | SQLite write speed analysis | High — no distributed benchmark |
| P99 latency (LocalPipeline) | Local profiling | Very high — LocalPipeline ≠ Spark |

### Tier 3 — Unmeasurable (Documented Limitations)

| Metric | Blocker | Fix Required |
|--------|---------|-------------|
| CRS003 recall | B2: duplicate injection broken | Fix `synthetic_injector.py` to emit original + duplicate |
| ML augmentation ΔF1 | Phase 3 optional; CRS003 broken | Complete Phase 3; fix B2 |
| Real-world GPS precision | No labeled authentic GTFS errors | Manual labeling of live feed |
| Distributed Flink latency | Infrastructure not deployed | Deploy SparkPipeline cluster |
| End-to-end throughput (distributed) | LocalPipeline only | Deploy distributed benchmark |

---

## References

- COMPLEXITY_ANALYSIS.md — Statistical properties, convergence rates, min-sample analysis
- HYPOTHESES.md — Full hypothesis formulations with IV/DV/mechanism/falsification criteria
- SIGNIFICANCE_TABLE.md — Novelty claims, effect sizes, CI requirements per claim
- NOVELTY_SCORES.md — PC assessment, critical caveats, RED FLAGS
- FORMULATION.md — TQS formula, violation definitions, evaluation protocol
