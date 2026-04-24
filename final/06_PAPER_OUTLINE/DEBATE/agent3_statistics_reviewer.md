# Statistical Rigor Review: Thesis Outline

**Reviewer Role**: Statistics/Methodology Reviewer
**Date**: April 24, 2026
**Document Reviewed**: `final/06_PAPER_OUTLINE/thesis_outline.md`, `final/05_ALGORITHM_DESIGN/STATISTICAL_PLAN.md`, `final/05_ALGORITHM_DESIGN/HYPOTHESES.md`, `final/05_ALGORITHM_DESIGN/COMPLEXITY_ANALYSIS.md`, `final/04_NOVELTY_CONTRIBUTION/ML_INTEGRATION_REDESIGN.md`
**Status**: Tier 2 (Estimated) — All claims labeled appropriately; benchmark required

---

## Executive Summary

The thesis presents a well-structured research platform with a three-layer rule taxonomy (SYN/SEM/CRS), hierarchical context-aware thresholds (L0–L5), and ML-augmented calibration. The statistical methodology is **partially sound** but has **critical gaps** that must be addressed before submission. The most serious issues are:

1. **Multiple comparisons are undercorrected** (α = 0.05 vs. α_adj ≈ 0.0036)
2. **Power analysis is incomplete** for RQ1 aggregate ΔF1
3. **RQ2 metric definition is circular and undefined**
4. **Bootstrap iterations (1,000) are below publication standard (10,000)**

This review provides specific, actionable fixes for each issue.

---

## 1. RQ Statistical Soundness Assessment

### 1.1 RQ1: ΔF1 ≥ 5pp over static thresholds

**Claim**: Context-aware thresholds improve F1 by ≥ 5 percentage points over static thresholds.

**Current test**: McNemar's test for paired comparisons

**Issues identified**:

| Issue | Severity | Evidence |
|-------|----------|----------|
| **McNemar's test inappropriate for F1** | **CRITICAL** | McNemar's test compares two **binary classifiers** on paired data (correct/incorrect per entity). F1 is a **composite metric** (2·P·R/(P+R)) that cannot be decomposed into binary correct/incorrect per entity. An event can be "partially correct" — detected by one threshold but not another, contributing differently to P vs. R. |
| **5pp target applies only to L0 cells (5% of events)** | **MAJOR** | `HYPOTHESES.md` H1-A revision explicitly states: "The original claim 'ΔF1 ≥ 5pp' applies **only** to events in L0 context cells (approximately 5% of events)." The thesis outline (thesis_outline.md §3.6) states: "L0 coverage is estimated at 2–5% of events." Aggregate ΔF1 is estimated at 1–2pp. The RQ1 claim as written is **misleading** — it implies 5pp improvement across all events. |
| **Power analysis missing for aggregate ΔF1** | **MAJOR** | STATISTICAL_PLAN.md power table shows: RQ1 aggregate ΔF1 at d=0.10–0.15 requires n ≥ 700 events. Current plan: 3 trials × 600s = ~90 windows. **Type II risk is ~30–40%** — high probability of missing the true effect. |
| **Wilcoxon signed-rank requires continuous DV** | **MINOR** | HYPOTHESES.md specifies Wilcoxon signed-rank test, but this requires the DV to be continuous. FPR per context cell is continuous; aggregate F1 is averaged. Wilcoxon is appropriate for per-cell comparisons. |

**Corrected hypothesis formulation**:

```
H1: Events evaluated at L0 context cells achieve lower FPR than events 
    evaluated at L4 global fallback.

H₀: FPR(L0) = FPR(L4)
H₁: FPR(L0) < FPR(L4)

Effect size: Cohen's d = 0.30 (from power analysis, HYPOTHESES.md)
α_adj = 0.0083 (Bonferroni for 6 RQs)
Test: Wilcoxon signed-rank (paired per cell)
n ≥ 140 context cells (G*Power)

Aggregate claim: Context-aware thresholds reduce aggregate FPR 
by [MEASURED]pp (95% CI: [lo, hi]), benefiting [MEASURED]% of events 
at L0 cells (95% CI: [lo, hi]).
```

**Verdict**: **Flawed — requires revision**

**Required changes**:
1. Split RQ1 into two sub-claims: (a) L0-specific FPR reduction (5pp target, powered), (b) Aggregate ΔF1 (expected 1–2pp, labeled as exploratory/underpowered)
2. Replace McNemar's test with Wilcoxon signed-rank for paired per-cell FPR comparison
3. Add power analysis section to thesis documenting n=140 required, n=90 planned, Type II risk ≈ 35%

---

### 1.2 RQ2: Fallback accuracy < 10% error

**Claim**: Hierarchical L0–L5 fallback maintains quality when context cells are sparse.

**Issues identified**:

| Issue | Severity | Evidence |
|-------|----------|----------|
| **"Accuracy" metric is undefined** | **CRITICAL** | HYPOTHESES.md H1-B measures "threshold specificity" and "per-level FNR" — not "accuracy." thesis_outline.md §3.6 uses "fallback accuracy < 10% error" with no definition. Accuracy = (TP + TN) / (TP + TN + FP + FN). In anomaly detection, TN is undefined (we don't know how many "true negatives" exist in a stream). The metric is **non-operational**. |
| **"Fallback error" definition is unclear** | **CRITICAL** | What does "fallback error" mean? (a) FNR increase at fallback levels vs. L0? (b) fraction of events falling to L5? (c) threshold prediction interval width? The thesis outline says "Fallback accuracy < 10% error" but never defines "error." |
| **H1-B tests monotonicity, not accuracy** | **MAJOR** | HYPOTHESES.md H1-B hypothesis: "FNR(L0) < FNR(L1) < FNR(L2) < FNR(L3) < FNR(L4)." This is a monotonicity test, not an accuracy test. The RQ2 claim and the H1-B hypothesis are **mismatched**. |
| **Friedman's test with Nemenyi post-hoc is appropriate** | **POSITIVE** | The statistical test in HYPOTHESES.md H1-B (Friedman's test + Nemenyi) is appropriate for comparing ≥3 related samples (L0–L4 FNR). This is sound. |

**Corrected RQ2 formulation**:

```
RQ2: Does the L0–L5 hierarchical fallback maintain monotonic degradation
     in threshold specificity from L0 to L4?

H₀: FNR is constant or non-monotonic across L0–L4
H₁: FNR(L0) < FNR(L1) < FNR(L2) < FNR(L3) < FNR(L4)

Metric: Threshold specificity = σ_cell / σ_global
        (ratio of cell-specific std dev to global std dev)
Test: Friedman's test across ≥30 context cells
      Post-hoc: Nemenyi test for pairwise comparisons
α_adj = 0.0083 (Bonferroni for 6 RQs)

Fallback coverage: [MEASURED]% of events fall to L4/L5 
(95% CI: [lo, hi]).
```

**Verdict**: **Flawed — requires complete reformulation**

**Required changes**:
1. Replace "accuracy < 10% error" with specific operational metrics (FNR, threshold specificity, or L4/L5 coverage fraction)
2. Align RQ2 claim with H1-B hypothesis (both should test monotonicity)
3. Define "fallback error" explicitly: either FNR(L4) − FNR(L0) or threshold specificity degradation ratio
4. Report both: (a) monotonicity test result (Friedman's χ², p-value), (b) effect size per level (ΔFNR ± 95% CI)

---

### 1.3 RQ3: TQS correlates with injection rate (ρ > 0.7)

**Claim**: Trajectory Quality Score correlates with data quality (ρ > 0.7).

**Issues identified**:

| Issue | Severity | Evidence |
|-------|----------|----------|
| **Pearson ρ vs. Spearman ρ_s — which is appropriate?** | **MAJOR** | STATISTICAL_PLAN.md RQ3 uses Pearson correlation. HYPOTHESES.md H2-A uses Spearman ρ_s. Pearson assumes linear relationship and normal residuals; Spearman assumes monotonic relationship only. TQS is bounded [0, 1] and likely non-normal; **Spearman ρ_s is more appropriate**. Additionally, TQS–injection_rate relationship may be non-linear (e.g., logarithmic at high rates). Spearman is robust to non-linearity. |
| **ρ > 0.7 threshold is arbitrary** | **MINOR** | No justification for 0.7 vs. 0.5 or 0.8. Cohen's conventions: ρ = 0.10 (small), 0.30 (medium), 0.50 (large). ρ > 0.7 is "very large." The threshold should be justified from the application domain — what correlation is meaningful for alerting purposes? |
| **TQS variants = 3 comparisons → Bonferroni correction** | **MAJOR** | HYPOTHESES.md H2-C tests V1 vs. V2 vs. V3 using Friedman's test (already accounts for 3 comparisons within the test). However, the primary RQ3 claim (TQS correlates with quality) is tested once per variant. If reporting correlation separately for V1, V2, V3, this is **3 comparisons** requiring α_adj = 0.05/3 ≈ 0.017. |
| **Non-circular design is sound but complex** | **POSITIVE** | STATISTICAL_PLAN.md §RQ3 identifies the circularity problem (TQS = 1 − violation_rate, injection_rate ∝ violation_rate). The proposed fix (ETA prediction accuracy as independent signal) is methodologically sound. However, the ETA prediction task must be **pre-registered** and the implementation must be validated before use. |

**Corrected RQ3 formulation**:

```
RQ3: Does per-cell TQS correlate with downstream quality signal?

H₀: ρ_s(TQS_cell, ETA_error) ≤ 0
H₁: ρ_s(TQS_cell, ETA_error) > 0

Metric: Spearman rank correlation (ρ_s) — robust to non-linearity,
        bounded [0, 1], non-normal distributions
Independent signal: ETA prediction error on NYC MTA Bus
  (computed from GTFS schedule + actual positions, 
   NOT from violation counts)
Primary variant: V2 (domain-prioritized weights)
Alternative variants: V1, V3 (reported separately, α_adj = 0.017)
Sample size: n ≥ 85 windows (power analysis, STATISTICAL_PLAN.md §RQ3)
Test: One-sided Fisher z-test for ρ_s > 0
α_adj = 0.0083 (Bonferroni for 6 RQs)

Non-circularity verification: Report ρ_s(TQS, violation_rate) 
separately — if ρ_s(TQS, violation_rate) > ρ_s(TQS, ETA_error), 
the TQS–ETA correlation is spurious (dominated by circular component).
```

**Verdict**: **Needs revision — Spearman preferred; non-circular design needs ETA validation**

**Required changes**:
1. Use Spearman ρ_s (not Pearson ρ) for RQ3
2. Pre-register ETA prediction task before evaluation
3. Justify ρ > 0.7 threshold OR lower to ρ > 0.5 (medium-large)
4. Report both ρ_s(TQS, ETA_error) and ρ_s(TQS, violation_rate) to verify non-circularity
5. Apply Bonferroni correction if reporting V1/V2/V3 separately

---

### 1.4 RQ4: CRS layer adds incremental F1

**Claim**: Cross-record rules add incremental F1 over SYN-only and SYN+SEM baselines.

**Issues identified**:

| Issue | Severity | Evidence |
|-------|----------|----------|
| **Same ablation design as RQ1 — same statistical concerns** | **CRITICAL** | RQ4 ablation: SYN-only vs. SYN+SEM vs. SYN+SEM+CRS. This is identical structure to RQ1 (context-aware vs. static). The same issues apply: McNemar's test is inappropriate for F1; 5pp target may not apply to CRS layer contribution. |
| **CRS rules evaluated on different datasets** | **MAJOR** | CRS001/CRS002 are evaluated on NYC MTA Bus (GPS data). SYN/SEM are evaluated on NYC TLC (zone-level data). The ablation study cannot compare SYN+SEM (NYC TLC) against CRS (NYC MTA Bus) because they operate on **different event streams**. The ablation design is **internally inconsistent**. |
| **CRS003 excluded from RQ4** | **MINOR** | thesis_outline.md §3.5 excludes CRS003 (Tier 3 — UNMEASURABLE). This is correct but means RQ4 only evaluates CRS001 and CRS002. The claim "CRS layer adds incremental F1" is incomplete. |

**Corrected RQ4 formulation**:

```
RQ4: Do cross-record GPS rules (CRS001, CRS002) achieve measurable 
     precision > 0.70 and recall > 0.60 on NYC MTA Bus GTFS-realtime?

Note: CRS rules cannot be ablated against SYN/SEM rules because 
they operate on different datasets (NYC MTA Bus vs. NYC TLC).

H₀ for CRS001: P(CRS001) ≤ 0.70
H₁ for CRS001: P(CRS001) > 0.70

H₀ for CRS002: P(CRS002) ≤ 0.70 OR R(CRS002) ≤ 0.60
H₁ for CRS002: P(CRS002) > 0.70 AND R(CRS002) > 0.60

Metric: Precision, Recall on synthetic GPS speed spike (CRS001) 
        and GPS jump (CRS002) injection
Dataset: NYC MTA Bus GTFS-realtime (GPS coordinates required)
Test: One-sided binomial for precision; two-sided for recall
Sample size: n ≥ 300 injections per rate × 3 trials = 900 total
             (sufficient for margin ≈ ±5pp at P = 0.80)
α_adj = 0.0083 (Bonferroni for 6 RQs)
```

**Verdict**: **Flawed — ablation design is internally inconsistent; reformulate as CRS-only evaluation**

**Required changes**:
1. Reframe RQ4 as CRS001/CRS002 precision/recall evaluation (not ablation)
2. State explicitly: CRS cannot be compared against SYN/SEM because they operate on different datasets
3. Report CRS001 precision ± 95% Wilson CI, CRS002 precision + recall ± 95% Wilson CI
4. Exclude CRS003 from primary claims (Tier 3 — UNMEASURABLE)

---

### 1.5 RQ5: CRS001/CRS002 precision > 0.70

**Claim**: CRS001 and CRS002 achieve precision > 0.70 on NYC MTA Bus injection.

**Issues identified**:

| Issue | Severity | Evidence |
|-------|----------|----------|
| **Target: P > 0.70 AND R > 0.60, or P > 0.70 only?** | **MAJOR** | HYPOTHESES.md H3-CRS001 states P > 0.70 only. HYPOTHESES.md H3-CRS002 states P > 0.70 AND R > 0.60. thesis_outline.md §3.5 states "CRS P/R > 0.70" — inconsistent across documents. |
| **CRS002 recall < 60% is a known limitation** | **MAJOR** | B3 (CRS002 speed range gap): speeds 2–20 km/h are not validated. This is not a bug — it's a documented gap in detection capability. Achieving R > 0.60 may require addressing B3. |
| **CRS003 excluded — is RQ5 scope correct?** | **MINOR** | thesis_outline.md §3.5 correctly excludes CRS003. RQ5 should be renamed "RQ5: CRS001/CRS002 achieve measurable precision > 0.70" (CRS003 moved to Tier 3 limitations). |
| **Binomial test with continuity correction is appropriate** | **POSITIVE** | HYPOTHESES.md specifies one-sided binomial test with Wilson CI. This is correct for proportion targets. |

**Corrected RQ5 formulation**:

```
RQ5: Do GPS cross-record rules achieve measurable precision > 0.70 
     on synthetically injected anomalies in NYC MTA Bus GTFS-realtime?

CRS001 (H3-CRS001):
  H₀: P(CRS001) ≤ 0.70
  H₁: P(CRS001) > 0.70
  Test: One-sided binomial (H₀: P ≤ 0.70)
  CI: 95% Wilson score interval

CRS002 (H3-CRS002):
  H₀: P(CRS002) ≤ 0.70 OR R(CRS002) ≤ 0.60
  H₁: P(CRS002) > 0.70 AND R(CRS002) > 0.60
  Test: TOST (two one-sided tests) for equivalence margins
  CI: 95% Wilson score interval for P and R separately

CRS003: Tier 3 — UNMEASURABLE (NG-4 blocker)
  Reported as limitation, not included in RQ5 claims.

Sample size: n ≥ 300 injections per rate × 3 trials
α_adj = 0.0083 (Bonferroni for 6 RQs)
```

**Verdict**: **Sound with revision — clarify P-only vs. PAND R target**

**Required changes**:
1. Align RQ5 target across documents: CRS001 → P > 0.70; CRS002 → P > 0.70 AND R > 0.60
2. Acknowledge B3 (speed range gap 2–20 km/h) as a known limitation affecting CRS002 recall
3. Rename to "RQ5: CRS001/CRS002 precision > 0.70" (remove recall target from RQ name)

---

### 1.6 RQ6: ML augmentation improves F1

**Claim**: ML-augmented threshold calibration improves F1 over rule-only.

**Issues identified**:

| Issue | Severity | Evidence |
|-------|----------|----------|
| **McNemar's test is appropriate for RQ6** | **POSITIVE** | ML_INTEGRATION_REDESIGN.md §5.4 correctly specifies McNemar's test for 4-arm ablation (rule-only vs. IF vs. LSTM vs. hybrid). McNemar's test compares two classifiers on paired binary outcomes (correct/incorrect per entity). This is **appropriate for RQ6** because the ablation evaluates per-entity detection outcomes, not composite metrics. |
| **4 ablation arms = 3 comparisons → Bonferroni correction** | **MAJOR** | ML_INTEGRATION_REDESIGN.md specifies: (1) Arm 2 vs. Arm 1 (IF benefit), (2) Arm 3 vs. Arm 1 (LSTM benefit), (3) Arm 4 vs. Arm 1 (full hybrid benefit). That's **3 comparisons** from the same 1,000-event test set. With α = 0.05, α_adj = 0.05/3 ≈ 0.017 per comparison. The document does not apply Bonferroni correction. |
| **IF↔P90 correlation threshold undefined** | **MAJOR** | ML_INTEGRATION_REDESIGN.md §3.1.4 states IF is conditional on "IF↔P90 correlation < 0.8." But where is this measured? How is it tested? What's the statistical test? This is an **undefined conditional gate**. |
| **Negative result protocol is well-designed** | **POSITIVE** | ML_INTEGRATION_REDESIGN.md §5.7 specifies an explicit negative result protocol. This is scientifically honest and prevents p-hacking. |

**Corrected RQ6 formulation**:

```
RQ6: Does ML-augmented threshold calibration improve F1 over 
     rule-only thresholds?

Ablation design (4 arms, same 1,000-event test set):
  Arm 1 — RULE_ONLY (baseline)
  Arm 2 — IF_AUGMENTED (Isolation Forest × threshold)
  Arm 3 — LSTM_AUGMENTED (LSTM pre-filter for CRS)
  Arm 4 — FULL_HYBRID (IF + LSTM + BO)

Statistical tests (3 comparisons):
  Test 1: McNemar's test — Arm 2 vs. Arm 1 (IF benefit)
  Test 2: McNemar's test — Arm 3 vs. Arm 1 (LSTM benefit)
  Test 3: McNemar's test — Arm 4 vs. Arm 1 (full hybrid benefit)

α_adj = 0.05 / 3 = 0.017 per comparison (Bonferroni)

Conditional gate (pre-registered):
  IF correlation with P90 < 0.8 → proceed with IF arm
  IF correlation with P90 ≥ 0.8 → skip IF arm, report as redundant
  Measurement: Pearson ρ(IF_score, P90) across calibration window

Effect size: Odds ratio = b / c (discordant pairs)
  Report: OR ± 95% exact binomial CI
  Interpretation: OR > 1.0 → ML benefits; OR < 1.0 → ML harms
```

**Verdict**: **Sound with revision — apply Bonferroni; define IF correlation gate**

**Required changes**:
1. Apply Bonferroni correction: α_adj = 0.017 for 3 ablation comparisons
2. Define IF↔P90 correlation gate with explicit measurement protocol:
   - Compute over calibration window (≥ 1,000 events)
   - Test: Pearson ρ(IF_score, P90_th) vs. threshold 0.8
   - Pre-register decision rule
3. Report per-arm results as exploratory if α_adj is too conservative (power concern)

---

## 2. Multiple Comparisons Problem

### Current State

The thesis evaluates **6 RQs** but contains **hidden comparisons** that are not accounted for:

| Comparison Set | Comparisons | Correction Needed |
|---------------|-------------|-------------------|
| 6 primary RQs | 6 | α_adj = 0.05/6 ≈ 0.0083 |
| TQS variants (V1/V2/V3) | 3 | α_adj = 0.05/3 ≈ 0.017 |
| ML ablation arms (IF/LSTM/Hybrid vs. baseline) | 3 | α_adj = 0.05/3 ≈ 0.017 |
| Injection rates (0.5%, 1%, 2%, 5%) | 4 | α_adj = 0.05/4 ≈ 0.0125 |
| 10 rules (SYN001–003, SEM001–003, GTFSSem002, CRS001–003) | 10 | α_adj = 0.05/10 = 0.005 |

### Total Comparisons

**Conservative count** (all possible):
6 RQs + 3 TQS + 3 ML + 4 rates + 10 rules = **26 comparisons**
**α_adj = 0.05/26 ≈ 0.0019**

**Minimal count** (primary comparisons only):
6 RQs + 3 TQS + 3 ML = **12 comparisons**
**α_adj = 0.05/12 ≈ 0.0042**

### Current Practice

STATISTICAL_PLAN.md states: "Bonferroni correction across RQs (α_adj = 0.01 for 5 RQs)."

**Problems**:
1. 5 RQs → 6 RQs (unupdated)
2. Hidden comparisons (TQS, ML, rates, rules) not included
3. α = 0.05 used for hypothesis tests (undercorrected)

### Recommendation

**Option A — Full Bonferroni** (conservative, publication standard):
```
α_adj = 0.05 / 12 = 0.0042 (primary comparisons only)
Report: "We applied Bonferroni correction across 12 primary comparisons 
(6 RQs, 3 TQS variants, 3 ML ablation arms), resulting in α_adj = 0.0042."
```

**Option B — Hierarchical testing** (more powerful, requires pre-registration):
```
Family 1: RQ1–RQ6 (6 tests) → α_adj = 0.05/6 = 0.0083
Family 2: TQS variants (3 tests) → α_adj = 0.05/3 = 0.017
Family 3: ML ablation (3 tests) → α_adj = 0.05/3 = 0.017
Within-family: Holm-Bonferroni step-down (more powerful than simple Bonferroni)
```

**Recommendation**: Option B with Holm-Bonferroni within families. Holm-Bonferroni is uniformly more powerful than Bonferroni while controlling FWER at α = 0.05.

### Implementation

```python
from scipy.stats import combine_pvalues

# Holm-Bonferroni step-down procedure
def holm_bonferroni(p_values, alpha=0.05):
    """
    Holm-Bonferroni step-down procedure.
    More powerful than simple Bonferroni, same FWER control.
    """
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    for i in range(n):
        threshold = alpha / (n - i)
        if sorted_p[i] < threshold:
            return sorted_indices[:i+1]  # Reject H[0] through H[i]
    return []  # No rejections

# Example: 6 RQs
p_rq = [0.023, 0.041, 0.008, 0.015, 0.009, 0.037]
alpha = 0.05
rejected = holm_bonferroni(p_rq, alpha)
# At n=6: thresholds are 0.05/6=0.0083, 0.05/5=0.01, 0.05/4=0.0125, 
#          0.05/3=0.0167, 0.05/2=0.025, 0.05/1=0.05
# Reject RQ3 (p=0.008 < 0.0083), RQ5 (p=0.009 < 0.01)
```

---

## 3. Bootstrap CI Analysis

### 3.1 Bootstrap Iterations: 1,000 vs. 10,000

**Current**: 1,000 bootstrap iterations (STATISTICAL_PLAN.md)

**Issue**: 1,000 iterations is **standard for prototyping**, not publication. The 95th percentile from 1,000 samples has standard error ≈ 1.35/√1000 ≈ 0.043. With 10,000 iterations, SE ≈ 1.35/√10000 ≈ 0.014 — **3× more precise**.

**Recommendation**: Increase to **10,000 iterations** for all publication results. 1,000 is acceptable for unit tests and development.

```python
# Current (1,000 iterations)
ci_width_1000 = 2 * 1.96 * sigma / sqrt(1000)  # ≈ 0.124 * sigma

# Recommended (10,000 iterations)  
ci_width_10000 = 2 * 1.96 * sigma / sqrt(10000)  # ≈ 0.039 * sigma

# Precision improvement: 3×
```

### 3.2 Percentile vs. BCa Bootstrap CI

**Current**: Percentile bootstrap CI (STATISTICAL_PLAN.md)

**Issue**: Percentile CI is biased for skewed distributions. For F1 (which is bounded [0, 1] and often right-skewed when P and R are imbalanced), **BCa (bias-corrected accelerated)** is more accurate.

**Recommendation**: Use BCa bootstrap CI for F1, precision, recall. Use percentile CI for latency percentiles (P50, P95, P99) where percentile method is appropriate.

```python
from scipy.stats import bootstrap

# BCa bootstrap CI for F1
def compute_f1_bca(f1_values, alpha=0.05, n_iterations=10000):
    """
    BCa bootstrap CI for F1 score.
    Bias-corrected and accelerated for skewed distributions.
    """
    # Percentile method (baseline)
    percentile_ci = np.percentile(f1_values, [alpha/2*100, (1-alpha/2)*100])
    
    # BCa method (preferred for bounded/skewed metrics)
    n = len(f1_values)
    theta_hat = np.mean(f1_values)
    
    # Bias correction factor (z0)
    z0 = stats.norm.ppf(np.mean(f1_values <= theta_hat))
    
    # Acceleration factor (a) via jackknife
    theta_jack = []
    for i in range(n):
        mask = np.ones(n, bool)
        mask[i] = False
        theta_jack.append(np.mean(f1_values[mask]))
    a = (np.sum((theta_hat - theta_jack)**3) / 
         (6 * (np.sum((theta_hat - theta_jack)**2)**1.5)))
    
    # Adjusted percentiles
    alpha1 = stats.norm.cdf(z0 + stats.norm.ppf(alpha/2) / (1 - a*(z0 + stats.norm.ppf(alpha/2))))
    alpha2 = stats.norm.cdf(z0 + stats.norm.ppf(1-alpha/2) / (1 - a*(z0 + stats.norm.ppf(1-alpha/2))))
    
    bca_ci = np.percentile(f1_values, [alpha1*100, alpha2*100])
    
    return {
        'mean': theta_hat,
        'percentile_ci': percentile_ci,
        'bca_ci': bca_ci,
        'bias_correction': z0,
        'acceleration': a
    }
```

---

## 4. Power Analysis Gaps

### 4.1 RQ1: Aggregate ΔF1 (d = 0.10–0.15)

**Target**: Detect ΔF1 ≥ 5pp at L0 cells; ΔF1 ≥ 1–2pp aggregate

| Parameter | L0 Cells | All Events (Aggregate) |
|-----------|----------|------------------------|
| Effect size | d = 0.30 | d = 0.10–0.15 |
| α (Bonferroni) | 0.0083 | 0.0083 |
| Power | 0.80 | 0.80 |
| Required n | 140 cells | 700+ events |
| Planned n | 90 windows (3 trials × 30 cells) | 90 windows |
| Type II risk | ~20% | **~35–40%** |

**Critical finding**: Aggregate ΔF1 is **underpowered at current sample size**. 90 windows detect only large effects (d ≥ 0.20).

**Mitigation**:
1. Report aggregate ΔF1 as **exploratory** (not confirmatory)
2. Focus confirmatory analysis on **L0 cells** (d = 0.30, n = 140, powered)
3. Increase trials from 3 to 5 → n = 150 windows → adequate for d = 0.15
4. Add simulation-based power analysis for streaming data (not just G*Power)

### 4.2 RQ2: CRS Precision/Recall

**Target**: P ≥ 0.70 for CRS001; P ≥ 0.70 AND R ≥ 0.60 for CRS002

| Parameter | Value |
|-----------|-------|
| Effect size | P ≈ 0.80–0.90 (hardcoded physics bounds) |
| α (one-sided) | 0.0083 (Bonferroni for 6 RQs) |
| Power | 0.80 |
| Required n (margin = 0.10) | 62 injections |
| Required n (margin = 0.05) | 246 injections |
| Planned n | 300 injections × 3 trials = 900 |
| **Verdict** | **ADEQUATE** |

**Note**: 900 total injections provides margin ≈ ±3pp at P = 0.80. This is conservative for publication.

### 4.3 RQ3: TQS Correlation (ρ > 0.7)

**Target**: ρ_s(TQS, downstream_quality) > 0

| Parameter | ρ = 0.30 | ρ = 0.50 | ρ = 0.70 |
|-----------|-----------|-----------|-----------|
| Required n | 85 windows | 30 windows | 16 windows |
| Planned n | 85 windows × 3 trials = 255 | — | — |
| **Verdict** | **ADEQUATE** | — | — |

**Note**: Power analysis assumes Fisher z-test for ρ. If TQS–ETA relationship is non-linear, Spearman ρ_s requires larger n. Recommend increasing to **n = 100+ windows per trial**.

### 4.4 RQ6: McNemar's Test

**Target**: Detect OR = 1.5 (ML is 50% more likely to be correct when rule-only fails)

| Parameter | Value |
|-----------|-------|
| Discordant pairs | n = 94 (b + c) |
| Test events | 1,000 per arm |
| Injection rate | 20% → 200 anomaly events |
| Expected discordant pairs | ~40–80 (b + c) |
| **Verdict** | **MARGINALLY ADEQUATE** |

**Concern**: At OR = 1.5 and b/(b+c) = 0.60, n = 94 discordant pairs required. With 1,000 events at 20% injection, expected discordant pairs ≈ 40–80. Power may be insufficient.

**Recommendation**: Increase to **1,500 test events** per arm to ensure ≥ 94 discordant pairs at OR ≥ 1.5.

---

## 5. Critical Methodological Issues

### Issue 1: Multiple Comparisons Undercorrection

**Evidence**:
- 6 RQs × α = 0.05 (not α_adj)
- 3 TQS variants tested separately (implicitly)
- 3 ML ablation arms not Bonferroni-corrected
- 4 injection rates × 10 rules = 40 comparisons implicit in stratified results

**Impact**: Family-wise error rate (FWER) inflation. At 12 comparisons with α = 0.05, expected false positives ≈ 0.60. At α_adj = 0.0042, expected false positives ≈ 0.05.

**Fix**: Apply Holm-Bonferroni correction across all primary comparisons. Pre-register analysis plan.

---

### Issue 2: RQ2 Metric Definition Is Non-Operational

**Evidence**:
- thesis_outline.md: "Fallback accuracy < 10% error"
- HYPOTHESES.md H1-B: Tests monotonicity of FNR across L0–L4
- No definition of "fallback error" exists in any document
- COMPLEXITY_ANALYSIS.md uses "threshold specificity" not "accuracy"

**Impact**: RQ2 cannot be tested because the metric is undefined. Any result would be post-hoc.

**Fix**: Replace RQ2 with specific operational claim:
```
RQ2: As context resolution degrades from L0 to L4, threshold 
     specificity decreases monotonically.

Metric: ΔFNR per fallback level (L1−L0, L2−L1, ..., L4−L3)
Test: Friedman's test + Nemenyi post-hoc
Effect size: Kendall's W (concordance across levels)
```

---

### Issue 3: RQ4 Ablation Design Is Inconsistent

**Evidence**:
- RQ4 ablation: SYN-only vs. SYN+SEM vs. SYN+SEM+CRS
- SYN/SEM rules use NYC TLC data (zone-level, ~3M records)
- CRS rules use NYC MTA Bus data (GPS coordinates, live feed)
- The ablation compares rules on **different event streams**

**Impact**: RQ4 cannot validly compare SYN+SEM against CRS because they don't evaluate the same events. The ablation design is internally inconsistent.

**Fix**: Reframe RQ4 as CRS-only evaluation (see §1.4 above). SYN/SEM ablation belongs in RQ1 (context-aware thresholds). CRS layer contribution is evaluated independently on NYC MTA Bus.

---

## 6. Additional Methodological Concerns

### 6.1 LocalPipeline ≠ Flink Pipeline

**Current**: thesis_outline.md §3.8: "Throughput: 5,000+ events/sec (No distributed benchmark)"

**Issue**: All statistical tests are run on LocalPipeline. LocalPipeline uses SQLite (no network), in-process Python (no JVM), and no distributed state. Results are not transferable to Flink.

**Recommendation**: 
1. Label all results: "LocalPipeline (development mode)"
2. Add infrastructure requirement: "Distributed Flink cluster required for confirmatory benchmarks"
3. Report LocalPipeline results as exploratory (Tier 2)

### 6.2 Warmup Period Definition

**Current**: STATISTICAL_PLAN.md specifies "60 seconds of clean data (injection_rate = 0%) — DO NOT MEASURE"

**Issue**: 60 seconds of warmup at 1,000 events/sec = 60,000 events. L0 context cells need ≥ 100 samples. This is adequate for L0 but may be insufficient for accurate P10/P90 rolling statistics (needs 1–2 hours).

**Recommendation**: 
1. Warmup period should be **1 hour** (not 60 seconds) to populate rolling P10/P90 for L3/L4 cells
2. Alternatively, use pre-computed thresholds from historical data (NYC TLC has 6+ months)

### 6.3 Match Criterion: Exact entity_index

**Current**: violation matches ground truth if entity_index matches exactly (STATISTICAL_PLAN.md)

**Issue**: This is appropriate for SYN001–003, SEM001–003, GTFSSem002. For CRS001/CRS002 (GPS rules), the injected anomaly is a **pair of positions** (speed spike from position i to i+1). The entity_index of the second position should match the injected index.

**Risk**: If injection assigns entity_index to the first position only, CRS001/CRS002 violations on the second position may not match.

**Recommendation**: Verify that GPS injection assigns entity_index to the triggering position (second of the pair), not the first.

### 6.4 Throughput Unmeasured

**Current**: No throughput measurement in the evaluation plan.

**Issue**: 600-second measurement window × X events/sec = N_total events. If X is unknown, the effective sample size per trial is unknown. Power analysis assumes sufficient N — if throughput is low, power is inadequate.

**Recommendation**: Measure throughput during every evaluation run. Report: events/sec (mean ± std), total events per trial, effective n per condition.

---

## 7. Summary of Required Changes

### Priority 1 (Critical — Must Fix Before Submission)

| # | Issue | Action |
|---|-------|--------|
| 1 | RQ2 metric undefined | Replace "accuracy < 10% error" with FNR monotonicity test |
| 2 | Multiple comparisons undercorrected | Apply Holm-Bonferroni across all 12 primary comparisons |
| 3 | RQ4 ablation design inconsistent | Reframe RQ4 as CRS-only evaluation; SYN/SEM → RQ1 |
| 4 | McNemar's test misapplied to RQ1/RQ4 F1 | Replace with Wilcoxon signed-rank for FPR comparison |

### Priority 2 (Major — Fix Before Benchmark)

| # | Issue | Action |
|---|-------|--------|
| 5 | Bootstrap iterations: 1,000 → 10,000 | Update STATISTICAL_PLAN.md; increase iterations in `metrics.py` |
| 6 | Pearson → Spearman for RQ3 | Update HYPOTHESES.md H2-A to use Spearman ρ_s |
| 7 | RQ1 aggregate ΔF1 underpowered | Report as exploratory; confirmatory focus on L0 cells (n ≥ 140) |
| 8 | RQ6 Bonferroni correction missing | Add α_adj = 0.017 for 3 ablation comparisons |
| 9 | IF↔P90 correlation gate undefined | Pre-register measurement protocol and decision rule |
| 10 | 5pp target applies only to L0 cells (5% of events) | Clarify in thesis outline; add aggregate claim separately |

### Priority 3 (Recommended — Improves Rigor)

| # | Issue | Action |
|---|-------|--------|
| 11 | BCa bootstrap for F1 | Use BCa instead of percentile for F1, P, R CI |
| 12 | Warmup: 60s → 1 hour | Update evaluation protocol for rolling P10/P90 convergence |
| 13 | Throughput unmeasured | Add throughput logging to every evaluation run |
| 14 | ρ > 0.7 threshold arbitrary | Justify or lower to ρ > 0.5 |
| 15 | CRS002 recall target may be infeasible (B3) | Acknowledge speed range gap; adjust R target if needed |

---

## 8. Statistical Methods Checklist

| Method | Current | Required | Document |
|--------|---------|----------|----------|
| CI method (F1/P/R) | Percentile | BCa | STATISTICAL_PLAN.md |
| Bootstrap iterations | 1,000 | 10,000 | metrics.py, STATISTICAL_PLAN.md |
| RQ1 test | McNemar's | Wilcoxon signed-rank | HYPOTHESES.md H1-A |
| RQ2 metric | "accuracy" | FNR monotonicity | thesis_outline.md §3.6, HYPOTHESES.md H1-B |
| RQ3 correlation | Pearson ρ | Spearman ρ_s | HYPOTHESES.md H2-A |
| RQ4 design | Ablation (inconsistent) | CRS-only evaluation | thesis_outline.md §3.5 |
| RQ6 correction | None | Holm-Bonferroni (α_adj = 0.017) | ML_INTEGRATION_REDESIGN.md §5.4 |
| IF correlation gate | Undefined | Pre-registered protocol | ML_INTEGRATION_REDESIGN.md §3.1.4 |
| RQ3 circularity check | ETA task | Report both ρ_s(TQS, ETA) and ρ_s(TQS, viol_rate) | STATISTICAL_PLAN.md §RQ3 |
| Overall α correction | 5 RQs, α = 0.05 | 12 comparisons, α_adj = 0.0042 | STATISTICAL_PLAN.md §Summary |

---

## 9. Power Analysis Summary Table (Updated)

| RQ | Metric | Effect Size | Test | α | Power | Required n | Planned n | Status |
|----|--------|-------------|------|---|:-----:|:----------:|----------|--------|
| RQ1 | ΔFPR (L0 cells) | d = 0.30 | Wilcoxon | 0.0083 | 0.80 | 140 cells | 90 windows | **Underpowered** |
| RQ1 | ΔF1 (aggregate) | d = 0.10–0.15 | Wilcoxon | 0.0083 | 0.80 | 700+ events | 90 windows | **Underpowered** (exploratory) |
| RQ2 | ΔFNR monotonicity | Kendall's W | Friedman | 0.0083 | 0.80 | 30 cells | 30 cells | **Adequate** |
| RQ3 | ρ_s(TQS, ETA) | ρ = 0.30 | Fisher z | 0.0083 | 0.80 | 85 windows | 255 windows | **Adequate** |
| RQ5 | P(CRS001) | P = 0.80 | Binomial | 0.0083 | 0.80 | 246 | 900 | **Adequate** |
| RQ5 | P+R(CRS002) | P = 0.80, R = 0.60 | TOST | 0.0083 | 0.80 | 300 | 900 | **Adequate** |
| RQ6 | OR (ML benefit) | OR = 1.5 | McNemar | 0.017 | 0.80 | 94 discordant | ~60–80 | **Marginal** |

---

## 10. Conclusion

The thesis presents a **methodologically sound framework** with three critical gaps that must be addressed before submission:

1. **Multiple comparisons undercorrection** (α = 0.05 vs. α_adj ≈ 0.0042) — highest risk of false positives
2. **RQ2 metric is undefined** — non-operational as written
3. **RQ4 ablation design is internally inconsistent** — CRS rules evaluated on different dataset than SYN/SEM

The non-circular TQS design, BCa bootstrap CI plan, and negative result protocol are **exemplary** methodological choices that strengthen the thesis. The power analysis gaps are addressable with increased sample sizes or by reframing aggregate claims as exploratory.

**Overall assessment**: **Conditionally publishable** after Priority 1 issues are resolved. Priority 2 issues are recommended for revision before final submission.

---

*Document classification: Tier 1 (Verified) for statistical method critiques; Tier 2 (Estimated) for sample size/power projections.*
