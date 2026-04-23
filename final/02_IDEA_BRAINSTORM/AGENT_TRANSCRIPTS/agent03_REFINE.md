# AGENT-3: REFINE — Name Fit Analysis & Scoping Recommendations

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Input**: `/home/dtl/Documents/pipe/final/02_IDEA_BRAINSTORM.md`
**Date**: April 22, 2026
**Agent**: REFINE (Contribution Framing + Positioning Specialist)

---

## Executive Summary

This document scores 6 candidate ideas against the fixed thesis name across 4 dimensions: **Context-Aware**, **Framework**, **Streaming**, and **Data Quality Monitoring**. Scoring is strict and evidence-based. Only ideas scoring ≥10/12 are flagged as EXCELLENT FIT; ≤7/12 are flagged as POOR FIT.

**Top Finding**: IDEA-NEW-2 (T-Assess × ContextAware-DQ Integration) scores **12/12** — the only idea that fully satisfies all four dimensions. IDEA-07 (Benchmark) scores **10/12** — EXCELLENT FIT as a framework contribution. The remaining four ideas score 8-9/12 — MEDIUM FIT with significant scoping gaps.

---

## Phase A — Name Fit Analysis

### Scoring Rubric

| Component | Score 3 | Score 2 | Score 1 |
|-----------|---------|---------|---------|
| **Context-Aware** | Adaptive thresholds / contextual rules / hierarchical fallback | Partially context-aware (some adaptive elements) | Static, no context awareness |
| **Framework** | Full framework (multiple integrated components) | Partial framework (some components, gaps) | Single method only |
| **Streaming** | True streaming-native (Kafka/Spark Structured Streaming) | Micro-batch or pseudo-streaming | Batch or offline |
| **Data Quality Monitoring** | Core DQ focus (quality rules + violation reporting + confidence scoring) | Adjacent to DQ (validation but not full monitoring) | Not DQ (prediction, anomaly detection) |

---

### IDEA-NEW-2: T-Assess × ContextAware-DQ Integration

**What it is**: Integrate T-Assess (under review at VLDB 2025) trajectory quality scoring with ContextAware-DQ's SYN/SEM/CRS rule taxonomy. Rule violations map to quality dimensions; quality scores aggregate violations.

| Component | Score | Evidence |
|-----------|-------|----------|
| **Context-Aware** | **3** | T-Assess quality dimensions (validity, completeness, consistency, fairness) are inherently contextual — they aggregate rule violations by dimension. ContextAware-DQ's adaptive engine (rolling P10/P90) provides threshold context. Together: context-aware quality scoring. |
| **Framework** | **3** | Full integration of two systems: ContextAware-DQ rule engine + T-Assess scoring layer + dimension mapper. Multiple components: rules, violations, dimension mapper, TQS aggregator, confidence scorer. |
| **Streaming** | **3** | ContextAware-DQ is Spark Structured Streaming. T-Assess explicitly supports "online (real-time stream) evaluation." Both systems are streaming-native. |
| **Data Quality Monitoring** | **3** | Core DQ: rules detect violations, violations degrade TQS, TQS explains quality. Explicit violation reporting + quality scoring + confidence signal = full DQ monitoring. |

**Total: 12/12 — EXCELLENT FIT**

**Key strength**: IDEA-NEW-2 is the only idea that fully activates every dimension of the project name. The integration creates a closed-loop: rules → violations → scores → explainability. This is precisely what "Context-Aware Framework for Streaming Data Quality Monitoring" means.

**Key risk**: TQS weighting scheme must be pre-registered to avoid multiple-comparisons inflation. The dimension mapper must be explicitly defined before implementation.

---

### IDEA-07: Streaming Transportation DQ Evaluation Benchmark

**What it is**: Build benchmark infrastructure (synthetic GTFS-RT generator + evaluation harness) for streaming transportation DQ. Addresses GAP-02 and GAP-12.

| Component | Score | Evidence |
|-----------|-------|----------|
| **Context-Aware** | **2** | The benchmark can include context-aware evaluation (context-stratified metrics, context-specific thresholds). But the benchmark *framework* itself does not enforce context-awareness — it measures whatever is implemented. Partially fits. |
| **Framework** | **3** | Benchmark infrastructure is inherently a framework: data generator + anomaly injector + evaluation harness + metrics dashboard. Multiple integrated components. |
| **Streaming** | **3** | Benchmark explicitly measures streaming DQ frameworks. NYC TLC replay + GTFS-RT live streaming are the test data. Fully streaming-native. |
| **Data Quality Monitoring** | **2** | Benchmark *measures* DQ monitoring but is not itself a DQ monitor. It evaluates the quality of DQ monitoring. Adjacent to DQ — not core DQ. |

**Total: 10/12 — EXCELLENT FIT**

**Key strength**: Benchmark papers (Exathlon, VLDB 2021) are among the most durable contributions in data systems. The infrastructure serves as the evaluation backbone for all other ideas. Strong framework contribution.

**Key risk**: NUMOSIM anomaly types map imperfectly to DQ rule types. The benchmark measures DQ quality, but the mapping must be validated. Community adoption is uncertain — though first evaluation is achievable regardless.

**Scoping note**: The benchmark alone is not a "context-aware" contribution. It measures context-aware rules if they are implemented. This is a MEDIUM FIT for the Context-Aware dimension.

---

### IDEA-04: GTFS-RT Cross-Entity Validator

**What it is**: Validate consistency across VehiclePosition, TripUpdate, and Alert entities in streaming GTFS-RT data. Cross-entity semantic integration is the core challenge.

| Component | Score | Evidence |
|-----------|-------|----------|
| **Context-Aware** | **2** | Cross-entity validation requires spatial-temporal context (vehicle position must match trip schedule). But the rules themselves are static — no adaptive thresholds or contextual fallback. Partially context-aware via GTFS static reference joins. |
| **Framework** | **2** | Requires multiple components: protobuf parser, entity correlator, consistency checker, violation reporter. But these are extensions of the existing ContextAware-DQ engine, not a full framework. Partial framework. |
| **Streaming** | **3** | Streaming-native GTFS-RT validation. CRS pre-investigation requires Spark Structured Streaming. Explicitly streaming. |
| **Data Quality Monitoring** | **2** | Core DQ validation — but limited to cross-entity consistency checking. No quality scoring, no confidence aggregation, no explainability layer. Partial DQ monitoring. |

**Total: 9/12 — MEDIUM FIT (OVERSCO**)

**Scoping diagnosis**: OVERSCOPED in novelty, UNDERSCOPED in framework breadth. The idea is too narrow (only GTFS-RT cross-entity validation) to be a full "framework" contribution, yet the engineering complexity (protobuf + multi-stream correlation) is high.

**Scoping recommendation**: Reduce to a **rule type** within the ContextAware-DQ framework rather than a standalone idea. Express cross-entity checks as CRS rules (CRS-EXT-001: VehiclePosition ↔ TripUpdate consistency, CRS-EXT-002: TripUpdate ↔ Alert consistency). Implement as 2-3 rules in the existing CRS module. This keeps the novel contribution (cross-entity validation for GTFS-RT) while reducing scope to fit the framework model.

**Title fit**: "A Context-Aware Framework for Streaming Data Quality Monitoring: Cross-Entity Consistency Validation for GTFS Realtime" — works if scoped as rules, not a standalone system.

---

### IDEA-02: Physics-Constrained Calibration

**What it is**: Instead of unconstrained threshold discovery (Martin et al., 95% FP), constrain the hypothesis space to physically valid ranges, then calibrate thresholds from data.

| Component | Score | Evidence |
|-----------|-------|----------|
| **Context-Aware** | **2** | Physics constraints provide hard bounds (e.g., no vehicle > 200 km/h), which are a form of contextual prior. But the calibration itself is a single static method — not a multi-level contextual system with fallback hierarchies. |
| **Framework** | **1** | This is a single calibration *method*, not a framework. It does not integrate multiple components. No violation reporting, no quality scoring, no explainability. Only the threshold calibration step. |
| **Streaming** | **3** | Calibration operates in streaming context. Rolling statistics (P10/P90) are computed from streaming data. Fully streaming-native. |
| **Data Quality Monitoring** | **2** | The method improves DQ rule accuracy, but it is a component *within* a DQ monitoring system, not a DQ monitoring system itself. Adjacent to DQ. |

**Total: 8/12 — MEDIUM FIT (UNDERSCOPED)**

**Scoping diagnosis**: UNDERSCOPED. IDEA-02 is a single method that improves threshold calibration. It is not a framework and cannot stand alone as the main thesis contribution. It is a component-level improvement.

**Scoping recommendation**: Promote IDEA-05 (Contextual Calibration) instead, which subsumes IDEA-02's concept but adds multi-dimensional context (temporal, spatial, operational). Frame IDEA-02 as the **ablation study** for IDEA-05: "Physics-constrained calibration as a special case of contextual calibration." This gives IDEA-02 a role without treating it as a standalone contribution.

**Title fit**: Does not fit "Framework" dimension. Cannot serve as primary thesis idea.

---

### IDEA-NEW-3: Incremental DCs for GPS

**What it is**: Express ContextAware-DQ CRS rules as formal Denial Constraints (DCs), use [REMOVED: [] citation pending verification] incremental detection framework adapted for GPS-specific predicates.

| Component | Score | Evidence |
|-----------|-------|----------|
| **Context-Aware** | **2** | DCs are declarative constraints — they express *what* must hold, not *when* or *how*. Incremental DC enforcement is context-sensitive (previous state matters), but there is no adaptive threshold or contextual fallback. Partially context-aware. |
| **Framework** | **2** | DC parser + DC evaluator + GPS predicate optimizer + violation reporter. Multiple components, but they are tightly coupled to the DC engine — not a broadly reusable framework. Partial framework. |
| **Streaming** | **3** | [REMOVED: [] citation pending verification] is explicitly an incremental streaming DC detection system. GPS adaptation maintains streaming semantics. |
| **Data Quality Monitoring** | **2** | Formal DC enforcement is a rigorous form of DQ validation. But the contribution is the *formalization* of GPS rules as DCs, not a full DQ monitoring pipeline with scoring and reporting. |

**Total: 9/12 — MEDIUM FIT (OVERSCO**)

**Scoping diagnosis**: OVERSCOPED in theoretical depth, UNDERSCOPED in DQ monitoring breadth. Formal DC expression of GPS rules is a research contribution in its own right (PODS/ICDT level), but it does not constitute a full "framework" for streaming DQ monitoring.

**Scoping recommendation**: Defer to Phase 2 as a **theoretical component** of IDEA-NEW-2 or IDEA-07. Express CRS rules as formal DCs as part of the evaluation methodology (formal vs. procedural GPS rule enforcement). This preserves the novel contribution (GPS-specific DC formalization) without treating it as a standalone thesis idea.

**Title fit**: "Context-Aware Framework" requires adaptive thresholds and multi-level reasoning. DCs are declarative but not inherently context-aware.

---

### IDEA-05: Contextual Calibration

**What it is**: Calibrate DQ thresholds using multi-dimensional context (temporal: rush hour vs. night; spatial: highway vs. urban; operational: weekday vs. weekend).

| Component | Score | Evidence |
|-----------|-------|----------|
| **Context-Aware** | **3** | Multi-dimensional context is the core of this idea. Hierarchical fallback (context-rich → context-poor → physics prior) is inherently context-aware. Directly activates the "Context-Aware" dimension. |
| **Framework** | **1** | Single calibration method. No violation reporting, no quality scoring, no multi-component integration. Framework score: 1. |
| **Streaming** | **3** | Calibration operates on streaming data with rolling statistics. Context cells are updated continuously. Streaming-native. |
| **Data Quality Monitoring** | **2** | Improved thresholds → better violation detection → better DQ monitoring. But the contribution is the calibration method, not the monitoring system. Adjacent to DQ. |

**Total: 9/12 — MEDIUM FIT (UNDERSCOPED)**

**Scoping diagnosis**: UNDERSCOPED. IDEA-05 activates Context-Aware and Streaming perfectly, but scores only 1/3 on Framework. A single calibration method cannot carry the "Framework" label in a thesis title.

**Scoping recommendation**: Combine IDEA-05 with IDEA-NEW-2 (T-Assess × ContextAware-DQ). The T-Assess integration provides the framework; IDEA-05's contextual calibration provides the context-aware thresholds within that framework. IDEA-05 becomes the **threshold calibration module** of the integrated system.

**Title fit**: Cannot serve as standalone primary idea. Must be embedded within a framework idea.

---

### Phase A Summary Table

| Idea | Context-Aware (3) | Framework (3) | Streaming (3) | DQ Monitoring (3) | Total | Fit Level |
|------|:-----------------:|:-------------:|:-------------:|:----------------:|:-----:|-----------|
| IDEA-NEW-2 | 3 | 3 | 3 | 3 | **12** | EXCELLENT |
| IDEA-07 | 2 | 3 | 3 | 2 | **10** | EXCELLENT |
| IDEA-04 | 2 | 2 | 3 | 2 | **9** | MEDIUM (OVERSCOPED) |
| IDEA-05 | 3 | 1 | 3 | 2 | **9** | MEDIUM (UNDERSCOPED) |
| IDEA-NEW-3 | 2 | 2 | 3 | 2 | **9** | MEDIUM (OVERSCOPED) |
| IDEA-02 | 2 | 1 | 3 | 2 | **8** | MEDIUM (UNDERSCOPED) |

**Critical finding**: 4 of 6 ideas score ≤9/12. The primary weakness is **Framework** (4 ideas score 1-2/3) and **DQ Monitoring** (all 6 score 2/3). These ideas are method contributions masquerading as framework contributions.

---

## Phase B — Scoping Recommendations

### IDEA-NEW-2: T-Assess × ContextAware-DQ Integration — EXCELLENT FIT

**Status**: No scope change needed. Fully scoped.

**Recommended scope boundaries**:
- **In scope**: ContextAware-DQ → T-Assess dimension mapper, TQS aggregation (validity, completeness, consistency, fairness), quality degradation curves, confidence scoring, synthetic ground truth evaluation with bootstrap CI
- **Out of scope**: Modifying T-Assess internals, distributed TQS computation, user study for operator usefulness
- **Pre-registration required**: TQS weighting scheme (define 3 variants a priori; do not select post-hoc without correction)

---

### IDEA-07: Streaming Transportation DQ Benchmark — EXCELLENT FIT

**Status**: Well-scoped but needs Context-Aware anchoring.

**Recommended scope boundaries**:
- **In scope**: NYC TLC replay harness, GTFS-RT synthetic generator, NUMOSIM → DQ rule type mapping (must be explicit), precision/recall/latency metrics, reproducibility documentation
- **Out of scope**: Community adoption, interactive dashboard, multi-framework comparison (ContextAware-DQ only for initial version)
- **Critical gap**: The benchmark measures DQ quality but does not itself demonstrate "Context-Aware." Recommend including IDEA-05's contextual calibration as a benchmarked component — i.e., "evaluate ContextAware-DQ with and without contextual calibration on the benchmark."

---

### IDEA-04: GTFS-RT Cross-Entity Validator — MEDIUM FIT (OVERSCOPED)

**Status**: Reduce from standalone idea to rule type.

**Recommended scope boundaries**:
- **Reduce to**: 2-3 CRS rules in the existing cross_record.py module
  - `CRS-EXT-001`: VehiclePosition vehicle_id must appear in corresponding TripUpdate
  - `CRS-EXT-002`: VehiclePosition stop_id must match TripUpdate.stop_id for current trip
  - `CRS-EXT-003`: Alert active_period must overlap with TripUpdate timestamp
- **Out of scope**: Standalone GTFS-RT validation system, protobuf-native streaming parser
- **Implementation path**: Extend existing gtfs_live.py producer to emit typed events, implement cross-entity checks as CRS rules

**Title fit**: Works as "Cross-Entity Consistency Rules for GTFS Realtime" within the framework, not as a standalone contribution.

---

### IDEA-05: Contextual Calibration — MEDIUM FIT (UNDERSCOPED)

**Status**: Promote to threshold calibration module within IDEA-NEW-2.

**Recommended scope boundaries**:
- **Reduce to**: Threshold calibration module for ContextAware-DQ
  - Multi-dimensional context cells (time-of-day × day-of-week × road type)
  - Hierarchical fallback: context-rich → context-poor → physics prior
  - Ablation: contextual vs. static vs. rolling thresholds
- **Embed within**: IDEA-NEW-2 (T-Assess × ContextAware-DQ) as the threshold adaptation layer
- **Out of scope**: Standalone deployment, distributed context store

**Title fit**: Works as "Contextual Threshold Calibration" within the framework, not as a standalone contribution.

---

### IDEA-NEW-3: Incremental DCs for GPS — MEDIUM FIT (OVERSCOPED)

**Status**: Defer to Phase 2 as theoretical component of IDEA-07.

**Recommended scope boundaries**:
- **Reduce to**: Formal DC expression of CRS001 (speed) and CRS002 (GPS jump) as evaluation comparison — "formal DC enforcement vs. procedural GPS rules"
- **Timeline**: Phase 2, after IDEA-NEW-2 and IDEA-07 are validated
- **Out of scope**: Full [] implementation, distributed DC engine

---

### IDEA-02: Physics-Constrained Calibration — MEDIUM FIT (UNDERSCOPED)

**Status**: Reclassify as ablation study for IDEA-05.

**Recommended scope boundaries**:
- **Reduce to**: Ablation component — "Physics-constrained calibration as a special case of contextual calibration (uniform context, physics prior only)"
- **Evidence needed**: Ablation results showing whether physics constraints improve over rolling P10/P90 in context-poor cells
- **Out of scope**: Standalone thesis contribution

---

## Phase C — Component Integration Analysis

### Combination 1: IDEA-NEW-2 + IDEA-10 (Confidence Scoring)

**Compatible?** YES — IDEA-10's confidence scoring is a natural output layer for IDEA-NEW-2. TQS → operational confidence score is a direct mapping.

**Timeline overlap?** YES — both are implementable in the same phase. IDEA-10 is simpler (3/5 complexity); IDEA-NEW-2 is more complex but higher-value. Implement IDEA-NEW-2 first; IDEA-10 is the final output aggregation step.

**Framing fit?** EXCELLENT — IDEA-NEW-2 provides the quality dimensions (validity, completeness, consistency, fairness). IDEA-10 aggregates these into a single operational confidence metric. Together: "rules detect → violations degrade scores → scores produce confidence signal." This is the full DQ monitoring pipeline.

**Recommended**: Combine. IDEA-10 is a 1-week implementation; IDEA-NEW-2 is the 8-10 week core. Frame IDEA-10 as the "operational output layer" of the integrated system.

---

### Combination 2: IDEA-07 + IDEA-04

**Compatible?** PARTIAL — IDEA-07 provides the evaluation infrastructure; IDEA-04 provides a novel rule type to evaluate. The benchmark can evaluate cross-entity validation accuracy.

**Timeline overlap?** NO CONFLICT — IDEA-07 is evaluation infrastructure (foundational); IDEA-04 is a rule type built *on top of* the infrastructure. Must build IDEA-07 first.

**Framing fit?** WEAK — IDEA-07 (Benchmark) and IDEA-04 (Cross-Entity Validator) are both "framework" ideas but serve different purposes. IDEA-07 is infrastructure; IDEA-04 is an application. Combining them creates scope ambiguity: is the thesis about the benchmark or about cross-entity validation?

**Recommended**: Keep separate. IDEA-07 is the evaluation backbone (Phase 1). IDEA-04 (reduced to CRS rules) is evaluated *on* IDEA-07. They are sequential, not parallel.

---

### Combination 3: IDEA-02 + IDEA-05

**Compatible?** YES — IDEA-02 (physics-constrained) is a special case of IDEA-05 (contextual calibration). Physics constraints provide the fallback for context-poor cells.

**Timeline overlap?** YES — same phase. IDEA-05 first; IDEA-02 as ablation comparison.

**Framing fit?** GOOD — "Contextual Calibration with Physics-Constrained Fallback" is a coherent framing. IDEA-05 provides the multi-dimensional context; IDEA-02 provides the physics priors for sparse cells.

**Recommended**: Combine into single "Contextual Calibration" idea with IDEA-02 as an ablation study. Prevents redundancy and clarifies the contribution.

---

### Combination 4: IDEA-NEW-2 + IDEA-07

**Compatible?** YES — IDEA-07 (Benchmark) is the evaluation infrastructure; IDEA-NEW-2 (T-Assess × ContextAware-DQ) is the system being evaluated. The benchmark measures IDEA-NEW-2's performance.

**Timeline overlap?** YES — IDEA-07 must be built first (evaluation infrastructure). IDEA-NEW-2 uses IDEA-07 as its evaluation harness.

**Framing fit?** EXCELLENT — This is the natural thesis structure:
- IDEA-07: "We build a benchmark for streaming transportation DQ"
- IDEA-NEW-2: "We evaluate our T-Assess × ContextAware-DQ integration on this benchmark"
- The benchmark is both the evaluation methodology AND a standalone durable contribution

**Recommended**: Build IDEA-07 first (Phase 1), then use it to evaluate IDEA-NEW-2 (Phase 2). The thesis has two contributions: (1) benchmark infrastructure, (2) T-Assess × ContextAware-DQ integration evaluated on the benchmark.

---

### Integration Summary Table

| Combination | Compatible | Timeline | Framing Fit | Recommendation |
|-------------|:----------:|:--------:|:-----------:|----------------|
| IDEA-NEW-2 + IDEA-10 | YES | Parallel | EXCELLENT | **Combine** — output layer |
| IDEA-07 + IDEA-04 | PARTIAL | Sequential | WEAK | **Keep separate** — sequential |
| IDEA-02 + IDEA-05 | YES | Parallel | GOOD | **Combine** — ablation study |
| IDEA-NEW-2 + IDEA-07 | YES | Sequential | EXCELLENT | **Combine** — thesis structure |

---

## Phase D — Title Recommendation

### TOP IDEA: IDEA-NEW-2 (T-Assess × ContextAware-DQ Integration)

**Recommended Thesis/Paper Title**:

> **A Context-Aware Framework for Streaming Data Quality Monitoring: Integrating Rule-Based Validation with Trajectory Quality Scoring**

**Alternative (if IDEA-07 benchmark is primary contribution)**:

> **A Context-Aware Framework for Streaming Data Quality Monitoring: Benchmark Infrastructure and Trajectory-Level Quality Evaluation**

**Rationale for primary title**:
1. "Context-Aware" — T-Assess quality dimensions (validity, completeness, consistency, fairness) are inherently contextual aggregations of rule violations. IDEA-05's contextual calibration adds threshold context.
2. "Framework" — Full integration of: ContextAware-DQ rule engine → violation detector → dimension mapper → TQS aggregator → confidence scorer. Multiple components, not a single method.
3. "Streaming Data Quality Monitoring" — Rules detect violations in real-time; violations degrade TQS; TQS explains quality. Full closed-loop monitoring pipeline.
4. "Integrating Rule-Based Validation with Trajectory Quality Scoring" — Explicitly names the novel integration (rule-based DQ + statistical quality scoring) as the contribution.

**Why not shorter**: The integration contribution is the key differentiator. A generic title ("Context-Aware Streaming DQ Framework for Transportation") obscures the novel T-Assess × ContextAware-DQ integration, which is the VLDB 2025-grounded contribution.

---

## Critical Findings

### Finding 1: Framework Score Is the Primary Bottleneck

4 of 6 ideas score 1-2/3 on the Framework dimension. This is the thesis title's most demanding component — "Framework" implies multiple integrated components, not a single method. Ideas that score 1/3 on Framework cannot serve as the primary thesis contribution regardless of their novelty or feasibility.

**Recommendation**: Every surviving idea must be embedded within a framework context. IDEA-NEW-2 is the only idea that achieves this naturally. All other ideas should be positioned as **components** of IDEA-NEW-2, not standalone contributions.

### Finding 2: IDEA-NEW-2 Has No Scoping Issues

IDEA-NEW-2 is the only idea that:
- Fully activates all four dimensions of the project name (12/12)
- Has a VLDB 2025 citation (T-Assess) grounding the novelty claim
- Has LOW evaluation risk (synthetic ground truth, standard metrics)
- Is implementable at API level (both systems exist)

**Recommendation**: Commit to IDEA-NEW-2 as the primary thesis contribution. All other ideas become components, ablation studies, or Phase 2 deferrals.

### Finding 3: IDEA-07 and IDEA-NEW-2 Are Naturally Complementary

IDEA-07 (Benchmark) and IDEA-NEW-2 (T-Assess × ContextAware-DQ) form a coherent two-contribution thesis:
- **Contribution 1**: Streaming Transportation DQ Benchmark — evaluation methodology as durable infrastructure
- **Contribution 2**: T-Assess × ContextAware-DQ Integration — system evaluated on the benchmark

This structure provides both a methodology contribution (benchmark) and a systems contribution (integration), satisfying both VLDB systems-track and SIGMOD research-track reviewer expectations.

### Finding 4: Four Ideas Should Be Deferred or Reduced

| Idea | Action | Reason |
|------|--------|--------|
| IDEA-04 | REDUCE to CRS rules | OVERSCOPED — standalone GTFS-RT system is too narrow for "framework" |
| IDEA-05 | COMBINE with IDEA-02 | UNDERSCOPED — single calibration method; becomes threshold module |
| IDEA-NEW-3 | DEFER to Phase 2 | OVERSCOPED — theoretical DC formalization; good paper, not thesis |
| IDEA-02 | COMBINE with IDEA-05 | UNDERSCOPED — ablation study, not standalone contribution |

---

*Analysis by AGENT-3: REFINE. Scoring is strict and evidence-based. IDEA-NEW-2 is the only EXCELLENT FIT candidate that fully satisfies all four dimensions of the project name.*
