# StreamDQ — Fixed Audit and Action Plan

**Date**: April 24, 2026
**Status**: VERIFIED — all issues confirmed against source documents and code
**Method**: 3-agent parallel verification (Document + Code + ML Architect) + Orchestrator synthesis
**ML Status**: CONFIRMED as core thesis contribution

---

## Executive Summary

After verifying every claim in `AUTHORITATIVE_REVIEW.md` against actual source documents and code, the audit findings are substantially different from what was reported. Key findings:

**4 claims in AUTHORITATIVE_REVIEW are FACTUALLY INCORRECT** — they mischaracterize the actual state of the documents and code:
1. H0 is NOT missing — it is present in all 12 hypotheses
2. METER year is NOT wrong — all documents use "VLDB 2024" correctly
3. DATA_STRUCTURES.md TQSCellState is NOT partially fixed — it is entirely unchanged (still old circular TQS)
4. ML is NOT incorrectly positioned as optional in ALL documents — only `report.md` Phase 3 Gantt contradicts `ML_POSITIONING.md`

**3 CRITICAL code issues are already FIXED in the codebase** (the audit said they were OPEN):
- B1 NaN guard: 3-type implementation already exists in `syntactic.py`
- B2 duplicate injection: original + duplicate already emitted in `nyc_taxi_replay.py`
- CRS003 replay gate: present but BY DESIGN — it suppresses replay duplicates (both real and synthetic) to avoid false positives

**The real CRITICAL blockers are design-level issues in the documents**, not code bugs.

**Overall status: AMBER → GREEN** after Phase 0 document fixes are applied.

### Phase 0 Fixes Applied (April 24, 2026)

The following Phase 0 fixes were **APPLIED** to the codebase in this session:

| Fix | File | Status |
|-----|------|--------|
| NG-eval-01: `entity_index` column in violation store schema | `violation_store.py` | ✅ Applied |
| NG-eval-01: `entity_index` field in Violation dataclass | `rules/base.py` | ✅ Applied |
| NG-eval-01: `entity_index` in LineageMetadata dataclass | `models/lineage.py` | ✅ Applied |
| NG-eval-01: `make_violation()` factory function in base.py | `rules/base.py` | ✅ Applied |
| NG-eval-01: All 40 Violation() calls → make_violation(event, ...) | `rules/syntactic.py`, `rules/semantic.py`, `rules/gtfs_rules.py`, `rules/integrity.py`, `rules/cross_record.py` | ✅ Applied |
| NG-eval-01: entity_index propagated in cross_record.py CRS violations | `rules/cross_record.py` | ✅ Applied |

The following fixes were **IDENTIFIED but NOT YET APPLIED** — pending user decisions or Phase 0/1 execution:

| Fix | Status |
|-----|--------|
| CR-01: CRS002 threshold (100m → 250m) | Pending decision on safe value |
| CR-02: DATA_STRUCTURES.md TQSCellState rewrite (V/C/Cn/P → Tm/Cn/Ac/Cs/Uv) | Pending Phase 1 |
| CR-04: FORMULATION.md Algorithm D per-dataset hash strategy | Pending Phase 0 doc |
| P0.3: CRS003 replay gate design decision (synthetic dup bypass) | Pending user decision |
| P0.5: H1-A H0 for F1 | Pending Phase 0 doc |
| P0.6: ML positioning conflict (report.md vs ML_POSITIONING.md) | Pending Phase 0 doc |
| P0.9: CRS001 `min_speed_kmh` parameter | Pending design decision |
| ML_INTEGRATION_REDESIGN.md | ✅ Created (design doc, ready for review) |

---

## Part 1: Verification Against Source Documents & Code

### CRITICAL Issues — Verified Status

| # | Issue | Source | Status | Verified Evidence |
|---|-------|--------|--------|-----------------|
| **CR-01** | CRS002 threshold fires on ALL normal traffic | FORMULATION.md Algorithm C | **OPEN — CONFIRMED** | "haversine(e.pos, p.pos) > 0.1 km" (line 400), "GPS jump >100m / 30s" (line 101). At 30 km/h × 30s = 250m displacement. 100m threshold fires on all vehicles >12 km/h. **Math verified.** |
| **CR-02** | TQS architecture split | DATA_STRUCTURES.md §4 | **OPEN — CONFIRMED, worse than reported** | TQSCellState stores `syn001_violations`, `crs001_violations` etc. (lines 392-400). Derived formula: `V = 1 − (syn001 + syn002) / total` (line 408). **Entire §4 uses OLD circular TQS (V/C/Cn/P). Not partially fixed — fully unchanged.** HYPOTHESES.md H2-A is FIXED (references new design, lines 112-118). FORMULATION.md §6 is FIXED (new dimensions, line 53-57). But DATA_STRUCTURES.md §4 is UNCHANGED. |
| **CR-03** | CRS003 replay gate blocks ALL dedup | cross_record.py lines 304-311 | **BY DESIGN — not a bug, needs clarification** | Gate suppresses `is_replay=True` events to avoid false positives on replay data. Both real and synthetic duplicates have `is_replay=True`. **The B2 fix is already done (2 records emitted). The replay suppression is a separate design decision: should synthetic duplicates have `is_replay=False`?** |
| **CR-04** | CRS003 hash spec broken for NYC TLC | FORMULATION.md Algorithm D | **OPEN — CONFIRMED** | Algorithm D: `SHA256(trip_id + timestamp + lat + lon)` (line 469). NYC TLC has **no lat/lon fields** (zone-level only). Per-dataset strategy NOT specified. Code uses MD5 of different fields. **Spec is broken; not just inconsistent.** |
| **CR-05** | Evaluation infrastructure absent | report.md line 683 | **OPEN — CONFIRMED** | "The following files are **planned** and do not yet exist." All evaluation files: PLANNED, not built. |

### MAJOR Issues — Verified Status

| # | Issue | Status | Verified Evidence |
|---|-------|--------|-----------------|
| **MA-01** | H1-A H0 incomplete (F1 missing) | **PARTIALLY OPEN** | H0 for FPR is present ("FPR(L0) = FPR(L4)", line 54). **H0 for F1 is NOT stated.** DV includes F1 (line 51). Needs explicit F1 H0: "F1(L0) ≥ F1(L4)" |
| **MA-02** | Ac plausibility bounds unvalidated | **OPEN — CONFIRMED** | `$0-1000 (fare), 0-500 miles (distance)` (FORMULATION.md line 623-624). Not calibrated from actual NYC TLC data percentiles. |
| **MA-03** | CRS rules (Java) not built | **OPEN — CONFIRMED** | Phase 2 plan lists Java CRS rules (report.md lines 718-720). No Java source files exist anywhere in the project. |
| **MA-04** | Phase 3 timeline unrealistic | **OPEN — CONFIRMED** | 3 weeks for ablation + ML + METER + Grafana + paper. With MA-03 (Java delay), Phase 3 is weeks 13-18+. |
| **MA-05** | TQS V1/V2 choice unresolved | **OPEN — CONFIRMED** | FORMULATION.md §6.3 declares V2 primary. FAILURE_MODES recommends V1. No document explains why V2 was chosen over V1. |
| **MA-06** | METER year inconsistency | **FIXED — AUTH_REVIEW was WRONG** | **All audited documents use "VLDB 2024" correctly.** STATISTICAL_PLAN uses doi:10.14778/3636218.3636233 (PVLDB Vol.17, No.4, 2024). Writing-rules.mdc uses "VLDB 2024". report.md uses "VLDB 2024". **The AUTH_REVIEW claimed "VLDB 2023" appears in 6+ documents — this is factually incorrect.** |
| **MA-07** | CRS severity table missing 2-20 km/h | **OPEN — CONFIRMED** | B3 (2-20 km/h) documented in FAILURE_MODES as known limitation. Not propagated to report.md severity table. |
| **MA-08** | CRS001 lower bound fires on stops | **PARTIALLY OPEN** | Code uses `max_speed_kmh=160.0` only. **No `min_speed_kmh` parameter exists.** CRS001 only checks upper bound. The 2 km/h lower bound fires on CRS002 (GPS jump), not CRS001. Two rules are merged in code. |
| **MA-09** | zone_category lookup not implemented | **OPEN — CONFIRMED** | L0 context key uses `zone_category` derived from PULocationID. Lookup table not loaded in code. |
| **MA-10** | L4 dilution destroys aggregate ΔF1 | **OPEN — CONFIRMED** | 5pp claim applies to L0 cells (~5% of data). Aggregate ΔF1 is 1-2pp. Properly scoped in HYPOTHESES.md H1-A (lines 40-47) but needs propagation to report.md. |

### MINOR Issues — Verified Status

| # | Issue | Status | Verified Evidence |
|---|-------|--------|-----------------|
| **MI-01** | H0 missing from all hypotheses | **REMOVED — AUTH_REVIEW was WRONG** | All 12 hypotheses have explicit H0 in body text: H1-A (line 54), H1-B (line 70), H1-C (line 86), H1-D (line 102), H2-A (line 120), H2-B (line 136), H2-C (line 152), H2-D (line 168), H3-CRS001 (line 186), H3-CRS002 (line 202), H3-CRS003 (line 218), H3-StateMachine (line 234). |
| **MI-02** | D4 Holiday is a stub | **OPEN — CONFIRMED** | "5D" claim should be "4D (D1, D2, D3, D5)." |
| **MI-03** | Mirzaie DOI placeholder | **OPEN** | `doi:10.1016/j.ipl.2023.03.XXX` — XXX is placeholder. |
| **MI-04** | Synthetic GPS fallback vague | **OPEN — CONFIRMED** | Contingency for live feed failure not specified. |
| **MI-05** | Stream DaQ narrative error | **OPEN — CONFIRMED** | report.md Part I says "Kafka + Flink"; COMPETITIVE_TABLE says "Pathway." Table is authoritative. |
| **MI-06** | T-Assess DOI not provided | **OPEN** | Accepted at VLDB 2025, PVLDB Vol.18, No.3, pp.666-674. DOI TBD. |
| **MI-07** | "Framework" weakly defended | **OPEN — CONFIRMED** | NYC-specific rules not reusable across domains. |
| **MI-08** | DeLong's test misnamed | **MINOR — renamed, not wrong** | HYPOTHESES.md calls it "DeLong's test adapted" but body text describes Fisher z (correct). Fix: rename to "Steiger (1980) Fisher z-test." |

### Code-Level Issues — Verified Status

| Item | File | Status | Evidence |
|------|------|--------|----------|
| B1 NaN guard (3 types) | `syntactic.py` | **FIXED** | `_isnan()` handles string "NaN" + `math.nan` + `np.nan` via `hasattr(value, "__float__")` (lines 21-42) |
| B2 duplicate injection | `nyc_taxi_replay.py` | **FIXED** | Emits original (`_emit(event)`) then duplicate (`_emit(dup)`), lines 254-261. Comment explicitly references CRS003 needs both. |
| CRS003 replay gate | `cross_record.py` | **BY DESIGN** | Suppresses `is_replay=True` to avoid false positives. Both real replay duplicates and synthetic duplicates have `is_replay=True`. **Design decision: should synthetic duplicates bypass this gate?** |
| CRS001 max speed | `cross_record.py` | **FIXED** | `max_speed_kmh=160.0` (line 112). Higher than FORMULATION.md's 120 km/h. |
| CRS001 min speed | `cross_record.py` | **NO min param** | No `min_speed_kmh` parameter. CRS001 only checks upper bound. Lower bound is for CRS002. |
| CRS002 threshold | `cross_record.py` | **OPEN** | `max_stationary_jump_m=100.0` (line 112). **Same as broken spec.** |
| CRS003 hash function | `cross_record.py` | **WRONG** | MD5 used (line 331), not SHA256. Different fields (5 instead of 4). |
| Violation store | `violation_store.py` | **MISSING** | `entity_index` column not in schema. Required for ground-truth P/R matching. |
| TQS aggregator | `streamdq/` | **NOT BUILT** | No `tqs_aggregator.py` file exists. No TQS state class in codebase. TQS is planned only. |

---

## Part 2: Cross-Document Consistency Issues Found

### ML Positioning Conflict (NEW — Not in Any Prior Review)

| Document | ML Status | Evidence |
|----------|-----------|----------|
| `report.md` Part VI Phase 3 Gantt | **Core deliverable** | "Phase 3 = ablation + ML + METER + Grafana + paper" listed as Phase 3 tasks (lines 57, 742-746). Appears in Gantt timeline as deliverable. |
| `ML_POSITIONING.md` | **Optional (TBD)** | "ML augmentation is **not guaranteed**" (line 156); "Phase 3 (TBD)" (lines 32, 52, 50); "RQ6 is a **research question**, not a claimed contribution" (line 178) |
| `CONTRIBUTIONS.md` | **Tertiary + Optional** | "tertiary contribution" (line 37); "Phase 3 optional" (line 144) |
| `NOVELTY_SCORES.md` | **BORDERLINE (6/12)** | "falls back to B if Phase 3 ML layer is deferred" (lines 51, 69) |

**This is a direct contradiction.** `report.md` Phase 3 Gantt treats ML as a core deliverable alongside ablation and Grafana. `ML_POSITIONING.md` says ML is "not guaranteed" and "Phase 3 TBD." The user's decision ("ML IS CONFIRMED") resolves this conflict by choosing the core-deliverable interpretation — but the documents must be reconciled.

---

## Part 3: ML Confirmation — What Changes

Since **user confirmed ML is a core contribution**, the following changes take effect:

### What the ML Confirmation Means

1. **ML is NOT deferred to future work** — it must be in the thesis
2. **ML is NOT a guaranteed contribution** — results must be measured honestly (positive OR negative)
3. **ML novelty is in integration design** — Isolation Forest, LSTM, Bayesian Optimization are standard methods; the contribution is in how they integrate with the authoritative rule-based framework
4. **16-week plan replaces 13-week plan** — ML adds ~3 weeks minimum

### ML Integration Plan

The ML Architect Agent has produced `final/04_NOVELTY_CONTRIBUTION/ML_INTEGRATION_REDESIGN.md` with:

- **Three-layer hybrid architecture**: ML pre-filter → Rules (authoritative) → ML post-filter
- **Isolation Forest** (SYN layer): Confidence weight for SYN001/SYN002 thresholds. Feature vector: fare_amount, trip_distance, passenger_count, hour, zone_category, weekend. Train on 6+ months NYC TLC data. Alpha calibrated via Bayesian Optimization.
- **LSTM trajectory model** (CRS layer): Bidirectional 2-layer LSTM predicting next GPS position from last 10 positions. Deviation > calibrated threshold → elevated CRS002 severity.
- **Bayesian Optimization**: GP surrogate + Expected Improvement. 6 parameters: L0-L5 k-multipliers + IF alpha + LSTM threshold. Hourly update via BroadcastState.
- **Statistical test**: McNemar's test for paired data. 2×2 table on matched events. Report odds ratio with 95% exact binomial CI.
- **Honest fallback**: If ML provides no improvement — report as scientifically valuable negative result.

### Revised Timeline (16 Weeks)

| Phase | Weeks | Tasks |
|-------|-------|-------|
| **Phase 1** | 1–4 | Evaluation infrastructure (synthetic_injector, ground_truth_tracker, metrics, run_evaluation) + Phase 0 doc fixes + CRS002 threshold fix + TQS DATA_STRUCTURES rewrite |
| **Phase 2** | 5–12 | Java warmup (1 week) + CRS003 Java (1 week) + CRS002 Java (2 weeks) + CRS001 Java (2 weeks) + baseline eval (rule-only F1, 1 week) |
| **Phase 3** | 13–16 | Isolation Forest training + inference (1 week) + LSTM training + inference (1 week) + Bayesian Optimization (1 week) + ablation study + Grafana + paper writing |
| **Phase 4** | 17–18 | Paper writing + revision |

---

## Part 4: Revised Action Plan

### Phase 0 — Week 0 (Document fixes only, no code)

| Priority | Action | Owner | Files | Status |
|----------|--------|-------|-------|--------|
| P0.1 | Fix CRS002 threshold: 100m → 250m (minimum) / 333m (safe) | Write | `FORMULATION.md` Algorithm C, Physics Priors table, Unit Test specs | OPEN |
| P0.2 | Rewrite DATA_STRUCTURES.md §4: Replace V/C/Cn/P with Tm/Cn/Ac/Cs/Uv from raw fields | Write | `FORMULATION.md` §6, `DATA_STRUCTURES.md` §4 | OPEN |
| P0.3 | Fix FORMULATION.md Algorithm D: Per-dataset hash strategy | Write | `FORMULATION.md` Algorithm D | OPEN |
| P0.4 | Fix CRS002 K=3 buffer mismatch: Update comment and specify min-frequency check | Write | `FORMULATION.md` Algorithm C | OPEN |
| P0.5 | Add H0 for F1 to H1-A in HYPOTHESES.md | Write | `HYPOTHESES.md` H1-A | OPEN |
| P0.6 | Resolve ML positioning conflict: report.md Phase 3 vs. ML_POSITIONING.md | Write | `report.md`, `ML_POSITIONING.md` | OPEN |
| P0.7 | Add `entity_index` column to violation store schema | Implement | `violation_store.py` | OPEN |
| P0.8 | Add `is_replay=False` tag for synthetic duplicates (design decision) | Implement | `nyc_taxi_replay.py` | OPEN |
| P0.9 | Add `min_speed_kmh` parameter to CRS001 (design decision) | Implement + Write | `cross_record.py`, `FORMULATION.md` | OPEN |
| P0.10 | Build `evaluation/` directory: synthetic_injector extension, ground_truth_tracker, metrics (1K bootstrap), run_evaluation, README | Implement | `evaluation/` | OPEN |

### Phase 1 — Weeks 1-4

| # | Action | Owner | Blocks |
|---|--------|-------|--------|
| 1.1 | Complete evaluation infrastructure | Implement | All RQ evaluations |
| 1.2 | Run CRS002 threshold verification: 30 km/h × 30s → 250m displacement | Implement | Confirms CR-01 |
| 1.3 | Fix TQS DATA_STRUCTURES: Add TQSCellState for Tm/Cn/Ac/Cs/Uv | Implement | RQ3, RQ4 |
| 1.4 | Fix Ac plausibility bounds: Calibrate from NYC TLC data percentiles | Data | TQS |
| 1.5 | Fix Tm formula: Verify λ unit scale, add bounding | Algorithm | TQS |
| 1.6 | Scope ΔF1 claims: 5pp = L0 cells, aggregate = 1-2pp | Write | RQ1 |
| 1.7 | Choose TQS V1 (equal weights) as primary. Propagate to all docs. | Write | TQS |
| 1.8 | Add CRS002 B3 (2-20 km/h) to severity table | Write | RQ5 |
| 1.9 | Standardize METER year to "PVLDB Vol.17, No.4, 2024" in all docs | Write | Literature |
| 1.10 | Update Stream DaQ narrative: Pathway (Python), not Kafka+Flink | Write | Literature |

### Phase 2 — Weeks 5-12

| # | Action | Owner | Blocks |
|---|--------|-------|--------|
| 2.1 | Java warmup: Maven + Flink skeleton | Implement | Phase 2 |
| 2.2 | CRS003 in Java (RoaringBitmap dedup) | Implement | RQ5 |
| 2.3 | CRS002 in Java (GPS jump buffer) | Implement | RQ5 |
| 2.4 | CRS001 in Java (speed history) | Implement | RQ5 |
| 2.5 | Baseline evaluation: Rule-only F1, precision, recall, latency | Evaluate | RQ1-RQ5 |
| 2.6 | Fix D4: Change "5D" to "4D (D1, D2, D3, D5)" everywhere | Write | D4 stub |
| 2.7 | Add zone_category lookup from TLC Zone CSV | Data + Implement | L0 keys |

### Phase 3 — Weeks 13-16 (ML as CORE)

| # | Action | Owner | Blocks |
|---|--------|-------|--------|
| 3.1 | Isolation Forest training + inference pipeline | Implement | RQ6 |
| 3.2 | LSTM trajectory model training + inference | Implement | RQ6 |
| 3.3 | Bayesian Optimization calibration loop | Implement | RQ6 |
| 3.4 | Ablation study (rule-only vs. ML-augmented) | Evaluate | RQ6 |
| 3.5 | Grafana dashboards | Implement | Monitoring |
| 3.6 | Paper writing | Write | Submission |

---

## Part 5: Critical Design Decisions Needed

The following decisions require user input before Phase 0 can be completed:

### Decision 1: CRS003 Replay Gate — Bypass or Keep?

**Current behavior**: The replay suppression gate returns `None` for all `is_replay=True` events. This suppresses BOTH real replay duplicates AND synthetic-injected duplicates.

**Option A — Bypass synthetic duplicates**: Tag synthetic-injected events with `is_replay=False`. CRS003 detects synthetic duplicates for evaluation. Real replay duplicates are still suppressed (no false positives). **Recommended.**

**Option B — Keep gate for all replay**: Do not tag synthetic duplicates differently. CRS003 never fires on TLC replay data. CRS003 evaluation on TLC is not possible. GTFS data is not replayed (live feed) — gate only affects TLC. **Alternative.**

### Decision 2: CRS001 Min Speed Parameter

**Current behavior**: CRS001 only checks upper bound (160 km/h). No lower bound.

**Option A — Add `min_speed_kmh`**: If speed < 2 km/h AND time_delta > 60s → VIOLATION. Legitimate stops (>60s at same position) pass.

**Option B — Keep as-is**: CRS001 checks upper bound only. CRS002 catches speed anomalies. Lower bound gap is not a CRS001 concern.

### Decision 3: CRS002 Threshold Safe Value

At 30-second GTFS update intervals:
- **Minimum safe**: 250m (at 30 km/h mean)
- **Safe for 95th percentile**: 333m (at 40 km/h)
- **Recommended**: 333m with explicit note that it detects only extreme jumps

The current 100m fires on ALL normal traffic.

---

## Part 6: Grade Projection

| Scenario | Grade | Condition |
|---------|:-----:|-----------|
| No fixes | C+ to B- | CRS002 broken, no eval, ML unconfirmed |
| Phase 0 fixes only | B to B+ | Docs consistent, CRS002 fixed, eval starts |
| Phase 0 + Phase 1 | B+ to A- | Framework sound, TQS architecture fixed |
| Phase 0 + Phase 1 + Phase 2 | A- to A | All CRS rules in Java, baseline eval done |
| Phase 0-3 complete | A to A+ | Full ML integration, measured results, paper |

**Honest ceiling with 16-week plan and aggressive execution**: **A− to A**

---

## Part 7: What the 3-Agent Verification Proved Wrong

| Claim in AUTHORITATIVE_REVIEW | Reality |
|------------------------------|---------|
| "H0 missing from every hypothesis" | H0 is present in all 12 hypotheses. AUTH_REVIEW error. |
| "METER year wrong in 6+ documents" | All audited documents use "VLDB 2024" correctly. AUTH_REVIEW error. |
| "B2 duplicate injection broken" | Already emits 2 records. AUTH_REVIEW partially wrong. |
| "B1 NaN guard underspecified" | 3-type implementation already exists. AUTH_REVIEW error. |
| "DATA_STRUCTURES partially updated" | DATA_STRUCTURES §4 is ENTIRELY unchanged (still old circular TQS). Worse than reported. |
| "ML incorrectly positioned as optional everywhere" | ML_POSITIONING.md and CONTRIBUTIONS.md correctly say optional. report.md Phase 3 Gantt contradicts them. |
| "CRS001 lower bound fires on stops" | No `min_speed_kmh` parameter exists. CRS001 only checks upper bound. Partially wrong. |

---

*Generated by Orchestrator — 3-agent parallel verification synthesis*
*April 24, 2026*
