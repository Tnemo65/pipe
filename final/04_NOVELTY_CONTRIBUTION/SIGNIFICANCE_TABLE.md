# Significance Table: Quantifying Novelty Claims

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Reviewer Role**: Statistical Analysis Specialist
**Date**: April 23, 2026

---

## Methodology Note

All significance assessments follow these tiers:

- **Tier 1 — Verified**: Benchmark results with measured data and bootstrap CI.
- **Tier 2 — Estimated**: Based on code analysis, power analysis, or prior work. Needs benchmark run to confirm.
- **Tier 3 — Unmeasurable**: Cannot be measured with current methodology or tools. Must be explicitly flagged.

Per the scientific honesty rules (WC1–WC3), every number is labeled with its tier.

---

## 1. Per-Claim Significance Table

| # | Novelty Claim | Baseline | Expected Δ | Effect Size | 95% CI | Measurability | Validation Experiment |
|---|---------------|----------|:----------:|:-----------:|:-------:|:-------------:|----------------------|
| 1 | Hierarchical context-aware thresholds (L0→L5) | Static thresholds (SYN-layer P=0.229 on LocalPipeline) | ΔF1 ≥ 5pp for context-aware vs. static | Cohen's d ≈ 0.30 (from power analysis) | [NEEDS BENCHMARK] | **Tier 2 — Estimated** | Ablation: static vs. L0-L4 vs. L5 on NYC TLC SYN/SEM, 1,000 bootstrap resamples |
| 2 | ML-augmented threshold calibration | Rule-only thresholds | ΔF1 ≥ 5pp for rule+ML vs. rule-only | Unknown | [UNMEASURABLE] | **Tier 3 — Unmeasurable** | Phase 3 ablation study; CRS003 duplicate injection must be fixed first |
| 3 | Context-decomposed TQS | Aggregate TQS (single score) | ρ > 0.7 for context-decomposed vs. aggregate | Pearson ρ target | [NEEDS BENCHMARK] | **Tier 2 — Estimated** | RQ3: Pearson + Spearman ρ, 1,000 bootstrap, NYC TLC 5M records |
| 4 | Multi-dimensional threshold calibration | Single-dimension thresholds | ΔF1 ≥ 5pp for 5D vs. 1D | Unknown | [NEEDS BENCHMARK] | **Tier 2 — Estimated** | Ablation: 1D vs. 3D vs. 5D on NYC TLC; requires D4 (External) implementation |
| 5 | Flink-native event-time GPS validation | Micro-batch processing (500ms default) | Sub-second vs. minute-scale latency | Architectural difference | [ESTIMATED only] | **Tier 2 — Estimated** | Latency profiling on Flink on NYC MTA Bus stream |
| 6 | Three-layer rule taxonomy (CRS focus) | SYN-only coverage | CRS layer detects anomalies SYN misses | F1 increment per layer | [NEEDS BENCHMARK] | **Tier 2 — Estimated** | Three-arm ablation: SYN-only vs. SYN+SEM vs. SYN+SEM+CRS |
| 7 | Ground-truth evaluation framework | No standardized benchmark for streaming DQ | N/A (methodology, not improvement) | N/A | N/A | **Tier 2 — Estimated** | Full evaluation run: precision, recall, F1, bootstrap CI on NYC TLC |
| 8 | Domain-specific GTFS GPS validation | No GPS validation for GTFS-realtime | P > 0.70 for CRS001/CRS002 on NYC MTA Bus | Rule-level precision | [NEEDS BENCHMARK] | **Tier 2 — Estimated** | RQ5: ground truth injection on NYC MTA Bus, P/R/F1 per rule, 95% bootstrap CI |

---

## 2. Claims Requiring Benchmark to Support

The following claims cannot be accepted as findings until a benchmark run provides measured data:

### 2.1 Context-Aware Threshold Improvement (Claim 1)

**Claim**: "Hierarchical context-aware thresholds achieve ΔF1 ≥ 5pp over static thresholds."

| Aspect | Status |
|--------|--------|
| Target Δ | 5pp (F1) |
| Justification | Power analysis: Cohen's d ≈ 0.30 requires ~100 events/cell at L0 |
| NYC TLC L0 coverage | 0–5% of events (estimated from 263 zones × 24h × ~5 records/cell/day) |
| **Problem** | At 0–5% L0 coverage, 95–100% of events fall through to L1–L4 |
| **Expected actual Δ** | Likely < 2pp when averaged across ALL events (not just L0 cells) |
| Benchmark needed | Run ablation on NYC TLC: separate metrics for L0 cells vs. L1–L4 cells |

**Statistical Threat**: The 5pp target is based on power analysis for L0 cells. But most events don't fall into L0 cells. The aggregate ΔF1 (all events, not just L0) is likely smaller. The paper must report both: (a) ΔF1 for events in L0 cells, and (b) ΔF1 for all events.

**Flag**: **ESTIMATED — needs benchmark.** Do NOT claim "5pp improvement" as a finding. Report what the benchmark shows.

---

### 2.2 TQS Correlation (Claim 3)

**Claim**: "Context-decomposed TQS correlates better with ground truth than aggregate TQS (ρ > 0.7)."

| Aspect | Status |
|--------|--------|
| Target ρ | > 0.7 (Pearson correlation) |
| Baseline | Aggregate TQS (single score for all events) |
| RQ3 method | Pearson ρ + Spearman ρ_s, 1,000 bootstrap |
| **Problem 1** | "Ground truth" = injection rate (0%, 5%, 10%, 20%). TQS = 1 − violation_rate. This is circular. |
| **Problem 2** | TQS weights (V2: 0.40×V + 0.20×C + 0.30×Cn + 0.10×P) are arbitrary. Changing weights changes ρ. |
| **Problem 3** | CRS rules (C dimension) are GPS-only on NYC MTA Bus, NOT on NYC TLC. On NYC TLC, C is always 1.0. |

**Circularity Proof**:
```
TQS_composite = 1 - (SYN001_violations + SYN002_violations + CRS001_violations + ...) / total_events
injection_rate = N_injected / total_events
If violations ∝ injection_rate (as intended), then TQS_composite ∝ injection_rate.
Therefore: correlation(TQS_composite, injection_rate) is guaranteed to be high.
```

**Flag**: **CIRCULAR — RQ3 measures whether the evaluation methodology is self-consistent, not whether TQS captures quality.** RQ3 must be redesigned to measure TQS against an independent quality signal (e.g., downstream prediction accuracy), not against injection rate.

**Statistical Threat**: The 0% injection rate produces TQS=1.0 (no violations). 20% injection rate produces TQS=0.8 (20% violations). The correlation is guaranteed by the experimental design.

---

### 2.3 ML Augmentation (Claim 2)

**Claim**: "ML-augmented threshold calibration achieves ΔF1 ≥ 5pp over rule-only."

| Aspect | Status |
|--------|--------|
| Phase | Phase 3 (Weeks 11–13), explicitly marked optional |
| Baseline | Rule-only thresholds |
| **Problem 1** | CRS003 duplicate injection is broken (B2). Isolation Forest calibration for CRS003 cannot be measured. |
| **Problem 2** | Isolation Forest and Bayesian Optimization are standard methods. The claim is "integration is novel." This is thin. |
| **Problem 3** | METER (Zhu et al., PVLDB 2024) already does concept drift detection per context cell. How is the integration distinct? |
| **Problem 4** | If Phase 3 is deferred (deadline pressure), this claim disappears entirely. |

**Flag**: **UNMEASURABLE until Phase 3 is completed.** Even then, the improvement is uncertain. Report as "potential future contribution" rather than a core claim.

---

### 2.4 GPS Validation Precision (Claim 8)

**Claim**: "CRS rules achieve P > 0.70 on NYC MTA Bus GTFS-realtime."

| Aspect | Status |
|--------|--------|
| Target P | > 0.70 (precision, per rule) |
| Data source | NYC MTA Bus GTFS-realtime (public feed, no API key) |
| **Problem 1** | CRS001 speed bounds [2, 120] km/h are hardcoded. NYC MTA Bus urban speeds are typically 20–50 km/h. 120 km/h is far above the relevant range. |
| **Problem 2** | CRS002 GPS jump >100m/30s. GTFS-realtime updates are every 30s (not 1s as stated in some sections). If updates are every 30s, the "30s window" IS the update interval. |
| **Problem 3** | No GPS ground truth for NYC MTA Bus. Anomalies are injected synthetically. Real GPS errors in the feed are unknown. |
| **Problem 4** | The [2, 120] km/h range is validated for buses, not for all GTFS-realtime vehicles. Other vehicle types (subway, ferry) are out of scope. |

**Flag**: **ESTIMATED — needs benchmark on real NYC MTA Bus GTFS-realtime.** The precision target of 0.70 is plausible for CRS001/CRS002 on injected anomalies, but the real-world precision on authentic GPS errors is unknown.

---

### 2.5 Three-Layer Taxonomy (Claim 6)

**Claim**: "The CRS layer provides incremental F1 over SYN+SEM alone."

| Aspect | Status |
|--------|--------|
| Metric | Incremental F1 from adding CRS layer |
| **Problem 1** | CRS rules operate on NYC MTA Bus (GTFS-realtime). SYN/SEM rules operate on NYC TLC. These are different datasets. |
| **Problem 2** | CRS003 (deduplication) recall is UNMEASURABLE. The CRS layer evaluation is incomplete. |
| **Problem 3** | The "incremental F1" depends on the injection distribution. If CRS anomalies (GPS speed, GPS jump) are rare in real data, the incremental F1 may be negligible. |

**Flag**: **ESTIMATED — requires benchmark.** Report incremental F1 separately for CRS001/CRS002 (measurable) and CRS003 (unmeasurable due to B2).

---

## 3. Claims That Are Unmeasurable (Tier 3)

| Claim | Why Unmeasurable | Blocker |
|-------|-----------------|---------|
| **CRS003 recall** | Duplicate injection is broken (B2). Original + duplicate are not both emitted. | Implementation bug in `synthetic_injector.py` |
| **ML augmentation F1** | Phase 3 is optional; CRS003 is broken; no ablation framework yet | Phase 3 not started; B2 |
| **Real-world GPS precision** | No ground truth for authentic NYC MTA Bus GPS errors | Requires manual labeling of real GTFS-realtime feed |
| **End-to-end Flink latency** | Only LocalPipeline benchmarked; distributed Flink not tested | Infrastructure not deployed |

---

## 4. Statistical Threats to Validity

### 4.1 Internal Validity Threats

| Threat | Affected Claims | Mitigation |
|--------|:---------------:|------------|
| **Synthetic anomaly distribution** | All evaluation claims | Report injection rate separately; acknowledge generalizability limitation |
| **Circular RQ3** | TQS correlation | Redesign RQ3 to use independent quality signal |
| **LocalPipeline ≠ Flink** | Latency, throughput claims | Clearly label as LocalPipeline results; do not claim Flink performance |
| **CRS003 unmeasurable** | CRS layer evaluation | Report CRS001/CRS002 separately; flag CRS003 as unmeasurable |
| **B2 blocks CRS003** | CRS003 recall, RQ6 (ML) | Fix B2 before evaluation; otherwise document as known limitation |

### 4.2 External Validity Threats

| Threat | Affected Claims | Mitigation |
|--------|:---------------:|------------|
| **NYC TLC zone-level only** | CRS001/CRS002 on TLC | Clearly scope CRS to NYC MTA Bus; SYN/SEM to NYC TLC |
| **Single dataset** | Generalizability | Acknowledge NYC TLC is one domain; NYC MTA Bus is second domain |
| **Synthetic anomalies** | Real-world performance | Acknowledge injected anomalies may not match real error patterns |

### 4.3 Statistical Design Threats

| Threat | Affected Claims | Mitigation |
|--------|:---------------:|------------|
| **α inflation** | All RQs | Bonferroni correction (α_adj = 0.01 for 6 RQs) |
| **Underpowered L0 cells** | RQ1 ΔF1 | Report L0-specific ΔF1 separately from aggregate ΔF1 |
| **Paired vs. unpaired** | RQ1 ablation | Wilcoxon signed-rank (paired) is correct; verify same injection seed |
| **Bootstrap iterations** | All CI | 1,000 iterations minimum (current standard) |

---

## 5. Effect Size Analysis

### 5.1 RQ1: Context-Aware vs. Static Thresholds

**Expected**: ΔF1 ≥ 5pp (target, from power analysis)
**Baseline**: SYN-layer P=0.229 (LocalPipeline, NYC TLC)

| Scenario | Expected ΔF1 | Cohen's d | Interpretation |
|----------|:------------:|:---------:|----------------|
| L0 cells only (5% of events) | 5–10pp | 0.30–0.50 | Medium effect |
| L0+L1 cells (15% of events) | 3–5pp | 0.20–0.30 | Small-to-medium effect |
| All events (including L4 fallback) | 1–3pp | 0.10–0.20 | Small effect |
| **Most likely (all events)** | **1–2pp** | **0.10–0.15** | **Small effect** |

**Critical insight**: The 5pp target is achievable only for events in L0 cells. The paper MUST report both L0-specific and aggregate ΔF1. Claiming "5pp improvement" as an overall finding when most events fall through to L4 would be misleading.

**Recommended language**: "On events in L0 context cells (5% of data), context-aware thresholds improve F1 by Xpp (95% CI: [a, b]). On all events including those falling through to L4 fallback, the aggregate improvement is Ypp (95% CI: [c, d])."

---

### 5.2 RQ5: CRS Rule Precision on NYC MTA Bus

**Expected**: P > 0.70 (target)

| Rule | Expected P | Reason |
|------|:----------:|--------|
| CRS001 (speed) | 0.80–0.90 | Hardcoded [2, 120] km/h; physically grounded; hard to false-positive |
| CRS002 (GPS jump) | 0.70–0.85 | 100m/30s threshold is conservative; requires consecutive positions |
| CRS003 (dedup) | **UNMEASURABLE** | B2: duplicate injection broken |
| **Overall CRS** | **0.75–0.85** | Weighted average; CRS003 excluded |

**Note**: Precision is expected to be high because hardcoded thresholds are conservative. Recall is more uncertain and requires ground truth injection.

---

## 6. Summary: What Is Measurable vs. Unmeasurable

### Measurable (Tier 1 — after benchmark)

| Metric | Method | CI Required |
|--------|--------|:-----------:|
| SYN001–003 precision/recall | Synthetic injection on NYC TLC | 95% bootstrap CI |
| SEM001–003 precision/recall | Synthetic injection on NYC TLC | 95% bootstrap CI |
| CRS001/CRS002 precision | Synthetic injection on NYC MTA Bus | 95% bootstrap CI |
| L0 context coverage | NYC TLC zone × hour analysis | Descriptive only |
| TQS correlation (RQ3) | Pearson ρ, 1,000 bootstrap | 95% CI (but see circularity issue) |
| RQ1 ΔF1 (L0 cells only) | Ablation: static vs. context-aware | 95% bootstrap CI |
| RQ1 ΔF1 (all events) | Ablation: static vs. context-aware | 95% bootstrap CI |

### Unmeasurable (Tier 3 — documented limitations)

| Metric | Reason | Blocker |
|--------|--------|---------|
| CRS003 recall | Duplicate injection broken | B2 |
| CRS003 precision | Duplicate injection broken | B2 |
| ML augmentation ΔF1 | Phase 3 optional; CRS003 broken | Phase 3 + B2 |
| Real-world GPS precision | No labeled real GTFS errors | Manual labeling required |
| Distributed Flink latency | Infrastructure not deployed | Not built |
| End-to-end throughput | Only LocalPipeline benchmarked | Not built |

### Estimated (Tier 2 — use cautiously)

| Metric | Estimate Basis | Uncertainty |
|--------|:-------------:|:-----------:|
| P99 latency | LocalPipeline profiling | High — LocalPipeline ≠ Flink |
| Throughput | SQLite write speed | High — no distributed benchmark |
| CRS rule coverage | NYC MTA Bus feed analysis | Medium — depends on feed quality |
| L0 cell coverage | NYC TLC zone × hour statistics | Medium — depends on actual data distribution |
