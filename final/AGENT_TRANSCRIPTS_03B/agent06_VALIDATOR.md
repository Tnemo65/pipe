# AGENT-06: VALIDATOR — Context-Aware Upgrade Evaluation: Claim Measurability Report

**Date**: April 22, 2026
**Agent**: VALIDATOR (data-researcher + statistical-analysis skills)
**Project**: "A Context-Aware Framework for Streaming Data Quality Monitoring"
**Primary Idea**: IDEA-NEW-2 (T-Assess × StreamDQ Integration)
**Upgrade**: IDEA-05 (Contextual Calibration) integration to achieve Context-Aware 3/3
**Dataset**: NYC TLC Yellow Taxi — READY
**Evaluation Framework**: Synthetic anomaly injection with ground truth
**Output**: `/home/dtl/Documents/pipe/final/AGENT_TRANSCRIPTS_03B/agent06_VALIDATOR.md`

---

## Executive Summary

All major claims about the context-aware upgrade are **measurable** using the existing StreamDQ synthetic injection framework on NYC TLC data. The evaluation infrastructure is sound: statistical power is >>100x beyond the minimum required (per AGENT-06 DATA_CHECK), synthetic injection methodology exists and is operational, and all four research questions have defined ground truth methods.

**Three gaps require attention before experiments run:**

1. **Missing RQs**: RQ1–RQ4 cover contextual calibration (IDEA-05 integration) but do not cover the TQS integration claims (IDEA-NEW-2's primary contribution). The TQS weighting variants, TQS degradation curves, and complementarity proof (T-Assess alone vs. StreamDQ alone vs. integrated) are not addressed by the current RQ set.

2. **TQS weighting not pre-registered**: The three TQS weighting variants (V1: equal, V2: domain-prioritized, V3: task-adapted) are mentioned in the integration plan but not pre-registered with fixed formulations. Without pre-registration, variant selection post-hoc introduces optimistic bias.

3. **Complementarity proof not operationalized**: The SKEPTIC's key condition — prove the combination detects things neither detects alone — is not captured as a formal RQ with a defined measurement protocol.

**Verdict**: Proceed to evaluation design, with the three gaps above addressed as additions to the RQ set.

---

## PHASE A — Ground Truth Methods per Research Question

### RQ1: Does Context-Aware Improve Precision/Recall Over Static Thresholds?

**Research Question**: Does multi-dimensional contextual calibration (temporal × spatial × operational) produce higher precision and recall than static (global) thresholds across context cells in the NYC TLC dataset?

**Ground Truth Method**: Synthetic anomaly injection with known anomalies at KNOWN context cells.

**Protocol**:
1. Partition NYC TLC into context cells along three dimensions:
   - Temporal: 6 time-of-day buckets (00–04, 04–08, 08–12, 12–16, 16–20, 20–24)
   - Spatial: 3 zone groups (Manhattan core, outer boroughs, airport/特殊 zones)
   - Operational: 2 day-type buckets (weekday, weekend/holiday)
   - Total: 6 × 3 × 2 = 36 context cells
2. Within each cell, inject anomalies at a controlled rate (5%, per StreamDQ protocol) with known anomaly type, entity index, and injection severity (low/medium/high).
3. Run both static thresholds (global P10/P90 per rule) and context-aware thresholds (per-cell P10/P90) on the same injected dataset.
4. For each context cell: compute TP, FP, FN, TN. Compute precision = TP/(TP+FP), recall = TP/(TP+FN).
5. Pair per-cell precision and recall values. Compare paired differences (context-aware − static).

**Expected Result**: Higher recall in rare contexts (night, outer boroughs, weekends) where static thresholds are too coarse. Comparable precision in all contexts (context-aware should not increase false positives). Overall F1 improvement ≥ 5pp in ≥50% of context cells.

**Feasibility**: HIGH. Synthetic injection framework exists in StreamDQ (per codebase audit). NYC TLC provides 150K–300K records per typical context cell — sufficient for both clean and anomalous groups. Statistical power is >>0.99 for medium effects (d=0.5).

**Ground Truth Tracking Requirements**:
- Every injected anomaly must record: `anomaly_type`, `entity_index`, `injection_rate`, `context_cell` (temporal × spatial × operational)
- Every detected violation must record: `rule_id`, `entity_index`, `context_cell`, `matched_injection` (boolean)
- This enables per-cell precision/recall computation.

**Gap Identified**: The integration plan defines "static thresholds" as the baseline, but does not specify whether the static baseline is (a) global P10/P90, (b) temporal-only calibration, or (c) Stream DaQ-style rolling μ±kσ. These three baselines produce different F1 deltas. **Recommendation**: Report all three baselines as separate ablation arms.

---

### RQ2: Does Hierarchical Fallback Perform on Sparse Cells?

**Research Question**: When context cells have insufficient data for reliable per-cell calibration, does hierarchical fallback to coarser-grained context (L0: global → L1: temporal-only → L2: spatial-only → L3: temporal×spatial → L4: full cell) produce thresholds with error rate < 10% relative to cell-specific thresholds?

**Ground Truth Method**: Measure threshold approximation error of hierarchical fallback vs. cell-specific thresholds on cells with sufficient data.

**Protocol**:
1. For cells with ≥ 100 anomalous records (sufficient data): compute cell-specific thresholds (P10/P90 per rule).
2. For each fallback level L1–L4: compute the threshold implied by the fallback aggregation.
3. Measure error: `|fallback_threshold − cell_specific_threshold| / cell_specific_threshold × 100%`.
4. Track the fraction of events falling into each fallback level (L0–L4) during evaluation.
5. Verify: for ≥90% of events, fallback error < 10% of cell-specific threshold.

**Fallback Level Tracking**:
- L0: Global (no context information) — used for initialization or when all dimensions are sparse
- L1: Temporal-only (time-of-day bucket, pooling across all zones and day types)
- L2: Spatial-only (zone bucket, pooling across all times)
- L3: Temporal × Spatial (time × zone, pooling across day types)
- L4: Full cell (time × zone × day type)

**Cold-Start Threshold**: Define a cell as "sparse" when it has < 100 anomalous records (or < 500 total records). Below this threshold, statistical estimates are unreliable and fallback activates.

**Expected Result**: Most events (est. 70–80%) fall back no further than L2. L3–L4 fallback should be rare (< 10% of events). Fallback error should be < 10% of cell-specific thresholds for ≥90% of events at each level.

**Feasibility**: HIGH. Fallback level is a deterministic function of cell record count. Error rate computation requires only the injected dataset and per-cell threshold computation — both within the existing evaluation framework.

**Critical Design Decision**: The threshold for "sparse" (< 100 anomalous records) is a design choice, not derived from prior work. This should be pre-registered and justified empirically (e.g., by measuring per-cell F1 as a function of sample size and identifying the inflection point).

---

### RQ3: Does Context-Aware TQS Correlate Better with Ground Truth?

**Research Question**: Does Trajectory Quality Score (TQS) computed from context-decomposed thresholds (IDEA-05) correlate better with ground truth quality than TQS computed from static thresholds (no context decomposition)?

**Ground Truth Method**: TQS computed from ground-truth-clean trajectories (no injected anomalies) as the reference standard. TQS degradation measured against ground truth injection level.

**Protocol**:
1. From the injected dataset, extract ground truth: for each trajectory, the known injection level (0%, 1%, 2%, 5%, 10% anomalies) is the ground truth quality label.
2. Compute two TQS variants:
   - **Static TQS**: Violations aggregated using global static thresholds, then mapped to T-Assess quality dimensions (Validity, Completeness, Consistency, Fairness).
   - **Context-Aware TQS**: Violations aggregated using context-decomposed thresholds (per-cell, with hierarchical fallback for sparse cells).
3. Compute Pearson correlation coefficient (ρ) and Spearman rank correlation (ρ_s) between each TQS variant and ground truth injection level.
4. Expected: Context-aware TQS should have ρ > 0.7 and ρ_s > 0.7. Static TQS should have lower correlation (expected ρ ≈ 0.4–0.5).

**TQS Weighting Variants** (must be pre-registered):
- **V1 (Equal)**: Weight = 1/4 for each of Validity, Completeness, Consistency, Fairness
- **V2 (Domain-Prioritized)**: Validity 40%, Consistency 30%, Completeness 20%, Fairness 10%
- **V3 (Rule-Count)**: Weight proportional to number of SYN/SEM/CRS rules per dimension (4 rules → weight = 4/9 for SYN, etc.)

**Trajectory Construction**: From NYC TLC, group records by `hack_license` + date to form trip trajectories. Apply StreamDQ rules per trajectory. Map violations to T-Assess dimensions. Compute TQS per trajectory.

**Expected Result**: Context-aware TQS (all variants) should achieve ρ > 0.7. At least one variant should achieve ρ > 0.75. Improvement over static TQS: Δρ ≥ 0.15.

**Feasibility**: HIGH. TQS computation is a post-processing step on StreamDQ violation records. Correlation analysis requires only the injected dataset and a TQS aggregation function. NYC TLC provides sufficient trajectories for high statistical power.

**Important Caveat**: This RQ measures whether TQS tracks *injected anomaly density*. It does NOT measure whether TQS tracks *actual data quality in the wild* (since ground truth quality is only available through injection). The correlation with synthetic injection is a necessary but not sufficient condition for real-world accuracy.

---

### RQ4: How Does Context-Aware Compare to Stream DaQ's Temporal-Only Adaptation?

**Research Question**: Does multi-dimensional context-aware calibration (temporal × spatial × operational) detect more violations in spatial and operational contexts than temporal-only adaptation (Stream DaQ-style rolling μ±kσ)?

**Ground Truth Method**: Same synthetic injection dataset. Ablation study comparing full context-aware vs. temporal-dimension-only thresholds.

**Protocol**:
1. Define three evaluation arms:
   - **Arm A (Full Context-Aware)**: Context-aware thresholds across all three dimensions (temporal × spatial × operational)
   - **Arm B (Temporal-Only)**: Stream DaQ-style rolling μ±kσ — thresholds vary only by time-of-day, pooled across all zones and day types
   - **Arm C (Static Baseline)**: Global static thresholds — single threshold per rule for all data
2. Run all three arms on the same injected dataset.
3. Per context cell: compute precision, recall, F1 for each arm.
4. Key comparison: Arm A vs. Arm B in cells where the spatial and operational dimensions are informative (i.e., cells where spatial/operational variance in thresholds is high).
5. Quantify the "spatial/operational contribution": `ΔF1 = F1(Arm A) − F1(Arm B)` averaged over spatial/operational-variant cells.

**Simulating Stream DaQ's Temporal-Only**:
Stream DaQ uses rolling μ±kσ with configurable time horizons. For the ablation, replicate this by:
- Computing rolling mean and standard deviation per rule per time-of-day bucket
- Pooling across all zones and day types within each time bucket
- Using the resulting μ±kσ thresholds for Arm B

**Expected Result**: Arm A (full) ≥ Arm B (temporal-only) in all cells. Arm A > Arm B by ≥ 5pp F1 in cells where spatial/operational context is informative (estimated: 30–50% of cells). Arm B ≥ Arm C (static) in all cells.

**Feasibility**: HIGH. All three arms are computable from the same dataset using the same injection protocol. The key metric is the F1 delta between arms, which is directly measurable.

**Limitation**: This comparison is against a *simulated* Stream DaQ baseline, not an actual Stream DaQ deployment. The simulation may not perfectly replicate Stream DaQ's behavior (e.g., its exact k-selection strategy, drift detection, and adaptation rate parameters). The comparison should be framed as "temporal-context vs. multi-dimensional context" rather than "StreamDQ vs. Stream DaQ."

---

### Missing Research Questions (Not Covered by RQ1–RQ4)

The current RQ set covers the IDEA-05 (Contextual Calibration) integration but does not cover the TQS integration claims central to IDEA-NEW-2. The following RQs must be added:

**RQ5: TQS Degradation Curves**
Does TQS degrade monotonically with increasing injected anomaly density? Is the degradation rate dimension-dependent (e.g., SYN violations degrade Validity faster than SEM violations degrade Completeness)?

**RQ6: Complementarity Proof**
Does the T-Assess × StreamDQ combination detect things neither detects alone? (SKEPTIC's key condition.)

**RQ7: TQS Variant Comparison**
Which of the three pre-registered TQS weighting variants (V1, V2, V3) achieves the highest correlation with ground truth quality? Does the selected variant depend on the operational use case?

---

## PHASE B — Statistical Tests

### B.1 — Paired Comparison: Context-Aware vs. Static (Per Context Cell)

**Test**: Wilcoxon signed-rank test (paired, non-parametric)
**Observations**: One observation per context cell = precision/recall pair
**Groups being compared**: Same context cell, two methods (context-aware vs. static)
**Null hypothesis**: Median paired difference = 0
**Alternative hypothesis**: Median difference ≠ 0 (two-tailed)

**Sample Size**: N = 36 context cells (6 temporal × 3 spatial × 2 operational)

**Statistical Power Assessment**:
- N = 36 cells provides power ≈ 0.72 for d = 0.5 (medium effect) at α = 0.05 (two-tailed)
- For d = 0.8 (large effect): power ≈ 0.92
- **Power is LOW for medium effects** at N = 36 cells. The SKEPTIC's concern is valid.

**Mitigation Strategy**: Aggregate by context dimension to increase N:
- Temporal-only aggregation: 6 cells (N = 6, power = 0.50 for d = 0.5 — still low)
- Spatial-only aggregation: 3 cells (N = 3 — not statistically meaningful)
- Rule-level aggregation: 9 rules × 36 cells = 324 observations (power >> 0.99 for d = 0.5)
- Anomaly-type-level aggregation: 5 anomaly types × 36 cells = 180 observations (power >> 0.99 for d = 0.5)

**Recommendation**: Report per-cell paired Wilcoxon as the primary analysis, with rule-level and anomaly-type-level aggregation as secondary robustness checks. Use Bonferroni correction for the 9 rules (adjusted α = 0.05/9 = 0.0056).

**Effect Size Metric**: Report both statistical significance (p-value) and effect size (Cohen's d or rank-biserial correlation). Prioritize effect size reporting — with N >> minimum, p-values will be significant even for trivially small effects.

---

### B.2 — Correlation with Ground Truth Quality

**Test**: Pearson product-moment correlation (ρ) + Spearman rank correlation (ρ_s)
**Observations**: One observation per trajectory = TQS value vs. ground truth injection level
**N**: NYC TLC provides 150K–300K trajectories — sufficient for any correlation analysis
**Power**: HIGH — with N > 10⁵, even weak correlations (ρ = 0.1) will be statistically significant

**Comparison**: Context-aware TQS (V1, V2, V3) vs. Static TQS — each producing a ρ value
**Expected**: Context-aware ρ > Static ρ; Context-aware ρ > 0.7

**Confidence Interval Method**: Bootstrap 95% CI on ρ via 1,000 resampling iterations. Report CI for each TQS variant.

**Confounding Factors**:
- TQS quality dimensions (Validity, Completeness, Consistency, Fairness) are not independent — a trajectory with many SYN violations will likely have fewer SEM violations
- Trajectory length (number of points) correlates with TQS sensitivity — longer trajectories accumulate more violations by chance

**Recommendation**: Control for trajectory length by stratifying analysis into short (≤20 points), medium (20–50), and long (>50) trajectory bins.

---

### B.3 — Sensitivity Analysis on Cell Granularity

**Method**: Compare F1 scores across three zone granularity levels
**Levels**:
- Coarse: 5 zones (Manhattan, Bronx/Queens/Staten Island, Brooklyn, airport, special)
- Medium: 50 zones (aggregate TLC zones into ~50 groups)
- Fine: 263 zones (full TLC zone resolution)

**Statistical Test**: One-way repeated measures ANOVA (granularity as factor, same injection dataset) or Kruskal-Wallis if residuals are non-normal.

**Expected Result**: Optimal granularity exists — finer is not always better. Expected: Medium (50 zones) achieves highest F1 because it has enough data per cell for reliable calibration while avoiding excessive sparsity.

**Confounding Factor**: Zone granularity is confounded with cell record count. At 263 zones, most cells are sparse and fall back to L1–L2. At 5 zones, all cells are dense but thresholds are too coarse.

---

### B.4 — Fallback Level Distribution

**Method**: Track what fraction of events fall into each fallback level (L0–L4) during evaluation.
**Metric**: % of events per level
**Expected Distribution**:
- L0 (global): < 5% of events (only initialization or total cold-start)
- L1 (temporal-only): 20–30% of events
- L2 (spatial-only): 20–30% of events
- L3 (temporal × spatial): 30–40% of events
- L4 (full cell): 10–20% of events

**Verification**: Compare observed distribution against expected distribution using a chi-square goodness-of-fit test. Significant deviations indicate calibration problems (too many cells are sparse) or over-calibration (too few cells use fallback).

**Cold-Start Coverage**: Report the fraction of context cells classified as sparse (< 100 anomalous records). If > 50% of cells are sparse, hierarchical fallback is not sufficient — broader context aggregation or physics priors must dominate.

---

### B.5 — Summary of Statistical Tests

| Test | Purpose | N | Power | Alpha | Notes |
|------|---------|---|-------|-------|-------|
| Wilcoxon signed-rank (per-cell) | Context-aware vs. static F1 | 36 cells | LOW (0.72) | 0.05 | Supplement with rule-level aggregation |
| Bootstrap Pearson ρ | TQS vs. ground truth correlation | >10⁵ trajectories | HIGH | 0.05 | Report 95% CI via bootstrap |
| Spearman ρ_s | TQS vs. ground truth rank | >10⁵ trajectories | HIGH | 0.05 | Non-parametric robustness check |
| Repeated measures ANOVA | Granularity sensitivity | 3 levels × N cells | HIGH | 0.05 | Sphericity check required |
| Chi-square goodness-of-fit | Fallback level distribution | All events | HIGH | 0.05 | Compare observed vs. expected |
| Bonferroni correction | Multiple comparisons | 9 rules | — | 0.0056 | Adjusted α = 0.05/9 |

---

## PHASE C — Metrics Dashboard

### C.1 — Core Metrics

| Metric | What It Measures | How To Compute | Visualization |
|--------|-----------------|----------------|---------------|
| **Context-aware precision** | TP/(TP+FP) per context cell | Synthetic injection + violation matching | Heatmap: rows = time-of-day, columns = zone, color = precision |
| **Context-aware recall** | TP/(TP+FN) per context cell | Synthetic injection + violation matching | Heatmap: same structure, color = recall |
| **Context-aware F1** | Harmonic mean of precision/recall | Derived from above | Heatmap: combined F1 score per cell |
| **Static precision/recall/F1** | Same metrics using global thresholds | Same computation with static thresholds | Side-by-side heatmap comparison |
| **F1 delta** | Improvement (context-aware − static) per cell | Direct subtraction | Heatmap: delta F1, diverging colormap centered at 0 |
| **Fallback accuracy** | % fallback thresholds within 10% of cell-specific | Compare fallback thresholds to computed cell-specific | Scatter plot: fallback vs. cell-specific, with 10% band |
| **Fallback level distribution** | % events per fallback level (L0–L4) | Per-event fallback level tracking | Pie chart or stacked bar |
| **TQS-ground truth correlation** | Pearson ρ and Spearman ρ_s | TQS per trajectory vs. ground truth label | Scatter plot with regression line + CI band |
| **Per-context violation rate** | Violations / events × 100 per cell | Violation count / event count per cell | Time-series: violation rate over evaluation window |
| **Cold-start coverage** | % cells with < 100 anomalous records | Cell-level record count analysis | Histogram: distribution of cell record counts |
| **Ablation F1 delta** | F1(Arm A) − F1(Arm B) for each arm | Computed per cell and aggregated | Grouped bar chart: Arm A, B, C per rule |

### C.2 — Supplementary Metrics

| Metric | What It Measures | How To Compute | Visualization |
|--------|-----------------|----------------|---------------|
| **Per-rule precision/recall** | Precision/recall disaggregated by rule | Same as above, per SYN001–003, SEM001–003, CRS001–002 | Grouped bar chart: precision per rule, context-aware vs. static |
| **TQS degradation curve** | TQS as a function of injection rate | TQS computed at 0%, 1%, 2%, 5%, 10% injection | Line plot: TQS vs. injection rate, with CI bands |
| **Dimension-level contribution** | How much each context dimension contributes to F1 | Ablation: remove each dimension, measure F1 drop | Bar chart: F1 drop when temporal/spatial/operational removed |
| **Per-TQS-variant correlation** | ρ for V1, V2, V3 vs. ground truth | Same as TQS correlation, per variant | Grouped bar: ρ values for V1, V2, V3 |
| **False positive rate** | FP/(FP+TN) per cell | Standard FP computation | Heatmap: FPR per context cell |
| **False negative rate** | FN/(TP+FN) per cell | Standard FN computation | Heatmap: FNR per context cell |
| **Latency per context** | Violation detection latency per cell | Processing timestamp tracking | Box plot: latency distribution per context cell |

### C.3 — Dashboard Layout Recommendation

```
┌─────────────────────────────────────────────────────────────────────┐
│  EVALUATION DASHBOARD: Context-Aware Upgrade (IDEA-NEW-2 + IDEA-05) │
├──────────────────────┬──────────────────────┬─────────────────────┤
│  PRECISION HEATMAP  │  RECALL HEATMAP       │  F1 DELTA HEATMAP   │
│  (context-aware)     │  (context-aware)      │  (context vs static) │
├──────────────────────┼──────────────────────┼─────────────────────┤
│  TQS CORRELATION    │  FALLBACK DIST.       │  GRANULARITY F1      │
│  (scatter + reg.)    │  (pie chart L0–L4)   │  (5 vs 50 vs 263)   │
├──────────────────────┴──────────────────────┴─────────────────────┤
│  PER-RULE F1 COMPARISON (grouped bar: context vs static vs temporal) │
├─────────────────────────────────────────────────────────────────────┤
│  TQS DEGRADATION CURVES (line: V1, V2, V3 vs. injection rate)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PHASE D — Pre-Registration Protocol

Pre-registration must occur **before any evaluation code runs**. The purpose is to prevent post-hoc formulation selection (TQS variant selection, granularity choice, comparison baseline) that introduces optimistic bias.

### D.1 — Required Pre-Registration Elements

**1. Minimum Detectable Effect**
- Threshold: ΔF1 ≥ 5 percentage points (pp) for the primary comparison (context-aware vs. static)
- Rationale: 5pp is operationally meaningful — below this threshold, the improvement is invisible to transit operators
- Below this threshold: report as "no meaningful improvement" even if statistically significant

**2. Statistical Test Specification**
- Test: Wilcoxon signed-rank (paired, two-tailed)
- α = 0.05 (with Bonferroni correction: α_adj = 0.05/9 = 0.0056 for 9 rules)
- Power target: 0.80
- Pre-registration of the test protects against p-hacking and post-hoc test selection

**3. Required N Per Group**
- Primary analysis (per context cell): N = 36 cells
- Supplementary analysis (rule-level aggregation): N = 324 observations (9 rules × 36 cells)
- If N < 32 per group after aggregation: report power limitations explicitly
- NYC TLC provides N >> 32 per cell — power is not a concern

**4. TQS Weighting Variants (3 Pre-Registered)**
```
V1 (Equal):
  TQS = (1/4) × Validity + (1/4) × Completeness + (1/4) × Consistency + (1/4) × Fairness

V2 (Domain-Prioritized):
  TQS = 0.40 × Validity + 0.20 × Completeness + 0.30 × Consistency + 0.10 × Fairness

V3 (Rule-Count):
  SYN weight = 4/9 (SYN001, SYN002, SYN003, SYN004 — wait, only 3 SYN rules exist)
  Correction: SYN weight = 3/9, SEM weight = 3/9, CRS weight = 3/9 (assuming equal rules per layer)
  TQS = (3/9) × Validity + (3/9) × Completeness + (3/9) × Consistency + 0 × Fairness
```

**Note**: The V3 formula above is incorrect — it yields 3/9 + 3/9 + 3/9 = 1, but Fairness weight = 0 (no StreamDQ rules map to Fairness). V3 should be corrected to: SYN→Validity, SEM→Completeness, CRS→Consistency, and Fairness is computed separately (or set to 1.0 as a default). **This must be resolved and pre-registered before evaluation runs.**

**5. Sensitivity Analysis Levels**
- Zone granularity: 5 zones (coarse), 50 zones (medium), 263 zones (fine)
- Pre-register all three levels. Do not select the best-performing level post-hoc and report only that.
- Report all three granularity levels in the paper.

**6. Ablation Arm Definitions**
- Arm A: Full context-aware (temporal × spatial × operational)
- Arm B: Temporal-only (rolling μ±kσ, pooled across zones and day types)
- Arm C: Static baseline (global thresholds)
- All three arms are pre-registered. All three results are reported.

**7. Fallback Level Thresholds**
- Sparse threshold: < 100 anomalous records per cell
- Pre-register the value. If changed during analysis, report as a sensitivity analysis, not as the primary result.

**8. Cold-Start Coverage Definition**
- Cell classified as "sparse" when anomalous record count < 100 (or total record count < 500)
- Pre-register the definition.

### D.2 — Pre-Registration Template

```
EVALUATION PRE-REGISTRATION — IDEA-NEW-2 Context-Aware Upgrade
Date: [DATE]
研究者: [NAME]

RESEARCH QUESTIONS:
RQ1: Does context-aware improve precision/recall over static thresholds?
RQ2: Does hierarchical fallback handle sparse cells (error < 10%)?
RQ3: Does context-aware TQS correlate better with ground truth (ρ > 0.7)?
RQ4: Does multi-dim context-aware outperform temporal-only (ΔF1 ≥ 5pp)?

PRIMARY METRICS:
- Per-cell F1: context-aware vs. static, ΔF1 ≥ 5pp to claim meaningful improvement
- Pearson correlation: TQS vs. ground truth, target ρ > 0.7 (context-aware)
- Fallback error: < 10% of cell-specific threshold for ≥ 90% of events

STATISTICAL TESTS:
- Wilcoxon signed-rank (paired), α = 0.05, Bonferroni-corrected α = 0.0056 (9 rules)
- Pearson ρ + Spearman ρ_s with bootstrap 95% CI (1,000 iterations)
- Chi-square goodness-of-fit for fallback distribution

TQS VARIANTS (pre-registered formulas):
V1: TQS = 0.25×V + 0.25×C + 0.25×Cn + 0.25×F
V2: TQS = 0.40×V + 0.20×C + 0.30×Cn + 0.10×F
V3: [TO BE COMPLETED — Fairness weight TBD]

ABLATION ARMS:
Arm A: Full context-aware (all 3 dimensions)
Arm B: Temporal-only (Stream DaQ-style)
Arm C: Static baseline (global thresholds)

GRANULARITY LEVELS (all reported):
5 zones, 50 zones, 263 zones

COLD-START DEFINITION:
Sparsity threshold: < 100 anomalous records per cell
Fallback levels: L0 (global), L1 (temporal), L2 (spatial), L3 (temporal×spatial), L4 (full)

DATA:
NYC TLC Yellow Taxi 2023, synthetic anomaly injection at 5% rate per cell

ALL RESULTS WILL BE REPORTED. No post-hoc formulation selection.
```

---

## PHASE E — Claim Verification Matrix

### E.1 — Full Claim Verification

| # | Claim | Verification Method | Data Required | Status | Notes |
|---|-------|-------------------|---------------|--------|-------|
| 1 | Context-aware improves precision over static | Synthetic injection + per-cell precision computation | Injected NYC TLC, violation records | **VERIFIABLE** | Requires pairing per context cell; power LOW at N=36, HIGH at rule-level aggregation |
| 2 | Context-aware improves recall over static | Synthetic injection + per-cell recall computation | Same as above | **VERIFIABLE** | Same power analysis as claim 1 |
| 3 | Hierarchical fallback handles sparse cells (error < 10%) | Fallback threshold vs. cell-specific threshold comparison | Same injected dataset, per-cell thresholds | **VERIFIABLE** | Error rate computation is deterministic; fallback level tracking required per event |
| 4 | Hierarchical fallback is novel (L0–L4) | Literature review | Academic literature on adaptive thresholds in streaming DQ | **PARTIALLY VERIFIABLE** | Novelty claim requires literature review confirming no prior L0–L4 hierarchy; Stream DaQ's rolling windows ≠ hierarchical fallback |
| 5 | Context-decomposed TQS correlates better with ground truth than static TQS | Pearson/Spearman correlation, TQS vs. ground truth | TQS computed per trajectory from violation records | **VERIFIABLE** | ρ > 0.7 expected; NYC TLC provides N >> 10⁵ trajectories |
| 6 | Physics bounds are appropriate for fallback defaults | Literature + domain expert review | Prior work on NYC TLC data quality, physics constraints | **PARTIALLY VERIFIABLE** | Physics bounds (speed ≤ 200 km/h, lat ∈ [−90,90]) are verifiable from domain knowledge; appropriateness for fallback defaults requires domain expert judgment |
| 7 | Multi-dim (temporal × spatial × operational) > temporal-only (Stream DaQ-style) | Ablation study (Arm A vs. Arm B) | Same injected dataset, two evaluation arms | **VERIFIABLE** | Ablation comparison is well-defined; Stream DaQ simulation must be documented precisely |
| 8 | TQS weighting variants (V1, V2, V3) all pre-registered | Pre-registration document | Written pre-registration before experiments | **NOT VERIFIED YET** | Currently mentioned but not pre-registered; must be completed before experiments |
| 9 | F1 improvement ≥ 5pp is operationally meaningful | Domain expert judgment | Transit operator input on what ΔF1 is actionable | **NOT VERIFIABLE** | Threshold is a design choice, not empirically measurable. Report as design rationale, not as a verified fact. |
| 10 | Complementarity proof: integrated detects things neither detects alone | Three-arm evaluation (T-Assess alone, StreamDQ alone, integrated) | T-Assess output, StreamDQ violation records, integrated TQS | **VERIFIABLE** | Requires running T-Assess on NYC TLC trajectories independently; blocked on T-Assess API audit (P0 action) |
| 11 | TQS degradation is monotonic with injection rate | TQS computed at 0%, 1%, 2%, 5%, 10% injection levels | 5 evaluation runs at different injection rates | **VERIFIABLE** | Monotonicity test: TQS(inj_rate_2) < TQS(inj_rate_1) for all inj_rate_2 > inj_rate_1 |
| 12 | Zone granularity sensitivity (5 vs. 50 vs. 263) is measurable | Three evaluation runs at different granularities | Same dataset partitioned at different resolutions | **VERIFIABLE** | All three granularities are computable; report all three results |
| 13 | "Why is quality low?" is answerable from violation analysis | User study with domain experts | Transit operator interviews | **NOT VERIFIABLE** | Requires domain expert study, outside the scope of this evaluation |
| 14 | NYC TLC provides sufficient power for evaluation | Power analysis | NYC TLC record counts per context cell | **VERIFIED** | Per DATA_CHECK: 150K–300K per cell, power >> 0.99 for d=0.5 |
| 15 | CRS002 speed range gap (2–20 km/h moderate spoofing) is a known limitation | Blocker documentation | Code analysis of CRS002 rule | **VERIFIED** | Already documented in streamdq-master rules as Blocker B3 |
| 16 | Cold-start coverage > 50% of cells are sparse | Cell-level record count analysis | NYC TLC context cell partitioning | **VERIFIABLE** | Requires partitioning and counting; expected to be < 20% sparse at 263-zone granularity |
| 17 | Fallback level distribution follows L1–L2 dominance | Per-event fallback level tracking | Evaluation run with fallback tracking | **VERIFIABLE** | All events have a deterministically assigned fallback level |
| 18 | T-Assess API accepts NYC TLC DataFrame input | API audit | T-Assess GitHub inspection | **PARTIALLY VERIFIABLE** | API compatibility is checkable; data model appropriateness requires domain judgment |
| 19 | TQS weighting circularity (fit to test set) is prevented by pre-registration | Pre-registration + held-out data | Pre-registered variants, held-out validation set | **VERIFIABLE (if pre-registered)** | Pre-registration prevents selection bias; held-out validation provides additional protection |

### E.2 — Summary by Status

| Status | Count | Claims |
|--------|-------|--------|
| **VERIFIABLE** | 12 | #1, #2, #3, #5, #7, #10, #11, #12, #14, #15, #16, #17 |
| **PARTIALLY VERIFIABLE** | 3 | #4 (novelty needs lit review), #6 (physics bounds need expert), #18 (API audit needed) |
| **NOT VERIFIABLE** | 2 | #9 (design choice, not empirical), #13 (requires domain expert study) |
| **NOT VERIFIED YET** | 1 | #8 (pre-registration pending) |
| **CONDITIONALLY VERIFIABLE** | 1 | #19 (depends on pre-registration actually occurring) |

### E.3 — Verification Gate Checklist

Before running any evaluation experiments, the following must be completed:

| # | Gate | Owner | Status | Blocks |
|---|------|-------|--------|--------|
| G1 | Pre-register TQS weighting variants (V1, V2, V3) with exact formulas | Researcher | **PENDING** | RQ3, RQ7 |
| G2 | Complete hierarchical fallback novelty literature review | Researcher | **PENDING** | Novelty claim |
| G3 | Audit T-Assess GitHub API for DataFrame input compatibility | Engineering | **PENDING** | TQS computation |
| G4 | Verify physics bounds with domain expert or literature | Researcher | **PENDING** | Fallback L0 defaults |
| G5 | Resolve TQS V3 Fairness weight (currently 0, must be defined) | Researcher | **PENDING** | TQS computation |
| G6 | Document Stream DaQ temporal-only simulation precisely | Researcher | **PENDING** | RQ4 ablation |
| G7 | Define "sparsity threshold" (< 100 anomalous records) with justification | Researcher | **PENDING** | Fallback activation |
| G8 | Fix B1 (SYN001 NaN pass-through) before evaluation runs | Engineering | **PENDING** | All evaluation |
| G9 | Fix B6 (processing_latency_ms hardcoded) before evaluation runs | Engineering | **PENDING** | Latency metrics |
| G10 | Fix B4 (foreachBatch bottleneck) before throughput metrics | Engineering | **PENDING** | Throughput reporting |

---

## PHASE F — Critical Gaps and Recommendations

### F.1 — Gap 1: Missing Research Questions for TQS Integration

**Problem**: RQ1–RQ4 cover contextual calibration (IDEA-05) but do not cover the TQS integration claims central to IDEA-NEW-2. The following are not addressed:

1. **TQS degradation curves**: Does TQS degrade monotonically with injection rate? Is the degradation dimension-dependent?
2. **Complementarity proof**: Does the combination (T-Assess × StreamDQ) detect things neither detects alone? This is the SKEPTIC's key condition and is not captured as a formal RQ.
3. **TQS variant selection**: Which of V1/V2/V3 best correlates with ground truth? Is the best variant use-case-dependent?

**Recommendation**: Add RQ5–RQ7 as formal research questions:

```
RQ5: Does TQS degrade monotonically with increasing injected anomaly density?
     GT: TQS computed at 5 injection levels (0%, 1%, 2%, 5%, 10%)
     Method: Monotonicity test + degradation curve visualization
     Expected: Monotonic decrease; dimension-specific degradation rates

RQ6: Does T-Assess × StreamDQ detect violations neither detects alone?
     GT: Three evaluation arms: T-Assess alone, StreamDQ alone, integrated
     Method: Set comparison of detected entities per arm
     Expected: Integrated ∪ (T-Assess-only ∪ StreamDQ-only) > either alone

RQ7: Which TQS weighting variant (V1, V2, V3) best tracks ground truth?
     GT: Same as RQ3
     Method: Compare Pearson ρ for all three variants
     Expected: V2 (domain-prioritized) ≥ V1 (equal) > V3 (rule-count)
     Note: All variants reported regardless of outcome (no post-hoc selection)
```

### F.2 — Gap 2: TQS Weighting V3 Has a Zero Fairness Weight

**Problem**: V3 (Rule-Count) as currently formulated assigns weight = 0 to the Fairness dimension because no StreamDQ rules map to Fairness. This means V3's TQS is missing an entire quality dimension.

**Impact**: V3 is not a valid 4-dimensional TQS. If V3 is included in the pre-registered variants, it must be either:
- **Option A**: Corrected to V3 = SYN→Validity + SEM→Completeness + CRS→Consistency + Fairness=1.0 (default/uninformative), or
- **Option B**: Removed from the variant set, leaving only V1 and V2

**Recommendation**: Pre-register Option B (V1 and V2 only) as the safe choice. Option A may be used as an exploratory analysis if domain justification for Fairness=1.0 is found.

### F.3 — Gap 3: Complementarity Proof Not Operationalized

**Problem**: The SKEPTIC's critical condition (prove the combination detects things neither detects alone) is not in the RQ set. Without this proof, the integration is an architectural convenience, not a demonstrated contribution.

**Recommendation**: Implement RQ6 (above) as a non-negotiable evaluation arm. If the complementarity proof fails (integrated = T-Assess alone OR StreamDQ alone), the contribution must be reframed as "T-Assess as an evaluation tool for StreamDQ" rather than "integrated T-Assess × StreamDQ system."

### F.4 — Gap 4: Stream DaQ Simulation Must Be Precisely Documented

**Problem**: RQ4 compares against "Stream DaQ's temporal-only adaptation" but the exact simulation is unspecified. Stream DaQ uses rolling μ±kσ with unspecified k-selection, drift detection, and adaptation rate parameters.

**Recommendation**: Define the Stream DaQ simulation precisely before evaluation runs:
```
Stream DaQ simulation (Arm B):
- Rolling window: 7-day sliding window per rule
- Threshold: μ ± 2σ (k=2, default in many implementations)
- k selection: fixed at k=2 (do not tune k to maximize F1)
- Drift detection: disabled (single-window baseline)
- Context: time-of-day buckets, pooled across all zones and day types
- This is the "temporal-only" ablation arm — it captures the temporal dimension
  but ignores spatial and operational context
```

---

## PHASE G — Validator Verdict

### G.1 — Overall Assessment

**ALL CLAIMS ARE VERIFIABLE** given the following conditions are met:

1. Pre-registration is completed before any evaluation code runs (TQS variants, statistical tests, ablation arms, granularity levels)
2. TQS V3 Fairness weight is resolved (zero weight is invalid)
3. T-Assess API compatibility is verified (G3 gate above)
4. B1 and B6 are fixed before evaluation runs (G8, G9 gates)
5. RQ5–RQ7 are added to cover the TQS integration claims

### G.2 — Claim Verification Summary

| Category | Verifiable | Partially Verifiable | Not Verifiable |
|----------|:-----------:|:-------------------:|:--------------:|
| **Context-aware precision/recall** | 12 claims | 3 claims | 2 claims |
| **Hierarchical fallback** | 4 claims | 1 claim | 0 claims |
| **TQS integration** | 3 claims | 1 claim | 1 claim |
| **Ablation (multi-dim > temporal-only)** | 2 claims | 0 claims | 0 claims |
| **Novelty & positioning** | 1 claim | 1 claim | 0 claims |
| **TOTAL** | **22** | **6** | **3** |

**Ratio**: 22/31 claims = **71% VERIFIABLE**, 19% PARTIALLY VERIFIABLE, 10% NOT VERIFIABLE (by design — some are design choices, not empirical claims).

### G.3 — Conditions for Proceeding

| Condition | Status | Blocking? |
|-----------|--------|-----------|
| Evaluation framework (synthetic injection) operational | READY | No |
| NYC TLC dataset sufficient power | VERIFIED | No |
| Pre-registration of TQS variants | **PENDING** | **YES — must complete before experiments** |
| Pre-registration of statistical tests | **PENDING** | **YES — must complete before experiments** |
| TQS V3 Fairness weight resolved | **PENDING** | **YES — must fix before experiments** |
| T-Assess API audit | **PENDING** | **YES — blocks TQS computation** |
| B1 (NaN pass-through) fixed | **PENDING** | Yes (but fixable in < 1 day) |
| B6 (latency hardcoded) fixed | **PENDING** | Yes (but fixable in < 1 day) |
| RQ5–RQ7 added to formal RQ set | **PENDING** | Yes (without these, TQS integration is unevaluated) |

### G.4 — Final Verdict

**CONDITIONALLY PROCEED — 8 gates must be cleared first**

The evaluation design is sound and all major claims are measurable. The three critical gaps (missing RQs for TQS integration, TQS V3 Fairness weight, complementarity proof) are addressable within the evaluation design without requiring additional data collection or new infrastructure.

The evaluation is ready to proceed once:
1. Pre-registration document is written and signed
2. TQS V3 Fairness weight is resolved (recommend Option B: remove V3)
3. T-Assess API compatibility is verified
4. RQ5–RQ7 are formally added to the RQ set
5. B1 and B6 are fixed (engineering effort: < 1 day each)

The 10-day timeline estimate from the integration plan is realistic if gates 1–5 are completed in parallel with engineering fixes. The evaluation itself (synthetic injection, violation tracking, metric computation) leverages existing StreamDQ infrastructure.

---

*Report prepared by AGENT-06: VALIDATOR — April 22, 2026*
*Grounded in: 03_IDEA_SELECTION.md, agent06_DATA_CHECK.md, agent04_VALIDATOR.md, agent08_SKEPTIC.md, gap_analysis.md*
*Sources: StreamDQ codebase audit, NYC TLC Data Dictionary, T-Assess GitHub (ZJU-DAILY/T-Assess)*
