# Algorithm Design: Failure Mode Analysis

**Scientific Critical Thinking Assessment**
**Project**: ContextAware-DQ
**Streaming Engine**: Apache Flink (Java for CRS, Python for SYN/SEM)
**Domain**: NYC TLC Yellow Taxi + NYC MTA Bus (GTFS-realtime)
**Date**: April 23, 2026

---

## Question 1: L0–L5 Fallback — Worst Case

### Assessment

The L4 dilution problem is structural and unavoidable. The document quantifies the fallback distribution for NYC TLC: L0 ≈ 0–5%, L1 ≈ 5–15%, L2 ≈ 15–30%, L3 ≈ 30–50%, **L4 (global) ≈ 20–40%** of events. The global fallback is computed from ALL events across all contexts — late-night fares averaged with rush-hour fares, airport zones averaged with outer-borough zones.

**The L4 dilution effect is asymmetric for TQS.** A $50 airport-to-Manhattan trip at 2 AM is normal. But compared to the global mean (which includes $10 outer-borough short trips, $80 Manhattan daytime trips), the global standard deviation is enormous, and the context-diluted threshold is so wide that the $50 trip may not register as a violation even if it is contextually unusual.

**The power analysis for L0 min-samples (100 events) is sound, but L4 is not analyzed.** What is the false positive rate at L4 when the global mean and std are computed from heterogeneous contexts? No power analysis is provided for L4.

**The L5 (physics priors) is NOT affected** by this dilution problem — [2, 120] km/h are hardcoded physics bounds, not data-driven. CRS001/CRS002 operate on NYC MTA Bus GPS data, which does not have zone-level sparsity.

### Failure Mode

| Mode | Severity | Likelihood | Impact |
|------|:--------:|:----------:|--------|
| L4 global mean masks context-specific patterns → systematic false negatives on 20–40% of events | **CRITICAL** | **HIGH** | TQS overestimates quality for sparse-context events; RQ1 ΔF1 for all-events likely 1–2pp, not 5pp |
| L4 global std inflated by heterogeneous contexts → systematically wide thresholds | **CRITICAL** | **HIGH** | CRS001/L4-style thresholds become near-useless for distinguishing anomalies |
| L4 events produce ambiguous violations — "violated global threshold but not context threshold" | **MAJOR** | **HIGH** | Context-decomposed TQS cannot explain L4 violations |
| TQS composite dominated by L4 behavior (largest event fraction) | **MAJOR** | **MEDIUM** | L0/L1 contributions drowned out in aggregate TQS |

### Mitigation

**Option A**: Acknowledge as Known Limitation: "20–40% of events use the global fallback. Aggregate TQS improvement is estimated 1–2pp. The contribution is most meaningful for high-traffic contexts (L0/L1 cells)."

**Option B (Recommended)**: Redesign L4 as a **Weighted Context Pool** — L4 should use a weighted pool of the 5–10 most similar L3 contexts, not a single global mean/std.

**Option C (Defensive)**: Report L0-specific and aggregate RQ1 metrics separately. Scope RQ1 claims to L0/L1 events, not all events.

---

## Question 2: TQS V2 Weights — Sensitivity Analysis

### Assessment

**Problem 1 — Weights are unprincipled.** The document says weights are "pre-registered" but provides no derivation. A reviewer will ask: "Why 0.40 for V and not 0.50? Why is Cn (0.30) weighted more than P (0.10)?"

**Problem 2 — C dimension is dead on NYC TLC.** CRS001/CRS002 require GPS coordinates, which are not available in NYC TLC zone-level data. On the primary evaluation dataset, C is always 1.0 (no violations possible). The 0.20 weight on C is effectively wasted.

**Problem 3 — RQ3 is circular.** TQS = 1 − violation_rate by construction. Correlation with injection rate is guaranteed by the experimental design. RQ3 measures self-consistency, not quality capture.

### TQS V2 Sensitivity Analysis

| Weight Vector | NYC TLC Score | NYC MTA Bus Score |
|-------------|:-------------:|:-----------------:|
| V2: (0.40, 0.20, 0.30, 0.10) | 0.935 | 0.905 |
| V1: (0.25, 0.25, 0.25, 0.25) | 0.938 | 0.900 |
| V3: (0.20, 0.35, 0.25, 0.20) | 0.948 | 0.895 |

**Key observations:**
- On NYC TLC: V3 > V1 > V2. V3 benefits from the dead C dimension.
- On NYC MTA Bus: V2 > V1 > V3. V2 outperforms when C is active.
- **Maximum spread**: <1.5pp across all variants — statistically negligible.
- **Ranking inconsistency**: The optimal variant depends on the dataset.

### Failure Mode

| Mode | Severity | Likelihood | Impact |
|------|:--------:|:----------:|--------|
| PC reviewer asks: "Where do the TQS V2 weights come from?" | **CRITICAL** | **HIGH** | TQS labeled "ad hoc" — loses scientific credibility |
| V3 rewards datasets without GPS (NYC TLC) over datasets with GPS violations (NYC MTA Bus) | **MAJOR** | **HIGH** | Backwards incentive; V3 should not be primary |
| C dimension (0.20 weight) is structurally dead on NYC TLC | **MAJOR** | **HIGH** | V2 is effectively a different formula on NYC TLC vs. NYC MTA Bus |
| RQ3 TQS correlation is circular by construction | **CRITICAL** | **HIGH** | RQ3 must be redesigned with an independent quality signal |

### Mitigation

**Option A (Recommended)**: Adopt V1 (equal weights: 0.25, 0.25, 0.25, 0.25) as the primary TQS variant. Equal weights are the only non-arbitrary choice without a principled derivation. V2 and V3 reported as sensitivity variants.

**Option B**: Redesign RQ3 with an independent quality signal (downstream prediction accuracy, expert annotation) — not injection rate.

---

## Question 3: CRS001 Speed Bounds — Edge Cases

### Assessment

**Lower bound (2 km/h) — creeping vehicle problem:** NYC MTA Bus vehicles in urban traffic regularly creep forward at 1–3 km/h. The 2 km/h threshold incorrectly flags creeping vehicles as violations. The fix: for GTFS-realtime at 30s update intervals, minimum distance at 2 km/h is ~17m. A creeping vehicle moves ~17m between updates — well below CRS002's 100m threshold. A creeping vehicle would fail CRS001 but pass CRS002.

**Upper bound (120 km/h) — permissive for spoofing detection:** 120 km/h is extremely permissive. A GPS spoofing attack reporting 90 km/h (realistic highway speed, impossible for urban buses) would pass CRS001. CRS002 (>100m/30s) partially fills this gap — but only for vehicles moving >100m between updates.

**CRS002 — wrong threshold for 30s update intervals:** At 30 km/h for 30s, a vehicle moves 250m. CRS002's 100m/30s threshold would fire on ALL urban-speed vehicles at 30s update intervals. This is a **critical calibration error**.

### Failure Mode

| Mode | Severity | Likelihood | Impact |
|------|:--------:|:----------:|--------|
| CRS002 fires on ALL urban-speed vehicles (>20 km/h) at 30s update intervals | **CRITICAL** | **HIGH** | Massive false positives; P > 0.70 target unreachable |
| Moderate GPS spoofing (20–90 km/h) invisible to both CRS001 and CRS002 | **CRITICAL** | **MEDIUM** | Detection gap; most realistic spoofing attacks undetected |
| Creeping vehicles (1–2 km/h) flagged by CRS001 | **MAJOR** | **HIGH** | False positives on congested urban routes |
| First GPS fix cold start produces erroneous position | **MAJOR** | **HIGH** | Systematic false positives at stream start |
| Boundary GPS noise at 120 km/h causes intermittent violations | **MINOR** | **MEDIUM** | Unstable borderline cases |

### Mitigation

**Option A (Critical)**: Fix CRS002 threshold for 30s update intervals. Set to 200–250m (at 30 km/h × 30s = 250m). Or normalize by update interval: `threshold = expected_speed × update_interval × safety_factor`.

**Option B**: Implement GPS warm-up period — ignore first 5 positions or first 30s per vehicle.

**Option C**: Implement Kalman filter for GPS jitter smoothing.

---

## Question 4: CRS003 Dedup — TTL Edge Cases

### Assessment

**TTL expiry — the silent false negative:** A duplicate arriving 310s after the original is NOT detected. The hash has expired from state. This is a silent false negative — the algorithm fails without any indication.

**CRS003 recall is [UNMEASURABLE] (B2):** The duplicate injection must emit TWO records (original + duplicate) for CRS003 to detect the duplicate. If it only emits one, recall is 0% by construction. This is a P0 blocker.

### Failure Mode

| Mode | Severity | Likelihood | Impact |
|------|:--------:|:----------:|--------|
| TTL expiry at T=310s causes silent false negatives | **CRITICAL** | **LOW** | Recall systematically underestimated; cannot be measured without fix |
| CRS003 recall UNMEASURABLE — B2 blocks evaluation | **CRITICAL** | **HIGH** | CRS layer evaluation incomplete; PC reviewer kill shot |

### Mitigation

**Option A (P0)**: Fix B2 — verify synthetic injector emits both original and duplicate records.

**Option B**: Increase TTL to 600s (10 minutes) to cover most GTFS trip durations.

**Option C**: Explicitly scope RQ5 to CRS001/CRS002 only; exclude CRS003 until B2 is fixed.

---

## Question 5: Physics Priors vs. Data-Driven Thresholds

### Assessment

**CRS002 100m/30s calibrated for 1s GPS updates, applied to 30s update data.** The document says "GTFS-realtime default update interval = 1s" but the 100m/30s threshold is calibrated for 1s intervals. At 30s intervals, a vehicle moving at 20 km/h travels 167m in 30s — above the 100m threshold. CRS002 would fire on all urban-speed vehicles.

**CRS001 [2, 120] km/h calibrated for highway maximum, not urban minimum.** The lower bound (2 km/h) is below the relevant range for urban segments (5–15 km/h). The upper bound (120 km/h) is justified for highway segments.

### Failure Mode

| Mode | Severity | Likelihood | Impact |
|------|:--------:|:----------:|--------|
| CRS002 fires on ALL urban-speed vehicles (>20 km/h) at 30s update intervals | **CRITICAL** | **HIGH** | CRS002 precision collapses; P > 0.70 unattainable |
| CRS002 threshold assumes 1s updates, applied to 30s data | **CRITICAL** | **HIGH** | Threshold is 30× too sensitive for 30s intervals |
| Moderate GPS spoofing (20–90 km/h) invisible to CRS001 | **CRITICAL** | **MEDIUM** | Detection gap |
| Hardcoded thresholds cannot adapt to highway vs. urban context | **MAJOR** | **HIGH** | Urban route anomalies indistinguishable from normal traffic |

### Mitigation

**Option A (Immediate)**: Recalibrate CRS002 threshold for 30s update intervals (200–250m).

**Option B**: Implement route geometry validation — compare VehiclePosition to GTFS Static route shapes. Positions 100m+ off-route are strong spoofing indicators.

**Option C**: Implement context-aware CRS thresholds (highway vs. urban route classification per GTFS static data).

---

## Failure Mode Taxonomy

### Critical Severity (Kill Shot)

| ID | Failure Mode | Likelihood | Mitigation |
|----|-------------|:----------:|------------|
| FM-01 | L4 global fallback dilutes context thresholds for 20–40% of events | **HIGH** | Option B: Weighted Context Pool for L4 |
| FM-02 | CRS002 fires on ALL urban-speed vehicles at 30s intervals | **HIGH** | Recalibrate threshold to 200–250m |
| FM-03 | CRS003 recall UNMEASURABLE (B2) — duplicate injection broken | **HIGH** | Fix B2 (P0, Week 8) |
| FM-04 | TQS V2 weights unprincipled — no derivation | **HIGH** | Adopt V1 (equal weights) as primary |
| FM-05 | RQ3 TQS correlation is circular by construction | **HIGH** | Redesign RQ3 with independent signal |
| FM-06 | C dimension dead on NYC TLC (0.20 weight wasted) | **HIGH** | Acknowledge; renormalize weights |

### Major Severity

| ID | Failure Mode | Likelihood | Mitigation |
|----|-------------|:----------:|------------|
| FM-07 | GPS jitter on stationary vehicles triggers CRS002 | **MEDIUM** | Kalman filter for jitter smoothing |
| FM-08 | Moderate spoofing (20–90 km/h) invisible to CRS001/CRS002 | **MEDIUM** | Route geometry validation |
| FM-09 | TQS variant ranking dataset-dependent (V3 best on TLC, V2 best on Bus) | **HIGH** | Report per-dataset TQS |
| FM-10 | L5 physics priors calibrated for highway, not urban minimum | **HIGH** | Context-aware CRS thresholds |
| FM-11 | V3 rewards datasets without GPS over datasets with GPS violations | **HIGH** | Remove V3 from primary claims |
| FM-12 | First GPS fix cold start produces erroneous position | **HIGH** | Warm-up period (ignore first 5 positions) |
| FM-13 | Creeping vehicles (1–2 km/h) flagged by CRS001 | **HIGH** | Adaptive lower bound |
| FM-14 | CRS002 100m/30s assumes 1s updates, NYC MTA Bus uses 30s | **HIGH** | Recalibrate for 30s intervals |

### Minor Severity

| ID | Failure Mode | Likelihood | Mitigation |
|----|-------------|:----------:|------------|
| FM-15 | TQS score variation <1.5pp between V1/V2/V3 | **MEDIUM** | Report sensitivity analysis in appendix |
| FM-16 | Boundary GPS noise at 120 km/h causes intermittent violations | **MEDIUM** | Add 5 km/h tolerance (125 km/h) |
| FM-17 | TTL expiry at T=310s causes silent false negatives | **LOW** | Increase TTL to 600s |
| FM-18 | Hash collision probability negligible (SHA-256) | **NEGLIGIBLE** | Document and dismiss |

---

## Recommendations

### Priority 1 — Critical (Must Fix Before Evaluation)

| # | Recommendation | Reason |
|---|---------------|--------|
| **R1** | Fix CRS003 duplicate injection (B2, P0) | CRS003 recall is UNMEASURABLE; CRS layer evaluation incomplete |
| **R2** | Fix CRS002 threshold for 30s update intervals | 100m/30s fires on all urban-speed vehicles; destroys precision |
| **R3** | Redesign RQ3 with independent quality signal | Correlation with injection rate is circular |
| **R4** | Adopt V1 (equal weights) as primary TQS variant | V2 weights unprincipled; V3 creates backwards incentive |
| **R5** | Explicitly scope RQ5 to CRS001/CRS002 only | CRS003 excluded until B2 is fixed |

### Priority 2 — Major (Should Fix Before Evaluation)

| # | Recommendation | Reason |
|---|---------------|--------|
| **R6** | GPS warm-up period (ignore first 5 positions) | Systematic false positives at stream start |
| **R7** | Kalman filter for GPS jitter | False positives on stationary vehicles |
| **R8** | Route geometry validation via GTFS Static | Fills detection gap for moderate spoofing |
| **R9** | Redesign L4 as Weighted Context Pool | Reduces L4 dilution for 20–40% of events |
| **R10** | Report L0-specific and aggregate RQ1 metrics separately | Scope claims to where method actually applies |

### Priority 3 — Significant (Plan for Phase 3)

| # | Recommendation | Reason |
|---|---------------|--------|
| **R11** | Context-aware CRS thresholds | Highway vs. urban route classification |
| **R12** | Implement D4 (External context: holiday) | Complete the 5D context decomposition |
| **R13** | CRS002 adaptive threshold by update interval | `f(update_interval, expected_speed)` |

### Priority 4 — Defensive

| # | Recommendation | Reason |
|---|---------------|--------|
| **R14** | Report TQS weight sensitivity analysis | Preempts "ad hoc" objection |
| **R15** | Document all limitations explicitly in paper | Demonstrates scientific honesty |
| **R16** | Reframe novelty claims conservatively | "For events in L0/L1 cells (~15% of data), context-aware thresholds improve F1 by Xpp" |

---

## Summary Assessment

The ContextAware-DQ algorithm design is **technically sound in its core architecture** (L0–L5 fallback, TQS scoring, CRS rules) but has **critical failure modes** in five areas:

| Area | Status | Fix |
|------|--------|-----|
| L4 dilution | **Critical** | Redesign L4 as Weighted Context Pool |
| CRS002 threshold | **Critical** | Recalibrate for 30s intervals (200–250m) |
| CRS003 recall | **Critical** | Fix B2 (P0, Week 8) |
| TQS weights | **Critical** | Adopt V1 (equal weights); redesign RQ3 |
| CRS002 GPS jitter | **Major** | Kalman filter + warm-up period |

**Path to accept**: Fix R1–R5 (critical) + R14–R16 (defensive). The framework can be a **Weak Accept** with honest limitations. Overclaiming (5pp ΔF1, CRS003 recall, TQS validity) will push it to **Reject**.

**Path to reject**: Any of FM-01 through FM-05 unaddressed at submission time.
