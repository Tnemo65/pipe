# StreamDQ Final Documents — Master Consolidated Review V2

**Date**: April 24, 2026
**Role**: Debate Moderator
**Method**: Adversarial synthesis of 4 specialist reviews — Scientific-Critical, Code Auditor, Statistics Agent, Literature Agent
**Sources**: `FINAL_PROJECT_AUDIT.md`, `COMPREHENSIVE_REVIEW.md`, `AUTHORITATIVE_REVIEW.md`, `FIXED_AUDIT_AND_PLAN.md`, + all adversarial agent challenges

---

## Executive Summary

After full adversarial review by four specialist agents, the StreamDQ documents are in **RED status** — the ground has shifted significantly from the prior review cycle. Three prior reviews contained factual errors that inflated the CRITICAL count. Four new code-level bugs were discovered that were absent from all prior reviews. Statistical methodology has four corrections needed. Literature citations have three year/DOI errors. And the CRS003 replay gate decision (Option A vs B) was misclassified in the FIXED_AUDIT as "Option B correct" — it is actually Option A (synthetic bypass).

**Overall status: RED → AMBER with immediate action on all CRITICAL items.**

### The 5 Most Impactful New Findings

1. **NG-1 (CRITICAL)**: CRS003 emits no violation when confidence ≤ 0.4 — state stored but no output → evaluation silently fails
2. **NG-4 (CRITICAL)**: `_enrich_with_lineage()` sets `is_replay=True` on synthetic duplicates → gate still blocks them despite B2 fix
3. **Option B (CRITICAL)**: The "keep gate" recommendation in FIXED_AUDIT is WRONG — it reduces evaluation scope; synthetic bypass (Option A) is correct
4. **Power analysis (MAJOR)**: G*Power used wrong test (paired Wilcoxon, not two-sample t); n=30 gives ~70-75% not 80%
5. **Literature (MINOR)**: METER year corrected to 2024 (not 2023); T-Assess year corrected to 2024 (not 2025); Mirzaie DOI confirmed placeholder

### Issues Corrected From Prior Reviews

|| Prior Review Said | Correction | Impact |
||------------------|------------|--------|
| H0 missing from every hypothesis | CRITICAL (M002, CR-02) | H0 is present in all 12 hypotheses (FIXED_AUDIT confirmed) | Downgrade to REMOVED |
| METER year wrong in 6+ docs | MAJOR (MA-07, MA-12) | All audited docs use "VLDB 2024" correctly (FIXED_AUDIT confirmed) | Downgrade to REMOVED |
| B2 duplicate injection broken | CRITICAL (CR-06, M014) | Already emits 2 records; real bug is `is_replay=True` gate (NG-4) | Reclassified as NG-4 |
| B1 NaN guard underspecified | MAJOR/MINOR | 3-type implementation already exists | REMOVED from issue register |
| DATA_STRUCTURES §4 partially fixed | MAJOR (MA-02) | Entirely unchanged — worse than reported | Correct severity was CRITICAL |
| ML incorrectly positioned as optional everywhere | MAJOR | Only `report.md` Phase 3 Gantt contradicts; others correct | Correct severity was MINOR |
| CRS001 lower bound fires on stops | MAJOR | No `min_speed_kmh` parameter exists; CRS001 only checks upper bound | Correct severity was MINOR |
| CRS003 MD5 vs SHA256 | CRITICAL (CR-04) | Spec is wrong for TLC; code is architecturally closer to correct | Downgrade to MAJOR with updated framing |
| 250m threshold sufficient | CRITICAL (CR-01) | Scientific-Critical: minimum 333m needed for 95th percentile | Escalate to CRITICAL+ |
| "1-2pp not meaningful" | MAJOR (MA-04) | At NYC TLC scale, 1-2pp × 500K/day = 5K-10K violations/day — IS meaningful | Reclassify as NOT a flaw |
| V1 equal weights non-arbitrary | MAJOR (MA-06) | Both V1 and V2 are design choices — neither is "non-arbitrary" | Correct characterization |

---

## Part 1: Updated Issue Register

### CRITICAL Issues (5 + 3 NEW from code audit = 8 total)

---

#### CR-01: CRS002 threshold fires on ALL normal urban traffic — minimum 333m required

**Location**: `FORMULATION.md` Algorithm C; `HYPOTHESES.md` H3-CRS002; `cross_record.py` `max_stationary_jump_m=100.0`

**What**: At 30-second GTFS update intervals, a bus at 30 km/h travels 250m — 2.5× above the 100m threshold. Every NYC MTA Bus in normal urban traffic fires CRS002. CRS002 precision = 0% by construction.

**Updated threshold recommendation** (Scientific-Critical challenge):
- **250m**: Minimum safe at 30 km/h mean speed
- **333m**: Required minimum — accounts for 95th percentile speed (~40 km/h) at 30s intervals (≈333m displacement)
- **Recommendation**: 333m. The prior review said "250m minimum, 333m safe." Scientific-Critical correctly identifies that 250m still fires on faster traffic.

**Additional issue (neither prior review caught)**: The Algorithm C K=3 buffer was calibrated for 1Hz data (3-second coverage), not 30s intervals (90-second coverage). Buffer and threshold were designed together for 1Hz, then data source switched without recalibration.

**Additional issue**: `cross_record.py` uses `max_stationary_jump_m=100.0` (same as broken spec). Changing FORMULATION.md alone is insufficient — code must also be updated.

**Status**: OPEN

**Action**: (1) Update code: `max_stationing_jump_m=100.0` → `333.0`; (2) Update FORMULATION.md Algorithm C threshold; (3) Update Physics Priors table; (4) Fix K=3 buffer comment or add minimum-frequency check; (5) Update TEST C2 spec

---

#### CR-02: TQS architecture split — three incompatible systems across documents

**Location**: `FORMULATION.md` §6 vs. `DATA_STRUCTURES.md` §4 vs. `HYPOTHESES.md` H2-A vs. `FAILURE_MODES.md` §Q2

**What**: Four documents use four different TQS systems:

| Document | Dimensions | Formula basis | Status |
|----------|:----------:|--------------|--------|
| `FORMULATION.md` §6 | Tm, Cn, Ac, Cs, Uv | Raw event fields | **Correct, non-circular ✓** |
| `DATA_STRUCTURES.md` §4 | V, C, Cn, P | Rule violation counts | **Circular by construction ✗** |
| `HYPOTHESES.md` H2-A | Mixed | Mixed | **Ambiguous — partially updated ✗** |
| `FAILURE_MODES.md` §Q2 | V=0.40, C=0.20, Cn=0.30, P=0.10 | Old system | **Old system, wrong dimensions ✗** |

`FORMULATION.md` §6 introduces an excellent non-circular TQS redesign. But `DATA_STRUCTURES.md` §4 was never updated — it still uses the OLD circular formula `V = 1 − (syn001+syn002)/N`. The Tm formula has an additional unit-scale problem: `exp(−λ · σ²_Δt)` with λ=0.01. If Δt is in milliseconds (Flink timestamps), σ²_Δt ≈ 10⁹–10¹² ms² → λ·σ²_Δt ≈ 10⁷–10¹⁰ → Tm ≈ 0 for all normal streams. The λ=0.01 constant was calibrated for second-scale data.

The prior reviews misdiagnosed the Tm formula as an "Ac plausibility" issue — it is a **Tm (Timeliness)** issue.

**Updated findings on TQS non-circularity** (Statistical challenge):
- H2-A variables CN, Ac, Cs, Uv are **circular by construction** — computed from data that includes injected anomalies (the DV). Only **Tm** is non-circular.
- The "non-circular redesign" in STATISTICAL_PLAN still references CN, Ac, Cs, Uv — which are circular. The claim of non-circularity is only valid for the Tm dimension.

**Status**: OPEN

**Action**: (1) Rewrite DATA_STRUCTURES.md §4 to implement Tm/Cn/Ac/Cs/Uv; (2) Update FAILURE_MODES §Q2 to new dimensions; (3) Fix Tm λ calibration for ms-scale data; (4) Acknowledge that CN, Ac, Cs, Uv are circular — only Tm is non-circular; (5) Update H2-A to reflect this limitation

---

#### CR-03: CRS003 replay gate decision — Option A (synthetic bypass) is CORRECT, Option B is WRONG

**Location**: `cross_record.py` lines 304-311; `nyc_taxi_replay.py`

**What — corrected classification**:

The prior FIXED_AUDIT_AND_PLAN.md said:
> "Option B — Keep gate for all replay: Do not tag synthetic duplicates differently. CRS003 never fires on TLC replay data. CRS003 evaluation on TLC is not possible."

**This is WRONG.** Scientific-Critical correctly identifies that Option B reduces evaluation scope by eliminating CRS003 from TLC evaluation entirely. CRS003 IS part of the evaluation — it cannot simply be removed.

**Correct analysis**:
- Option A (synthetic bypass): Tag synthetic-injected events with `is_replay=False`. CRS003 detects synthetic duplicates for evaluation. Real replay duplicates still suppressed (no false positives on replay data). **This is the correct approach.**
- Option B (keep gate): CRS003 evaluation on TLC becomes impossible. RQ5 CRS003 evaluation collapses. **Wrong.**

**Status**: OPEN — Option A must be implemented

**Action**: Tag synthetic-injected duplicates with `is_replay=False` in `nyc_taxi_replay.py`. Estimated: 5-10 lines of code.

---

#### CR-04: CRS003 hash — spec is wrong for TLC; MD5 vs SHA256 is a secondary issue

**Location**: `FORMULATION.md` Algorithm D vs. `cross_record.py`

**What — corrected framing** (Scientific-Critical challenge):

The prior review said "spec is broken; code is closer to correct." This framing stands but needs clarification:

| Aspect | FORMULATION.md | Actual Code |
|--------|---------------|-------------|
| Hash function | SHA256 | MD5 |
| Fields (NYC TLC) | `trip_id + timestamp + lat + lon` | `trip_id + PULocationID + DOLocationID + passenger_count + trip_distance` |

The **spec is catastrophically wrong** for NYC TLC — it references lat/lon fields that don't exist. The **code is architecturally more sensible** — it uses semantic fields appropriate for zone-level data. However, the code uses MD5 (cryptographically broken) and includes 5 fields vs. the spec's 4-field design.

The MD5 vs SHA256 debate (raised in Scientific-Critical) is a **red herring**. For a non-cryptographic deduplication hash, MD5's collision resistance is irrelevant. The real question is whether the field selection is correct. The code's semantic field approach is better suited for TLC; for GTFS (which has GPS), lat/lon should be included.

**Status**: OPEN

**Action**: Update FORMULATION.md Algorithm D with per-dataset strategy: "NYC TLC: SHA256(trip_id + timestamp + PULocationID + DOLocationID); NYC MTA Bus: SHA256(trip_id + timestamp + lat + lon)."

---

#### CR-05: Evaluation infrastructure absent (unchanged from prior reviews)

**Location**: All documents that reference measured results

**What**: Every measured benchmark number is Tier-2 or Tier-3. No evaluation directory, no synthetic injector integration, no ground truth tracker, no metrics module, no run script exists. This was the top priority in all prior reviews and remains so.

**Status**: OPEN

**Action**: Build `evaluation/` directory: synthetic_injector extension, ground_truth_tracker.py, metrics.py (10K bootstrap iterations minimum — see Statistical Findings), run_evaluation.py, README.md

---

#### NEW NG-1: CRS003 confidence ≤ 0.4 silently stores state but emits no violation (potential deadlock)

**Location**: `cross_record.py` `evaluate_duplicate_event()` — confidence threshold logic

**What**: The code stores the event hash in the dedup state when confidence ≤ 0.4, but returns `None` (no violation). This means:
1. The duplicate IS tracked (future duplicates won't fire — state is correct for dedup purposes)
2. But NO violation is emitted for evaluation
3. Ground truth tracker won't see the detected violation
4. Recall silently drops to 0% for low-confidence duplicates

This is NOT the same as the replay gate issue (NG-4). NG-1 is a separate code path — even non-replay duplicates at low confidence will fail to produce violations.

**Status**: NEW — Not in any prior review

**Action**: (1) Remove confidence threshold from violation emission path, OR (2) Store low-confidence violations separately for post-hoc analysis, OR (3) Document confidence threshold behavior explicitly with reasoning

---

#### NEW NG-2: CRS003 temporal clustering suppresses post-detection duplicates

**Location**: `cross_record.py` `evaluate_duplicate_event()`

**What**: After CRS003 detects a duplicate and emits a violation, subsequent occurrences of the same hash within the temporal window are suppressed by the deduplication state. Post-detection duplicates (same trip injected twice, then the duplicate appears multiple times) are consumed by the dedup mechanism rather than emitting violations. This reduces CRS003 recall.

**Status**: NEW — Not in any prior review

**Action**: Add post-detection duplicate counter. Distinguish: (a) first detection → emit violation, (b) subsequent detections within window → emit secondary violation with `is_repeat=True` flag. Update ground truth tracker to handle repeat detections.

---

#### NEW NG-4: `_enrich_with_lineage()` sets `is_replay=True` on synthetic duplicates — gate still blocks them

**Location**: `nyc_taxi_replay.py` — `_enrich_with_lineage()` or `_emit()` methods

**What**: Even after the B2 fix (2 records emitted), the code path that enriches synthetic events with lineage metadata sets `is_replay=True`. This means the synthetic duplicate STILL triggers the replay suppression gate in `evaluate_duplicate_event()` and is blocked.

This is the root cause of the CRS003 evaluation failure — NOT the replay gate per se (which is correct design), but the failure to tag synthetic events as non-replay.

**Note**: The FIXED_AUDIT correctly identified this as a design decision but chose Option B (keep gate) as "alternative." Scientific-Critical correctly identifies this is Option A — the correct path. NG-4 is the implementation-level manifestation of the same issue.

**Status**: NEW — Not in any prior review

**Action**: In `_enrich_with_lineage()` or `_emit()`, add logic: if event is synthetic duplicate → set `is_replay=False`. Alternatively, add explicit `is_synthetic` flag and bypass replay check when `is_synthetic=True`.

---

### MAJOR Issues (Updated)

---

#### MA-01: H1-A H0 incomplete — but adding F1 H0 may HURT the hypothesis

**Location**: `HYPOTHESES.md` H1-A; `STATISTICAL_PLAN.md` H1-A

**What — updated analysis** (Scientific-Critical challenge):

The DV for H1-A includes: (a) FPR, (b) F1 per context cell, (c) aggregate F1. The H₀ states "FPR(L0) ≥ FPR(L4)" but F1 has no H₀.

**Scientific-Critical raises a critical concern**: Adding F1 H0 might HURT the hypothesis. The primary mechanism is FPR reduction — context-aware thresholds should reduce false positives on L0 cells. The FPR mechanism is theoretically cleaner and more defensible. F1 is confounded by detection rate — if context-aware thresholds have lower recall on L0, F1 could decrease even if FPR decreases. Adding F1 to the hypothesis creates an additional failure mode.

**Correct approach**: H1-A should focus on FPR as the primary DV. F1 can be reported descriptively but should not be a formal hypothesis. If F1 is included, the H₀ should be one-sided: "H₀: F1(L0) ≤ F1(L4)."

**Status**: OPEN

**Action**: (1) Keep FPR as primary DV with explicit H₀; (2) Report F1 descriptively (not as formal hypothesis) with honest CI; (3) If F1 is included as hypothesis, use one-sided H₀

---

#### MA-02: Ac plausibility bounds — LOOSE BY DESIGN, not a flaw (corrected)

**Location**: `FORMULATION.md` §6.2.3

**What — corrected classification** (Scientific-Critical challenge):

The prior reviews classified "Ac bounds are loose ($0-1000 fare, 0-500 miles)" as MAJOR because bounds will misclassify. Scientific-Critical correctly identifies this is **loose by design** — wide plausibility bounds serve as a safety net, not a fine-grained validator. Tight bounds (e.g., $50-200 fare) would create false positives on premium rides. Loose bounds are intentional.

**This is NOT a flaw — it is correct design.** The issue was misclassified in prior reviews.

**However**: The bounds still need to be validated. If the 95th percentile of NYC TLC fares is $50 and the bound is $1000, that's fine. If it's $5000, the bound is wrong. The issue is **unvalidated bounds**, not **loose bounds**.

**Status**: OPEN — Validate, not tighten

**Action**: Calibrate bounds from actual NYC TLC data percentiles (e.g., 99th percentile fare, 99th percentile distance). Document the percentile used. Loose is fine; unvalidated is not.

---

#### MA-03: CRS rules (Java) not built — 7 weeks required (updated)

**Location**: `report.md` Part VI Phase 2; `cross_record.py`

**What**: CRS rules are Python-only. Java Flink implementations (required for production pipeline) don't exist. Updated estimate with graduated complexity:

| Phase | Rule | Complexity | Duration |
|-------|------|:---------:|----------|
| Java warmup | Maven + Flink skeleton | Low | 1 week |
| CRS003 | RoaringBitmap dedup | Low | 1 week |
| CRS002 | GPS jump buffer | Medium | 2 weeks |
| CRS001 | Speed history | High | 2 weeks |
| Integration | Wire into Flink job | Medium | 1 week |
| **Total** | | | **7 weeks** |

**Status**: OPEN

**Action**: Update Phase 2 timeline to 7 weeks. Start Java warmup in Week 5.

---

#### MA-04: Aggregate ΔF1 IS meaningful at NYC TLC scale (corrected)

**Location**: `HYPOTHESES.md` H1-A; `SIGNIFICANCE_TABLE.md`

**What — corrected classification** (Scientific-Critical challenge):

The prior review said "1-2pp not meaningful." Scientific-Critical correctly identifies this is wrong at NYC TLC scale:

- NYC TLC ~500,000 trips/day
- 1pp × 500K = 5,000 correctly classified events/day
- 2pp × 500K = 10,000 correctly classified events/day

**1-2pp IS meaningful at scale.** The claim does not need defending as "small but meaningful." At 500K events/day, 1pp = 5K events. This should be stated as an operational benefit, not defended as a small number.

**However**: The L4 dilution issue remains valid. 1-2pp is the aggregate figure; the headline claim must be scoped to L0 cells.

**Status**: OPEN — Restate as meaningful at scale, not as "small but meaningful"

**Action**: Reframe: "At NYC TLC scale (500K events/day), 1-2pp aggregate improvement translates to 5,000-10,000 additional correctly classified events per day. For events in L0 context cells (5% of data), the improvement is 5pp."

---

#### MA-05: TQS V1/V2 — BOTH are design choices, neither is "non-arbitrary" (corrected)

**Location**: `FAILURE_MODES.md` §Q2; `FORMULATION.md` §6.3

**What — corrected analysis** (Scientific-Critical challenge):

FAILURE_MODES recommends V1 (equal weights) as "principled." FORMULATION uses V2 as primary. Scientific-Critical correctly identifies that **V1 equal weights is NOT non-arbitrary** — it is just a different design choice than V2. Equal weights implies all dimensions are equally important, which is itself an assumption.

The V1/V2 debate is a design decision with trade-offs:
- **V1 (equal)**: Principled baseline; no domain assumptions; harder to justify if domain knowledge exists
- **V2 (prioritized)**: Domain-informed; weights need justification; captures NYC TLC-specific risk hierarchy

**Neither is objectively correct.** The choice should be documented with reasoning, not framed as "V1 is correct, V2 is wrong."

**Status**: OPEN

**Action**: (1) Document both V1 and V2 as legitimate design choices with trade-offs; (2) Choose one as primary based on reasoning (V1 if no domain knowledge, V2 if NYC TLC domain justifies it); (3) Report both in sensitivity analysis

---

#### MA-06: ML integration — "no improvement" is the most likely outcome (new)

**Location**: `ML_POSITIONING.md`; `report.md` Phase 3; `final/04_NOVELTY_CONTRIBUTION/ML_INTEGRATION_REDESIGN.md`

**What** (Scientific-Critical challenge): The ML integration design (Isolation Forest + LSTM + Bayesian Optimization) is a 3-5 week investment. Scientific-Critical identifies this as high risk because:

1. Standard ML methods (Isolation Forest, LSTM) are well-established — the contribution is in integration design, not ML novelty
2. If ML provides no improvement over rules-only, the 3-5 week investment is lost
3. The honest fallback ("report as negative result") is scientifically valuable but weakens the thesis narrative

**Scientific-Critical's assessment**: "ML provides no improvement" is the most likely outcome. This is a risk that should be explicitly acknowledged, not hidden in "Phase 3 TBD."

**Status**: OPEN

**Action**: (1) Acknowledge ML risk explicitly in planning documents; (2) Set clear go/no-go criteria for ML Phase 3 (e.g., "if IF precision < 0.75 at Week 14, defer to future work"); (3) Budget 3-5 weeks with explicit acceptance of negative-result possibility

---

#### MA-07: CRS severity table missing 2-20 km/h (B3) — unchanged from prior reviews

**Location**: `report.md` §Severity-to-Alert

**What**: CRS002 severity maps only "<1 km/h → CRITICAL" and ">100m jump → HIGH." The 2-20 km/h moderate spoofing range (B3) is not in the severity table.

**Status**: OPEN

**Action**: Add "CRS002 IMPOSSIBLE_SPEED (2-20 km/h) → MEDIUM" to severity table. Acknowledge B3 gap.

---

#### MA-08: CRS001 lower bound — no `min_speed_kmh` parameter exists (corrected)

**Location**: `FORMULATION.md` Algorithm B; `cross_record.py`

**What — corrected** (from FIXED_AUDIT): CRS001 only checks upper bound (`max_speed_kmh=160.0`). No `min_speed_kmh` parameter exists. The lower bound concern is for CRS002 (GPS jump detection), not CRS001.

**However**: The code uses `min_speed_kmh=2.0` for the upper bound in some path, and the FORMULATION says 120 km/h while the code uses 160 km/h. The spec/code mismatch is still present.

**Status**: OPEN — Code/spec mismatch on upper bound

**Action**: (1) Choose upper bound: 120 km/h (NYC highway limit) or 160 km/h (more tolerant); propagate to both FORMULATION and code; (2) Clarify that CRS001 lower bound concern (stops) is addressed via CRS002 GPS jump, not CRS001 speed check

---

#### MA-09: zone_category lookup not implemented — unchanged

**Location**: `FORMULATION.md` §L0

**Status**: OPEN — 20-line data loading task

---

#### MA-10: CRS rules only run on NYC MTA Bus (secondary dataset) — unchanged

**Location**: `report.md`; `HYPOTHESES.md`

**What**: CRS001/CRS002 require GPS. NYC TLC has no GPS (zone-level only). CRS rules run on NYC MTA Bus GTFS-realtime only. Reframe: "CRS rules demonstrate GPS validation on GTFS-realtime; NYC TLC uses SYN/SEM."

**Status**: OPEN

---

### Statistical Findings — CORRECTIONS

---

#### STAT-01: RQ1 power analysis uses wrong test — paired Wilcoxon requires more samples

**Location**: `STATISTICAL_PLAN.md` §RQ1 Power Analysis

**What — corrected** (Statistics Agent challenge):

The current power analysis uses G*Power's two-sample t-test design:
- n=30 per group → 80% power for d=0.50

**Problem**: The actual test is a **paired Wilcoxon signed-rank test** (matched context cells, same trial period). For paired data:
- The effective n is the number of **pairs**, not individual observations
- The correlation between pairs REDUCES the effective variance, which HELPS power — but the paired design also means the test is sensitive to the number of matched pairs
- With n=30 matched cell-pairs: actual power ≈ **70-75%** (not 80%) for d=0.50

**Fix**: Recalculate power for paired Wilcoxon using appropriate software (R `power.t.test` with `paired=TRUE`, or G*Power for Wilcoxon signed-rank). The n=30 claim is not wrong — it's conservative — but the 80% power claim is slightly inflated.

**Status**: OPEN — Power analysis method needs correction

**Action**: Recalculate power for paired Wilcoxon. Expected: n=30 still gives ~75-80% power for d=0.50 — still acceptable but not 80%.

---

#### STAT-02: H2-B requires Meng's z-test for dependent correlations, not Fisher z

**Location**: `HYPOTHESES.md` H2-B; `STATISTICAL_PLAN.md` §H2-B

**What — corrected** (Statistics Agent challenge):

H2-B tests whether TQS correlates with injection rate differently than violation rate. The test involves comparing two correlations on the **same subjects** (cell-level metrics). This is a test of **dependent correlations** — the same set of context cells appears in both correlations.

**Meng's z-test** (Meng et al., 1992) is the correct test for dependent correlations. The current Fisher z (for independent samples) is **incorrect** — it treats the two correlations as independent when they share the same subjects.

**Reference**: Meng, X.-L., Rosenthal, R., & Rubin, D. B. (1992). Comparing correlated correlation coefficients. Psychological Bulletin, 111(1), 172–175.

**Status**: OPEN — Method must change from Fisher z (independent) to Meng's z-test (dependent)

**Action**: Replace Fisher z with Meng's z-test in H2-B and STATISTICAL_PLAN.md §H2-B. Add citation.

---

#### STAT-03: Bonferroni correction applied at wrong level — should be at hypothesis level

**Location**: `STATISTICAL_PLAN.md` §Multiple Testing Correction

**What — corrected** (Statistics Agent challenge):

The current plan applies Bonferroni correction at the **RQ level** (5 RQs → α_adj = 0.01). This is insufficient.

The correct application: Bonferroni at the **hypothesis level** (12 hypotheses → α_adj = 0.004). RQ is an organizational unit, not a statistical unit. Each hypothesis is an independent test.

**Status**: OPEN

**Action**: Apply Bonferroni at hypothesis level: α_adj = 0.05/12 = 0.0042. Update STATISTICAL_PLAN.md §Multiple Testing.

---

#### STAT-04: McNemar test assumes OR=1.5 — if OR=1.2, needs n=1000+

**Location**: `ML_INTEGRATION_REDESIGN.md`; `STATISTICAL_PLAN.md` §RQ6

**What — corrected** (Statistics Agent challenge):

The McNemar test is proposed for comparing rule-only vs. ML-augmented systems. The power analysis assumes OR=1.5 (medium effect). If the actual OR is 1.2 (small effect):
- Required n ≈ 1,000+ matched pairs
- Current plan may be underpowered for detecting small ML improvements

**Status**: OPEN

**Action**: (1) Use OR=1.2 in power calculation; (2) Increase matched pairs to 1,000+ for RQ6; (3) Alternatively, use exact binomial McNemar with continuity correction for small samples

---

#### STAT-05: Bootstrap iterations — 1,000 is insufficient for P99 metrics

**Location**: `STATISTICAL_PLAN.md` §Bootstrap CI

**What — corrected** (Statistics Agent challenge):

P99 latency requires estimating the 99th percentile. With 1,000 bootstrap iterations:
- Only ~10 samples exceed the 99th percentile
- **Too noisy for reliable CI estimation**

**Required**: Minimum **10,000 bootstrap iterations** for P99 metrics. For stable P99 CI, 50,000 iterations recommended.

**Status**: OPEN

**Action**: Change `metrics.py` bootstrap iterations from 1,000 to **10,000 minimum** (50,000 for P99).

---

#### STAT-06: H2-A only Tm is non-circular — CN, Ac, Cs, Uv are circular by construction

**Location**: `HYPOTHESES.md` H2-A; `STATISTICAL_PLAN.md` RQ3

**What — confirmed** (Statistics Agent challenge):

H2-A tests "TQS decreases with injection rate." The claim of non-circularity is only valid for the **Tm** (Timeliness) dimension:
- **Tm**: `exp(−λ · σ²_Δt)` — computed from raw inter-arrival times; non-circular ✓
- **Cn** (Completeness): Missing field count — will increase with injection rate → circular ✗
- **Ac** (Accuracy): Plausibility bounds — will flag injected anomalies → circular ✗
- **Cs** (Coherence): GPS trajectory coherence — CRS rules detect injected GPS anomalies → circular ✗
- **Uv** (Uniqueness): Hash distinctness — duplicates injected → circular ✗

Only Tm is non-circular. The weighted aggregate TQS score is still partially circular.

**Status**: OPEN — Only Tm can be tested non-circularly

**Action**: Rewrite H2-A to test Tm only (non-circular). Add CN, Ac, Cs, Uv as exploratory measures with honest acknowledgment of circularity.

---

#### STAT-07: L0 coverage estimated at 5%, not measured

**Location**: `HYPOTHESES.md` H1-A; `report.md` §L0-L5 power analysis

**What — confirmed** (Statistics Agent challenge):

The 5% L0 cell coverage estimate is not empirically measured. If L0 coverage is actually 0.5% (not 5%):
- Fewer L0 cells → less statistical power
- H1-C (which depends on L0 cell availability) may not be feasible

**Status**: OPEN

**Action**: Run empirical analysis on NYC TLC data to measure actual L0 coverage. Adjust power analysis accordingly.

---

### MINOR Issues (Updated)

| # | Issue | Status | Notes |
|---|-------|--------|-------|
| MI-01 | DeLong naming — Fisher z test is correct; name is wrong | OPEN | Rename to "Meng's (1992) z-test for dependent correlations" |
| MI-02 | D4 Holiday stub — "5D" should be "4D" | OPEN | Change everywhere |
| MI-03 | Mirzaie DOI placeholder — CONFIRMED invalid (XXX placeholder) | OPEN | Search for actual article number or remove |
| MI-04 | Synthetic GPS fallback vague | OPEN | Specify GTFS static route geometry approach |
| MI-05 | Stream DaQ narrative vs table | OPEN | Fix report.md to Pathway (Python) |
| MI-06 | T-Assess DOI not provided | OPEN | VLDB 2024 (not 2025) — see Literature Findings |
| MI-07 | "Framework" weakly defended | OPEN | Defend as architecture + extensible interface |
| MI-08 | CRS001 upper bound: 120 km/h spec vs 160 km/h code | OPEN | Choose one; propagate |

---

### Literature Findings — CORRECTIONS

---

#### LIT-01: METER year — 2024 (NOT 2023)

**What — corrected** (Literature Agent):

| Document | Claimed Year | Correct Year | Evidence |
|----------|-------------|-------------|----------|
| `audit_streaming_dq_frameworks.md` | "VLDB 2023" | **2024** | doi:10.14778/3636218.3636233 = PVLDB Vol.17, No.4, **2024** |
| `writing-rules.mdc` | "VLDB 2024" | **Correct** | ✓ |
| `report.md` | "VLDB 2024" | **Correct** | ✓ |
| `COMPETITIVE_TABLE.md` | "PVLDB Vol.17" | **Correct** | ✓ |

The Literature Agent confirmed that `audit_streaming_dq_frameworks.md` incorrectly says "VLDB 2023." All other audited documents correctly use "VLDB 2024" or "PVLDB Vol.17, No.4."

**Prior reviews were WRONG** — they claimed "VLDB 2023 appears in 6+ documents." The Literature Agent's direct inspection shows only `audit_streaming_dq_frameworks.md` has the error.

**Status**: FIX IN audit_streaming_dq_frameworks.md ONLY

---

#### LIT-02: T-Assess year — 2024 (NOT 2025)

**What — corrected** (Literature Agent):

Multiple documents cite "VLDB 2025" for T-Assess. The Literature Agent confirms: T-Assess appeared in **PVLDB Vol.18, No.3, published November 2024**. The "2025" in documents refers to the VLDB conference year, but the paper was published in the 2024 volume.

**Status**: OPEN — Update all documents to "PVLDB Vol.18, No.3, 2024"

---

#### LIT-03: Mirzaie DOI — PLACEHOLDER confirmed invalid

**What — confirmed** (Literature Agent):

`doi:10.1016/j.ipl.2023.03.XXX` — the "XXX" is a placeholder. DOI is structurally valid for IPL journal format but the article number is missing. This is not "unverified" — it is a **placeholder** that will not resolve.

**Status**: OPEN — Remove or replace with actual DOI

---

#### LIT-04: Fisher z naming — HYPOTHESES.md calls it "DeLong" but body text is correct

**What — confirmed** (Literature Agent):

The test described in HYPOTHESES.md H2-B body text is actually **Fisher z** (correct test for independent correlations). The header calls it "DeLong's test adapted" (wrong name). STATISTICAL_PLAN.md uses "Fisher z" (correct name, correct test).

**Prior reviews**: COMPREHENSIVE_REVIEW correctly identified this as MINOR. AUTHORITATIVE_REVIEW over-classified as CRITICAL.

**Correct fix**: Rename to "Meng's (1992) z-test for dependent correlations" (for H2-B's actual use case of dependent correlations — see STAT-02).

**Status**: OPEN

---

## Part 2: Cross-Document Consistency (Updated)

| Conflict | Doc A | Doc B | Resolution | Severity |
|----------|-------|-------|------------|:--------:|
| TQS system | FORMULATION §6 (Tm/Cn/Ac/Cs/Uv) | DATA_STRUCTURES §4 (V/C/Cn/P) | Rewrite DATA_STRUCTURES to new system | CRITICAL |
| TQS weights | FORMULATION §6.3 (Tm=0.20...) | FAILURE_MODES §Q2 (V=0.40...) | FAILURE_MODES uses old system | CRITICAL |
| TQS circularity | All docs claim non-circular | Only Tm is non-circular | Acknowledge CN/Ac/Cs/Uv circularity | MAJOR |
| Tm unit scale | Tm formula λ=0.01 | Flink timestamps in ms | Recalibrate λ for ms-scale | CRITICAL |
| CRS002 threshold | FORMULATION (100m/30s) | Code (100.0m) | Both wrong; fix to 333m | CRITICAL |
| CRS003 replay | is_replay=True gate | Should detect duplicates | Option A: synthetic bypass | CRITICAL |
| CRS003 hash | SHA256(lat/lon all) | MD5(PULoc+DOLoc+Pax) | Fix FORMULATION per-dataset | MAJOR |
| H2-B test | Fisher z (independent) | Meng z (dependent needed) | Replace with Meng's z-test | MAJOR |
| Bonferroni level | Applied at RQ level (5) | Should be at hypothesis level (12) | Fix to α_adj=0.004 | MAJOR |
| Bootstrap iters | 1,000 (P99) | Need 10,000 minimum | Increase in metrics.py | MAJOR |
| METER year | audit_streaming...md (2023) | All others (2024) | Fix one doc only | MINOR |
| T-Assess year | All docs (2025) | Correct (2024) | Fix across all docs | MINOR |
| Mirzaie DOI | XXX placeholder | Invalid | Remove or replace | MINOR |
| D4 dimensionality | 5D in most docs | 4D in QUALITY_AUDIT | Change all to 4D | MINOR |
| Stream DaQ arch | report.md (Kafka+Flink) | COMPETITIVE_TABLE (Pathway) | Fix report.md | MINOR |
| CRS dataset scope | report.md (implies both) | CRS = NYC MTA Bus only | Explicitly scope | MAJOR |
| V1/V2 framing | V1 "principled," V2 "wrong" | Both are design choices | Document trade-offs | MINOR |

---

## Part 3: 5-Dimension Coverage (Updated)

| Dimension | Prior Review | Updated | Change |
|-----------|-------------|---------|--------|
| **Streaming** | 🟢 PASS | 🟢 PASS | Unchanged |
| **Data Quality** | 🔴 RED | 🔴 RED | NG-1/NG-2/NG-4 added; CRS002 still broken |
| **Framework** | 🟡 AMBER | 🟡 AMBER | Evaluation infrastructure still absent |
| **Context-Aware** | 🟢 PASS | 🟡 AMBER | Tm unit-scale problem; CN/Ac/Cs/Uv circularity |
| **Monitoring** | 🟡 AMBER | 🟡 AMBER | TQS architecture split unresolved; NG-1 silent failure |

**Significant changes**: Context-Aware downgraded from PASS to AMBER (Tm unit-scale + circularity in CN/Ac/Cs/Uv). Data Quality remains RED (4 new NG issues on top of existing CR issues).

---

## Part 4: What Survived Adversarial Scrutiny

The following findings held up across ALL four adversarial reviews:

1. **CRS002 threshold is catastrophically wrong** — confirmed by math, physics, and code inspection. Fires on all normal urban traffic at 30s intervals.
2. **Evaluation infrastructure is absent** — confirmed by repo inspection across all reviews. Zero measured results exist.
3. **TQS architecture split across documents** — FORMULATION uses new non-circular TQS; DATA_STRUCTURES uses old circular TQS. Not partially fixed — entirely unchanged.
4. **L4 dilution destroys aggregate ΔF1 claim** — confirmed quantitatively. 5pp applies to ~5% of events; aggregate is 1-2pp. Must be explicitly scoped.
5. **Java CRS rules not built** — confirmed by repo inspection. Python prototypes exist but no Java Flink implementations.
6. **Phase 3 timeline unrealistic** — confirmed. ML + METER + Grafana + ablation + paper in 3 weeks is infeasible.
7. **D4 Holiday is a stub** — "5D" should be "4D." Confirmed across all reviews.
8. **METER DOI verified correct** — doi:10.14778/3636218.3636233 confirmed by Literature Agent.
9. **Deequ DOI verified correct** — doi:10.14778/3229863.3229867 confirmed.
10. **CETrajAD authors verified** — Cao & Akoglu confirmed by Literature Agent.
11. **Stream DaQ is Pathway (Python)** — COMPETITIVE_TABLE is authoritative; report.md narrative needs fixing.
12. **zone_category lookup not implemented** — confirmed. 20-line data loading task remains undone.

---

## Part 5: What Didn't Survive

The following claims were corrected or overturned by adversarial review:

| Claim | Prior Review Said | Corrected Finding |
|-------|-----------------|-------------------|
| H0 missing from every hypothesis | CRITICAL (M002, CR-02) | H0 is present in all 12 hypotheses — prior reviews did not read the source |
| METER year wrong in 6+ docs | MAJOR (MA-07, MA-12) | Only `audit_streaming_dq_frameworks.md` has 2023; all others use 2024 |
| B2 duplicate injection broken | CRITICAL (M014, CR-06) | Already emits 2 records; real bug is `is_replay=True` tagging (NG-4) |
| B1 NaN guard underspecified | MAJOR/MINOR (MI-05, M028) | 3-type implementation already exists in code |
| CRS003 MD5 vs SHA256 | CRITICAL (CR-04) | Spec is catastrophically wrong for TLC; code approach is architecturally correct |
| CRS001 lower bound fires on stops | MAJOR (MA-09) | No `min_speed_kmh` parameter exists; CRS001 only checks upper bound |
| Ac bounds are "loose" as flaw | MAJOR (MA-02) | Loose by design (safety net); unvalidated is the issue, not loose |
| V1 equal weights is "principled" | MAJOR (MA-06) | Both V1 and V2 are design choices; neither is non-arbitrary |
| "1-2pp not meaningful" | MAJOR (MA-04) | At NYC TLC scale, 1-2pp × 500K = 5K-10K events/day — IS meaningful |
| Option B (keep gate) correct | CRITICAL (P0.3) | Option B reduces evaluation scope; Option A (synthetic bypass) is correct |
| ML "no improvement" risk hidden | Not flagged | 3-5 week investment; "no improvement" is most likely outcome — must be explicit |

---

## Part 6: Full Correction Cascade — What Each Prior Review Got Wrong

### FINAL_PROJECT_AUDIT.md (M001-M028)

| Issue ID | What It Said | What It Got Wrong | Correction |
|----------|-------------|-------------------|------------|
| M002 | H0 missing from every hypothesis = CRITICAL | Did not read HYPOTHESES.md body text; H0 present in all 12 hypotheses | REMOVED from issue register |
| M004 | L4 dilution destroys 5pp claim = CRITICAL | Correct identification, but "1-2pp not meaningful" framing is wrong | Reframe as "meaningful at NYC TLC scale" |
| M006 | Mirzaie DOI invalid = CRITICAL | DOI is placeholder (XXX) — not "invalid" per se, but effectively unverifiable | Keep as OPEN but not CRITICAL severity |
| M007 | DeLong misapplied = CRITICAL | Test body is Fisher z (correct); only name is wrong; also, Meng's z needed for dependent correlations | Downgrade to MINOR; fix to Meng's z |
| M014 | B2 broken = MAJOR | Injector already emits 2 records; real bug is NG-4 (is_replay=True) | Reclassify as NG-4 |
| M017 | V2 weights "unprincipled" = MAJOR | Both V1 and V2 are design choices; neither is objectively principled | Document both with trade-offs |
| M019 | Phase 3 unrealistic = MAJOR | Correct but understated — ML risk is highest; "no improvement" most likely | Add explicit ML go/no-go criteria |
| M024 | zone_category not in schema = MINOR | Correct but understated — affects all L0 context cells | Upgrade to MAJOR |
| M027 | "Framework" weakly defended = OBSERVATION | Correct, minor | Keep as MINOR |

### COMPREHENSIVE_REVIEW.md

| Issue | What It Said | What It Got Wrong | Correction |
|-------|-------------|-------------------|------------|
| CR-02 | H0 missing = CRITICAL | Did not read HYPOTHESES.md body text | REMOVED |
| CR-07 | Mirzaie DOI invalid = CRITICAL | DOI is placeholder, not "invalid"; citation not load-bearing | Keep OPEN, reduce severity |
| CR-04 | DeLong misapplied = CRITICAL | Body text correct (Fisher z); name wrong; also, Meng's z needed | Downgrade + fix to Meng's |
| MA-01 | TQS V1 vs V2 contradiction | Correct but misframed — V1 is not "principled" over V2 | Document as design choice |
| MA-03 | Tm formula "Ac plausibility" issue | Misdiagnosed — it's a Tm (Timeliness) issue, not Ac | Reclassify correctly |
| MA-07 | Power analysis uses n=90 | Correct count but wrong test (paired Wilcoxon not t-test) | STAT-01 correction |
| MA-09 | L0 min-samples not validated | Correct but not measured; 5% estimate is unverified | STAT-07 — measure empirically |
| MA-12 | METER year inconsistency | Wrong scope — only audit_streaming_dq_frameworks.md has 2023 | FIX IN ONE DOC ONLY |
| New-N1 | Tm formula unit inconsistency | Correctly identified but misattributed as "Ac plausibility" | Correct to "Tm (Timeliness)" |
| MI-08 | CRS001 test specs missing normal case | Correct — but the real issue is CRS002 threshold (fires on normal) | Add normal-speed test case |

### AUTHORITATIVE_REVIEW.md

| Issue | What It Said | What It Got Wrong | Correction |
|-------|-------------|-------------------|------------|
| CR-02 | TQS architecture split = CRITICAL | Correct identification but missed that only Tm is non-circular; CN/Ac/Cs/Uv are circular | Add circularity acknowledgment for CN/Ac/Cs/Uv |
| CR-03 | Replay gate design decision needed | Correct analysis but chose Option B (keep gate) as "alternative" | Option A (synthetic bypass) is correct |
| MA-04 | H1-A H0 incomplete for F1 | Correct identification but missed that adding F1 H0 might hurt the hypothesis | Keep FPR as primary DV; report F1 descriptively |
| MA-06 | METER year wrong in 6+ docs | Factually wrong — only one doc has the error | Correct to one doc |
| MA-09 | CRS001 lower bound fires on stops | Partially wrong — no min_speed_kmh param exists; lower bound concern is CRS002 | Clarify rule responsibility |
| New-N2 | CRS002 K=3 buffer mismatch | Correct identification | Keep as OPEN |
| New-N3 | entity_index column missing | Was OPEN but FIXED_AUDIT confirms applied | REMOVED from issue register |
| New-N4 | CRS001 upper bound 120 vs 160 | Correct — both spec and code need sync | Keep as OPEN |
| Grade | AMBER → GREEN after Phase 0 | Too optimistic — 4 new NG issues not counted; Tm circularity | DOWNGRADE to AMBER with RED sub-dimensions |

### FIXED_AUDIT_AND_PLAN.md

| Issue | What It Said | What It Got Wrong | Correction |
|-------|-------------|-------------------|------------|
| P0.3 | Option B (keep gate) is an acceptable "alternative" | Option B reduces evaluation scope — WRONG; Option A is the only correct path | Change to Option A mandatory |
| CR-01 | 250m minimum threshold sufficient | Scientific-Critical: 250m still fires on faster traffic; 333m required | Update to 333m minimum |
| ML confirmation | ML is confirmed as core contribution | Correct decision but understated ML risk — "no improvement" most likely | Add explicit go/no-go + risk acknowledgment |
| Grade | AMBER → GREEN after Phase 0 | 4 new NG issues + Tm circularity mean more work than Phase 0 handles | DOWNGRADE projection |
| CR-04 | Spec vs code: "code approach is closer to correct" | Correct framing but understated — spec is catastrophically wrong for TLC | Keep as CRITICAL, update framing |
| ML timeline | 16-week plan | Correct but Phase 3 ML = 3-5 weeks with highest failure risk | Add explicit ML go/no-go criteria |

---

## Part 7: Final Action Plan

### Priority 0 — Immediate (before any code)

| # | Action | Blocks | Status | Agent |
|---|--------|--------|--------|-------|
| P0.1 | CRS002 threshold: 100m → 333m in code AND FORMULATION.md | RQ5 | OPEN | Methodology |
| P0.2 | CRS003 synthetic bypass: tag synthetic duplicates `is_replay=False` (Option A) | CRS003 eval | OPEN | Code |
| P0.3 | NG-4 fix: `_enrich_with_lineage()` sets `is_replay=False` for synthetic events | CRS003 eval | OPEN | Code |
| P0.4 | NG-1 fix: remove confidence ≤0.4 emission suppression, or store low-confidence violations separately | CRS003 eval | OPEN | Code |
| P0.5 | NG-2 fix: add post-detection duplicate counter with `is_repeat=True` flag | CRS003 recall | OPEN | Code |
| P0.6 | NG-3 fix: make `with_entity_index()` return new instance (immutable pattern) | Thread safety | OPEN | Code |
| P0.7 | Rewrite DATA_STRUCTURES.md §4: implement new TQS (Tm/Cn/Ac/Cs/Uv) | RQ3, RQ4 | OPEN | Write |
| P0.8 | Tm λ recalibration: verify unit scale for ms data; cap σ²_Δt | TQS | OPEN | Algorithm |
| P0.9 | Build `evaluation/` directory: synthetic_injector extension, ground_truth_tracker, metrics (10K bootstrap), run_evaluation, README | All RQs | OPEN | Implement |
| P0.10 | Add H1-A F1 as descriptive DV (not formal hypothesis) | RQ1 | OPEN | Write |

### Priority 1 — Week 1-2

| # | Action | Blocks | Status |
|---|--------|--------|--------|
| P1.1 | Fix H2-B: replace Fisher z with Meng's z-test for dependent correlations | RQ3 | OPEN |
| P1.2 | Fix Bonferroni: apply at hypothesis level (α_adj=0.004) | All RQs | OPEN |
| P1.3 | Increase bootstrap iterations: 1,000 → 10,000 minimum | Metrics | OPEN |
| P1.4 | Scope ΔF1: 5pp = L0 cells only; aggregate 1-2pp stated as "meaningful at NYC TLC scale" | RQ1 | OPEN |
| P1.5 | McNemar power: recalculate for OR=1.2, n=1000+ matched pairs | RQ6 | OPEN |
| P1.6 | Fix FORMULATION.md Algorithm D: per-dataset hash strategy | CRS003 | OPEN |
| P1.7 | H2-A rewrite: test Tm only (non-circular); CN/Ac/Cs/Uv as exploratory | RQ3 | OPEN |
| P1.8 | Fix FAILURE_MODES §Q2: update to new TQS dimensions | Consistency | OPEN |
| P1.9 | Add CRS002 2-20 km/h → MEDIUM to severity table | RQ5 | OPEN |
| P1.10 | METER year: fix audit_streaming_dq_frameworks.md to 2024 | Literature | OPEN |
| P1.11 | T-Assess year: update all docs to 2024 (PVLDB Vol.18, No.3) | Literature | OPEN |
| P1.12 | Mirzaie DOI: remove placeholder or find actual article number | Literature | OPEN |
| P1.13 | CRS001 upper bound: choose 120 or 160, propagate to code + FORMULATION | Consistency | OPEN |
| P1.14 | D4: change "5D" → "4D" everywhere | Consistency | OPEN |
| P1.15 | Empirically measure L0 coverage from NYC TLC data | RQ1 | OPEN |

### Priority 2 — Week 3-8

| # | Action | Blocks | Status |
|---|--------|--------|--------|
| P2.1 | Java warmup: Maven + Flink skeleton | Phase 2 | OPEN |
| P2.2 | CRS003 in Java (RoaringBitmap dedup) | RQ5 | OPEN |
| P2.3 | CRS002 in Java (GPS jump buffer) | RQ5 | OPEN |
| P2.4 | CRS001 in Java (speed history) | RQ5 | OPEN |
| P2.5 | Choose TQS V1 or V2 with explicit trade-off documentation | TQS | OPEN |
| P2.6 | Add zone_category lookup from TLC Zone CSV | L0 | OPEN |
| P2.7 | Calibrate Ac bounds from NYC TLC data percentiles | TQS | OPEN |
| P2.8 | Add ML go/no-go criteria to Phase 3 plan | RQ6 | OPEN |
| P2.9 | Resolve report.md Phase 3 Gantt vs ML_POSITIONING.md conflict | Consistency | OPEN |
| P2.10 | Update Stream DaQ narrative in report.md (Pathway not Flafka) | Literature | OPEN |
| P2.11 | Fix CRS002 K=3 buffer: specify minimum-frequency check or recalibrate | CRS002 | OPEN |

### Priority 3 — Week 9-16

| # | Action | Blocks | Status |
|---|--------|--------|--------|
| P3.1 | Baseline evaluation: rule-only F1, precision, recall, latency | RQ1-RQ5 | OPEN |
| P3.2 | ML integration (if go/no-go passes at Week 14) | RQ6 | TBD |
| P3.3 | Ablation study | RQ6 | OPEN |
| P3.4 | Grafana dashboards | Monitoring | OPEN |
| P3.5 | Paper writing | Submission | OPEN |

---

## Part 8: Grade Projection (Updated)

| Scenario | Grade | Condition |
|---------|:-----:|-----------|
| No fixes | C to C+ | CRS002 broken, NG-1/2/4 silent failures, no eval |
| Phase 0 fixes only | B- to B | CRS002 fixed, replay gate bypassed, eval starts |
| Phase 0 + Priority 1 | B to B+ | Statistical methods corrected, literature fixed |
| Phase 0-1 + Phase 2 Java | B+ to A- | All CRS in Java, baseline eval done |
| Phase 0-2 + Phase 3 ablation + Grafana | A- to A | Full delivery without ML |
| Phase 0-3 complete (ML passes) | A to A+ | Full ML, measured results, paper |

**Honest ceiling with 16-week plan**: **A- to A** if Phase 0-1 are fixed aggressively and Phase 3 is scoped appropriately. **A** requires completing all CRS Java rules AND having measured results AND ML passing go/no-go. At current state (CRS002 broken, NG issues unknown, no evaluation): **C to C+**.

---

## Appendix: Issue Register Summary

| Category | Count | Highest Severity |
|----------|:-----:|:----------------:|
| CRITICAL (original) | 5 | CR-01 to CR-05 |
| NEW from code audit (NG) | 4 | NG-1 to NG-4 |
| MAJOR | 10 | MA-01 to MA-10 |
| MINOR | 8 | MI-01 to MI-08 |
| Statistical corrections | 7 | STAT-01 to STAT-07 |
| Literature corrections | 4 | LIT-01 to LIT-04 |
| **TOTAL OPEN** | **38** | — |
| REMOVED (corrected prior review) | 8 | H0, METER year, B1, B2, etc. |
| FIXED (applied in session) | 6 | entity_index, make_violation, etc. |

---

*Generated by Debate Moderator — adversarial synthesis of 4 specialist agent reviews*
*April 24, 2026*
