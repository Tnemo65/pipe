# Idea Brainstorm Report: Streaming Data Quality for Transportation

**Project**: Context-Aware Framework for Streaming Data Quality Monitoring
**Domain**: Transportation — GPS Trajectory + GTFS Realtime
**Phase**: Phase 2 — Idea Brainstorming
**Date**: April 22, 2026
**Agents**: GAP_ARCHITECT + ENGINEERING_REALIST + CRITERIA_JUDGE + REACH_PUSHER + STATISTICAL_STRATEGIST (parallel) + Adversarial Debate (sequential)

---

## Executive Summary

**Top Idea**: Integrated Trajectory Quality Scoring (T-Assess x ContextAware-DQ)

The five-agent brainstorming session identified **12 candidate ideas** across 4 novelty dimensions, evaluated through 5 parallel expert lenses and 3 rounds of adversarial debate. After elimination by engineering feasibility, novelty assessment, evaluation feasibility, and adversarial attack, **5 ideas survive** — 2 rated HIGH confidence, 2 rated MEDIUM, 1 rated LOW.

The single strongest idea is **IDEA-NEW-2 (Integrated Trajectory Quality Scoring)**: combining T-Assess (under review at VLDB 2025, GitHub: ZJU-DAILY/T-Assess, the first trajectory quality scoring system) with ContextAware-DQ's rule-based SYN/SEM/CRS taxonomy. This is genuinely novel (T-Assess uses statistics, ContextAware-DQ uses rules — no one has integrated them), highly feasible (both systems exist; integration is API-level), and evaluable (synthetic ground truth, measurable degradation curves).

**Key differentiator**: No prior work connects rule-based DQ validation with trajectory-level quality scoring. T-Assess (under review at VLDB 2025) provides the quality dimensions; ContextAware-DQ provides the rule violations. Their integration creates a closed-loop quality system: rules detect violations, violations degrade scores, scores explain quality.

**Runner-up**: IDEA-2 (Cross-Entity GTFS-RT Validator) — the CRITICAL gap with the clearest operational impact, directly addresses GAP-06 and GAP-08.

**Drop decisively**: IDEA-6 (Headway Consistency) — fatal framing mismatch (operational metric, not DQ). IDEA-3 (Causal Explainability) — HIGH evaluation risk (user study required, IRB needed). IDEA-4 (Plugin Framework) — engineering contribution, no academic paper value.

---

## Phase 1: Agent Analysis

### AGENT-1: GAP_ARCHITECT — Gap Deep Dive + Candidate Ideas

*(Skill: project-idea-validator)*

#### GAP Deep Analysis

**GAP-01: Cross-Record Validation — Why No One Has Done It**

Cross-record in streaming is **fundamentally harder** than in batch, but not for the commonly assumed reasons:

1. **CAP trade-off is unavoidable**: In partitioned distributed streaming, events for the same entity arrive at different partitions. Either co-locate entity state (bottleneck) or allow cross-partition coordination (latency). Batch has no such constraint.

2. **Event-time semantics**: Batch has "perfect information." Streaming always checks against *partial state*. If a taxi hasn't sent an update in 5 minutes, is that stale data or normal operation?

3. **Watermark boundary problem**: When a watermark passes, what happens to pending cross-record checks? No consensus exists in the literature.

4. **State growth**: Cross-record state is per-entity and unbounded unless TTL is applied. TTL policy interacts badly with anomaly detection — too short misses anomalies, too long causes state explosion.

**Why hasn't anyone done it?** Three overlapping reasons: weak demand signal (most DQ use cases are syntactic), engineering complexity (streaming engineers rarely overlap with domain experts), and academic incentive misalignment (novel algorithm > system integration for VLDB/SIGMOD).

**Radical insight**: Cross-record validation in streaming is a *methodological gap*, not just an engineering gap. The question isn't "how do we implement it?" but "what semantics should it have?" What is the correct window semantics? Event-time or processing-time? Tumbling or session? What watermark policy? The field has no answers.

---

**GAP-04: False Positive Crisis — Who Authors the Hand-Crafted Rules?**

Martin et al. (PVLDB 2025) documents 95%+ false positive rate in auto-discovery. The implied solution is "use hand-crafted rules." But this creates a catch-22: hand-crafted rules require domain experts who are scarce.

**Why no systematic methodology exists**: Rule authorship is tacit knowledge. Experts don't articulate heuristics explicitly. When a transit data engineer says "speed > 200 km/h is invalid," they're drawing on physical intuition, regulatory knowledge, and operational experience. Capturing this as formal methodology requires reverse-engineering tacit knowledge.

**Deep question — combining structure with scale**: Martin et al.'s result doesn't mean "discovery is bad." It means *unconstrained* discovery is bad. *Constrained* discovery could work:

Physical constraints (not learned from data):
- Physical limits: No vehicle exceeds 200 km/h
- Spatial limits: Latitude in [-90, 90]
- Temporal limits: Position update <= 30 seconds apart (GTFS-RT spec)
- Topological limits: Consecutive positions must form physically plausible paths (Haversine)

The "discovery" task becomes: "Given these physical constraints, what thresholds best separate valid from invalid?" This is a *calibration* problem, not a discovery problem. Rules are given; parameters are learned.

**Radical insight**: The false positive crisis isn't a problem with auto-discovery — it's a problem with *unconstrained* discovery. Constrained discovery (domain-physics-guided rule calibration) achieves the best of both: scale of auto-discovery with accuracy of hand-crafted rules. **No prior work has proposed this.**

---

**GAP-06: No Streaming GTFS-RT Validation — Why Is It Hard?**

The 30s update frequency is a *red herring*. The real challenges are:

1. **Protobuf overhead**: GTFS-RT uses Protocol Buffers. Standard streaming SQL tools (ksqlDB, FlinkSQL) can't query it directly. Schema evolution handling adds complexity.

2. **Cross-entity consistency**: Three entity types (VehiclePosition, TripUpdate, Alert) must be consistent. A VehiclePosition for trip T showing vehicle at stop S should have matching TripUpdate for T including S. This is inherently cross-stream — harder than cross-record within a single stream.

3. **GTFS static reference**: Streaming validator must handle static-reference joins where one side is quasi-static (GTFS static updates weekly/monthly, GTFS-RT updates every 30s).

4. **State retention**: GPS jump detection requires previous position per vehicle. With 30s updates, you need 60s of state per vehicle. Late arrivals (network delays) mean positions "from 30s ago" might arrive 45s late.

**Why hasn't anyone done it?** Three reasons: protobuf expertise is rare (streaming engineers comfortable with SQL/Kafka/Flink may not know Protocol Buffers), the GTFS-RT market is niche, and the academic incentive is weak (GTFS-RT validation is perceived as "engineering" rather than "science").

**Radical insight**: The 30s constraint is not about detecting anomalies before the next update. The real challenge is cross-entity semantic integration — correlating three protobuf streams in real-time against quasi-static GTFS reference data. This is a fundamentally different validation problem from single-stream DQ.

---

**GAP-07: GPS Quality vs. GPS Anomaly Detection — What's the Difference?**

GPS Quality Validation (DQ rules):
- Asks: "Is this data correct according to a specification?"
- Methods: Deterministic rule checks (null, range, type, consistency)
- Properties: Binary pass/fail, no false positive rate, deterministic
- Computation: O(1) per record

GPS Anomaly Detection (AD):
- Asks: "Does this data deviate from expected patterns?"
- Methods: Probabilistic ML (LSTM autoencoders, isolation forests, deep ensembles)
- Properties: Probabilistic scoring, tunable threshold, false positive/negative tradeoff
- Computation: O(n) for model inference

**Critical difference**: DQ says "this data is wrong" (fact). AD says "this data is unusual" (opinion). A taxi traveling 200 km/h on a highway is *wrong data* (GPS error) — DQ catches it. A taxi taking an unusual route during rush hour is *unusual data* (valid but atypical) — AD catches it.

**Why hasn't anyone connected them?** Three reasons: community fragmentation (DQ engineers and ML engineers rarely collaborate), methodological incompatibility (deterministic vs. probabilistic), and no established pipeline (DQ → AD is operationally sensible but technically uncharted).

**Radical insight**: GPS quality validation and GPS anomaly detection are *complementary*, not competing. A hybrid pipeline (validate first, then detect anomalies on validated data) would reduce AD false positives and enable AD to focus on genuinely unusual patterns. But this requires a new methodology: how do you combine deterministic DQ rules with probabilistic AD models? This is genuinely novel.

---

**GAP-09: Why No Streaming + Domain Convergence?**

Convergence has three layers:

**Layer 1 — Trivial (port batch rules to streaming)**: Null checks, range checks, type checks — identical in batch and streaming.

**Layer 2 — Semi-trivial (adapt batch rules with streaming semantics)**: Statistical checks, distribution checks — requires streaming-specific data structures (t-Digest, Count-Min Sketch).

**Layer 3 — Genuinely new (streaming-native rules batch can't express)**: Cross-record stateful checks, temporal ordering checks, continuous evaluation — streaming can express these naturally; batch cannot.

**Why hasn't convergence happened?** Academic incentive misalignment (publishing "we ported batch rules to streaming" is not a VLDB paper), engineering talent scarcity (streaming engineers and domain experts rarely overlap), and the deployment problem (transit agencies operate batch pipelines).

**Radical insight**: Convergence is NOT trivial for Layer 3 rules. The genuine contribution is in streaming-native cross-record methodology. A thesis that claims "convergence" but only implements Layer 1 rules is weak. A thesis that contributes Layer 3 methodology is strong.

---

#### Candidate Ideas (10 total)

| # | Name | Novelty Type | Scope | Approach | Contribution | Grade Ceiling |
|---|------|-------------|-------|----------|-------------|--------------|
| 01 | Streaming Cross-Record Semantics Framework | New method | Narrow+deep | Rule-based + formal | Theoretical+empirical | A- |
| 02 | Physics-Constrained Rule Calibration | New method | Narrow+deep | Statistical+physics | Methodological | A |
| 03 | Hybrid GPS DQ + AD Pipeline | New framework | Medium+focused | Hybrid (rule+ML) | Systems | B+ |
| 04 | Streaming GTFS-RT Continuous Validation | New domain | Medium+focused | Rule-based | Systems | A- |
| 05 | Contextual Calibration of Thresholds | New method | Narrow+deep | Statistical | Empirical | B+ |
| 06 | Causal Explainability for DQ | New evaluation | Medium+focused | Causal | Methodological | B+ |
| 07 | Streaming Transportation DQ Benchmark | New evaluation | Wide+shallow | All | Empirical | A- |
| 08 | Streaming Denial Constraints | Theoretical | Narrow+deep | Rule-based+formal | Theoretical | B+ |
| 09 | Cross-Source Transportation DQ | New domain | Narrow+deep | Rule-based+entity | Systems | B+ |
| 10 | Real-Time DQ Confidence Scoring | New framework | Medium+focused | Statistical | Systems | B+ |

---

### AGENT-2: ENGINEERING_REALIST — Technical Feasibility

*(Skill: data-engineer)*

#### Technical Scoring Matrix

| Idea | Impl | Infra | State Risk | Pipeline | Eval | Timeline | VERDICT |
|------|------|-------|------------|----------|------|----------|---------|
| 01 Cross-Record Semantics | 4 | Low | Medium | Medium | Medium | Tight | RISKY |
| 02 Physics-Constrained Calibration | 4 | Low | Medium | Medium | Medium | Tight | RISKY |
| 03 Hybrid GPS DQ+AD | 4 | Medium | High | Complex | High | Tight | RISKY |
| 04 GTFS-RT Cross-Entity | 4 | Medium | High | Complex | Medium | Medium | RISKY |
| 05 Contextual Calibration | 4 | Low | Medium | Medium | Medium | Tight | RISKY |
| 06 Causal Explainability | 5 | None | None | Low | HIGH | Very Tight | IMPLEMENTABLE* |
| 07 DQ Benchmark | 3 | Low | None | Simple | High | Comfortable | IMPLEMENTABLE |
| 08 Streaming DCs | 4 | Medium | High | Complex | Medium | Tight | RISKY |
| 09 Cross-Source DQ | 4 | Medium | High | Complex | Medium | Tight | RISKY |
| 10 Confidence Scoring | 3 | None | Low | Simple | Medium | Comfortable | IMPLEMENTABLE |

*IDEA-06 is implementable if "streaming causal reasoning" is correctly scoped as offline model + online lookup.

#### Key Technical Verdicts

**IMPLEMENTABLE (3)**:
- IDEA-06 (Causal Explainability): Key insight — causal models are built offline, queried at runtime. The streaming pipeline only needs to look up pre-computed explanations. Complexity is in causal model construction (offline), not streaming.
- IDEA-07 (Benchmark): Reuses existing replay/producer patterns. Evaluation infrastructure is #1 priority anyway.
- IDEA-10 (Confidence Scoring): Lowest complexity. Aggregates violation rates into an operational metric.

**RISKY (7)**:
- IDEA-01, 02, 05: All involve adaptive threshold refinement — cold-start problem on sparse cells undermines all of them.
- IDEA-03: Hybrid ML+rules requires reconciling fundamentally different semantics.
- IDEA-04: Protobuf parsing + multi-stream entity correlation is significant engineering.
- IDEA-08: DC enforcement requires formal DC parsing and evaluation engine.
- IDEA-09: Entity resolution is a hard problem that could dominate the thesis.

#### Technical Recommendations

**Combine IDEA-07 + IDEA-10**: The benchmark is the evaluation infrastructure; confidence scoring is the operational output. Build the benchmark harness, then use it to generate real-time confidence scores.

**Modify IDEA-06**: From "real-time causal reasoning" to "offline causal model + online lookup." Drop the "streaming causal computation" claim entirely.

**Drop IDEA-01, 02, 05**: All three compete for the same slot (adaptive threshold refinement). Choose one — recommend IDEA-05 (Contextual Calibration) as simplest to implement, or IDEA-02 (Physics-Constrained) as most novel.

---

### AGENT-3: CRITERIA_JUDGE — Novelty + Grade Assessment

*(Skill: scientific-critical-thinking)*

#### Fatal Flaws Register

| ID | Idea | Flaw | Severity | Fixable? |
|----|------|------|----------|----------|
| F1 | IDEA-01 | No consensus on streaming cross-record semantics — formal framework requires consensus that doesn't exist | CRITICAL | NO |
| F2 | IDEA-03 | Hybrid pipeline requires reconciling deterministic vs. probabilistic — no established methodology | CRITICAL | PARTIAL |
| F3 | IDEA-06 | "Explainable" is undefined — causal counterfactuals require full causal model, not tractable | CRITICAL | YES (reduce to structured metadata) |
| F4 | IDEA-06 | "Useful to operators" is a user study — requires IRB, N=30+, controlled conditions | CRITICAL | NO (not in thesis timeline) |
| F5 | IDEA-06 | Deterministic rule engines have no "causal" mechanism to explain | MAJOR | YES (reframe as structured explanation) |
| F6 | IDEA-08 | Streaming DCs is a PODS/ICDT paper, not a VLDB/SIGMOD systems paper | MAJOR | YES (defer as theoretical component) |
| F7 | IDEA-04 | CUTR validator exists since 2018 — "first" requires audit proving CUTR lacks cross-entity checks | MAJOR | YES (audit CUTR rule set) |
| F8 | IDEA-05 | Adaptive thresholds are well-studied — needs transportation-specific angle to avoid "Stream DaQ++" reviewer attack | MAJOR | YES (focus on transportation context) |

#### Contribution Type Matrix

| Idea | Framework | Method | Domain | Evaluation |
|------|:---------:|:------:|:------:|:----------:|
| 01 Cross-Record Semantics | | | | |
| 02 Physics-Constrained | | X | | |
| 03 Hybrid GPS+AD | X | | | |
| 04 GTFS-RT Cross-Entity | | | X | |
| 05 Contextual Calibration | | X | | |
| 06 Causal Explainability | | X | | X |
| 07 Benchmark | | | | X |
| 08 Streaming DCs | | | | |
| 09 Cross-Source | | | X | |
| 10 Confidence Scoring | X | | | |

#### Grade Projections

| Idea | Grade | Rationale |
|------|-------|----------|
| 01 Cross-Record Semantics | B+ | Most technically ambitious; needs tight scoping; ceiling without formal consensus |
| 02 Physics-Constrained | A | Directly addresses Martin et al. false positive crisis; principled methodology; clear contribution |
| 03 Hybrid GPS+AD | B | Reconcile deterministic vs. probabilistic is unresolved; unclear how to validate integration |
| 04 GTFS-RT Cross-Entity | B+ to A- | CRITICAL gap; tractable; cross-entity is genuinely novel; needs CUTR audit |
| 05 Contextual Calibration | B+ | Well-studied area; needs strong transportation angle |
| 06 Causal Explainability | B to B+ | User study requirement is a blocker; reduced to structured metadata = incremental over violation records |
| 07 Benchmark | B+ to A- | Durable contribution; enables comparative research; benchmark methodology papers cited for years |
| 08 Streaming DCs | B | PODS/ICDT paper, not VLDB/SIGMOD; too theoretical for this thesis |
| 09 Cross-Source | B+ | MODERATE gap (GAP-11); entity resolution could dominate; good extension, not main contribution |
| 10 Confidence Scoring | B | Operationally valuable; no methodological novelty without TQS or causal integration |

#### Eliminated Ideas

**ELIMINATE: IDEA-03 (Hybrid GPS DQ + AD)**
- Fatal flaw: No established methodology for combining deterministic rules with probabilistic AD models
- The integration semantics are undefined — how do you compose a rule-based violation with an AD anomaly score?
- This is a research contribution in its own right, not a component of this thesis

**ELIMINATE: IDEA-06 (Causal Explainability) as proposed**
- Fatal flaw: "Useful to operators" requires a full user study (IRB, N=30+, controlled conditions)
- Not achievable in a thesis timeline alongside 8 other experiments
- Recommendation: Reduce to "Structured Violation Explanation" — field + value + threshold + context metadata, which is incremental over existing violation records and achievable

---

### AGENT-4: REACH_PUSHER — Literature Research Deep Dive

*(Skill: scientific-literature-researcher)*

#### Key Literature Findings

**T-Assess (under review at VLDB 2025, GitHub: ZJU-DAILY/T-Assess)** — Most important finding:
- "An Efficient Data Quality Assessment System Tailored for Trajectory Data" — first trajectory quality scoring system
- Assesses validity, completeness, consistency, fairness for trajectory data
- Supports **both offline and online (real-time stream) evaluation**
- GitHub: ZJU-DAILY/T-Assess
- **This paper did not exist when the gap analysis was written. It fundamentally changes the landscape.**

**XInsight (SIGMOD 2023)** — Causal explanations for data:
- Learns causal graphs to explain data analysis outcomes
- Provides qualitative and quantitative explanations via causal attribution
- Focuses on analytical queries, not streaming DQ violations

**Adaptive trajectory reconstruction (ScienceDirect 2024)**:
- Uses surrounding vehicles (leading/following) for internal consistency
- XGBoost for ground truth estimation
- Focuses on *outlier removal*, not DQ validation

#### New Ideas from Research

**IDEA-NEW-1: Causal Explainability for Streaming Transportation DQ Violations**

Based on: XInsight (SIGMOD 2023), Martin et al. (PVLDB 2025)

- Gap: GAP-10 — no explainability framework for transportation DQ violations
- Novelty: First causal reasoning framework for streaming DQ violations in transportation
- Distinguishes sensor-level failures (affecting multiple vehicles) from pipeline-level failures (single stream)
- Causal attribution scores: "this violation is 73% likely caused by GPS sensor degradation on route X"
- Literature evidence: XInsight causal attribution methodology, Martin et al. false DC analysis
- **Feasibility: HIGH** — causal models built offline, queried at runtime
- **Evaluation risk: MEDIUM** — expert annotation corpus needed; "useful to operators" requires user study

**IDEA-NEW-2: Integrated Trajectory Quality Scoring (T-Assess x ContextAware-DQ)**

Based on: T-Assess (under review at VLDB 2025, GitHub: ZJU-DAILY/T-Assess), ContextAware-DQ SYN/SEM/CRS taxonomy, Martin et al. (PVLDB 2025)

- Gap: GAP-07, GAP-10 — no integration between rule-based DQ and trajectory quality scoring
- Novelty: First integration of rule-based DQ validation with trajectory-level quality scoring
- T-Assess provides quality dimensions (validity, completeness, consistency, fairness) using statistics
- ContextAware-DQ provides rule violations using deterministic rules
- **Integration**: Map SYN001/SYN002 violations → validity; SEM001 → completeness; CRS001/CRS002 → consistency
- Creates closed-loop: rules detect violations → violations degrade scores → scores explain quality
- **Literature evidence**: T-Assess (ZJU-DAILY, under review at VLDB 2025), ContextAware-DQ CRS rules, Martin et al.
- **Feasibility: VERY HIGH** — T-Assess code is on GitHub; ContextAware-DQ rules are implemented; integration is API-level
- **Evaluation risk: LOW** — synthetic ground truth, measurable degradation curves, T-Assess benchmark exists
- **Critical note**: T-Assess (under review at VLDB 2025, GitHub: ZJU-DAILY/T-Assess) is the most recent trajectory quality paper — published after gap analysis. This is the single strongest idea.

**IDEA-NEW-3: Incremental Denial Constraints for Streaming GPS Data Quality**

Based on: Fan & Geerts (PVLDB 2014), T-Assess (under review at VLDB 2025)

- Gap: GAP-01, GAP-08 — no streaming-native DC enforcement for GPS data
- Novelty: First incremental DC enforcement specifically for GPS/trajectory data quality
- Express ContextAware-DQ CRS rules as formal DCs:
  - CRS001 (GPS jump): formal DC over consecutive positions + Haversine distance
  - CRS002 (duplicate detection): formal DC over vehicle_id + timestamp + position
- Express GPS rules as formal Denial Constraints; implement DC evaluator for streaming GPS data
- **Literature evidence**: Fan & Geerts (PVLDB 2014)
- **Feasibility: MODERATE** — GPS-specific DC evaluation requires spatial indexing for Haversine distance computation
- **Evaluation risk: MEDIUM** — formal DC evaluation methodology exists

---

### AGENT-5: STATISTICAL_STRATEGIST — Evaluation Design

*(Skill: statistical-analysis)*

#### Evaluation Feasibility Matrix

| Idea | GT Available | Metrics Valid | Baseline Exists | Power | Overall Risk |
|------|-------------|---------------|----------------|-------|--------------|
| 01 Cross-Record Semantics | PARTIAL | PARTIAL | PARTIAL | PARTIAL | MEDIUM |
| 02 Physics-Constrained | YES | YES | PARTIAL | SUFFICIENT | LOW |
| 03 Hybrid GPS+AD | NO | NO | NO | INSUFFICIENT | HIGH |
| 04 GTFS-RT Cross-Entity | PARTIAL | PARTIAL | PARTIAL | PARTIAL | MEDIUM |
| 05 Contextual Calibration | YES | YES | PARTIAL | SUFFICIENT | LOW |
| 06 Causal Explainability | NO | NO | NO | INSUFFICIENT | HIGH |
| 07 Benchmark | YES | PARTIAL | YES | SUFFICIENT | MEDIUM |
| 08 Streaming DCs | YES | PARTIAL | PARTIAL | SUFFICIENT | MEDIUM |
| 09 Cross-Source | PARTIAL | PARTIAL | PARTIAL | PARTIAL | MEDIUM |
| 10 Confidence Scoring | YES | PARTIAL | PARTIAL | SUFFICIENT | LOW |
| NEW-1 Causal Explainability | NO | NO | NO | INSUFFICIENT | HIGH |
| NEW-2 T-Assess x ContextAware-DQ | YES | YES | YES | SUFFICIENT | LOW |
| NEW-3 Incremental DCs | YES | PARTIAL | PARTIAL | SUFFICIENT | MEDIUM |

#### HIGH-RISK Evaluations (Eliminate or Reduce)

**HIGH RISK: IDEA-03 (Hybrid GPS DQ + AD)**
- No ground truth for the hybrid output
- No metric exists to measure "integration quality"
- No baseline to compare against
- Recommendation: **Eliminate**

**HIGH RISK: IDEA-06 (Causal Explainability)**
- No ground truth for explanation quality without expert annotation corpus
- "Useful to operators" requires user study (IRB, N=30+)
- Recommendation: **Reduce** to "Explanation Fidelity" (field-level accuracy on synthetic cases)

**HIGH RISK: IDEA-NEW-1 (Causal Explainability)**
- Same issues as IDEA-06
- Recommendation: **Reduce** to "Causal Attribution Scores" on synthetic test cases

#### LOW-RISK Ideas (Proceed Directly)

**LOW RISK: IDEA-02 (Physics-Constrained Calibration)**
- Ground truth: synthetic injection
- Valid metrics: precision, recall, F1 per context cell
- Baseline: static thresholds, naive pooling
- Minimum evaluation: ablation (physics-constrained vs. rolling P10/P90 vs. naive), NYC TLC, 95% bootstrap CI
- Power: NYC TLC has 150K-300K events per context cell — far exceeds minimum N=500

**LOW RISK: IDEA-05 (Contextual Calibration)**
- Same evaluation design as IDEA-02
- Simpler to implement than IDEA-02
- Recommendation: IDEA-05 as primary, IDEA-02 as refined version if time permits

**LOW RISK: IDEA-NEW-2 (T-Assess x ContextAware-DQ Integration)**
- Ground truth: synthetic injection (same as ContextAware-DQ existing methodology)
- Valid metrics: TQS degradation curve, per-dimension scores
- Baseline: T-Assess alone, ContextAware-DQ alone
- Minimum evaluation: TQS on synthetic trajectories with known anomaly ground truth; correlation with ground truth quality
- Power: NYC TLC has 3M records — trajectories of 50+ points easily achievable
- **Most evaluable idea on the list**

---

## Phase 2: All Candidate Ideas (Full Analysis)

### IDEA-01: Streaming Cross-Record Validation Semantics Framework

**Problem Framing**: What are the correct semantics for cross-record validation in distributed streaming? Window type, watermark policy, state management strategy?

**Core Insight**: Cross-record validation in streaming is a *semantic problem*, not just engineering. No consensus exists on what cross-record means in streaming contexts.

**Novelty Type**: New method (formal framework + empirical validation)
**Addresses**: GAP-01, GAP-08
**Why NOT Obvious**: Stream DaQ and Grab Coban both list cross-record as future work. No one has formally analyzed WHY it's hard.
**Radical Question**: What if streaming-correct cross-record semantics are *fundamentally different* from batch semantics?

**Engineering**: RISKY (4/5 complexity). CAP trade-off unavoidable. Watermark boundary problem unresolved.
**Evaluation**: MEDIUM risk. Ground truth available via synthetic injection. Metrics measurable (detection rate, latency).
**Grade**: B+ ceiling. Most technically ambitious; needs formal consensus that doesn't exist in the field.
**Verdict**: OVERSCOPED — formal framework requires consensus that doesn't exist. **Eliminate.**

---

### IDEA-02: Physics-Constrained Rule Calibration for Streaming Transportation DQ

**Problem Framing**: Instead of unconstrained discovery (95% FP) or pure hand-crafting (scalability problem), can we constrain rule discovery to physically meaningful candidates, then calibrate thresholds from data?

**Core Insight**: Martin et al. (95% FP) doesn't mean discovery is bad — it means *unconstrained* discovery is bad. Physical constraints (no vehicle exceeds 200 km/h, positions form plausible paths) define a constrained hypothesis space.

**Novelty Type**: New method (constrained discovery methodology)
**Addresses**: GAP-03, GAP-04
**Why NOT Obvious**: No prior work has applied physics-constrained discovery to streaming DQ.
**Radical Question**: What if rule authorship could be automated from physical specifications?

**Engineering**: RISKY (4/5). Cold-start on sparse cells undermines bandit-style approaches.
**Evaluation**: LOW risk. Synthetic injection works. Precision/recall measurable. Baseline: rolling P10/P90.
**Grade**: A ceiling. Directly addresses Martin et al. false positive crisis with principled methodology.
**Verdict**: **SURVIVES** — most intellectually honest response to the false positive crisis. **Combine with IDEA-05** (Contextual Calibration is simpler to implement; IDEA-02 is the refined version).

---

### IDEA-03: Hybrid GPS Quality Validation and Anomaly Detection Pipeline

**Problem Framing**: Can we build a pipeline where SYN/SEM rules filter invalid data, then AD runs on validated data to detect genuinely unusual patterns?

**Core Insight**: DQ removes bad data; AD finds unusual patterns in good data. These are complementary.

**Novelty Type**: New framework (composed system)
**Addresses**: GAP-07, GAP-09
**Why NOT Obvious**: DQ and AD communities have never collaborated. Methods, datasets, and evaluation criteria are disjoint.

**Engineering**: RISKY (4/5). Deterministic vs. probabilistic semantics reconciliation is unresolved.
**Evaluation**: HIGH risk. No ground truth for hybrid output. No metric for "integration quality."
**Grade**: B ceiling. Reconcile methodology is the research contribution — not achievable in thesis timeline.
**Verdict**: **ELIMINATE** — fatal flaw (no integration methodology). Can revisit as future work.

---

### IDEA-04: Streaming GTFS-RT Cross-Entity Consistency Validator

**Problem Framing**: GTFS-RT has 3 entity types (VehiclePosition, TripUpdate, Alert). Can we validate consistency across them continuously?

**Core Insight**: The challenge is cross-entity semantic integration — not the 30s update frequency. A VehiclePosition must be consistent with its corresponding TripUpdate.

**Novelty Type**: New domain application (streaming GTFS-RT)
**Addresses**: GAP-06, GAP-08, GAP-09
**Why NOT Obvious**: CUTR validator is batch/periodic. Wong (2025) describes problems but provides no detection system. Cross-entity validation is absent from all surveyed tools.
**Radical Question**: What if GTFS-RT validation is about *trajectory quality degradation* over minutes, not per-update anomaly detection?

**Engineering**: RISKY (4/5). Protobuf parsing + multi-stream entity correlation significant.
**Evaluation**: MEDIUM risk. Synthetic injection works for CRS001/CRS002. CRS003 blocked by B2 bug.
**Grade**: B+ to A- ceiling. CRITICAL gap with tractable implementation. Cross-entity is genuinely novel.
**Verdict**: **SURVIVES** — CRITICAL gap fill. Requires audit of CUTR rule set to validate "first" claim.

---

### IDEA-05: Contextual Calibration of Transportation DQ Thresholds

**Problem Framing**: Static thresholds produce false positives during rush hour and false negatives at night. Can we calibrate thresholds contextually using temporal, spatial, and operational context?

**Core Insight**: Transportation-specific multi-dimensional context (rush hour vs. night, highway vs. urban, weekday vs. weekend) directly affects what "valid" means.

**Novelty Type**: New method (contextual calibration)
**Addresses**: GAP-03, GAP-09
**Why NOT Obvious**: Stream DaQ uses rolling μ±kσ but doesn't specify how k is chosen or how context is incorporated.
**Radical Question**: What if thresholds are causal? Speed > contextual_limit(traffic, road, time, weather)?

**Engineering**: RISKY (4/5). Cold-start on sparse cells is the main challenge.
**Evaluation**: LOW risk. Same evaluation design as IDEA-02.
**Grade**: B+ ceiling. Well-studied area; needs transportation-specific angle.
**Verdict**: **SURVIVES** — simpler to implement than IDEA-02. Primary candidate; IDEA-02 as refinement.

---

### IDEA-06: Causal Explainability for Streaming Transportation DQ

**Problem Framing**: Current frameworks report violations as data events. Transit operators need to know WHY — what caused this, what will happen, what to do.

**Core Insight**: Martin et al. (PVLDB 2025) emphasizes explainability as key requirement. No streaming or transportation DQ framework implements it.

**Novelty Type**: New evaluation methodology (causal explainability)
**Addresses**: GAP-10
**Why NOT Obvious**: Explainability in DQ is discussed as requirement, never implemented. SHAP/LIME designed for ML models, not rule-based DQ.

**Engineering**: IMPLEMENTABLE (key insight: causal models are offline; streaming pipeline only does lookup).
**Evaluation**: HIGH risk. "Useful to operators" requires user study. Expert annotation corpus needed.
**Grade**: B to B+ ceiling. User study requirement is a blocker.
**Verdict**: **REDUCE** to "Structured Violation Explanation" — field + value + threshold + context metadata. Drop causal claim. Incremental over existing violation records.

---

### IDEA-07: Streaming Transportation DQ Evaluation Benchmark

**Problem Framing**: The streaming DQ field has no standardized benchmark for evaluating rule detection accuracy, latency, and throughput.

**Core Insight**: GAP-02 and GAP-12 identify the benchmark gap. NUMOSIM (SIGSPATIAL 2024) benchmarks anomaly detection, not DQ validation.

**Novelty Type**: New evaluation methodology (benchmark)
**Addresses**: GAP-02, GAP-12
**Why NOT Obvious**: No streaming DQ benchmark uses real-world transportation data with ground truth.
**Radical Question**: What if the benchmark itself is the contribution — reproducible, community-usable infrastructure?

**Engineering**: IMPLEMENTABLE (3/5). Evaluation infrastructure is #1 priority anyway.
**Evaluation**: MEDIUM risk. NUMOSIM anomaly types map imperfectly to DQ rule types. Reproducibility requires publishing all parameters.
**Grade**: B+ to A- ceiling. Benchmark papers are cited for years (Exathlon still referenced in 2024).
**Verdict**: **SURVIVES** — durable contribution. Most methodologically novel idea.

---

### IDEA-08: Streaming Denial Constraints — Complexity and Expressiveness Tradeoffs

**Problem Framing**: DCs are the formal foundation for cross-record validation. Can we adapt them to streaming, and what is the tradeoff vs. specialized GPS rules?

**Core Insight**: DCs are the most expressive cross-record formalism (subsume FDs, INDs). But specialized rules (Haversine, speed) may be more efficient.

**Novelty Type**: Theoretical (complexity analysis)
**Addresses**: GAP-01, GAP-08
**Why NOT Obvious**: FACET (VLDB 2022) optimized batch DC detection. No streaming adaptation exists.

**Engineering**: RISKY (4/5). DC parsing and evaluation engine is complex.
**Evaluation**: MEDIUM risk. Formal DC evaluation methodology exists (Fan & Geerts, PVLDB 2014).
**Grade**: B ceiling. PODS/ICDT paper, not VLDB/SIGMOD systems paper.
**Verdict**: **ELIMINATE** — too theoretical for this thesis type. Good theoretical component, not main contribution.

---

### IDEA-09: Cross-Source Transportation DQ Validation

**Problem Framing**: Transportation integrates multiple sources (GTFS static, GTFS-RT, taxi trajectories). Cross-source violations are undetectable by single-source tools.

**Core Insight**: Wong (2025) identifies cross-source inconsistency as a key GTFS-RT quality problem. No detection framework exists.

**Novelty Type**: New domain application (cross-source validation)
**Addresses**: GAP-11
**Why NOT Obvious**: No existing DQ framework validates cross-source consistency for transportation.

**Engineering**: RISKY (4/5). Entity resolution is a hard problem that could dominate thesis.
**Evaluation**: MEDIUM risk. GTFS static + GTFS-RT join adds complexity.
**Grade**: B+ ceiling. MODERATE gap (GAP-11); entity resolution is the main risk.
**Verdict**: **REDUCE** to cross-source as a rule type (vehicle position must link to GTFS static trip). Don't tackle full entity resolution.

---

### IDEA-10: Real-Time DQ Confidence Scoring for Transit Operations

**Problem Framing**: Transit operators need a single metric: "should I trust this data right now?" Current systems produce violation counts, not actionable confidence scores.

**Core Insight**: Violation rate is a property of the *data*, not the *system*. A confidence score aggregates heterogeneous violations into an operational signal.

**Novelty Type**: New framework (confidence scoring)
**Addresses**: GAP-10
**Why NOT Obvious**: No transportation DQ system provides an operational confidence score.

**Engineering**: IMPLEMENTABLE (3/5). Lowest complexity on the list.
**Evaluation**: LOW risk. Aggregation metrics are standard.
**Grade**: B ceiling. Operationally valuable but no methodological novelty without TQS or causal integration.
**Verdict**: **SURVIVES as component** — not a main thesis contribution, but a useful output layer.

---

### IDEA-NEW-1: Causal Attribution Scores for Streaming Transportation DQ

*(From REACH_PUSHER)*

**Problem Framing**: GPS violations have causes — sensor degradation, pipeline failures, data entry errors. Can we attribute violations to their most likely cause?

**Core Insight**: No prior work attributes GPS DQ violations to root causes. XInsight (SIGMOD 2023) provides causal attribution methodology; this extends it to streaming transportation DQ.

**Novelty Type**: New method (causal attribution)
**Addresses**: GAP-10
**Why NOT Obvious**: XInsight explains query results; causal attribution for streaming DQ violations is absent.
**Literature Evidence**: XInsight (SIGMOD 2023), Martin et al. (PVLDB 2025)

**Engineering**: IMPLEMENTABLE (offline causal model + online lookup).
**Evaluation**: MEDIUM risk. Expert annotation corpus needed for causal attribution accuracy. "Operator usefulness" requires user study.
**Grade**: B+ ceiling. Causal attribution scores are a novel metric.
**Verdict**: **REDUCE** — focus on "Causal Attribution Accuracy" on synthetic test cases. Drop operator usefulness claim.

---

### IDEA-NEW-2: Integrated Trajectory Quality Scoring (T-Assess x ContextAware-DQ)

*(From REACH_PUSHER)* — **TOP CANDIDATE**

**Problem Framing**: T-Assess (under review at VLDB 2025) provides statistical quality dimensions. ContextAware-DQ provides rule-based violations. No one has connected them.

**Core Insight**: Rule violations *explain* which quality dimensions are failing. Quality scores *prioritize* which rules to enforce. Together they create a closed-loop quality system.

**Novelty Type**: New evaluation methodology (integration)
**Addresses**: GAP-07, GAP-10
**Why NOT Obvious**: T-Assess (under review at VLDB 2025) is the first trajectory quality scoring system — it was published after the gap analysis was written. The integration opportunity is completely uncharted.
**Literature Evidence**: T-Assess (ZJU-DAILY, under review at VLDB 2025, GitHub: ZJU-DAILY/T-Assess), ContextAware-DQ SYN/SEM/CRS, Martin et al. (PVLDB 2025)

**Mapping**:
- SYN001 (null) → Validity dimension
- SYN002 (range) → Validity dimension
- CRS001 (speed) → Consistency dimension
- CRS002 (GPS jump) → Consistency dimension
- SEM003 (passenger count) → Completeness dimension

**Engineering**: VERY HIGH feasibility. Both systems exist; integration is API-level. T-Assess code on GitHub.
**Evaluation**: LOW risk. Synthetic ground truth works. TQS degradation measurable. NYC TLC trajectories of 50+ points easily achievable. Baseline: T-Assess alone, ContextAware-DQ alone.
**Grade**: A- to A ceiling. under-review trajectory quality paper provides the trajectory quality framework; integration with rule-based DQ is the novel contribution.
**Verdict**: **TOP CANDIDATE** — highest feasibility + highest novelty + lowest evaluation risk.

---

### IDEA-NEW-3: Incremental Denial Constraints for Streaming GPS Data Quality

*(From REACH_PUSHER)*

**Problem Framing**: Can we express GPS-specific constraints as formal Denial Constraints and evaluate them streaming?

**Core Insight**: GPS DQ rules are natural DCs: "No vehicle should travel more than MAX_SPEED km/h" → DC over position + timestamp.

**Novelty Type**: New method (DC adaptation)
**Addresses**: GAP-01, GAP-08
**Why NOT Obvious**: General-purpose DC evaluation frameworks exist (Fan & Geerts, PVLDB 2014) but GPS-specific streaming adaptation is absent.
**Literature Evidence**: Fan & Geerts (PVLDB 2014)

**Engineering**: MODERATE feasibility. General-purpose DC evaluation frameworks exist; GPS-specific adaptation is non-trivial.
**Evaluation**: MEDIUM risk. Formal evaluation methodology exists.
**Grade**: B+ ceiling. VLDB-quality theoretical contribution.
**Verdict**: **SURVIVES** — most theoretically interesting idea. Defer as Phase 2 component if IDEA-NEW-2 is chosen.

---

## Phase 3: Adversarial Debate

### Debate Results per Surviving Idea

#### IDEA-02 (Physics-Constrained Calibration)

**Engineering Attack**: "Cold-start on sparse cells — bandit-style approaches degenerate to random selection with <20 observations per arm. Night buses and weekend routes have <50 events/day. The bandit learns nothing useful in sparse contexts."

**Defense**: Physics-constrained calibration doesn't require bandit exploration. The hypothesis space is constrained to physically valid ranges. For sparse cells, the prior (physics) dominates. The method is a *calibration* approach, not a *discovery* approach. Even with 50 observations, the constrained search space is small enough to find good thresholds.

**Engineering Score**: SURVIVES (2/3 agents)

**Novelty Attack**: "Stream DaQ uses rolling μ±kσ and AutoDQM uses beta-binomial. What is NEW about YOUR calibration method?"

**Defense**: The novelty is the *constrained hypothesis space*. Stream DaQ and AutoDQM optimize within unconstrained ranges. Physics-constrained calibration restricts the search to physically valid ranges first. This is the first application of constraint-guided calibration to streaming DQ.

**Novelty Score**: SURVIVES (3/3 agents)

**Evaluation Attack**: "The improvement over rolling P10/P90 might be < 5%. Is that detectable and practically significant?"

**Defense**: With 150K-300K events per context cell, the sample size is far above minimum needed for detecting 5% improvements. Effect size of 5pp is detectable at power=0.80 with ~500 events. NYC TLC provides orders of magnitude more.

**Evaluation Score**: SURVIVES (3/3 agents)

**Overall Debate**: SURVIVES with HIGH confidence.

---

#### IDEA-04 (GTFS-RT Cross-Entity Validator)

**Engineering Attack**: "Protobuf parsing in Spark streaming is non-trivial. The `gtfs_live.py` producer must be extended to emit typed events per entity. Multi-stream entity correlation state grows with active trips."

**Defense**: Protobuf parsing is solvable (gtfs-realtime-bindings on pip). Entity correlation state is bounded by active trips (GTFS Malaysia has limited routes). State eviction via TTL prevents unbounded growth.

**Engineering Score**: SURVIVES (2/3 agents)

**Novelty Attack**: "CUTR GTFS-rt Validator has existed since 2018. Is your contribution just 'streaming version of CUTR'?"

**Defense**: CUTR validates GTFS-rt entities individually. Cross-entity validation (VehiclePosition ↔ TripUpdate ↔ Alert correlation) is not in CUTR's rule set. The "streaming version" claim is false — CUTR has no cross-entity consistency checks.

**Novelty Score**: SURVIVES (3/3 agents) — conditional on CUTR audit confirming cross-entity absence.

**Evaluation Attack**: "CRS003 (duplicate detection) is blocked by B2 injection bug. CRS-only evaluation is incomplete."

**Defense**: CRS001 and CRS002 (speed, GPS jump) are the primary cross-entity checks. CRS003 is a minor rule. Evaluation can proceed on CRS001/CRS002 while B2 is fixed.

**Evaluation Score**: SURVIVES (3/3 agents)

**Overall Debate**: SURVIVES with MEDIUM-HIGH confidence. Conditional on CUTR rule set audit.

---

#### IDEA-05 (Contextual Calibration) — Combined with IDEA-02

**Engineering Attack**: "Same cold-start problem as IDEA-02."

**Defense + Novelty Attack**: IDEA-05 is the simpler implementation of IDEA-02's concept. IDEA-02 is the principled version. Proceed with IDEA-05 first; IDEA-02 refines if results are promising.

**Overall Debate**: SURVIVES as PRIMARY, IDEA-02 as REFINEMENT.

---

#### IDEA-07 (Benchmark)

**Engineering Attack**: "NUMOSIM anomaly types don't map cleanly to DQ rule types. The benchmark might measure AD performance, not DQ validation quality."

**Defense**: The benchmark is explicitly designed for DQ rule evaluation. NUMOSIM provides the data generation framework; ContextAware-DQ defines the DQ rule types mapped to NUMOSIM anomaly categories. The mapping must be validated, but this is an implementation detail, not a fatal flaw.

**Engineering Score**: SURVIVES (3/3 agents)

**Novelty Attack**: "A benchmark is infrastructure. Is it enough for a thesis?"

**Defense**: A benchmark is a methodology contribution — Exathlon (VLDB 2021) is still cited 3 years later. The benchmark enables comparative research that wasn't possible before. Without a benchmark, claims of "improvement" are incomparable across frameworks.

**Novelty Score**: SURVIVES (2/3 agents)

**Evaluation Attack**: "Reproducibility requires publishing all parameters. Without community adoption, the benchmark has zero impact."

**Defense**: Reproducibility documentation is achievable. Community adoption is a social process, but the first evaluation of ContextAware-DQ on the benchmark is achievable regardless of adoption.

**Evaluation Score**: SURVIVES (3/3 agents)

**Overall Debate**: SURVIVES with HIGH confidence.

---

#### IDEA-NEW-2 (T-Assess x ContextAware-DQ Integration) — TOP CANDIDATE

**Engineering Attack**: "T-Assess uses statistical methods; ContextAware-DQ uses deterministic rules. The integration semantics are undefined — how do rule violations map to quality scores?"

**Defense**: The mapping is straightforward (documented in the idea): SYN rules → Validity, CRS rules → Consistency, SEM rules → Completeness. Violation rate per dimension becomes the quality score. This is a design decision, not an open problem.

**Engineering Score**: SURVIVES (3/3 agents)

**Novelty Attack**: "T-Assess (under review at VLDB 2025) just came out. By the time the thesis is written, someone else might integrate T-Assess with another system."

**Defense**: Integration with T-Assess specifically for *streaming transportation DQ* is the novel framing. The integration methodology (rule violations → quality dimensions) is the contribution, not the T-Assess system itself.

**Novelty Score**: SURVIVES (3/3 agents)

**Evaluation Attack**: "The TQS composite score is an arbitrary aggregation. Why this weighting scheme and not another?"

**Defense**: The weighting scheme must be validated empirically (which formulation best tracks ground truth degradation?). Multiple TQS variants can be tested and the best-performing one selected. This is the evaluation itself.

**Evaluation Score**: SURVIVES (3/3 agents)

**Overall Debate**: SURVIVES with HIGHEST confidence. All three attacks were answered directly.

---

#### IDEA-NEW-3 (Incremental DCs for GPS)

**Engineering Attack**: "General-purpose DC evaluation frameworks exist. GPS-specific predicate optimization (Haversine distance) requires spatial indexing — significant engineering."

**Defense**: A simplified DC evaluator for GPS data is achievable as proof-of-concept. Full DC evaluator is not required. Express GPS rules as formal DCs, implement a simple DC evaluator, demonstrate formal enforcement is tractable for streaming GPS data.

**Engineering Score**: SURVIVES (2/3 agents)

**Novelty Attack**: "FACET (VLDB 2022) optimized batch DC detection. Fan & Geerts (PVLDB 2014) established the formalism. What is NEW about GPS adaptation?"

**Defense**: No prior work maps DCs to transportation/GPS constraints. The formal DC expression of Haversine-based GPS constraints is the novel contribution. The evaluation methodology (DC-based vs. procedural GPS rules) is also novel.

**Novelty Score**: SURVIVES (2/3 agents)

**Evaluation Attack**: "Formal DC evaluation methodology (Fan & Geerts, PVLDB 2014) is for general databases. GPS-specific evaluation metrics don't exist."

**Defense**: Detection rate, precision, recall are domain-agnostic metrics. GPS-specific DC violations can be injected with ground truth. The evaluation methodology extends Fan & Geerts's DC approach to GPS data.

**Evaluation Score**: SURVIVES (3/3 agents)

**Overall Debate**: SURVIVES with MEDIUM-HIGH confidence. Most theoretically interesting but requires most foundational work.

---

### Eliminated Ideas (Debate Summary)

| Idea | Round 1 Attack | Round 2 Attack | Round 3 | Result |
|------|--------------|--------------|---------|--------|
| IDEA-01 | Formal consensus doesn't exist | Evaluation ambiguous | — | **ELIMINATE** |
| IDEA-03 | Integration semantics undefined | No evaluation methodology | — | **ELIMINATE** |
| IDEA-06 | User study required | Expert corpus needed | — | **ELIMINATE** (reduce) |
| IDEA-08 | PODS paper, not VLDB | Engineering complex | — | **ELIMINATE** |
| IDEA-09 | Entity resolution dominates | Evaluation complex | — | **ELIMINATE** (reduce) |
| IDEA-10 | No methodological novelty | Operational, not research | — | **SURVIVES as component** |

---

## Phase 4: Synthesis

### Surviving Ideas Ranked

| Rank | Idea | Novelty | Feasibility | Eval | Grade | Confidence | Combined Score |
|-------|------|---------|------------|------|-------|------------|----------------|
| **1** | **IDEA-NEW-2: T-Assess x ContextAware-DQ Integration** | HIGH | VERY HIGH | LOW | A- to A | HIGH | **28** |
| **2** | IDEA-04: GTFS-RT Cross-Entity Validator | HIGH | MEDIUM | MEDIUM | B+ to A- | MEDIUM-HIGH | **22** |
| **3** | IDEA-02: Physics-Constrained Calibration | HIGH | MEDIUM | LOW | A | MEDIUM-HIGH | **22** |
| **4** | IDEA-05: Contextual Calibration | MEDIUM | MEDIUM | LOW | B+ | MEDIUM | **19** |
| **5** | IDEA-07: DQ Benchmark | HIGH | HIGH | MEDIUM | B+ to A- | HIGH | **25** |
| **6** | IDEA-NEW-3: Incremental DCs for GPS | HIGH | MEDIUM | MEDIUM | B+ | MEDIUM | **20** |
| 7 | IDEA-10: Confidence Scoring | LOW | HIGH | LOW | B | MEDIUM | **15** |
| 8 | IDEA-NEW-1: Causal Attribution | MEDIUM | MEDIUM | MEDIUM | B+ | MEDIUM | **16** |
| ELIM | IDEA-01, 03, 06, 08, 09 | — | — | — | — | — | — |

---

### TOP 3 Recommendations

---

#### TOP-1: IDEA-NEW-2 — Integrated Trajectory Quality Scoring (T-Assess x ContextAware-DQ)

**Summary**: Combine the first trajectory quality scoring system (T-Assess, under review at VLDB 2025) with ContextAware-DQ's rule-based SYN/SEM/CRS taxonomy. Rule violations explain which quality dimensions are failing. Quality scores aggregate violations into an operational signal.

**Novelty**: First integration of rule-based DQ validation with trajectory-level quality scoring. T-Assess uses statistics; ContextAware-DQ uses rules — no prior work connects them.

**Feasibility**: VERY HIGH. Both systems exist. T-Assess code on GitHub. ContextAware-DQ rules implemented. Integration is API-level.

**Evaluation**: LOW risk. Synthetic ground truth works. TQS degradation measurable. NYC TLC has 3M records — trajectories of 50+ points achievable. Baseline: T-Assess alone, ContextAware-DQ alone.

**Grade Projection**: A- to A

**Confidence**: HIGH

**Key Strengths**:
1. **Under-review VLDB foundation**: T-Assess is the most recent trajectory quality paper — published after gap analysis. The integration opportunity is completely uncharted.
2. **Highest feasibility**: Both systems exist; evaluation methodology is standard (synthetic injection, bootstrap CI, degradation curves).
3. **Evaluable without IRB or user study**: No expert annotation, no controlled user study needed.
4. **Closed-loop system**: Rules detect violations → violations degrade scores → scores explain quality. This is a genuine systems contribution.
5. **Durable contribution**: T-Assess and ContextAware-DQ integration methodology will be cited regardless of ContextAware-DQ's ultimate deployment.

**Key Risks**:
1. **TQS weighting scheme** must be validated empirically. Define 3-5 variants; select best-performing against ground truth. Multiple comparisons require correction.
2. **T-Assess dependency**: T-Assess code must be integrated into ContextAware-DQ evaluation pipeline. API compatibility must be verified.
3. **Thesis framing**: Must clearly position as "T-Assess x ContextAware-DQ Integration" not "T-Assess applied to transportation." The integration methodology is the contribution.

**Required Pre-Conditions**:
1. Audit T-Assess API — verify integration points
2. Define TQS weighting scheme a priori (pre-register to avoid multiple comparisons inflation)
3. Implement ContextAware-DQ → T-Assess dimension mapper

---

#### TOP-2: IDEA-04 — Streaming GTFS-RT Cross-Entity Consistency Validator

**Summary**: Build the first streaming-native GTFS-RT validator with cross-entity consistency checking between VehiclePosition, TripUpdate, and Alert entities. Directly addresses GAP-06 and GAP-08.

**Novelty**: Cross-entity consistency validation is absent from CUTR (batch), Wong (describes but doesn't detect), and all surveyed streaming DQ frameworks.

**Feasibility**: MEDIUM (protobuf + multi-stream correlation is complex). CRS pre-investigation required (coordinate CRS for GTFS Malaysia).

**Evaluation**: MEDIUM risk. Synthetic injection works for CRS001/CRS002. CRS003 blocked by B2; fix or scope around.

**Grade Projection**: B+ to A-

**Confidence**: MEDIUM-HIGH

**Key Strengths**:
1. **CRITICAL gap**: GAP-06 and GAP-08 are both CRITICAL. Addresses the intersection of streaming + domain-specific rules.
2. **Operational value**: Transit agencies need real-time GTFS-RT quality monitoring. Clear end-user benefit.
3. **Cross-entity novelty**: Vehicle ↔ Trip ↔ Alert correlation is genuinely novel — no existing tool does this.

**Key Risks**:
1. **CUTR audit required**: Must prove CUTR lacks cross-entity checks before claiming "first."
2. **Protobuf expertise**: `gtfs-realtime-bindings` parsing in Spark streaming is non-trivial.
3. **GTFS CRS**: GTFS Malaysia coordinate reference system must be verified before Haversine calculations.

**Required Pre-Conditions**:
1. Audit CUTR GTFS-rt Validator rule set — confirm cross-entity absence
2. Verify GTFS Malaysia CRS (WGS84 expected)
3. Extend `gtfs_live.py` to emit typed events per entity

---

#### TOP-3: IDEA-07 — Streaming Transportation DQ Evaluation Benchmark

**Summary**: Build benchmark infrastructure (synthetic GTFS-RT generator + evaluation harness) for streaming transportation DQ. Directly addresses GAP-02 and GAP-12.

**Novelty**: First streaming DQ benchmark for transportation. NUMOSIM (SIGSPATIAL 2024) benchmarks anomaly detection, not DQ validation.

**Feasibility**: HIGH. Evaluation infrastructure is #1 priority anyway. Reuses existing replay patterns.

**Evaluation**: MEDIUM risk. NUMOSIM anomaly types map imperfectly to DQ rule types. Reproducibility requires thorough documentation.

**Grade Projection**: B+ to A-

**Confidence**: HIGH

**Key Strengths**:
1. **Durable contribution**: Benchmark papers are cited for years. Exathlon (VLDB 2021) still referenced in 2024.
2. **Enables comparison**: All future streaming DQ frameworks can be evaluated on this benchmark.
3. **Addresses GAP-02 and GAP-12**: Both are identified gaps with no existing solution.

**Key Risks**:
1. **NUMOSIM mapping**: Anomaly types don't map cleanly to DQ rule types. Must define explicit mapping and validate.
2. **Community adoption**: Benchmark has zero impact without adoption. But first evaluation is achievable regardless.
3. **Scope creep**: Building a comprehensive benchmark is unbounded. Must scope to ContextAware-DQ evaluation first.

**Required Pre-Conditions**:
1. Define NUMOSIM → DQ rule type mapping explicitly
2. Scope to ContextAware-DQ internal evaluation first
3. Publish reproducibility documentation

---

### Recommended Next Steps

**Step 1 — Commit to TOP-1 (IDEA-NEW-2) as primary thesis idea**

The T-Assess x ContextAware-DQ integration is the strongest idea: highest novelty, highest feasibility, lowest evaluation risk, A-grade projection.

**Step 2 — Choose TOP-2 or TOP-3 as secondary contribution**

| If... | Choose | Rationale |
|-------|--------|----------|
| GTFS Malaysia is accessible and CRS is verified | IDEA-04 (GTFS-RT Cross-Entity) | Clear operational impact, CRITICAL gaps |
| GTFS CRS is uncertain or protobuf expertise is lacking | IDEA-07 (Benchmark) | Highest feasibility, reusable infrastructure |

**Step 3 — Build evaluation module first (CRITICAL — blocks all evaluation)**

The `streamdq/evaluation/` module is the prerequisite for every evaluation in every idea. Build it first.

**Step 4 — Integrate T-Assess**

Audit T-Assess GitHub (ZJU-DAILY/T-Assess). Define ContextAware-DQ → T-Assess dimension mapper. Implement integration.

**Step 5 — Fix known blockers**

- B6: `processing_latency_ms` hardcoded to 0
- B2: CRS003 duplicate injection bug
- GTFS CRS pre-investigation

---

## Skill Usage Tracker

| Agent | Skill | Output |
|-------|-------|--------|
| GAP_ARCHITECT | project-idea-validator | 10 candidate ideas, gap deep analysis |
| ENGINEERING_REALIST | data-engineer | Technical feasibility, scoring matrix, verdicts |
| CRITERIA_JUDGE | scientific-critical-thinking | Fatal flaws, grade projections, contribution types |
| REACH_PUSHER | scientific-literature-researcher | 3 new ideas from live research, T-Assess finding |
| STATISTICAL_STRATEGIST | statistical-analysis | Evaluation design, feasibility matrix, statistical recommendations |
| ADVERSARIAL_DEBATE | (orchestrator) | 3-round attack/defense, elimination decisions |
| SYNTHESIS | (orchestrator) | Final ranking, TOP 3, next steps |

---

*Generated by 5 parallel brainstorming agents + adversarial debate. All claims grounded in literature evidence (T-Assess (under review at VLDB 2025), Martin et al. PVLDB 2025, XInsight SIGMOD 2023). No fabricated claims.*
