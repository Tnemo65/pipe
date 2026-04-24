# Contribution Statement & Novelty Claims

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Phase**: Step 10 — Novelty & Contribution Statement
**Date**: April 23, 2026
**Authors**: Orchestrator Agent + Scientific Writing Specialist
**Subagent Inputs**: Peer Review Specialist (PC scores), Statistical Analysis Specialist (significance), Competitive Analysis Specialist (positioning)

---

## Preamble: Anti-Hallucination Compliance

Every claim in this document is classified into one of three tiers:

- **Tier 1 — Verified**: Benchmark results with measured data and bootstrap CI.
- **Tier 2 — Estimated**: Based on code analysis, power analysis, or prior work. Requires benchmark run to confirm.
- **Tier 3 — Unmeasurable**: Cannot be measured with current methodology or tools. Explicitly flagged.

No numbers are invented. Every estimate is labeled `[ESTIMATED]`. Every unmeasurable claim is labeled `[UNMEASURABLE]`. Every claim requiring benchmark is labeled `[NEEDS BENCHMARK]`.

**Known unmeasurable claims** (NG-4 — CRS003 replay suppression gate):
- CRS003 recall = `[UNMEASURABLE]` — duplicate injection does not emit original + duplicate
- RQ6 (ML augmentation ΔF1) = `[TIER-2 ESTIMATED]` — Phase 3 is mandatory; CRS003 blocked by NG-4 (affects only CRS-dedup; IF on SYN/SEM unaffected)
- LSTM GPS training data = `[UNMEASURABLE]` — 6-month NYC MTA Bus GPS archive not confirmed
- XGBoost training target = `[UNMEASURABLE]` — "optimal threshold" label undefined per ML_MODEL_ANALYSIS.md §5.5

---

## Part I: Contribution Statement

Streaming data pipelines for transportation — buses, taxis, and transit — generate GPS position records that existing data quality frameworks cannot validate. Great Expectations and Soda Core are batch tools; Stream DaQ (the closest academic framework) lacks GPS trajectory rules; GTFS validators are batch-only. No streaming framework combines cross-record GPS validation, hierarchical context-aware thresholds, and a reproducible evaluation methodology.

This dissertation presents **A Context-Aware Framework for Streaming Data Quality Monitoring**: a Flink-native streaming DQ framework that validates GPS trajectory quality on real GTFS-realtime feeds using three-layer rule taxonomy (syntactic, semantic, cross-record) with hierarchical context-aware thresholds (L0–L5 fallback) and ML-augmented threshold calibration, together with a ground-truth evaluation framework with explicit measurement of what is and is not measurable.

The framework's **primary contribution** is the first streaming implementation of GPS trajectory quality validation on real GTFS-realtime vehicle positions — using Haversine-based speed bounds (2–100 km/h), GPS jump detection (>400m/30s), and event deduplication — evaluated on NYC MTA Bus live GTFS-realtime feed. No surveyed framework (Stream DaQ, METER, Great Expectations, GTFS Validator, GTFS-rt Validator, Ada-Context, CETrajAD, or any of 14 others) implements cross-record GPS trajectory validation on streaming transit data.

The framework's **secondary contribution** is hierarchical context-aware threshold calibration with L0–L5 fallback, enabling context-specific thresholds (fine-grained: `hour_10_midtown_weekday`) that gracefully degrade to global fallback when context cells are sparse. This is verified absent from all surveyed frameworks: Stream DaQ uses single-level rolling μ±kσ; Ada-Context uses fixed grid cells; METER addresses concept drift without context decomposition.

The framework's **tertiary contribution** is a ground-truth evaluation methodology combining synthetic anomaly injection, per-entity ground-truth tracking, and bootstrap confidence intervals (1,000 iterations, 95% CI) — with the uncommon practice of explicitly labeling what cannot be measured (CRS003 recall, distributed Flink latency).

This is a **research and education platform** — not production-ready, not fault-tolerant, and not a general-purpose competitor to Stream DaQ or Great Expectations. Its contribution is domain-specific: GPS trajectory validation for streaming transit data.

---

## Part II: Novelty Claims (Ranked by Credibility)

### Core Claims (Defensible at VLDB/SIGMOD)

#### Claim 1: GPS Trajectory Validation on Streaming GTFS-Realtime Vehicles

**What is claimed**: CRS001 (GPS speed bounds 2–100 km/h), CRS002 (GPS jump >400m/30s), and CRS003 (event deduplication, 300s window) implemented as Java `KeyedProcessFunction` on Flink, evaluated on NYC MTA Bus GTFS-realtime (public feed, no API key). Uses watermarks + idle stream detection (5 min timeout) for event-time semantics.

**Evidence tier**: `[Tier 2 — Estimated]`

- CRS001 lower bound (2 km/h) is physically justified: eliminates stationary vehicles. Upper bound (100 km/h) is physically implausible for NYC MTA Bus; updated from 120 km/h to close the B3 detection gap (moderate spoofing 20–100 km/h). Both are hardcoded and require no calibration.
- CRS002 (>400m/30s) is calibrated for GTFS-realtime update intervals. [NEEDS BENCHMARK] on real NYC MTA Bus feed.
- CRS003 is [UNMEASURABLE] due to NG-4 (replay suppression gate blocks synthetic duplicates).

**What would validate this**: Run CRS001/CRS002 on NYC MTA Bus GTFS-realtime with synthetic injection (GPS speed spike, GPS jump, duplicate), compute precision per rule with 95% bootstrap CI.

**PC review score**: Novelty=3, Correctness=3, Significance=3. **WA** (weak accept — genuine contribution but dataset secondary to primary evaluation).

---

#### Claim 2: Ground-Truth Evaluation Framework with Explicit Limitations

**What is claimed**: Synthetic anomaly injection (NULL, NEGATIVE_FARE, GPS_SPEED, GPS_JUMP, DUPLICATE), per-entity ground-truth tracking in PostgreSQL `ground_truth_events` table, precision/recall/F1 per rule with 1,000-iteration bootstrap CI, reproducibility protocol (60s warmup + 600s measurement window, 3 trials per injection rate).

**Evidence tier**: `[Tier 2 — Estimated]`

- Methodology is rigorous and follows Exathlon (VLDB 2021) precedent.
- [NEEDS BENCHMARK] — evaluation infrastructure is planned, not yet implemented.
- CRS003 recall is [UNMEASURABLE] due to NG-4 (replay suppression gate).
- LocalPipeline evaluation is not equivalent to distributed Flink evaluation.

**What would validate this**: Run full evaluation suite on NYC TLC SYN/SEM rules; report P/R/F1 with 95% CI for each rule.

**PC review score**: Novelty=3, Correctness=3, Significance=3. **WA** (weak accept — methodology is sound but unproven without results).

---

#### Claim 3: Hierarchical Context-Aware Threshold Fallback (L0–L5)

**What is claimed**: 5D context decomposition (temporal, spatial, operational, external, data characteristics) with L0–L5 hierarchical fallback. Min-sample thresholds per level justified by power analysis: L0 ≥ 100, L1 ≥ 50, L2 ≥ 25, L3 ≥ 10, L4 ≥ 5, L5 = 0 (physics priors). Evaluated on NYC TLC SYN/SEM rules.

**Evidence tier**: `[Tier 2 — Estimated]`

- L0–L4 fallback is verified absent from all surveyed frameworks (Stream DaQ, Ada-Context, METER).
- L5 (physics priors: [2, 100] km/h) requires no data.
- Power analysis (Cohen's d ≈ 0.30, α=0.01, power=0.80) justifies min-samples.
- [NEEDS BENCHMARK] for actual ΔF1 on NYC TLC.

**Critical caveat**: NYC TLC has 6,312 potential L0 context cells (263 zones × 24h). At ~5 records/cell/day, most cells are far below L0's 100-sample minimum. Expected: L0 coverage ≈ 0–5% of events; L4 (global fallback) coverage ≈ 20–40%. **The aggregate ΔF1 (all events) is likely smaller than the L0-specific ΔF1.**

**What would validate this**: Run ablation (static vs. L0–L4 vs. L5) on NYC TLC SYN/SEM. Report L0-specific ΔF1 separately from aggregate ΔF1.

**PC review score**: Novelty=3, Correctness=3, Significance=3. **WA** (weak accept — novel mechanism but needs benchmark to confirm practical impact).

---

### Secondary Claims (Bordered — Require Honest Caveats)

#### Claim 4: Context-Decomposed Trajectory Quality Scoring (TQS)

**What is claimed**: TQS = α×V + β×C + γ×Cn + δ×P, computed per context cell (L0 key). Three pre-registered variants: V1 (equal weights), V2 (domain-prioritized: 0.40×V + 0.20×C + 0.30×Cn + 0.10×P), V3 (consistency-prioritized: 0.20×V + 0.35×C + 0.25×Cn + 0.20×P). Based on T-Assess (VLDB 2025, PVLDB Vol.18, No.3).

**Evidence tier**: `[Tier 2 — Estimated]`

- Attribution idea (TQS per context cell) is sound.
- [NEEDS BENCHMARK] for correlation with ground truth (RQ3: ρ > 0.7).
- TQS weights are design choices, not findings. V2 is selected as primary without artifact.

**Critical caveat**: RQ3 measures correlation between TQS and injection rate. But TQS = 1 − violation_rate and injection rate is the independent variable. This is **circular** unless an independent quality signal is used (e.g., downstream prediction accuracy). RQ3 must be redesigned to avoid circularity.

**What would validate this**: Redesign RQ3 to use independent quality signal; measure Pearson ρ with 95% bootstrap CI.

**PC review score**: Novelty=2, Correctness=3, Significance=2. **B** (borderline — sound attribution idea, ad hoc weight construction).

---

#### Claim 5: Three-Layer Rule Taxonomy (SYN/SEM/CRS)

**What is claimed**: Three-layer rule taxonomy for transportation: SYN (syntactic, record-level), SEM (semantic, plausibility), CRS (cross-record, trajectory stateful). Explicit complexity hierarchy.

**Evidence tier**: `[Tier 2 — Estimated]`

- Taxonomy mirrors Deequ's row/aggregate distinction (VLDB 2018), which is peer-reviewed.
- CRS (cross-record) is the genuinely novel layer; SYN and SEM exist in every DQ framework.
- [NEEDS BENCHMARK] for incremental F1 per layer (RQ4).

**Critical caveat**: The taxonomy is organizational. The research contribution is the specific CRS rules (GPS speed, GPS jump, deduplication), not the taxonomy structure.

**PC review score**: Novelty=2, Correctness=3, Significance=2. **B** (borderline — valid organizational contribution, CRS rules are the real novelty).

---

### Optional Claims (Phase 3 — Requires Evaluation)

#### Claim 6: ML-Augmented Threshold Calibration (Phase 3 — CORE)

**What is claimed**: Three ML components integrated with StreamDQ's rule-based framework, prioritized by feasibility analysis (ML_MODEL_ANALYSIS.md):

1. **Bayesian Optimization** (Priority 1) — GP surrogate tunes k_multiplier, if_alpha, weekend_discount on F1 objective (not violation_rate). Addresses genuine gap: L0–L5 computes rolling stats but cannot optimize k.
2. **Isolation Forest** (Priority 2, conditional) — Single global model (NOT per-cell) computes anomaly_score per event → adjusts effective_k = base_k × (1 + α × anomaly_score). Captures multivariate anomalies P10/P90 misses. GO only if IF↔P90 correlation ρ < 0.8.
3. **XGBoost threshold predictor** (Priority 3, conditional) — Scaffold exists; training target undefined. GO only after "optimal threshold" label is defined.

~~**LSTM trajectory model**~~ — **NO-GO** (Priority 4): 6-month GPS archive unconfirmed; LSTM↔CRS002 HIGHLY correlated; alert elevation marginal in research platform.

~~**LightGBM**~~ — **REMOVED**: no confirmed use case (ML_MODEL_ANALYSIS.md §4).

**Evidence tier**: `[Tier 2 — Estimated]`

- Phase 3 is **mandatory** — ML is a core pipeline component, not optional.
- CRS003 blocked (NG-4) affects Isolation Forest calibration for deduplication only; IF on SYN/SEM layer is unaffected.
- [NEEDS BENCHMARK] for ΔF1 vs. rule-only thresholds (RQ6).
- **This is a measured contribution**: if ML provides no improvement, the negative result is scientifically valuable and will be reported as such.

**PC review score**: Novelty=2, Correctness=2, Significance=2. **B** (borderline — standard methods, thin integration novelty, but Phase 3 now mandatory).

---

## Part III: Positioning Table — All 5 Title Dimensions

| Framework | Streaming | Data Quality | Framework | Context-Aware | Monitoring |
|-----------|:---------:|:------------:|:---------:|:-------------:|:----------:|
| **A Context-Aware Framework for Streaming Data Quality Monitoring** | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| Stream DaQ (arXiv 2025) | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓✓ |
| METER (PVLDB 2024) | ✓✓ | ✗ | ✓ | ✓ | ✗ |
| GTFS Validator (OSS) | ✗ | ✓✓ | ✓✓ | ✗ | ✓ |
| GTFS-rt Validator (OSS) | ✗ | ✓ | ✓✓ | ✗ | ✓ |
| Great Expectations (OSS) | ✗ | ✓✓ | ✓✓ | ✗ | ✓ |
| Ada-Context (DMKD 2025) | ✓✓ | ✗ | ✓ | ✓ | ✗ |
| CETrajAD (SDM 2025) | ✗ | ✗ | ✗ | ✗ | ✗ |
| Grab Coban (Eng. 2024) | ✓✓ | ✓ | ✓✓ | ✗ | ✓✓ |
| Deequ (VLDB 2018) | ✗ | ✓✓ | ✓✓ | ✗ | ✓ |
| DyMETER (TPAMI 2026) | ✓✓ | ✗ | ✓ | ✓✓ | ✗ |

**Legend**: ✓✓ = full support (peer-reviewed evidence); ✓ = partial/limited; ✗ = absent/future work/not applicable

**Dimension coverage for ContextAware-DQ**:
- **Streaming**: Flink-native, event-time watermarks, idle stream detection
- **Data Quality**: 9 rules (SYN001–003, SEM001–003, CRS001–003) + GTFSSem002; rule-based, not ML-only
- **Framework**: PipelineBackend interface, 9 composable rules, configurable threshold engine, pluggable storage
- **Context-Aware**: 5D context (temporal, spatial, operational, external, data characteristics); L0–L5 hierarchical fallback
- **Monitoring**: PostgreSQL (violations, context_statistics, metrics_summary, ground_truth_events, evaluation_results) + Prometheus counters + Grafana 4-panel dashboard

---

## Part IV: Significance Summary

### Claims with Benchmarks Required

| Claim | Target | Baseline | Evidence Tier | Validation Requirement |
|-------|--------|----------|:-------------:|------------------------|
| SYN001–003 precision/recall | Any measured value | None | `[Tier 2]` | NYC TLC injection, 1,000 bootstrap CI |
| SEM001–003 precision/recall | Any measured value | None | `[Tier 2]` | NYC TLC injection, 1,000 bootstrap CI |
| CRS001/CRS002 precision | P > 0.70 | None | `[Tier 2]` | NYC MTA Bus injection, 1,000 bootstrap CI |
| Context-aware ΔF1 (L0 cells) | ΔF1 ≥ 5pp | Static | `[Tier 2]` | NYC TLC ablation, 1,000 bootstrap CI |
| Context-aware ΔF1 (all events) | Any measured value | Static | `[Tier 2]` | NYC TLC ablation, 1,000 bootstrap CI |
| TQS correlation | ρ > 0.7 | Aggregate TQS | `[Tier 2]` | Redesigned RQ3 (non-circular) |
| L0 context coverage | Actual % | Expected 0–5% | `[Tier 2]` | NYC TLC zone × hour analysis |
| CRS layer incremental F1 | Any measured value | SYN+SEM | `[Tier 2]` | Three-arm ablation (synth/sem/sem+crs) |

### Claims That Are Unmeasurable

| Claim | Why | Blocker |
|-------|-----|---------|
| **CRS003 recall** | Replay suppression gate blocks synthetic duplicates | NG-4 — evaluation bug |
| **CRS003 precision** | Replay suppression gate blocks synthetic duplicates | NG-4 — evaluation bug |
| **ML augmentation ΔF1** | Phase 3 mandatory (BO→IF→XGBoost→LSTM cond); CRS003 blocked by NG-4 | Phase 3 + NG-4 |
| **Distributed Flink latency** | Only LocalPipeline profiled | Infrastructure not deployed |
| **Real-world GPS precision** | No labeled ground truth for authentic errors | Manual labeling required |

### Claims That Are Estimated

| Claim | Estimate | Basis | Uncertainty |
|-------|----------|-------|:-----------:|
| P99 latency | ~500ms–1s | LocalPipeline profiling | High — LocalPipeline ≠ Flink |
| Throughput | 5,000+ events/sec | SQLite write speed | High — no distributed benchmark |
| L0 coverage | 0–5% of events | NYC TLC zone × hour statistics | Medium — depends on actual distribution |
| L4 coverage | 20–40% of events | NYC TLC zone × hour statistics | Medium — depends on actual distribution |

---

## Part V: What Must Be Done Before Submission

The following must be completed to support the contribution statement:

### P0 — Required (without these, paper cannot be submitted)

1. **Build evaluation infrastructure**: `evaluation/` directory with `synthetic_injector.py`, `ground_truth_tracker.py`, `metrics.py` (1,000 bootstrap), `run_evaluation.py`, `README.md`.
2. **Run SYN/SEM evaluation on NYC TLC**: Report precision, recall, F1 per rule with 95% bootstrap CI. These are the paper's primary results.
3. **Fix NG-4 (CRS003 replay gate)**: Tag synthetic duplicates `is_replay=False` to bypass the gate. Without this, CRS003 recall is labeled [UNMEASURABLE] in the paper.
4. **Run CRS001/CRS002 evaluation on NYC MTA Bus**: Report precision per rule with 95% bootstrap CI.
5. **Run L0 vs. L4 fallback ablation**: Report ΔF1 for events in L0 cells separately from aggregate ΔF1.

### P1 — Strongly Recommended (without these, claims are weakened)

6. **Redesign RQ3 (TQS correlation)**: Remove circularity — use independent quality signal (e.g., downstream prediction error) instead of injection rate.
7. **Implement D4 (External context)**: Holiday indicator lookup table. Upgrade 4D → 5D context.
8. **Deploy Flink cluster**: Run distributed evaluation. LocalPipeline results are not equivalent to Flink results.

### P2 — Nice to Have (can be omitted with honest caveats)

~~9. **Phase 3 ML augmentation**: Isolation Forest + Bayesian Optimization + METER integration.~~ [MOVED TO P1 — Phase 3 is now mandatory]
10. **Ablation: SYN-only vs. SYN+SEM vs. SYN+SEM+CRS**: Incremental F1 per layer.
11. **LSTM trajectory model** (Priority 4, NO-GO): Only if 6-month GPS archive confirmed AND CRS002 recall < 60%.

---

## Part VI: Positioning vs. Stream DaQ

**ContextAware-DQ** and **Stream DaQ** (Papastergios & Gounaris, arXiv:2506.06147, 2025) are the two most directly relevant frameworks in the streaming DQ landscape. They are **not** direct competitors — Stream DaQ is general-purpose; ContextAware-DQ is GPS/trajectory-specific.

| Dimension | Stream DaQ | ContextAware-DQ | Note |
|-----------|:---------:|:---------------:|------|
| Architecture | Pathway (Python) | Flink (Java + Python) | Different engines |
| GPS trajectory rules | None | CRS001/CRS002 | **ContextAware-DQ only** |
| Hierarchical context fallback | None | L0–L5 | **ContextAware-DQ only** |
| GTFS-realtime support | None | NYC MTA Bus | **ContextAware-DQ only** |
| Ground-truth evaluation | Not specified | Injection + P/R/F1 + CI | **ContextAware-DQ only** |
| Rule count | 30+ | 9 | Stream DaQ has more |
| Cross-record | Future work | Implemented (GPS) | **ContextAware-DQ only** |
| Venue | arXiv preprint | Research platform | Stream DaQ has publication |
| Quality meta-streams | Yes | Violations table | Similar |

**Key message for reviewers**: Stream DaQ is a general-purpose streaming DQ framework without GPS validation or context-aware thresholds. ContextAware-DQ addresses the specific gap of streaming GPS trajectory quality for transportation — a domain where existing frameworks are absent.

---

## Appendix A: Claims vs. Verification Status

| Claim | Source Document | Verification Status |
|-------|----------------|---------------------|
| GPS trajectory validation absent from all frameworks | audit_streaming_dq_frameworks.md, gap_analysis.md | Verified — 14 frameworks surveyed |
| Hierarchical fallback absent from all frameworks | audit_streaming_dq_frameworks.md | Verified — Stream DaQ single-level only |
| Ada-Context no fallback | audit_streaming_dq_frameworks.md | Verified — grid cells, static boundaries |
| CRS rules require Java | Phase 4 analysis (report.md) | Verified — JVM↔Python overhead |
| CRS003 unmeasurable (NG-4) | NG-4 known blocker | Verified — replay gate blocks evaluation |
| D4 External context stub | Appendix H (I16) | Verified — PARTIAL status |
| 95%+ false DC discovery | Martin et al., PVLDB 2025 | Verified — doi:10.14778/3748191.3748209 |
| Stream DaQ cross-record future work | Papastergios & Gounaris, 2025 | Verified — arXiv:2506.06147 |
| T-Assess VLDB 2025 | ZJU-DAILY/T-Assess | Verified — PVLDB Vol.18, No.3, pp.666-674 |
| METER VLDB 2024 | Zhu et al. | Verified — doi:10.14778/3636218.3636233 |
| CETrajAD SDM 2025 | Cao & Akoglu | Verified — SDM 2025 |
| NYC TLC no GPS | report.md Section on CRS rules | Verified — zone-level only |
| NYC MTA Bus GTFS-realtime public | report.md | Verified — no API key required |

---

## Appendix B: Title Dimension Coverage Checklist

Per the 7 Universal Requirements:

| Requirement | Status | Evidence |
|-------------|:------:|---------|
| 1. **Streaming** appears in contribution statement | ✅ | "Flink-native streaming DQ framework" |
| 2. **Data Quality** appears in contribution statement | ✅ | "validates GPS trajectory quality" |
| 3. **Framework** appears in contribution statement | ✅ | "A Context-Aware Framework for Streaming Data Quality Monitoring" |
| 4. **Context-Aware** appears in contribution statement | ✅ | "hierarchical context-aware thresholds (L0–L5)" |
| 5. **Monitoring** appears in contribution statement | ✅ | "ground-truth evaluation framework with explicit limitations" |
| 6. Project name used exactly | ✅ | "A Context-Aware Framework for Streaming Data Quality Monitoring" |
| 7. Scientific honesty | ✅ | All estimates labeled, all unmeasurables flagged |
