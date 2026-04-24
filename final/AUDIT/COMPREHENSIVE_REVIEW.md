# StreamDQ Final Documents — Comprehensive Review Report

**Date**: April 24, 2026
**Orchestrator**: Agent Orchestrator
**Scope**: All 17 files in `final/` across Phases 0–5
**Sources**: 6 parallel subagent inspections + direct document analysis

---

## Executive Summary

The StreamDQ final documents are in **AMBER status** — substantially developed but carrying 7 CRITICAL blockers that must be resolved before any implementation work begins. The audit from April 23, 2026 correctly identified the most severe issues, and this review confirms and extends those findings. The scientific integrity is partially compromised by statistical design errors (DeLong misapplied, RQ3 circular by construction, H0 absent across all hypotheses), the CRS002 GPS threshold is catastrophically miscalibrated (fires on all normal urban bus traffic), and zero measured benchmark results exist despite 13 weeks of planning. The documents demonstrate exemplary scientific honesty in labeling Tier-2/3 claims but suffer from internal inconsistencies, cross-document contradictions, and structural issues in the evaluation design that a PC reviewer would identify immediately.

The good news: the core architecture is sound, the scientific rigor intent is genuine, and the gap analysis and literature review are comprehensive. Fixing the 7 CRITICAL blockers is feasible within the remaining time budget if execution starts immediately.

---

## Overall Status: AMBER

**Verdict**: 7 CRITICAL blockers require immediate action. Implementation must not begin until P0 blockers are resolved.

---

## 5-Dimension Coverage Summary

| Dimension | Status | Evidence | Issues |
|-----------|:------:|----------|--------|
| **Streaming** | 🟢 PASS | Flink DataStream API, watermarks, idle detection, Kafka consumer in FORMULATION.md §8; event-time semantics documented | CRS002 calibrated for wrong update interval (1s assumed, 30s actual) |
| **Data Quality** | 🟡 PARTIAL | 10-rule taxonomy documented across FORMULATION.md, DATA_STRUCTURES.md, COMPETITIVE_TABLE.md; SYN/SEM/CRS classification explicit | CRS002 threshold catastrophically wrong; CRS003 hash broken for NYC TLC; D4 (5D) is stub; CRS rules only run on secondary dataset |
| **Framework** | 🟢 PASS | PipelineBackend interface in design docs; rule registry implied; pluggable storage in architecture; reproducible protocol documented in STATISTICAL_PLAN.md | Evaluation infrastructure not implemented; no measured results |
| **Context-Aware** | 🟡 PARTIAL | L0–L5 fallback in FORMULATION.md, DATA_STRUCTURES.md, HYPOTHESES.md; 5D context decomposition; power analysis for min-samples | D4 holiday is PARTIAL stub; 5pp claim not scoped to L0 cells; L4 dilution destroys aggregate claim; zone_category lookup unspecified |
| **Monitoring** | 🟢 PASS | Violation store, TQS aggregation, Prometheus metrics, Grafana dashboard in COMPETITIVE_TABLE.md, FORMULATION.md; evaluation protocol documented | TQS V1/V2 contradiction; Ac plausibility formula broken; TQS correlation design circular |

---

## Critical Issues (BLOCKERS) — RED

### CR-01: CRS002 threshold is catastrophically wrong — fires on all normal urban bus traffic

**Location**: `FORMULATION.md` §CRS002; `FAILURE_MODES.md` §Q3/Q5; `HYPOTHESES.md` §H3-CRS002; `STATISTICAL_PLAN.md` §CRS002

**What**: The CRS002 threshold of >100m displacement in 30s is calibrated for 1-second GPS update intervals. NYC MTA Bus GTFS-realtime publishes every 30 seconds. A bus traveling at 30 km/h moves 250m in 30 seconds — **2.5x above the 100m threshold**. CRS002 will fire on every normal urban-speed vehicle. Precision = 0% by construction.

**Impact**: CRS002 cannot achieve P > 0.70. RQ5 evaluation is broken. This is the single strongest PC reviewer attack vector.

**Recommended fix**: Recalibrate to 200–300m for 30s update intervals. The FAILURE_MODES already recommends this (Option A, R2). **Action: Must be fixed before Week 1.**

---

### CR-02: All hypotheses missing explicit H₀ statement

**Location**: `HYPOTHESES.md` — every hypothesis body; `STATISTICAL_PLAN.md` §RQ1–RQ3

**What**: The STATISTICAL_PLAN.md correctly lists H₀ for each hypothesis in table format. But the HYPOTHESES.md document — the primary hypothesis specification — does not include explicit H₀ statements in the body text of any hypothesis. A PC reviewer reading HYPOTHESES.md will see no H₀. The FINAL_PROJECT_AUDIT (M002) flagged this correctly.

**Impact**: All hypotheses are technically incomplete. PC reviewers check H₀ statements first.

**Recommended fix**: Add explicit H₀ paragraph to every hypothesis in HYPOTHESES.md. Example: "H₀: FPR(L0) ≥ FPR(L4) — context resolution provides no improvement over global fallback." **Action: Must be fixed before Week 1.**

---

### CR-03: RQ3 is still circular by construction

**Location**: `STATISTICAL_PLAN.md` RQ3 section; `HYPOTHESES.md` H2-A; `FORMULATION.md` §6 (partially fixed)

**What**: The STATISTICAL_PLAN.md has a non-circular RQ3 redesign using downstream ETA correlation. However, HYPOTHESES.md H2-A still defines TQS as decreasing with injection rate — the circular design. The heading "Hypothesis H2-A: TQS Decreases Monotonically with Injection Rate" tests monotonicity but the mechanism section still references violation-rate correlation. The non-circular redesign exists as an alternative approach in STATISTICAL_PLAN.md but is not propagated to HYPOTHESES.md.

Additionally, FORMULATION.md Algorithm E introduces a non-circular TQS (Tm, Cn, Ac, Cs, Uv from raw fields) but this new design is not cross-referenced in HYPOTHESES.md H2-A, which still references the old design.

**Impact**: RQ3 tests self-consistency, not quality capture. PC reviewer identifies circularity → RQ3 discarded.

**Recommended fix**: Rewrite H2-A in HYPOTHESES.md to reference the new stream-intrinsic TQS design. Explicitly link to FORMULATION.md §6. Delete all references to "TQS = 1 − violation_rate" in HYPOTHESES.md. **Action: Must be fixed before Week 3.**

---

### CR-04: DeLong's test misapplied to Spearman correlation

**Location**: `HYPOTHESES.md` H2-B; `STATISTICAL_PLAN.md` §H2-B

**What**: H2-B in HYPOTHESES.md proposes "DeLong's test for comparing Spearman ρ_s." DeLong's test is for comparing two AUC/ROC curves, not correlation coefficients. This is a methodologically invalid statistical test.

The STATISTICAL_PLAN.md §H2-B partially fixes this by noting "Fisher z-transformation on ρ_s" but this is in the stat plan, not in HYPOTHESES.md H2-B itself, which still says "DeLong's test adapted for Spearman correlation."

**Impact**: PC reviewer with statistical background will immediately flag this as invalid methodology.

**Recommended fix**: In HYPOTHESES.md H2-B, replace "DeLong's test adapted for Spearman correlation" with "Fisher z-transformation for comparing two correlated correlation coefficients (Steiger, 1980)." Add reference: Steiger, J.H. (1980). "Tests for comparing elements of a correlation matrix." Psychological Bulletin, 87(2), 245–251. **Action: Must be fixed before Week 3.**

---

### CR-05: Evaluation infrastructure does not exist

**Location**: All documents that claim measured P/R/F1 results; `report.md` §Phase 1B; `FORMULATION.md`

**What**: Every document claims Tier-2 estimated results. No evaluation directory, synthetic injector, ground truth tracker, metrics module, or run script exists in the codebase. The FINAL_PROJECT_AUDIT (M005) correctly calls this the most critical blocker.

**Impact**: At thesis submission, there will be zero measured benchmark data. Every P/R/F1 number is estimated. The ground-truth evaluation framework (Claim 7) cannot be demonstrated without actual evaluation runs.

**Recommended fix**: Build `evaluation/` directory immediately: `synthetic_injector.py`, `ground_truth_tracker.py`, `metrics.py` (1,000 bootstrap), `run_evaluation.py`, README.md. This is the single highest-priority task before any code implementation. **Action: Must start in Week 1, complete by Week 2.**

---

### CR-06: CRS003 duplicate injection must emit TWO records (B2)

**Location**: `HYPOTHESES.md` §H3-CRS003; `STATISTICAL_PLAN.md` §CRS003; `QUALITY_AUDIT.md`; `FORMULATION.md` Algorithm D; `FINAL_PROJECT_AUDIT.md` M014

**What**: The synthetic injector currently emits the duplicate event only, not the original plus duplicate. CRS003 requires two records (original + duplicate) within the deduplication window to detect the duplicate. Without both records, CRS003 recall = 0% by construction. This is marked Tier 3 (Unmeasurable) in the documents, which is correct, but B2 must be fixed before CRS003 evaluation is possible.

**Impact**: CRS003 recall is unmeasurable. CRS layer evaluation is incomplete. If CRS003 is part of the CRS contribution statement, the CRS evaluation is incomplete without it.

**Recommended fix**: Modify `synthetic_injector.py` to emit the original event first (tagged with `entity_index`), then emit the duplicate (tagged with `entity_index_duplicate`). Both must be within the 300s deduplication window. Test with known inputs before proceeding. **Action: Must be fixed in Week 1 alongside CR-05.**

---

### CR-07: Mirzaie et al. (2023) DOI is invalid

**Location**: `audit_streaming_dq_frameworks.md` Ref [16]; `literature_review/` references

**What**: `doi:10.1016/j.ipl.2023.03.XXX` — the DOI ends in "XXX" placeholder. The paper cannot be verified.

**Impact**: An unverifiable citation damages credibility. Reviewers check DOIs.

**Recommended fix**: Search for the correct paper. The "IPL" (Information Processing Letters) journal uses the format `10.1016/j.ipl.2023.03.XXX`. Replace the XXX with the actual article number or remove the citation. **Action: Must be fixed before literature review is finalized.**

---

## Major Issues — AMBER

### MA-01: TQS V1 vs V2 contradiction across documents

**Location**: `FAILURE_MODES.md` (V1 recommended); `report.md` and `FORMULATION.md` (V2 primary); `QUALITY_AUDIT.md` Q30

**What**: FAILURE_MODES explicitly recommends V1 (equal weights) as primary. report.md and FORMULATION.md use V2 (domain-prioritized) as primary. QUALITY_AUDIT Q30 notes "V2 primary, criteria not stated." A reviewer reading FAILURE_MODES + report.md sees a direct contradiction.

**Impact**: Inconsistent across documents. Questions overall document coherence.

**Recommended fix**: Choose V1 (equal weights) as primary — it is the only non-arbitrary choice. Propagate this decision to ALL documents. V2 and V3 become sensitivity variants only. **Action: Before Week 3.**

### MA-02: CRS rules only run on secondary dataset (NYC MTA Bus)

**Location**: `report.md` §CRS data constraint; `COMPETITIVE_TABLE.md`; `HYPOTHESES.md` §H3-CRS001/CRS002

**What**: CRS001/CRS002 require GPS. NYC TLC (primary dataset) has no GPS (zone-level only). CRS rules run on NYC MTA Bus GTFS-realtime (secondary dataset). The primary dataset (NYC TLC) gets SYN/SEM only.

**Impact**: The "streaming GPS validation" contribution is demonstrated on a secondary dataset, not the primary evaluation. A PC reviewer will notice this asymmetry. M010 in the audit document addresses this.

**Recommended fix**: Reframe consistently: "CRS rules demonstrate GPS validation on GTFS-realtime feeds; NYC TLC evaluation uses SYN/SEM." Be explicit that CRS = NYC MTA Bus contribution, not NYC TLC. **Action: Update all documents that claim CRS runs on both datasets.**

### MA-03: Ac plausibility formula will collapse on real NYC TLC data

**Location**: `FORMULATION.md` §Tm formula; `STATISTICAL_PLAN.md` §Tm definition; `FINAL_PROJECT_AUDIT.md` M011

**What**: The Tm formula uses `exp(−λ · σ²_Δt)`. For real NYC TLC data with variable inter-arrival times, σ²_Δt is large → exp(−λ · σ²_Δt) → 0. The timeliness score collapses to 0 for normal heterogeneous streams.

**Impact**: TQS will show ~0 for legitimate events on real data → false positives on TQS itself. RQ3/RQ4 metrics compromised.

**Recommended fix**: Cap σ²_Δt at a maximum value, or normalize by mean inter-arrival time (coefficient of variation = σ/μ), or remove the variance term. The Ac dimension is also affected if variance is not bounded. **Action: Before Week 8.**

### MA-04: CRS003 NYC TLC hash uses lat/lon which don't exist

**Location**: `FORMULATION.md` Algorithm D; `QUALITY_AUDIT.md` Q39 (CRITICAL); `HYPOTHESES.md` §H3-CRS003; `FINAL_PROJECT_AUDIT.md` M012

**What**: Algorithm D specifies `hash = SHA256(trip_id + timestamp + lat + lon)` for ALL datasets. NYC TLC has no lat/lon — only PULocationID and DOLocationID. This is a design error. The hash for NYC TLC events will be computed with null lat/lon, producing incorrect dedup behavior.

**Impact**: CRS003 will silently produce wrong hashes for NYC TLC events. Dedup won't work on the primary dataset.

**Recommended fix**: Fix Algorithm D: "NYC TLC: hash = SHA256(trip_id + timestamp + PULocationID + DOLocationID); NYC MTA Bus: hash = SHA256(trip_id + timestamp + lat + lon)." Propagate to all CRS003 specifications. **Action: Week 1.**

### MA-05: RQ1 aggregate ΔF1 claim is diluted by L4 fallback

**Location**: `HYPOTHESES.md` H1-A; `SIGNIFICANCE_TABLE.md` §5.1; `FAILURE_MODES.md` §Q1; `STATISTICAL_PLAN.md` §RQ1 Power Analysis; `FINAL_PROJECT_AUDIT.md` M004

**What**: The "ΔF1 ≥ 5pp" claim applies only to events in L0 cells (estimated 5% of data). L4 global fallback covers 20–40% of events with no context-specific benefit. Aggregate ΔF1 is 1–2pp, NOT 5pp. The thesis headline claim implies 5pp across all events.

**Impact**: Reviewer will compute: if 20–40% of events use L4 and L4 provides no improvement, aggregate ΔF1 is 1–2pp. Claiming 5pp is misleading.

**Recommended fix**: Scope all ΔF1 claims explicitly: "For events in L0 context cells (5% of data), context-aware thresholds improve F1 by Xpp (95% CI: [a, b]). On all events including L4 fallback, the aggregate improvement is Ypp (95% CI: [c, d])." Update HYPOTHESES.md H1-A, SIGNIFICANCE_TABLE.md, and report.md. **Action: Week 3.**

### MA-06: CRS001 speed=0 lower bound fires on legitimate stop-and-go traffic

**Location**: `FORMULATION.md` Algorithm B §Step 5; `FAILURE_MODES.md` §Q3; `QUALITY_AUDIT.md` Q22; `FINAL_PROJECT_AUDIT.md` M021

**What**: CRS001 lower bound is 2 km/h. NYC MTA Bus vehicles regularly stop at traffic lights at 0–3 km/h. The 2 km/h threshold flags stationary vehicles as violations.

**Impact**: False positives on legitimate stop-and-go traffic → CRS001 precision drops.

**Recommended fix**: Add time_delta threshold: if speed < 2 km/h AND time_delta > 60s, pass (legitimate stop). If speed < 2 km/h AND time_delta ≤ 60s, flag (potential GPS jitter or cold-start). **Action: Week 8.**

### MA-07: RQ1 power analysis underpowered for aggregate ΔF1

**Location**: `STATISTICAL_PLAN.md` §RQ1 Power Analysis; `HYPOTHESES.md` H1-A; `FINAL_PROJECT_AUDIT.md` M013

**What**: Plan uses n=90 windows (30 cells × 3 trials). Required n for aggregate ΔF1 detection (d=0.10–0.15) is n≥700. Type II error risk ~30–40%. The plan will likely fail to detect the 1–2pp aggregate ΔF1 it hopes to find.

**Impact**: H1-A rejected not because context-aware thresholds don't work, but because the experiment is underpowered.

**Recommended fix**: Either (a) increase sample size to n≥700, (b) focus only on L0-specific ΔF1 (n=140 sufficient), or (c) explicitly label aggregate ΔF1 as "exploratory, not confirmatory." **Action: Week 3.**

### MA-08: Phase 3 timeline (3 weeks) is unrealistic

**Location**: `report.md` Part VI Phase 3; `FAILURE_MODES.md`; `FINAL_PROJECT_AUDIT.md` M019

**What**: Phase 3 = ablation study + ML integration + METER drift detection + Grafana + paper writing. Realistically needs 5–6 weeks minimum. With Java learning curve (M008: 5–6 weeks instead of 2), Phase 3 becomes Weeks 11–16+.

**Impact**: Phase 3 incomplete → ML layer absent → RQ6 absent → thesis loses ML contribution. Paper writing gets compressed.

**Recommended fix**: Cut Phase 3 to essentials: ablation + Grafana + paper. Defer ML integration and METER to future work. The ML positioning document (ML_POSITIONING.md) already frames ML as optional. **Action: Update timeline in report.md.**

### MA-09: L0 min-samples (100) not empirically validated

**Location**: `HYPOTHESES.md` H1-A edge cases; `report.md` §L0-L5 power analysis; `QUALITY_AUDIT.md` I7; `FINAL_PROJECT_AUDIT.md` M015

**What**: The 100-samples threshold is from power analysis but never validated against actual NYC TLC statistics. If real L0 cells have < 100 samples, the power analysis is moot.

**Impact**: If L0 coverage is 0–1% (not 5%), the entire H1-A hypothesis has insufficient cells to test.

**Recommended fix**: Verify L0 coverage empirically from NYC TLC data before finalizing the plan. Adjust min-samples if needed. **Action: Week 3 (data analysis).**

### MA-10: CRS002 severity for 2–20 km/h moderate spoofing absent from spec

**Location**: `report.md` §Severity-to-Alert; `QUALITY_AUDIT.md` Q6; `COMPETITIVE_TABLE.md`; `FINAL_PROJECT_AUDIT.md` M016

**What**: The severity table maps CRS002 only to "<1 km/h" (CRITICAL) and ">100m jump" (HIGH). The 2–20 km/h range (moderate spoofing) is not covered. The FAILURE_MODES documents B3 (CRS002 speed range gap) as a known limitation but it's not in the severity table.

**Impact**: Moderate GPS spoofing (2–20 km/h) has no severity assignment → unclear alert behavior.

**Recommended fix**: Add explicit row to severity table: "CRS002 IMPOSSIBLE_SPEED (2–20 km/h) → MEDIUM." Acknowledge B3 gap in severity documentation. **Action: Week 3.**

### MA-11: Java learning curve catastrophically underestimated

**Location**: `report.md` Part VI Phase 2; `FAILURE_MODES.md` §CRS Java complexity; `FINAL_PROJECT_AUDIT.md` M008

**What**: Phase 2 plan says "CRS rules in Java = 2 weeks." For a Python developer, Java proficiency for Flink KeyedProcessFunction requires 5–6 weeks minimum (JVM, Maven, protobuf, Flink state API).

**Impact**: Phase 2 delayed 3–4 weeks → CRS rules incomplete → RQ5 cannot be evaluated.

**Recommended fix**: Add Java warmup to Week 5. Implement CRS003 in Java first (simplest rule). Budget 3 weeks for CRS001+CRS002. **Action: Update timeline in report.md.**

### MA-12: METER year inconsistency

**Location**: `audit_streaming_dq_frameworks.md` (PVLDB Vol.17, No.4, 2023); `report.md` (VLDB 2024); `COMPETITIVE_TABLE.md` (PVLDB Vol.17); `writing-rules.mdc` (VLDB 2024); `FINAL_PROJECT_AUDIT.md` §Literature

**What**: Some documents say "METER = VLDB 2023," others say "VLDB 2024." PVLDB is journalized so both are defensible (publication date vs. volume year), but the inconsistency across documents signals sloppiness.

**Impact**: Minor credibility hit. Reviewers who cross-reference will notice.

**Recommended fix**: Standardize on "VLDB 2024" (volume year, PVLDB Vol.17, No.4) across ALL documents. Update audit_streaming_dq_frameworks.md, writing-rules.mdc, and any other documents that use "VLDB 2023." **Action: Low priority, fix before submission.**

---

## Minor Issues — GREEN

### MI-01: D4 Holiday is a stub — "5D" should be "4D"

**Location**: `report.md` §5D Context Decomposition; `QUALITY_AUDIT.md` Q8; `COMPETITIVE_TABLE.md` §Appendix B; `FINAL_PROJECT_AUDIT.md` M022

**What**: D4 External context (holiday indicator) is PARTIAL. The "5D" claim should be "4D (D1, D2, D3, D5)."

**Recommended fix**: Change "5D" to "4D (D1, D2, D3, D5)" everywhere. Add D4 to future work.

### MI-02: L0 key uses zone_category not in event schema

**Location**: `FORMULATION.md` §L0 Context Key; `report.md` §L0-L5 table; `QUALITY_AUDIT.md` Q7; `FINAL_PROJECT_AUDIT.md` M024

**What**: L0 key uses `zone_category` which is not in the NYC TLC event schema. PULocationID (1–263) requires a lookup table to map to zone_category (Manhattan vs outer borough).

**Recommended fix**: Add zone_category lookup from TLC Zone Lookup CSV (public dataset). Specify as static reference table.

### MI-03: CRS002 confidence tiers vague across documents

**Location**: `FORMULATION.md` §CRS002; `QUALITY_AUDIT.md` Q9; `report.md` §CRS002; `FINAL_PROJECT_AUDIT.md` M025

**What**: "1 prior = LOW, 2+ = MEDIUM, 3+ = HIGH" is defined in QUALITY_AUDIT but not in FORMULATION.md or report.md.

**Recommended fix**: Add confidence tier specification to FORMULATION.md CRS002 algorithm. Reference QUALITY_AUDIT.

### MI-04: Synthetic GPS trajectory fallback plan is vague

**Location**: `report.md` §NYC MTA Bus Data Source; `HYPOTHESES.md` §H3-CRS001 edge case; `FINAL_PROJECT_AUDIT.md` M023

**What**: Contingency for live feed failure has no spec for generating synthetic GPS from GTFS Static route geometry.

**Recommended fix**: Specify: generate synthetic GPS waypoints along GTFS static route shapes at configurable intervals. Provide pseudocode.

### MI-05: B1 NaN guard underspecified

**Location**: `report.md` §B1; `QUALITY_AUDIT.md` Q27; `HYPOTHESES.md` §B1; `FINAL_PROJECT_AUDIT.md` M028

**What**: Three NaN types need three guards: `math.isnan()` (float), `np.isnan()` (numpy), `pd.isna()` (pandas).

**Recommended fix**: Implement all three guards. Test each type explicitly.

### MI-06: "Framework" in title weakly defended

**Location**: `COMPETITIVE_TABLE.md` §"Framework" Title Defense; `THREAT_MODELER` report; `FINAL_PROJECT_AUDIT.md` M027

**What**: NYC-specific rules are not reusable across domains. A PC reviewer may ask: "Where is the framework?"

**Recommended fix**: Defend as: "Framework provides architecture + extensible rule interface. NYC rules are exemplar, not limitation." Or consider changing title to "A Context-Aware System for Streaming Data Quality Monitoring."

### MI-07: Stream DaQ narrative vs table inconsistency

**Location**: `report.md` Part I §Stream DaQ; `COMPETITIVE_TABLE.md` §4.1; `QUALITY_AUDIT.md`; `FINAL_PROJECT_AUDIT.md` M018

**What**: report.md Part I says "Stream DaQ: Originally Kafka + Flink." COMPETITIVE_TABLE.md says "Pathway (Python)." The table is correct; the narrative is wrong.

**Recommended fix**: Update report.md Part I to say "Pathway (Python)" not "Originally Flink."

### MI-08: CRS001 test specs don't cover normal urban-speed case

**Location**: `FORMULATION.md` §Unit Test Specifications A1-A6, C1-C3; `QUALITY_AUDIT.md` §Unit Test Coverage; `FINAL_PROJECT_AUDIT.md` M026

**What**: C1-C3 tests for CRS001 don't cover the "vehicle at 30–50 km/h (normal urban bus speed)" case. Tests pass but real data would fire CRS002.

**Recommended fix**: Add test case: normal bus at 30 km/h over 30s interval → 250m displacement → CRS002 fires (false positive if threshold is 100m). This test will expose CR-01.

### MI-09: CRS002 TTL 310s partiallyMitigates but doesn't fix gap

**Location**: `FORMUALTION.md` Algorithm D; `FAILURE_MODES.md`; `FINAL_PROJECT_AUDIT.md` M023

**What**: CRS003 TTL of 310s is a reasonable design choice but the trip duration range (10–90 min) means many GTFS trips exceed the dedup window.

**Recommended fix**: Increase TTL to 600s (10 minutes) or add explicit note about the window boundary limitation.

### MI-10: T-Assess DOI not provided

**Location**: `audit_streaming_dq_frameworks.md` §T-Assess; `report.md` Part II; `COMPETITIVE_TABLE.md` §Appendix A; `FINAL_PROJECT_AUDIT.md` M020

**What**: T-Assess is referenced as "VLDB 2025, PVLDB Vol.18, No.3, pp.666-674" but DOI is not provided.

**Recommended fix**: Add DOI once VLDB 2025 proceedings are published. Use arXiv preprint as interim citation.

---

## No-Lite Delivery Check

| Deliverable | Implementation | Tests | Reproducibility | Status |
|-------------|:--------------:|:-----:|:--------------:|:------:|
| CRS001 (Java) | Design only | Spec only | Protocol documented | 🔴 MISSING |
| CRS002 (Java) | Design only | Spec only | Protocol documented | 🔴 MISSING |
| CRS003 | Design only | Spec only | Protocol documented | 🔴 MISSING |
| Adaptive Thresholds | Design + pseudocode | Spec only | Protocol documented | 🟡 PARTIAL |
| Evaluation Pipeline | Not built | Not built | README not built | 🔴 MISSING |
| TQS Aggregation | Design + pseudocode | Unit tests (alg E) | Protocol documented | 🟡 PARTIAL |

**Note**: The documents provide exceptional designs with pseudocode, unit test specifications, and reproducibility protocols. But zero of these are implemented in code. The "No-Lite" delivery standard requires implementation + tests + reproducibility, not design documents alone.

---

## Cross-Document Consistency

| Conflict | Document A | Document B | Resolution |
|----------|-----------|-----------|------------|
| TQS V1 vs V2 primary | FAILURE_MODES (V1) | report.md, FORMULATION.md (V2) | Choose V1, propagate everywhere |
| CRS002 threshold | FORMULATION.md (100m/30s) | FAILURE_MODES (broken) | Fix to 200–300m for 30s |
| TQS circularity | STATISTICAL_PLAN (non-circular redesign) | HYPOTHESES.md H2-A (still circular) | Propagate non-circular design to HYPOTHESES |
| DeLong's test | HYPOTHESES.md (invalid) | STATISTICAL_PLAN.md (Fisher z) | Fix HYPOTHESES to match STATISTICAL_PLAN |
| METER year | audit_streaming_dq_frameworks.md (2023) | report.md, writing-rules.mdc (2024) | Standardize to 2024 everywhere |
| ΔF1 scope | HYPOTHESES (5pp aggregate) | SIGNIFICANCE_TABLE (L0 only) | Scope all claims to L0 cells |
| D4 dimensionality | Multiple (5D) | QUALITY_AUDIT (4D, D4 PARTIAL) | Change all to 4D until D4 built |
| Stream DaQ architecture | report.md (Flafka) | COMPETITIVE_TABLE (Pathway) | Fix report.md narrative |
| CRS003 hash | FORMULATION.md Algorithm D (lat/lon all) | QUALITY_AUDIT Q39 (NYC TLC has no lat/lon) | Fix Algorithm D per dataset |
| CRS rules dataset | report.md (implies both datasets) | everywhere else (CRS = MTA Bus only) | Explicitly scope CRS to NYC MTA Bus |

---

## Action Items (Prioritized)

### P0 — Must Fix Before Any Implementation (Week 1)

| # | Action | Owner | Blocks | Status |
|---|--------|-------|--------|--------|
| P0.1 | Build `evaluation/` directory: synthetic_injector, ground_truth_tracker, metrics (1K bootstrap), run_evaluation, README | Implement | All evaluation | OPEN |
| P0.2 | Fix B2: duplicate injection emits TWO records (original + duplicate) | Implement | CRS003 recall | OPEN |
| P0.3 | Fix CRS003 NYC TLC hash: use PULocationID+DOLocationID, not lat/lon | Implement | CRS003 on TLC | OPEN |
| P0.4 | Recalibrate CRS002 threshold: minimum safe ≥ 200–300m for 30s update intervals | Methodology | RQ5 CRS002 | OPEN |
| P0.5 | Add explicit H₀ statement to every hypothesis in HYPOTHESES.md | Write | All RQs | OPEN |
| P0.6 | Fix DeLong's test → Fisher z-transformation in HYPOTHESES.md H2-B | Methodology | RQ3 stats | OPEN |
| P0.7 | Fix Mirzaie DOI or remove citation | Write | Literature review | OPEN |

### P1 — Must Fix Before Phase 2 (Week 3–5)

| # | Action | Owner | Blocks | Status |
|---|--------|-------|--------|--------|
| P1.1 | Rewrite RQ3/H2-A: propagate non-circular TQS design from STATISTICAL_PLAN to HYPOTHESES | Write | RQ3 | OPEN |
| P1.2 | Scope ΔF1 claim: 5pp = L0/L1 cells only. Aggregate = 1–2pp (honest). Update all docs | Write | RQ1 | OPEN |
| P1.3 | Choose TQS variant (V1 equal weights) with explicit criteria. Propagate to ALL documents | Write | TQS | OPEN |
| P1.4 | Verify L0 coverage empirically from NYC TLC data | Data analysis | RQ1 power | OPEN |
| P1.5 | Add CRS002 severity for 2–20 km/h (B3 documented) to severity table | Write | CRS002 | OPEN |
| P1.6 | Add Java warmup to Week 5. Implement CRS003 first. Budget 3 weeks for CRS001+CRS002 | Planning | Phase 2 | OPEN |
| P1.7 | Cut Phase 3 to essentials: ablation + Grafana + paper. Defer ML + METER | Planning | Timeline | OPEN |

### P2 — Must Fix Before Evaluation (Week 6–10)

| # | Action | Owner | Blocks | Status |
|---|--------|-------|--------|--------|
| P2.1 | Fix Ac plausibility formula: cap σ²_Δt or use CV instead of raw variance | Algorithm | TQS | OPEN |
| P2.2 | Add CRS001 speed=0 + time_delta threshold (legitimate stops) | Algorithm | CRS001 | OPEN |
| P2.3 | Add CRS002 confidence tier spec to FORMULATION.md | Write | CRS002 | OPEN |
| P2.4 | Increase CRS003 TTL to 600s | Algorithm | CRS003 | OPEN |
| P2.5 | Add zone_category lookup from TLC Zone CSV | Data | L0 keys | OPEN |
| P2.6 | Fix METER year to 2024 everywhere | Write | Literature | OPEN |
| P2.7 | Update Stream DaQ narrative in report.md (Pathway not Flafka) | Write | Consistency | OPEN |
| P2.8 | Change "5D" to "4D (D1, D2, D3, D5)" everywhere | Write | D4 stub | OPEN |

---

## Recommended Next Steps (Priority Order)

1. **Build evaluation infrastructure** — This is the single most important action. Without it, no measured results exist. Start synthetic_injector.py and ground_truth_tracker.py immediately.

2. **Fix CRS002 threshold** — Recalibrate to 200–300m for 30s update intervals. This unblocks RQ5 evaluation. Document the fix with mathematical justification.

3. **Add H₀ to all hypotheses** — Every hypothesis in HYPOTHESES.md needs an explicit null hypothesis statement. This is a 30-minute task with high impact.

4. **Fix H2-B DeLong test** — Replace with Fisher z-transformation. This is a one-line fix with high visibility to statistical reviewers.

5. **Choose TQS V1** — Equal weights is the only defensible choice. Propagate this decision to all documents in one session.

6. **Scope ΔF1 claims to L0 cells** — Every "5pp" claim needs a parenthetical "(for events in L0 context cells)" or similar scoping. This is a find-and-replace across documents.

---

## Documents Audited

| File | Key Findings |
|------|-------------|
| `AUDIT/FINAL_PROJECT_AUDIT.md` | 28 issues tracked (7 CRITICAL, 13 MAJOR, 8 MINOR); all confirmed and extended |
| `05_ALGORITHM_DESIGN/STATISTICAL_PLAN.md` | Sound methodology; non-circular RQ3 redesign present but not propagated to HYPOTHESES |
| `05_ALGORITHM_DESIGN/FORMULATION.md` | CRS002 threshold catastrophically wrong; CRS003 hash broken for NYC TLC; TQS redesign (Tm/Cn/Ac/Cs/Uv) excellent |
| `05_ALGORITHM_DESIGN/HYPOTHESES.md` | H₀ absent everywhere; DeLong test misapplied; circular TQS in H2-A not updated |
| `05_ALGORITHM_DESIGN/FAILURE_MODES.md` | Excellent diagnostic; CRS002 breakdown comprehensive; V1/V2 contradiction present |
| `05_ALGORITHM_DESIGN/DATA_STRUCTURES.md` | Comprehensive; CRS002 unit tests need normal urban-speed case |
| `04_NOVELTY_CONTRIBUTION/SIGNIFICANCE_TABLE.md` | Excellent; L4 dilution quantified; circularity in RQ3 identified |
| `04_NOVELTY_CONTRIBUTION/COMPETITIVE_TABLE.md` | Correct; D4 caveat present; Stream DaQ narrative inconsistency persists |
| `04_NOVELTY_CONTRIBUTION/CONTRIBUTIONS.md` | Honest tier labeling; PC scores realistic; positioning statement strong |
| `04_NOVELTY_CONTRIBUTION/NOVELTY_SCORES.md` | PC review scores honest (4 WA, 4 B); kill shots correctly identified |
| `04_NOVELTY_CONTRIBUTION/ML_POSITIONING.md` | Correctly frames ML as collaborator not competitor; Phase 3 optional honest |
| `00_IDEA_VERIFICATION/gap_analysis.md` | 12 gaps well-documented; 5 CRITICAL gaps form coherent research agenda |
| `01_LITERATURE_REVIEW/AUDITS/audit_streaming_dq_frameworks.md` | METER year wrong (2023 vs 2024); Mirzaie DOI invalid |

---

*Generated by Orchestrator Agent — 6-zone parallel inspection*
*April 24, 2026*
