# StreamDQ Final Documents — Authoritative Consolidated Review

**Date**: April 24, 2026
**Orchestrator**: Agent Orchestrator
**Method**: 4-agent parallel debate synthesis + code verification
**Sources**: `FINAL_PROJECT_AUDIT.md`, `COMPREHENSIVE_REVIEW.md`, + 4 expert debate agents + direct codebase inspection

---

## Executive Summary

The StreamDQ final documents contain a substantial body of high-quality work — well-structured gap analysis, honest Tier-2/3 claim labeling, sound statistical methodology, and a genuine commitment to scientific rigor. However, the two existing reviews contain **4 significant factual errors** that undermine their credibility, and **11 issues** that were either missed or misclassified.

This synthesis resolves those errors, reconciles the contradictions between the two reviews, and provides a consolidated action plan with accurate severity ratings.

**Overall status: AMBER — significant work remains, but the foundation is sound.**

### The 4 Factual Errors in Existing Reviews

| Error | Review A says | Review B says | Truth |
|-------|-------------|-------------|-------|
| **H0 presence** | CRITICAL: H0 missing from every hypothesis | CRITICAL: H0 missing from every hypothesis | **REMOVED**: H0 is explicitly present in all 12 hypotheses in body text |
| **B2 fix status** | MAJOR: injector emits 1 record | CRITICAL: injector emits 1 record | **DOWNGRADE**: Injector already emits 2 records; real bug is the replay suppression gate |
| **B1 NaN guard** | MAJOR/MINOR: underspecified | MINOR: underspecified | **REMOVED**: 3-guard implementation already exists in code |
| **Mirzaie DOI** | CRITICAL: "invalid DOI" | CRITICAL: "invalid DOI" | **DOWNGRADE**: UNVERIFIED (not INVALID); DOI format is structurally correct |

These errors are not minor — they shift the CRITICAL count from 7 to 5, change the prioritization of 3 action items, and reveal that the audits did not verify claims against the actual codebase.

---

## Revised Master Issue Register

### CRITICAL Issues (5) — Fix before any implementation

#### CR-01: CRS002 threshold fires on ALL normal urban traffic (both reviews correct, both understated)

**Location**: `FORMULATION.md` Algorithm C; `HYPOTHESES.md` H3-CRS002; `FAILURE_MODES.md` §Q3; `DATA_STRUCTURES.md` test T6

**What**: At 30-second GTFS update intervals, a bus at 30 km/h travels 250m — **2.5× above the 100m threshold**. Every NYC MTA Bus in normal urban traffic fires CRS002. CRS002 precision = 0% by construction. RQ5 evaluation collapses.

**Additional complexity (neither review caught)**: The Algorithm C pseudocode uses a buffer of K=3 positions with a comment saying "covers 30s window at **1Hz**." At 1Hz, K=3 covers 3 seconds. At 30s intervals, K=3 covers 90 seconds. The buffer size was calibrated for 1Hz updates but the threshold was set for 30s intervals. These design parameters are **incompatible by construction**.

**Verification**: The unit test spec (TEST C2) says "Two positions **200m apart** → VIOLATION." At 30 km/h for 30s, displacement = 250m. This test would fire on normal traffic with the 100m threshold. The test specification is internally consistent with the broken threshold — but both the threshold AND the test are wrong.

**Fix**: (1) Change threshold to ≥250m (at 95th percentile speed of ~40 km/h, safe threshold is ~333m); (2) Update Algorithm C Step 3 pseudocode; (3) Update TEST C2 spec; (4) Update Physics Priors table. Estimated effort: 15 minutes for code, 30 minutes for docs.

**Status**: OPEN

---

#### CR-02: TQS architecture split — NEW non-circular vs. OLD circular (newly identified)

**Location**: `FORMULATION.md` §6 vs. `DATA_STRUCTURES.md` §4 vs. `HYPOTHESES.md` H2-A

**What**: Three documents use three different TQS systems:

| Document | Dimensions | Formula basis | Circular? |
|----------|:----------:|--------------|:---------:|
| `FORMULATION.md` §6 | Tm, Cn, Ac, Cs, Uv | Raw event fields | **Non-circular ✓** |
| `DATA_STRUCTURES.md` §4 | V, C, Cn, P | Rule violation counts | **Circular by construction ✗** |
| `HYPOTHESES.md` H2-A | Not specified | Mixed | **Ambiguous** |

`FORMULATION.md` §6 introduces an excellent non-circular TQS redesign (Tm from σ²_Δt, Cn from missing_count, Ac from raw plausibility, Cs from GPS coherence, Uv from hash distinctness — all from raw fields). `HYPOTHESES.md` H2-A was updated to reference this new design.

**But `DATA_STRUCTURES.md` §4 was NOT updated.** It still defines TQSCellState with violation counters (`syn001_violations`, `crs001_violations`, etc.) and derives the OLD TQS formula: `V = 1 − (syn001+syn002)/N` using rule outcomes.

If code is written against `DATA_STRUCTURES.md`, the non-circular design is irrelevant — the code will be circular by construction.

**Additional finding (new)**: `FORMULATION.md` §6.3 TQS V2 weights are `(Tm=0.20, Cn=0.25, Ac=0.20, Cs=0.25, Uv=0.10)`. `FAILURE_MODES.md` §Q2 TQS V2 weights are `(V=0.40, C=0.20, Cn=0.30, P=0.10)` — different dimensions, different weights. These are not weight variants of the same system; they are different systems.

**Fix**: (1) `DATA_STRUCTURES.md` §4 must be rewritten to implement the new Tm/Cn/Ac/Cs/Uv TQSCellState (not V/C/Cn/P). (2) `HYPOTHESES.md` H2-A must explicitly reference the new TQS dimensions. (3) `FAILURE_MODES.md` TQS sensitivity analysis must use the new dimensions. Estimated: 2-3 hours of doc revision.

**Status**: OPEN

---

#### CR-03: CRS003 replay suppression gate blocks ALL deduplication on TLC data (newly identified)

**Location**: `cross_record.py` lines 304-311; `nyc_taxi_replay.py` lines 202, 258-262

**What**: Both reviews agree the duplicate injection is broken (B2). The reviews disagree on whether the injector is fixed. **Code inspection reveals**: the injector already emits original + duplicate. But `evaluate_duplicate_event()` has this guard:

```python
if lineage.get("is_replay", False):
    return None  # ← SUPPRESSES ALL REPLAY DUPLICATES
```

NYC TLC replay data has `is_replay=True` for ALL events. The replay suppression gate silently disables CRS003 for the primary dataset — both for real duplicates AND for synthetic-injected duplicates.

**Impact**: CRS003 precision = 0% AND recall = 0% on NYC TLC replay. Not just unmeasurable — actively non-functional.

**Fix**: The injected duplicate must be tagged with `is_replay=False` to bypass the replay suppression gate. Estimated: 5-10 lines of code.

**Note**: The B2 "duplicate injection" issue is therefore correctly identified but incorrectly described. The fix is NOT "emit two records" (already done). The fix is "bypass replay suppression for injected duplicates."

**Status**: OPEN

---

#### CR-04: CRS003 hash mismatch between spec and implementation (newly identified)

**Location**: `FORMULATION.md` Algorithm D vs. `cross_record.py` hash computation

**What**:

| Aspect | FORMULATION.md | Actual Code |
|--------|---------------|-------------|
| Hash function | SHA256 | MD5 |
| Fields (NYC TLC) | `trip_id + timestamp + lat + lon` | `trip_id + PULocationID + DOLocationID + passenger_count + trip_distance` |

The spec requires `lat + lon` which don't exist in NYC TLC. The code uses semantic fields instead. This is a design divergence — the spec and code take different approaches.

**Impact**: The spec is wrong for NYC TLC (no GPS). The code is architecturally different from the spec (semantic dedup vs. GPS dedup). GTFS-realtime dedup path is not specified in either the spec or the code.

**Fix**: Update FORMULATION.md Algorithm D to specify per-dataset hash strategy: "NYC TLC: SHA256(trip_id + timestamp + PULocationID + DOLocationID); NYC MTA Bus: SHA256(trip_id + timestamp + lat + lon)." Estimated: 30 minutes.

**Status**: OPEN

---

#### CR-05: Evaluation infrastructure does not exist (both reviews correct)

**Location**: All documents that reference measured results

**What**: Every measured benchmark number is Tier-2 or Tier-3. No evaluation directory, no synthetic injector integration, no ground truth tracker, no metrics module, no run script exists.

**Fix**: Build `evaluation/` directory: `synthetic_injector.py` (extend existing replay), `ground_truth_tracker.py`, `metrics.py` (1,000 bootstrap), `run_evaluation.py`, `README.md`. Estimated: 1-2 weeks.

**Status**: OPEN

---

### MAJOR Issues (10) — Fix before Phase 2

#### MA-01: L4 dilution destroys aggregate ΔF1 claim (confirmed by both reviews)

**Location**: `HYPOTHESES.md` H1-A; `SIGNIFICANCE_TABLE.md` §5.1; `STATISTICAL_PLAN.md` §RQ1

**What**: 5pp ΔF1 applies to ~5% of events in L0 cells. L4 fallback covers 20-40% of events with no improvement. Aggregate ΔF1 is 1-2pp, NOT 5pp. The claim requires explicit scoping.

**Fix**: Scope all ΔF1 claims: "For events in L0 context cells, context-aware thresholds improve F1 by ≥5pp (95% CI: [a, b]). On all events including L4 fallback, aggregate improvement is 1-2pp (95% CI: [c, d])."

**Status**: OPEN

---

#### MA-02: Ac plausibility bounds unvalidated (confirmed by both reviews)

**Location**: `FORMULATION.md` §6.2.3

**What**: NYC TLC Ac bounds are $0-1000 (fare), 0-500 miles (distance). Airport trips regularly exceed $100. Long trips can exceed 50 miles. These bounds will flag legitimate events as low-quality. The bounds should be calibrated from actual NYC TLC data distributions, not set as round numbers.

**Note**: The reviews label this as an "Ac plausibility formula" issue about `exp(−λ · σ²_Δt)`. That formula is about **Tm** (Timeliness), not Ac (Accuracy). The λ = 0.01 constant also has unit-scale concerns: if Δt is in milliseconds, then λ · σ²_Δt ≈ 10⁷ for typical variance, making Tm ≈ 0 always. This is a **Tm** issue, not Ac.

**Fix**: (1) Calibrate Ac bounds from NYC TLC data percentiles. (2) Verify Tm formula unit consistency (λ calibration for ms-scale data). (3) Add bounding/clipping for extreme σ²_Δt values.

**Status**: OPEN

---

#### MA-03: CRS rules (Java) not built — Phase 2 plan is optimistic

**Location**: `report.md` Part VI Phase 2; `cross_record.py` (Python implementation only)

**What**: All CRS rules are implemented in Python. Java Flink implementations (required for stateful production pipeline) don't exist. A graduated plan:

| Phase | Rule | Complexity | Duration |
|-------|------|:---------:|----------|
| Java warmup | Maven + Flink skeleton | Low | 1 week |
| CRS003 | RoaringBitmap dedup | Low | 1 week |
| CRS002 | GPS jump buffer | Medium | 2 weeks |
| CRS001 | Speed history | High | 2 weeks |
| Integration | Wire all three into Flink job | Medium | 1 week |
| **Total** | | | **7 weeks** |

5-6 weeks (from reviews) is slightly pessimistic; 7 weeks with the graduated path is more accurate.

**Fix**: Update Phase 2 timeline to 7 weeks with graduated complexity path. Implement CRS003 first.

**Status**: OPEN

---

#### MA-04: H1-A H0 is incomplete (newly identified)

**Location**: `HYPOTHESES.md` H1-A; `STATISTICAL_PLAN.md` H1-A

**What**: The DV for H1-A includes three measures: (a) FPR, (b) F1 per context cell, (c) aggregate F1. The H₀ states: "FPR(L0) ≥ FPR(L4)." F1 is a DV but has no H₀ statement. If the test fails on F1 but passes on FPR, the hypothesis outcome is ambiguous.

**Fix**: Add explicit H₀ for F1: "H₀: F1(L0) ≤ F1(L4) — context resolution provides no improvement on F1." Or separate H1-A into H1-A-FPR and H1-A-F1.

**Status**: OPEN

---

#### MA-05: Phase 3 timeline unrealistic (confirmed by both reviews)

**Location**: `report.md` Part VI Phase 3; `ML_POSITIONING.md` (frames ML as optional)

**What**: Phase 3 = ablation + ML + METER + Grafana + paper = 3 weeks. Realistically needs 5-6 weeks minimum. With Java delay (MA-03), Phase 3 becomes Weeks 13-18+.

**Fix**: Cut Phase 3 to essentials: ablation + Grafana + paper. Defer ML integration and METER to future work. ML_POSITIONING.md already frames ML as optional Phase 3.

**Status**: OPEN

---

#### MA-06: TQS V1/V2 choice unresolved (confirmed by both reviews)

**Location**: `FAILURE_MODES.md` §Q2 (V1 recommended); `FORMULATION.md` §6.3 (V2 default); `report.md` (V2 used)

**What**: FAILURE_MODES recommends V1 (equal weights, principled). FORMULATION uses V2 (domain-prioritized, unprincipled). No document explains why V2 was chosen.

**Fix**: Choose V1 (equal weights) as primary. Equal weights is the only non-arbitrary choice without domain-derived evidence. V2 becomes a sensitivity variant only.

**Status**: OPEN

---

#### MA-07: METER year inconsistency (confirmed by both reviews)

**Location**: 8+ documents with inconsistent year citations

**What**: The paper appeared at VLDB 2023 conference and was published in PVLDB Vol.17, No.4 (2024). "VLDB 2024" refers to a DIFFERENT conference. 6+ documents use "VLDB 2024" incorrectly.

**Fix**: Standardize to "PVLDB Vol.17, No.4, 2024" (journal citation format). Do NOT use "VLDB 2024" — this names a different conference.

**Status**: OPEN

---

#### MA-08: CRS severity table missing 2-20 km/h range (B3) (confirmed by both reviews)

**Location**: `report.md` §Severity-to-Alert; `QUALITY_AUDIT.md` Q6; `COMPETITIVE_TABLE.md`

**What**: CRS002 severity maps only "<1 km/h → CRITICAL" and ">100m jump → HIGH." The 2-20 km/h moderate spoofing range (B3) is not in the severity table. B3 is documented as a known limitation but not propagated to the alerting specification.

**Fix**: Add "CRS002 IMPOSSIBLE_SPEED (2-20 km/h) → MEDIUM" to severity table. Acknowledge B3 gap.

**Status**: OPEN

---

#### MA-09: CRS001 lower bound fires on legitimate stop-and-go traffic (confirmed by both reviews)

**Location**: `FORMULATION.md` Algorithm B §Step 5; `cross_record.py` `max_speed_kmh=160` vs `min_speed_kmh=2`

**What**: CRS001 lower bound is 2 km/h. NYC MTA Bus regularly stops at traffic lights at 0-3 km/h. The code uses `min_speed_kmh=2.0` (not `max_speed_kmh=120` as in FORMULATION). The code uses 160 km/h for the upper bound (not 120 km/h as in FORMULATION).

**Note**: There's also a code vs. spec mismatch: the FORMULATION says 120 km/h upper bound; the code uses 160 km/h. Neither review caught this.

**Fix**: Add time_delta threshold: if speed < 2 km/h AND time_delta > 60s → VIOLATION (GPS jitter). If speed < 2 km/h AND time_delta ≤ 60s → pass (legitimate stop).

**Status**: OPEN

---

#### MA-10: zone_category lookup not implemented (confirmed by both reviews)

**Location**: `FORMULATION.md` §L0; `DATA_STRUCTURES.md`

**What**: L0 context key uses `zone_category` which is not in the event schema. NYC TLC Zone Lookup CSV (public dataset) provides the mapping. This is a 20-line data loading task + static reference, not a blocking dependency.

**Fix**: Download TLC Zone Lookup CSV. Load PULocationID → zone_category mapping at startup. Use in `ck(e, L0)` computation.

**Status**: OPEN

---

### MINOR Issues (7) — Fix before paper submission

#### MI-01: DeLong's test — naming error, method is correct (revised severity)

**Location**: `HYPOTHESES.md` H2-B; `STATISTICAL_PLAN.md` §H2-B

**What**: HYPOTHESES.md calls the test "DeLong's test adapted for Spearman correlation." STATISTICAL_PLAN calls it "Fisher z-transformation on ρ_s." The method described — Fisher z-transformation with bootstrap CI — is the correct test for comparing two Spearman correlations (Steiger, 1980).

**Both reviews classify this as CRITICAL.** This is **overkill**. The method is correct. Only the name is wrong. A PC reviewer reading the body text sees Fisher z, not DeLong.

**Fix**: Change section header to "Steiger's (1980) Fisher z-test for comparing correlated correlation coefficients." Add Steiger (1980) reference. Estimated: 10 minutes.

**Status**: OPEN

---

#### MI-02: D4 Holiday is a stub — "5D" should be "4D" (confirmed by both reviews)

**Location**: `report.md` §5D Context Decomposition; `QUALITY_AUDIT.md` Q8

**What**: D4 External context (holiday indicator) is PARTIAL. The "5D" claim should be "4D (D1, D2, D3, D5)."

**Status**: OPEN

---

#### MI-03: Mirzaie DOI placeholder (revised severity)

**Location**: `audit_streaming_dq_frameworks.md` Ref [16]

**What**: `doi:10.1016/j.ipl.2023.03.XXX` — XXX is a placeholder. Both reviews say "invalid DOI."

**Correction**: The DOI format is structurally valid for IPL (Elsevier). The XXX was generated during drafting. This is **UNVERIFIED** (not INVALID). An invalid DOI doesn't resolve; this one might. The citation is not load-bearing — Mirzaie is background literature, not a primary reference.

**Fix**: Search for the actual article number and replace XXX. If not found, remove. Estimated: 5 minutes.

**Status**: OPEN

---

#### MI-04: Synthetic GPS trajectory fallback plan vague (confirmed by both reviews)

**Location**: `report.md` §NYC MTA Bus Data Source; `HYPOTHESES.md` §H3-CRS001

**What**: Contingency for live feed failure lacks specification for synthetic GPS from GTFS Static route geometry.

**Fix**: Specify: generate synthetic GPS waypoints along GTFS static route shapes at configurable intervals. Provide pseudocode.

**Status**: OPEN

---

#### MI-05: Stream DaQ architecture narrative vs. table (confirmed by both reviews)

**Location**: `report.md` Part I; `COMPETITIVE_TABLE.md` §4.1

**What**: report.md says "Originally Kafka + Flink." COMPETITIVE_TABLE says "Pathway (Python)." The table is authoritative. The narrative phrase "originally" is an unsupported speculation.

**Fix**: Update report.md to say "Stream DaQ: Pathway (Python/Rust hybrid)." Remove "originally Kafka + Flink" unless a citation proves it.

**Status**: OPEN

---

#### MI-06: T-Assess DOI not provided (confirmed by both reviews)

**Location**: `audit_streaming_dq_frameworks.md`; `COMPETITIVE_TABLE.md`; `report.md`

**What**: T-Assess is the theoretical basis for the TQS dimension mapping (Claim 3). It is referenced as "accepted at VLDB 2025, PVLDB Vol.18, No.3" but no DOI. T-Assess is more important than other missing DOIs because it is a theoretical dependency, not just a competitive reference.

**Fix**: Obtain DOI when VLDB 2025 proceedings are published. Use PVLDB Vol.18, No.3 format.

**Status**: OPEN

---

#### MI-07: "Framework" in title weakly defended (confirmed by both reviews)

**Location**: `COMPETITIVE_TABLE.md` §"Framework" Title Defense

**What**: NYC-specific rules may not be reusable across domains. Reviewers may ask: "Where is the framework?"

**Fix**: Defend as "Framework provides architecture + extensible rule interface. NYC rules are exemplar, not limitation." Or consider "A Context-Aware System."

**Status**: OPEN

---

## Issues Both Reviews Missed (New)

### New-N1: Tm formula unit inconsistency (CRITICAL — Tm dimension)

The Tm formula uses `exp(−λ · σ²_Δt)` with λ = 0.01. If Δt is in milliseconds (typical for Flink timestamps), then σ²_Δt is on the order of 10⁹–10¹² ms². λ · σ²_Δt ≈ 10⁷–10¹⁰, making `exp(−large_number) ≈ 0` for all normal streams. Tm would be 0 for everything. The formula was apparently calibrated for seconds-scale data.

Both reviews (M011/MA-03) flagged this as an "Ac plausibility" issue — it is a **Tm (Timeliness)** issue. The reviews misdiagnosed the dimension.

**Fix**: Verify Δt unit in the Tm formula. If ms: recalibrate λ (e.g., λ = 10⁻⁹ for ms-scale data). Or normalize σ²_Δt by the mean inter-arrival time.

**Status**: OPEN

---

### New-N2: CRS002 Algorithm C K=3 buffer mismatch (MAJOR)

The comment in Algorithm C Step 5 says "covers 30s window at **1Hz**." At 1Hz, K=3 covers 3 seconds. At 30s intervals, K=3 covers 90 seconds. The buffer size and update interval are mismatched. This is the root cause of the threshold calibration error: the threshold (100m/30s) and the buffer (K=3 for 1Hz) were designed together for 1Hz data, then the data source switched to 30s intervals without recalibrating either.

**Fix**: Either (a) recalibrate threshold for 30s intervals, or (b) specify that CRS002 requires high-frequency GPS updates and add a minimum-frequency check.

**Status**: OPEN

---

### New-N3: PostgreSQL schema lacks entity_index column (MAJOR — evaluation)

The evaluation rules (STATISTICAL_PLAN.md §EV-GT2) require correlating violations to injected anomalies via `entity_index`. The current `violation_store.py` schema has no `entity_index` column. Without this column, ground truth correlation cannot be done.

**Fix**: Add `entity_index TEXT` column to violation store schema. Index on `(entity_index, rule_id, detected_at)` for efficient matching.

**Status**: OPEN

---

### New-N4: CRS001 upper bound mismatch (MINOR — spec vs code)

FORMULATION.md Algorithm B says CRS001 upper bound = 120 km/h. `cross_record.py` code uses `max_speed_kmh=160.0`. Neither review caught this.

**Fix**: Choose one and propagate. Recommend 120 km/h (standard highway speed limit in NYC).

**Status**: OPEN

---

### New-N5: CRS003 hash function mismatch (documented above as CR-04)

---

### New-N6: CRS002 severity mapping conflates two separate checks (MINOR)

`evaluate_trajectory_anomaly()` handles both CRS001 (speed bounds) and CRS002 (GPS jump) in a single function. The severity table maps "CRS002" to severity levels but conflates speed-based violations (CRS001) with displacement-based violations (CRS002). The FORMULATION.md separates these as Algorithms B and C.

**Fix**: Separate severity mappings for CRS001 (IMPOSSIBLE_SPEED) and CRS002 (GPS_JUMP).

**Status**: OPEN

---

## 5-Dimension Coverage (Revised)

| Dimension | Status | Rationale |
|-----------|:------:|----------|
| **Streaming** | 🟢 PASS | Flink DataStream, watermarks, event-time, Kafka. Design is sound. |
| **Data Quality** | 🔴 RED | CRS002 non-functional on real data (CR-01). CRS003 replay gate broken (CR-03). CRS003 hash mismatched (CR-04). These are not missing features — the rules don't work as specified. |
| **Framework** | 🟡 AMBER | Architecture is modular, PipelineBackend interface well-designed, rule registry implied. But evaluation infrastructure absent (CR-05). Java CRS rules not built. |
| **Context-Aware** | 🟢 PASS | L0-L5 hierarchy is well-specified. Power analysis documented. Fallback mechanism mathematically sound. D4 stub is minor. L4 dilution is acknowledged and quantified. |
| **Monitoring** | 🟡 AMBER | TQS has unresolved architecture split (CR-02). Tm formula unit issue (New-N1). Ac bounds unvalidated (MA-02). Violation store lacks entity_index (New-N3). |

**Significant change from existing reviews**: Data Quality is RED (not PARTIAL). Context-Aware is PASS (not PARTIAL). Monitoring is AMBER (not PASS).

---

## Cross-Document Consistency (Final)

| Conflict | Doc A | Doc B | Resolution | Severity |
|----------|-------|-------|------------|:--------:|
| TQS system | FORMULATION.md §6 (new: Tm/Cn/Ac/Cs/Uv) | DATA_STRUCTURES.md §4 (old: V/C/Cn/P) | Rewrite DATA_STRUCTURES to implement new TQS | CRITICAL |
| TQS weights | FORMULATION.md §6.3 (Tm=0.20...) | FAILURE_MODES §Q2 (V=0.40...) | FAILURE_MODES uses old system; update to new | CRITICAL |
| TQS TQS | FORMULATION.md §6 (new non-circular) | HYPOTHESES.md H2-A (mixed) | H2-A updated to reference new; confirm | MAJOR |
| CRS002 threshold | FORMULATION.md (100m/30s) | FAILURE_MODES §Q3 (fires all normal) | Fix to 250-333m for 30s | CRITICAL |
| CRS002 buffer | Algorithm C (K=3, 1Hz comment) | Algorithm C (100m/30s) | Buffer/threshold mismatched; fix both | CRITICAL |
| CRS002 speed | FORMULATION.md (120 km/h) | Code (160 km/h) | Choose; propagate | MINOR |
| CRS002 algorithm | FORMULATION.md (Algorithms B+C separate) | Code (merged function) | Document the merge; separate severity | MINOR |
| CRS003 hash | FORMULATION.md (SHA256 lat/lon) | Code (MD5 PULoc+DOLoc+Pax) | Fix FORMULATION.md per-dataset | CRITICAL |
| CRS003 replay | Code (is_replay=True gate) | Expected behavior (should detect) | Bypass gate for injected duplicates | CRITICAL |
| TQS circularity | FORMULATION.md §6 (non-circular) | HYPOTHESES.md H2-A (was circular, updated) | Confirmed updated | MAJOR |
| DeLong test | HYPOTHESES.md (wrong name) | STATISTICAL_PLAN.md (Fisher z, correct) | Fix HYPOTHESES naming | MINOR |
| METER year | audit_streaming_dq_frameworks.md (2023) | report.md, writing-rules.mdc (2024) | PVLDB Vol.17, No.4, 2024 everywhere | MAJOR |
| D4 dimensionality | Multiple docs (5D) | QUALITY_AUDIT (4D, D4 PARTIAL) | Change all to 4D | MINOR |
| Stream DaQ arch | report.md Part I (Kafka+Flink) | COMPETITIVE_TABLE (Pathway) | Fix report.md narrative | MINOR |
| CRS rules dataset | report.md (implies both datasets) | everywhere else (CRS = MTA Bus only) | Explicitly scope CRS to NYC MTA Bus | MAJOR |
| B1 NaN guard | Both reviews (underspecified/pending) | Code (3 guards already implemented) | Documented — implementation exists | REMOVED |

---

## No-Lite Delivery Assessment

| Deliverable | Implementation | Tests | Reproducibility | Status |
|------------|:--------------:|:-----:|:--------------:|:------:|
| SYN001-003 (Python) | ✅ Implemented | ✅ Unit tests | Protocol documented | 🟢 DONE |
| SEM001-003 (Python) | ✅ Implemented | ✅ Unit tests | Protocol documented | 🟢 DONE |
| CRS003 (Python) | ✅ Implemented | ✅ Spec | Protocol documented | 🟡 BUGGY |
| CRS001/CRS002 (Python) | ✅ Implemented | ⚠️ Partial | Protocol documented | 🟡 BUGGY |
| CRS rules (Java Flink) | ❌ Not built | ❌ None | Protocol in FORMULATION.md | 🔴 MISSING |
| Evaluation Pipeline | ❌ Not built | ❌ None | Protocol in STATISTICAL_PLAN | 🔴 MISSING |
| TQS Aggregation | ✅ Implemented | ⚠️ Partial | Protocol documented | 🟡 INCONSISTENT |

**The Python pipeline is ~70% implemented.** The Java CRS rules are 0% built. The evaluation infrastructure is 0% built. The reviews were accurate about what doesn't exist but conflated the Python prototype (which exists and works) with the production Flink implementation (which doesn't).

---

## Revised Action Items

### P0 — Week 1 (blocking)

| # | Action | Owner | Blocks | Status |
|---|--------|-------|--------|--------|
| P0.1 | Fix CRS002 threshold: change 100m → 250m (minimum) / 333m (safe) | Methodology | RQ5 | OPEN |
| P0.2 | Fix CRS002 Algorithm C K=3 buffer mismatch | Methodology | RQ5 | OPEN |
| P0.3 | Fix CRS003 replay suppression gate: tag injected duplicate `is_replay=False` | Code | CRS003 eval | OPEN |
| P0.4 | Update FORMULATION.md Algorithm D per-dataset hash spec | Write | CRS003 | OPEN |
| P0.5 | Rewrite DATA_STRUCTURES.md §4 to implement new TQS (Tm/Cn/Ac/Cs/Uv) | Write | RQ3/RQ4 | OPEN |
| P0.6 | Build `evaluation/` directory: synthetic_injector, ground_truth_tracker, metrics (1K bootstrap), run_evaluation, README | Implement | All RQs | OPEN |
| P0.7 | Add entity_index column to PostgreSQL violation store schema | Implement | Ground truth correlation | OPEN |
| P0.8 | Fix H1-A H0: add F1 null hypothesis or split into two hypotheses | Write | RQ1 | OPEN |

### P1 — Week 2-3

| # | Action | Owner | Blocks | Status |
|---|--------|-------|--------|--------|
| P1.1 | Scope ΔF1 claims: 5pp = L0/L1 cells only. Aggregate = 1-2pp | Write | RQ1 | OPEN |
| P1.2 | Choose TQS V1 (equal weights) with criteria. Propagate to all docs | Write | TQS | OPEN |
| P1.3 | Fix Tm formula: verify λ calibration for ms-scale data; cap σ²_Δt | Algorithm | TQS | OPEN |
| P1.4 | Calibrate Ac plausibility bounds from NYC TLC data percentiles | Data | TQS | OPEN |
| P1.5 | Add CRS002 severity for 2-20 km/h (B3) to severity table | Write | RQ5 | OPEN |
| P1.6 | Add Java warmup week to Phase 2 plan. CRS003 first | Planning | Phase 2 | OPEN |
| P1.7 | Cut Phase 3 to essentials: ablation + Grafana + paper. Defer ML + METER | Planning | Timeline | OPEN |

### P2 — Week 4-8

| # | Action | Owner | Blocks | Status |
|---|--------|-------|--------|--------|
| P2.1 | Implement Java CRS003 (RoaringBitmap dedup) — Flink | Implement | RQ5 | OPEN |
| P2.2 | Implement Java CRS002 (GPS jump buffer) — Flink | Implement | RQ5 | OPEN |
| P2.3 | Implement Java CRS001 (speed history) — Flink | Implement | RQ5 | OPEN |
| P2.4 | Add zone_category lookup from TLC Zone CSV | Data | L0 keys | OPEN |
| P2.5 | Add CRS001 speed=0 + time_delta threshold | Algorithm | CRS001 | OPEN |
| P2.6 | Standardize METER year to "PVLDB Vol.17, No.4, 2024" in all docs | Write | Literature | OPEN |
| P2.7 | Fix CRS001 upper bound: 120 km/h in code and FORMULATION | Code/Doc | Consistency | OPEN |
| P2.8 | Separate CRS002 severity table: CRS001 vs. CRS002 | Write | RQ5 | OPEN |
| P2.9 | Implement TQS sensitivity analysis (V1 vs. V2 vs. V3) | Implement | RQ4 | OPEN |

---

## What Both Reviews Got Right

Despite the errors identified above, both reviews correctly identified the following critical structural issues:

1. **CRS002 threshold is wrong** — confirmed by math and code inspection
2. **Evaluation infrastructure is absent** — confirmed by repo inspection
3. **RQ3 circularity exists in DATA_STRUCTURES** — confirmed; new TQS design exists but not propagated
4. **L4 dilution destroys aggregate ΔF1** — confirmed; requires explicit scoping
5. **Phase 3 is unrealistic** — confirmed; ML + METER should be deferred
6. **Java learning curve is underestimated** — partially confirmed; 7 weeks with graduated path is more accurate than 2 weeks
7. **TQS V1/V2 choice unresolved** — confirmed; V1 equal weights is the principled choice
8. **D4 is a stub** — confirmed; "5D" should be "4D"

---

## Grade Projection (Revised)

| Scenario | Grade | Condition |
|---------|:-----:|-----------|
| Current plan, no fixes | C+ to B- | CRS002 broken, no eval |
| Fix P0 only | B to B+ | Core works, eval starts |
| Fix P0 + P1 | B+ to A- | Framework sound, CRS works |
| Fix ALL P0/P1/P2 | A- to A | All issues resolved, CRS in Java |
| Fix ALL + Phase 3 ML | A to A+ | Full delivery, requires 7+ weeks |

**Honest ceiling with 13-week timeline**: **A−** if P0/P1 are fixed aggressively and Phase 3 is scoped appropriately. **A** requires completing all CRS Java rules AND having measured results. At current state (CRS002 broken, no evaluation), realistic ceiling is **B+**.

---

## Documents Audited

| File | Key Findings |
|------|-------------|
| `FINAL_PROJECT_AUDIT.md` | 28 issues tracked; 4 factual errors identified |
| `COMPREHENSIVE_REVIEW.md` | Comprehensive synthesis; same 4 factual errors |
| `FORMULATION.md` | New non-circular TQS (excellent); CRS002 threshold wrong; CRS003 hash wrong |
| `HYPOTHESES.md` | H0 present in all 12 hypotheses (review error); H2-A updated to new TQS |
| `DATA_STRUCTURES.md` | Still uses OLD circular TQS (V/C/Cn/P); not updated to FORMULATION.md §6 |
| `FAILURE_MODES.md` | Excellent diagnostics; TQS V2 weights inconsistent with new system |
| `STATISTICAL_PLAN.md` | Sound methodology; H1-A H0 incomplete (missing F1) |
| `COMPETITIVE_TABLE.md` | Correct; D4 caveat present |
| `ML_POSITIONING.md` | Correctly frames ML as optional |
| `cross_record.py` | CRS003 replay gate bug; CRS001 160 km/h (not 120); 3 NaN guards implemented |
| `nyc_taxi_replay.py` | B2 fix partially done (2 records emitted); replay flag tagging issue |
| `violation_store.py` | Missing entity_index column |

---

## Verification Checklist

Before this review is used as a planning document, the following must be verified:

- [ ] Confirm CRS002 fires on all traffic >12 km/h (run unit test with 30 km/h, 30s interval)
- [ ] Confirm TQSCellState in DATA_STRUCTURES uses violation counters (read code)
- [ ] Confirm replay suppression gate blocks CRS003 on TLC replay (read code)
- [ ] Confirm H0 statements in all 12 hypotheses in HYPOTHESES.md (read source)
- [ ] Confirm B1 NaN guard implementation in syntactic.py (read code)
- [ ] Verify DyMETER DOI `10.1109/TPAMI.2026.3682661` against IEEE Xplore
- [ ] Verify Chen et al. T-ITS DOI against IEEE Xplore
- [ ] Obtain T-Assess DOI from VLDB 2025 proceedings

---

*Generated by Orchestrator — 4-agent parallel debate synthesis*
*April 24, 2026*
