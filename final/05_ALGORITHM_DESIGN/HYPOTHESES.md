# Algorithm Hypotheses: ContextAware-DQ Framework

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Role**: Hypothesis Generation Specialist
**Date**: Thursday, April 23, 2026
**Target**: VLDB/SIGMOD research platform
**Domain**: NYC TLC Yellow Taxi + NYC MTA Bus GTFS-realtime
**Engine**: Apache Flink (Java + Python async RPC)

---

## Preamble: Anti-Hallucination Compliance

Every hypothesis follows three evidence tiers:

- **Tier 1 — Verified**: Grounded in prior work or code inspection, falsifiable by experiment
- **Tier 2 — Estimated**: Mechanistic reasoning, requires benchmark to confirm
- **Tier 3 — Unmeasurable**: Known methodological blocker prevents measurement

No numbers are invented. Estimated claims are labeled `[ESTIMATED]`. Known blockers are cited by ID (B1–B6, I1–I25).

**Known blockers affecting hypotheses:**

| ID | Blocker | Affected Hypotheses |
|----|---------|-------------------|
| B2 | CRS003 duplicate injection does NOT emit original + duplicate | H3-CRS003 only |
| B6 | `processing_latency_ms` hardcoded to 0 | Latency hypotheses (all) |
| I7 | L0 min-samples (100) derived without empirical validation | H1-L0 only |
| I16 | D4 External context (holiday) is a stub | H1-D only |
| I24 | CRS002 threshold (>100m/30s) validated for buses, not all vehicles | H3-CRS002 only |

---

## Algorithm 1: L0–L5 Hierarchical Context-Aware Threshold Fallback

### Hypothesis H1-A: Context Resolution Improves Detection Accuracy [REVISED — Tier 2]

**H1-A**: Events evaluated at finer-grained context levels (L0–L1) yield lower false-positive rates than events evaluated at coarser fallback levels (L4–L5).

**[REVISED — L4 dilution analysis]** per SIGNIFICANCE_TABLE.md §5.1 and QUALITY_AUDIT.md: The original claim "ΔF1 ≥ 5pp" applies only to events in L0 context cells (approximately 5% of events). SIGNIFICANCE_TABLE.md §5.1 proves that the aggregate ΔF1 across ALL events is estimated at 1–2pp, not 5pp, because L4 cells contain 20–40% of events with no context-specific threshold benefit.

**Revised claim**:
- Per-L0-cell ΔF1: ≥1pp estimated [Tier 2 — L4 dilution accounted for in aggregate]
- Up to 5pp for events in L0-optimal cells (high-traffic zones with ≥100 samples) [Tier 2 — power analysis, Cohen's d ≈ 0.30]
- L0 coverage: ~5% of events (needs verification from actual NYC TLC statistics)
- Aggregate ΔF1 (all events): ≥1pp estimated, upper bound ~5pp if L0 coverage exceeds expectations

| Field | Value |
|-------|-------|
| **IV** | Context resolution level selected for threshold lookup: `L0` (hour × zone_category × weekend, min 100 samples) vs. `L4` (global, min 5 samples) |
| **DV** | (a) False positive rate (FPR): legitimate events flagged as violations; (b) F1 score per context cell; (c) Aggregate F1 across all events |
| **Mechanism** | NYC TLC taxi fares are conditionally dependent on time and location. Rush-hour midtown fares differ systematically from late-night outer-borough fares. A global threshold (L4) cannot capture these conditional distributions; it must over-generalize, either over-flagging legitimate variation in high-variance cells or under-flagging violations in low-variance cells. Context-specific thresholds (L0) capture the conditional $P(\text{fare} \mid \text{hour}, \text{zone\_category}, \text{weekend})$, yielding narrower prediction intervals and fewer classification errors. |
| **Falsification** | Aggregate ΔF1 < 1pp at 95% CI → H1-A rejected. Per-L0-cell ΔF1 < 2pp at 95% CI → per-cell effect smaller than power analysis suggests. |
| **H₀** | Context resolution provides no improvement: FPR(L0) = FPR(L4) (or worse) |
| **Statistical Test** | Wilcoxon signed-rank test (paired, per context cell) comparing FPR at L0 vs. L4 across ≥ 30 context cells. α = 0.05, Bonferroni-corrected to α_adj = 0.01 across 5 RQs. Effect size: Cohen's d ≥ 0.30 (from power analysis in report.md §L0-L5). Bootstrap: 1,000 iterations for CI. Report both per-L0-cell and aggregate ΔF1. |
| **Edge Cases** | (1) **L0 dilution**: NYC TLC has 263 zones × 24h = 6,312 potential L0 cells. Expected L0 coverage: 0–5% of events. Aggregate ΔF1 reflects dilution. Test must report both per-L0-cell and aggregate metrics. (2) **Cold start**: Day 1 has no context statistics. All events fall to L5 (physics priors). (3) **Temporal drift**: A zone's fare distribution may shift. Stale L0 thresholds may outperform fresh L4 thresholds. (4) **Overfitting**: L0 cells with < 100 samples that pass the min-sample check may have thresholds fit to noise. (5) **D4 holiday stub**: holiday dimension is unimplemented (I16). The 5D context is effectively 4D. |

---

### Hypothesis H1-B: Hierarchical Fallback Degrades Gracefully

**H1-B**: As the context lookup falls back from L0 to L5, the threshold's specificity decreases monotonically (i.e., the threshold prediction interval widens), and the false-negative rate increases monotonically.

| Field | Value |
|-------|-------|
| **IV** | Fallback level selected: L0 → L1 → L2 → L3 → L4 → L5 |
| **DV** | Threshold specificity: ratio of cell-specific std dev to global std dev (expected: decreasing), and per-level violation detection rate |
| **Mechanism** | Each fallback level aggregates over more context dimensions, reducing the conditionality of the threshold. At L0, the threshold is specific to `hour_10_midtown_weekday`. At L4, it is global. The monotonic increase in variance at coarser levels is a mathematical consequence of the law of total variance: $\sigma^2_{\text{global}} = \mathbb{E}[\sigma^2_{\text{cell}}] + \text{Var}(\mu_{\text{cell}})$. The prediction interval widens at each fallback, reducing the ability to distinguish violations from legitimate variation. |
| **Falsification** | FNR(L0) ≥ FNR(L4) at any injection rate, or variance(threshold_L0) ≥ variance(threshold_L4). Both would indicate the fallback provides no information value. NOTE: FNR improvement at L0 is estimated for ~5% of events only; aggregate FNR improvement across all events is estimated at 1–2pp (significantly diluted by L4/L3 coverage of 60–80% of events). |
| **H₀** | Fallback levels are indistinguishable: variance(threshold) is constant across L0–L4, or FNR is non-monotonic |
| **Statistical Test** | Friedman's test (non-parametric repeated measures) across L0–L4 threshold specificity, across ≥ 30 context cells. Post-hoc Nemenyi test for pairwise comparisons. Report ΔFNR per level with 95% bootstrap CI. |
| **Edge Cases** | (1) **L5 discontinuity**: L5 (physics priors, [2, 120] km/h for CRS001) is categorical, not statistical. It does not use the same threshold metric. L5 should be excluded from the monotonicity test. (2) **Non-monotonic drift**: If temporal trends cause some L1 cells to have wider distributions than L2 cells (e.g., rush-hour high variance in all zones), the monotonicity assumption breaks. |

---

### Hypothesis H1-C: L0 Cell Coverage Determines Aggregate ΔF1

**H1-C**: The aggregate ΔF1 (static vs. context-aware, across all events) is proportional to the fraction of events falling into L0–L2 cells.

| Field | Value |
|-------|-------|
| **IV** | Fraction of events at each fallback level: $f_{L0}, f_{L1}, f_{L2}, f_{L3}, f_{L4}$ |
| **DV** | Aggregate ΔF1 (context-aware − static), across the full event stream |
| **Mechanism** | If context-aware thresholds only improve F1 for events in L0 cells (ΔF1_L0), and L0 cells contain only $f_{L0}$ of events, then the aggregate improvement is approximately $\Delta F1_{\text{aggregate}} \approx f_{L0} \cdot \Delta F1_{L0} + f_{L1} \cdot \Delta F1_{L1} + \cdots$. Given $f_{L0} \approx 0.05$ (estimated from 263 zones × 24h, ~5 records/cell/day), the aggregate ΔF1 is dominated by L4/L3 coverage (estimated 20–40% and 30–50%, respectively), where the improvement per event is smaller. |
| **Falsification** | Aggregate ΔF1 ≥ 5pp without L0 coverage ≥ 10%. This would contradict the power analysis estimate that 100 samples/cell are needed for 5pp detection. Either the min-sample thresholds are wrong, or the ΔF1 target is wrong. |
| **H₀** | Aggregate ΔF1 is independent of L0 coverage: ΔF1_aggregate = ΔF1_static + constant |
| **Statistical Test** | Spearman rank correlation (ρ_s) between $f_{L0}$ and ΔF1_aggregate across multiple evaluation runs with varying data distributions. Ablation: vary the fraction of events in high-traffic zones (e.g., filter to top-20 zones vs. bottom-100 zones) and measure the resulting ΔF1. |
| **Edge Cases** | (1) **CRS rules bypass this**: CRS001/CRS002 use GPS coordinates, not zone-level context. They are not subject to the L0 sparsity problem on NYC MTA Bus (continuous GPS stream). (2) **Temporal concentration**: If high-fare events cluster in peak hours, L0 coverage may be concentrated in a few cells that dominate aggregate metrics. |

---

### Hypothesis H1-D: D4 External Context (Holiday) Modulates Violation Rate

**H1-D**: Including holiday information in the context key (upgrading D4 from stub to functional) changes the violation rate on holidays vs. non-holidays beyond what temporal features alone capture.

| Field | Value |
|-------|-------|
| **IV** | Context key includes holiday indicator (D4) vs. omits it (D4 stub) |
| **DV** | Change in violation rate on holiday events (expected increase, as holiday demand patterns differ) |
| **Mechanism** | NYC TLC trip patterns on Thanksgiving, Christmas, and New Year's differ systematically: higher proportion of airport trips, longer distances, higher fares per mile. A temporal-only context key (hour + weekday) cannot distinguish a 10 AM Tuesday in December that is a normal workday from one that is a holiday. Adding D4 captures this structural shift. |
| **Falsification** | Violation rate on holidays with D4-enabled thresholds is equal to or greater than violation rate with D4-disabled thresholds. If D4 widens rather than narrows the threshold (capturing holiday variance), it may increase rather than decrease violations. |
| **H₀** | D4 provides no additional discriminative power: violation rate(hour_weekday_holiday) = violation rate(hour_weekday) |
| **Statistical Test** | Paired t-test (or Wilcoxon if non-normal) comparing violation rates on matched holiday/non-holiday days at the same hour × zone_category. Requires holiday calendar lookup table (NYE, Thanksgiving, etc.) and ≥ 3 holiday events in the dataset. |
| **Edge Cases** | (1) **Data coverage**: NYC TLC replay data may not include enough holidays to validate. (2) **D4 is PARTIAL (I16)**: The holiday indicator is marked as unimplemented. This hypothesis is conditional on D4 being completed. |

---

## Algorithm 2: TQS (Trajectory Quality Scoring) Aggregation

### Hypothesis H2-A: TQS Decreases Monotonically with Injection Rate

**H2-A**: TQS composite score (V2: 0.20×Tm + 0.25×Cn + 0.20×Ac + 0.25×Cs + 0.10×Uv) decreases monotonically as synthetic anomaly injection rate increases from 0% to 20%.

| Field | Value |
|-------|-------|
| **IV** | Synthetic anomaly injection rate: 0%, 5%, 10%, 20% (per evaluation run) |
| **DV** | TQS_composite score (V2), measured per 600-second window |
| **Mechanism** | TQS is defined as a weighted combination of five stream-intrinsic dimensions (Tm, Cn, Ac, Cs, Uv), each computed directly from raw event properties. Injected anomalies affect these dimensions directly: negative fare_amount → Ac; null passenger_count → Cn; GPS speed spike → Cs; duplicate injection → Uv. As injection rate increases, more raw values are anomalous, and TQS dimensions degrade. |
| **Falsification** | TQS does not decrease monotonically with injection rate. Specifically, if TQS(5%) ≥ TQS(0%) or TQS(10%) ≤ TQS(20%) + noise, the calibration curve is broken. Alternatively: the slope of TQS vs. injection rate differs significantly from expectations. |
| **H₀** | TQS is uncorrelated with injection rate: Spearman ρ_s(TQS, injection_rate) = 0 |
| **Statistical Test** | Spearman rank correlation (ρ_s) with 95% bootstrap CI (1,000 iterations). Target: ρ_s < -0.9 (near-perfect negative correlation). Report Pearson ρ as well. Use ≥ 3 trials per injection rate. |
| **Edge Cases** | (1) **Non-circular construction**: Unlike the original TQS = 1 − violation_rate, the new TQS uses only raw event properties. Correlation with injection rate is expected (anomalies affect raw values) but is NOT guaranteed by construction. (2) **Anomaly type matters**: SYN anomalies (null, NaN) primarily affect Cn and Ac. CRS anomalies (GPS speed, jump) affect Cs. Duplicate injection affects Uv. Some injection types may not affect TQS if they don't target the measured dimensions. (3) **CRS rules on NYC TLC**: Cs on NYC TLC uses price-per-mile consistency, not GPS. CRS anomalies do not affect Cs on NYC TLC. |

---

### Hypothesis H2-B: Context-Decomposed TQS Correlates with Quality Better than Aggregate TQS

**H2-B**: TQS computed per context cell (L0 key) shows higher Spearman correlation with per-cell injection rate than TQS computed at the aggregate (all-events) level.

| Field | Value |
|-------|-------|
| **IV** | TQS aggregation level: per context cell (L0) vs. aggregate (all events) |
| **DV** | Spearman correlation coefficient ρ_s(TQS, injection_rate) at each aggregation level |
| **Mechanism** | Aggregate TQS pools all context cells, washing out cell-specific quality signals. If only `hour_14_Manhattan_weekday` has high quality problems, the aggregate TQS dilutes this signal across all other cells. Per-cell TQS preserves this signal, enabling "Why is quality low?" attribution. However: if quality problems are uniform across all context cells (e.g., a systematic data pipeline bug), aggregate TQS is sufficient. The hypothesis predicts context heterogeneity in violation rates. |
| **Falsification** | ρ_s(per-cell TQS, injection_rate) ≤ ρ_s(aggregate TQS, injection_rate). If per-cell TQS is no better, the context decomposition adds no diagnostic value. |
| **H₀** | Aggregation level does not affect TQS validity: ρ_s(per-cell) = ρ_s(aggregate) |
| **Statistical Test** | DeLong's test for comparing two correlated AUC/ROC curves (adapted for Spearman correlation: compare Fisher-transformed z-scores of ρ_s per cell vs. aggregate). Report 95% bootstrap CI for the difference Δρ_s = ρ_s(per-cell) − ρ_s(aggregate). |
| **Edge Cases** | (1) **Non-circular construction**: Both TQS and injection rate are per-cell quantities. The correlation is not circular because TQS is computed from raw event properties, not rule outcomes. (2) **Cell sparsity**: Low-sample cells produce noisy TQS estimates. High-injection cells may have fewer clean events for calibration. |

---

### Hypothesis H2-C: TQS Variants V1, V2, V3 Are Statistically Distinguishable

**H2-C**: The three pre-registered TQS variants (V1: equal ω=0.20; V2: domain ω_Tm=0.20, ω_Cn=0.25, ω_Ac=0.20, ω_Cs=0.25, ω_Uv=0.10; V3: consistency-heavy ω_Cs=0.35) produce statistically distinguishable quality rankings across context cells.

| Field | Value |
|-------|-------|
| **IV** | TQS variant: V1, V2, or V3 |
| **DV** | TQS score per context cell; rank ordering of context cells by TQS |
| **Mechanism** | V2 weights Completeness (Cn=0.25) and Consistency (Cs=0.25) at the highest, reflecting domain knowledge that null/NaN fields and GPS coherence are most critical for NYC TLC and NYC MTA Bus quality. V3 weights Consistency (Cs=0.35) highest. V1 is a neutral baseline. Different weights assign different severity to different quality dimensions, producing different quality rankings. |
| **Falsification** | Kendall's W (coefficient of concordance) across V1, V2, V3 for the same context cells is not significantly different from 1/3 (i.e., all three variants produce the same ranking). If W ≈ 1.0, the weights are irrelevant. |
| **H₀** | TQS variants are equivalent: Kendall's W = 1/3 (random agreement) |
| **Statistical Test** | Friedman's test for related samples (V1, V2, V3 TQS scores across ≥ 30 context cells). If Friedman χ² is significant (p < 0.05), post-hoc Nemenyi test identifies which pairs differ. Report Kendall's W with 95% bootstrap CI. |
| **Edge Cases** | (1) **CRS dominates Cs on NYC MTA Bus**: Cs varies with GPS violations. On NYC TLC, Cs uses price-per-mile consistency. V3 (consistency-weighted) behaves differently on the two datasets. (2) **V2 weights are ad hoc**: The weights are a design choice, not a finding. The test only distinguishes variants from each other, not whether any variant is "correct." |

---

### Hypothesis H2-D: TQS Captures Quality Degradation Beyond Simple Violation Rate

**H2-D**: TQS composite explains more variance in an independent quality signal than a simple raw-field metric.

| Field | Value |
|-------|-------|
| **IV** | Quality metric: TQS composite (5 dimensions from raw events) vs. single-dimension raw field rate |
| **DV** | Explained variance (R²) in an independent quality signal |
| **Mechanism** | TQS disaggregates raw event properties into five dimensions (Tm, Cn, Ac, Cs, Uv). This enables: (a) dimension-specific alerts ("Cs is low → GPS quality problem"), and (b) weighted combination that may better predict downstream quality impacts. If only the total violation count matters for downstream tasks, simple metrics are sufficient. If dimension-specific quality matters (e.g., GPS coherence violations cause ETA prediction failures), TQS adds value. |
| **Falsification** | R²(TQS_composite) ≤ R²(single_raw_field_metric) for any downstream quality signal. If TQS adds no explanatory power beyond a single metric, the multi-dimensional decomposition is unjustified. |
| **H₀** | TQS adds no explanatory power: R²(TQS) ≤ R²(single_raw_field_metric) |
| **Statistical Test** | Compare nested models: single raw field metric (1 predictor) vs. TQS with all five dimensions (5 predictors). F-test for nested models, or compare AIC/BIC. Requires an independent quality signal (e.g., downstream ETA prediction accuracy on NYC MTA Bus) — NOT injection rate (which would reintroduce circularity). |
| **Edge Cases** | (1) **No independent signal available**: Requires a non-circular quality signal. The candidate is downstream ETA prediction error: high-quality GPS positions → accurate ETAs → low prediction error. TQS should correlate with ETA error reduction. (2) **Overfitting**: Adding dimensions increases degrees of freedom. With few context cells, TQS may appear better due to overfitting, not genuine improvement. |

---

## Algorithm 3: CRS State Machine (Cross-Record GPS Rules)

### Hypothesis H3-CRS001: GPS Speed Bounds Detect Synthetic Speed Violations with P > 0.70

**H3-CRS001**: CRS001 (Haversine-based speed bounds [2, 120] km/h) achieves precision > 0.70 on synthetically injected GPS speed spike anomalies in NYC MTA Bus GTFS-realtime streams.

| Field | Value |
|-------|-------|
| **IV** | Speed injection: synthetic GPS position pairs producing computed speed > 120 km/h vs. normal vehicle positions (speed 0–80 km/h) |
| **DV** | Precision: fraction of CRS001 violations that match injected speed spikes (entity_index match), among all CRS001 violations |
| **Mechanism** | NYC MTA buses operate at 0–80 km/h in urban service. Speed > 120 km/h is physically impossible for a bus on city streets and is indicative of GPS data errors (position jumps, sensor glitches, or deliberate spoofing). Haversine distance / time delta between consecutive VehiclePosition messages gives a direct physical speed estimate. The [2, 120] km/h bounds are conservative: 2 km/h eliminates stationary vehicles, 120 km/h provides a safety margin above highway speed limits. |
| **Falsification** | Precision(CRS001) ≤ 0.70 at 95% bootstrap CI. Specifically, if the lower bound of the 95% CI for P(CRS001) is below 0.70, reject H3-CRS001. |
| **H₀** | P(CRS001) ≤ 0.70 |
| **Statistical Test** | One-sided binomial test for precision ≥ 0.70. Compute 95% Wilson CI. Bootstrap: 1,000 resamples of injection trials (3 trials × 600s per rate). Report precision per injection rate (5%, 10%, 20%) separately. |
| **Edge Cases** | (1) **Real speed violations missed**: CRS001 cannot detect actual GPS spoofing that stays within [2, 120] km/h. (2) **Stationary vehicles at speed=0**: The 2 km/h lower bound passes legitimate stationary vehicles. A position reporting error producing speed < 2 km/h will not trigger CRS001. (3) **GTFS-realtime update interval**: GTFS-realtime updates are every ~30s. Computing speed from positions 30s apart introduces larger Haversine errors (±5m GPS jitter). |

---

### Hypothesis H3-CRS002: GPS Jump Detection Distinguishes Real Bus Routes from Spoofed Positions

**H3-CRS002**: CRS002 (> 100m displacement in 30s window) achieves precision > 0.70 and recall > 0.60 on synthetically injected GPS jump anomalies in NYC MTA Bus GTFS-realtime streams.

| Field | Value |
|-------|-------|
| **IV** | GPS jump injection: two vehicle positions at the same timestamp or within 30s, separated by > 100m, vs. normal consecutive bus positions |
| **DV** | (a) Precision: fraction of CRS002 violations that match injected jumps; (b) Recall: fraction of injected jumps that trigger CRS002 violations |
| **Mechanism** | NYC MTA buses follow fixed routes with stop spacing of typically 100–400m. Between two consecutive GTFS-realtime updates (every ~30s), a bus cannot physically travel > 100m in 30s if stopped at a traffic light, but it also cannot teleport > 100m between two reports that are nominally simultaneous. The 100m threshold is calibrated to: (a) exceed normal stop-to-stop movement at speed < 12 km/h, and (b) detect sudden position resets (spoofing, sensor reboot, vehicle reassignment). |
| **Falsification** | (a) Precision(CRS002) ≤ 0.70 (false positives exceed 30%), indicating buses regularly travel > 100m between updates in normal operation. (b) Recall(CRS002) ≤ 0.60, indicating CRS002 fails to detect the majority of injected jumps. |
| **H₀** | P(CRS002) ≤ 0.70 OR R(CRS002) ≤ 0.60 |
| **Statistical Test** | Two one-sided binomial tests (TOST equivalence): precision ≥ 0.70 and recall ≥ 0.60. McNemar's test for paired comparisons (with-state vs. without-state). 95% Wilson CI for each. Bootstrap: 1,000 resamples. |
| **Edge Cases** | (1) **Stop spacing**: In dense urban areas, stops may be < 100m apart. A bus traveling between two closely spaced stops could legitimately exceed 100m in 30s at 12 km/h. The 100m threshold is exactly at the boundary of normal operation. (2) **GTFS-realtime idle**: If a bus stops reporting for > 5 minutes, Flink's idle stream detection may emit a position jump at resumption. This should be filtered. (3) **Vehicle reassignment**: NYC MTA may reassign a vehicle ID to a different physical bus. CRS002 treats this as spoofing. (4) **Known limitation (B3)**: CRS002 has a speed range gap of 2–20 km/h moderate spoofing. |

---

### Hypothesis H3-CRS003: Hash-Based Deduplication Detects Injected Duplicates [UNMEASURABLE]

**H3-CRS003**: CRS003 (hash of trip_id + timestamp + lat + lon, 300s window) achieves measurable recall on synthetically injected duplicate events.

| Field | Value |
|-------|-------|
| **IV** | Duplicate injection: emitting the same (trip_id, timestamp, lat, lon) hash twice within a 300s window |
| **DV** | Recall: fraction of injected duplicates that are detected by CRS003 (i.e., second occurrence within 300s window flagged) |
| **Mechanism** | Hash-based deduplication works by computing H = SHA256(trip_id ‖ timestamp ‖ lat ‖ lon) for each event and storing H in a per-hash state with 310s TTL. If the same H appears within 300s, the second occurrence is flagged as a duplicate. |
| **Falsification** | **(BLOCKED by B2)**: CRS003 recall is [UNMEASURABLE] because duplicate injection does NOT emit both original and duplicate events. CRS003 requires seeing two records (original + duplicate) to detect the duplicate. If the injector only emits the duplicate, CRS003 has no first record to compare against, and recall = 0 by construction. |
| **H₀** | Recall(CRS003) = 0 (cannot be measured with current injection) |
| **Statistical Test** | **UNMEASURABLE until B2 is fixed.** Fix: `synthetic_injector.py` must emit both the original event and the duplicate event, tagged with `entity_index` and `entity_index_duplicate` respectively. After fix: McNemar's test comparing matched injection trials with/without deduplication. |
| **Edge Cases** | (1) **B2 is P0**: Risk register marks this as "HIGH likelihood, HIGH impact." (2) **Hash collision**: SHA256 has negligible collision probability (2^-256). Not a practical concern. (3) **Window boundary**: If the first occurrence is at t=0 and the second at t=301s, the second falls outside the 300s window. The TTL (310s) partially mitigates out-of-order processing. |

---

### Hypothesis H3-StateMachine: Per-Vehicle State Tracking Enables CRS Detection That Is Impossible Without State

**H3-StateMachine**: CRS rule violations (CRS001 + CRS002) require per-vehicle state (last position, last timestamp, per-hash dedup set). A stateless evaluation produces zero CRS violations.

| Field | Value |
|-------|-------|
| **IV** | State tracking: per-vehicle KeyedState (RocksDB) vs. stateless evaluation (no state) |
| **DV** | Number of CRS violations detected (CRS001 + CRS002) per 600-second window |
| **Mechanism** | CRS001 computes speed = Haversine(pos_t, pos_{t-1}) / (t − t_{−1}). Without state, the previous position is unknown. CRS002 computes displacement between positions at similar timestamps. Without state, the prior position is unknown. State is a computational requirement, not a design choice. The state TTL (10 min) ensures stale state is evicted, preventing old vehicle IDs from consuming memory. |
| **Falsification** | A stateless evaluation detects any CRS001 or CRS002 violations. This would indicate the violations are detectable from a single event record (e.g., a speed field in the GTFS message, which it is not), making state unnecessary. |
| **H₀** | CRS violations are detectable without state |
| **Statistical Test** | Paired design: run the same evaluation twice, with and without per-vehicle state, on identical data. McNemar's test for paired binary outcomes (violation detected vs. not). Expected result: violations = 0 without state, violations > 0 with state. |
| **Edge Cases** | (1) **Checkpoint restart**: After a Flink checkpoint/restart, per-vehicle state is restored from RocksDB. If state is not checkpointed, violations during the gap are missed. (2) **State migration**: Flink state schema evolution must be handled. (3) **Java implementation required**: CRS rules must be in Java KeyedProcessFunction. Python state access (PyFlink JVM↔Python serialization) is a performance bottleneck. |

---

## Summary Hypothesis Table

| ID | Algorithm | Hypothesis | IV | DV | Falsification | Test | Tier |
|----|-----------|-----------|----|----|---------------|------|------|
| **H1-A** | L0-L5 Fallback | Context resolution improves detection accuracy (≥1pp aggregate, up to 5pp per L0 cell) | L0 vs. L4 threshold level | FPR, F1 per cell, aggregate F1 | FPR(L0) ≥ FPR(L4) at 95% CI | Wilcoxon signed-rank (paired, ≥ 30 cells), α=0.01 | **Tier 2** |
| **H1-B** | L0-L5 Fallback | Fallback degrades threshold specificity monotonically | Fallback level L0–L4 | Threshold variance, FNR | FNR non-monotonic or constant | Friedman's test + Nemenyi post-hoc | **Tier 2** |
| **H1-C** | L0-L5 Fallback | L0 cell coverage determines aggregate ΔF1 | $f_{L0}$ fraction of events | Aggregate ΔF1 | ΔF1 ≥ 5pp without L0 coverage ≥ 10% | Spearman ρ_s (f_L0 vs. ΔF1), ablation by zone | **Tier 2** |
| **H1-D** | L0-L5 Fallback | Holiday indicator modulates violation rate | D4 enabled vs. disabled | Holiday violation rate | Rate(hour_weekday_holiday) = Rate(hour_weekday) | Paired t-test (holiday vs. matched non-holiday) | **Tier 2** [conditional on I16] |
| **H2-A** | TQS | TQS decreases monotonically with injection rate | Injection rate 0–20% | TQS_composite | ρ_s(TQS, rate) ≥ 0 or non-monotonic | Spearman ρ_s, 95% bootstrap CI, ≥ 3 trials/rate | **Tier 2** |
| **H2-B** | TQS | Per-cell TQS correlates better than aggregate TQS | TQS aggregation level | ρ_s(TQS, per-cell injection rate) | ρ_s(per-cell) ≤ ρ_s(aggregate) | DeLong's test (Fisher z-transformed ρ_s) | **Tier 2** |
| **H2-C** | TQS | V1/V2/V3 produce distinguishable quality rankings | TQS variant (V1, V2, V3) | TQS score per cell, cell ranking | Kendall's W ≤ 1/3 (equivalent rankings) | Friedman's test + Nemenyi post-hoc, ≥ 30 cells | **Tier 2** |
| **H2-D** | TQS | TQS explains more variance than single raw field metric | Metric: TQS vs. single raw field rate | R² on independent quality signal | R²(TQS) ≤ R²(single_raw_field_metric) | F-test (nested models), AIC/BIC comparison | **Tier 2** [needs independent downstream signal] |
| **H3-CRS001** | CRS State | GPS speed bounds achieve P > 0.70 on synthetic spikes | Speed > 120 km/h injection | Precision(CRS001) | P(CRS001) ≤ 0.70 at 95% CI | One-sided binomial, Wilson CI, 1,000 bootstrap | **Tier 2** |
| **H3-CRS002** | CRS State | GPS jump detection achieves P > 0.70, R > 0.60 | Jump > 100m/30s injection | Precision(CRS002), Recall(CRS002) | P ≤ 0.70 OR R ≤ 0.60 at 95% CI | Two one-sided binomial (TOST), McNemar's test | **Tier 2** |
| **H3-CRS003** | CRS State | Hash-based deduplication achieves measurable recall | Duplicate injection (original + dup) | Recall(CRS003) | Recall(CRS003) = 0 (blocked by B2) | **UNMEASURABLE** — B2 blocks measurement | **Tier 3** [blocked by B2] |
| **H3-StateMachine** | CRS State | CRS violations require per-vehicle state | Stateful vs. stateless evaluation | CRS violation count | Any CRS violations detected without state | McNemar's test (paired, binary outcome) | **Tier 2** |

---

## Research Question Mapping

| RQ | Question | Mapped Hypotheses |
|----|----------|-------------------|
| **RQ1** | Does context-aware threshold adaptation improve F1 over static? | H1-A, H1-B, H1-C |
| **RQ2** | Does hierarchical fallback maintain quality on sparse context cells? | H1-B, H1-C |
| **RQ3** | Does context-decomposed TQS correlate with ground truth better than aggregate? | H2-B, H2-C |
| **RQ4** | Does TQS accurately quantify quality degradation with injection rate? | H2-A, H2-D |
| **RQ5** | Do CRS rules achieve precision > 0.70 on NYC MTA Bus? | H3-CRS001, H3-CRS002, H3-StateMachine |
| **RQ6** | Does ML-augmented threshold calibration improve F1 over rule-only? | Not covered (Phase 3 optional, blocked by B2) |

---

## Critical Caveats

1. **H1-A aggregate ΔF1 is diluted by L4 coverage**: The estimated L0 coverage of 0–5% means most events fall to L4. Reviewers will ask: "What fraction of events actually benefit from context-aware thresholds?" H1-C directly addresses this. Aggregate ΔF1 is estimated at 1–2pp, not 5pp.

2. **H2-D requires an independent downstream signal**: TQS must be validated against ETA prediction error, not injection rate. If no downstream signal is available, H2-D cannot be tested.

3. **H3-CRS003 is Tier 3 — UNMEASURABLE**: B2 (duplicate injection broken) prevents CRS003 recall measurement. Fix B2 before evaluation. This is documented in the known blockers.

4. **D4 (Holiday) is unimplemented**: H1-D is conditional on completing the holiday calendar lookup (I16, PARTIAL status).

5. **CRS rules are GPS-only**: CRS001/CRS002 require lat/lon from NYC MTA Bus. They are not evaluated on NYC TLC (zone-level only). H3-CRS001 and H3-CRS002 apply to the secondary dataset, not the primary evaluation.

6. **LocalPipeline ≠ Flink**: All hypotheses are designed for LocalPipeline evaluation. Distributed Flink results may differ. Latency hypotheses (implied by H3-StateMachine) are not testable on LocalPipeline.

---

## Statistical Testing Protocol

1. **Resampling**: 1,000 bootstrap iterations with replacement
2. **CI Type**: 95% percentile interval (standard bootstrap)
3. **Paired designs**: Preserve pairing in resampling units
4. **Multiple comparisons**: Bonferroni correction across RQs (α_adj = 0.01 for 6 RQs)
5. **Effect sizes**: Always report alongside p-values (Cohen's d for means, Kendall's W for rankings, Spearman ρ_s for correlations)
6. **Reproducibility**: Seed all random number generators; log seeds in evaluation run metadata
7. **Warmup**: 60 seconds of clean data (no injection) before each measurement window
8. **Measurement window**: 600 seconds (10 minutes) per trial
9. **Trials per condition**: 3 independent trials
10. **Match criterion**: Violation matches ground truth if `entity_index` matches exactly (not fuzzy)
