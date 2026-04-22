# AGENT-5: THREAT ANALYSIS — Competitor Preemption Risk & Defense Strategies

**Agent**: THREAT (Adversarial Competitive Analysis)
**Date**: April 22, 2026
**Input Files**: `final/02_IDEA_BRAINSTORM.md`, `final/AUDITS/audit_streaming_dq_frameworks.md`
**Output**: `final/AGENT_TRANSCRIPTS/agent05_THREAT.md`

---

## Methodology

This analysis applies the scientific-critical-thinking framework to evaluate preemption risk. For each competitor × idea pair, I assess whether the competitor could plausibly publish the same idea before the December 2026 submission. Risk is assessed on:

1. **Technical overlap**: Does the competitor have the same components?
2. **Publication timeline**: When could they realistically publish?
3. **Domain focus**: Is transportation/GPS their target domain?
4. **Integration novelty**: Is the specific combination novel, or just the components?

I distinguish between **component preemption** (competitor has the parts) and **integration preemption** (competitor combines them the same way). Integration novelty is harder to preempt.

---

## PHASE A — Competitor Preemption Analysis

### Competitor Profiles

#### C1: Stream DaQ (Papastergios & Gounaris, arXiv 2025)
- **Status**: Preprint on arXiv (cs.DB 2506.06147)
- **Code**: GitHub (Bilpapster/Stream-DaQ) — framework exists
- **Cross-record**: Listed as future work; no GPS trajectory analysis
- **Domain**: Generic; no GTFS-specific or transportation-specific rules
- **Adaptive thresholds**: Rolling μ±kσ — most sophisticated among competitors
- **Key weakness**: Generic framework, no domain-specific validation, arXiv preprint only
- **Threat level to this thesis**: LOW for domain ideas, MEDIUM for adaptive threshold ideas

#### C2: T-Assess Team (ZJU-DAILY, VLDB 2025)
- **Status**: Published at VLDB 2025
- **Code**: GitHub (ZJU-DAILY/T-Assess) — code exists
- **Domain**: Trajectory data quality scoring — first trajectory quality system
- **Approach**: Statistical quality dimensions (validity, completeness, consistency, fairness)
- **Supports**: Both offline and online (real-time stream) evaluation
- **Key weakness**: No rule-based DQ validation; no GPS-specific rules; no StreamDQ integration
- **Threat level to this thesis**: HIGH for IDEA-NEW-2 (direct overlap), LOW for everything else

#### C3: Weever Team (VLDB 2024)
- **Status**: Published at VLDB 2024
- **Code**: Not verified on GitHub
- **Domain**: General databases — no GPS/trajectory domain
- **Approach**: Incremental DC detection (denial constraints)
- **Key weakness**: General-purpose; GPS adaptation is absent; no transportation domain
- **Threat level to this thesis**: LOW for all ideas (domain mismatch is decisive)

#### C4: Industry (Grab, Confluent)
- **Status**: Engineering blogs; no academic publications
- **Code**: Internal/closed or loosely maintained
- **Domain**: Production FlinkSQL/Kafka DQ — no GPS-specific rules
- **Approach**: Static semantic rules in FlinkSQL; LLM-based rule recommendation (Grab)
- **Key weakness**: No academic paper trajectory; no cross-record GPS; no evaluation framework
- **Threat level to this thesis**: LOW (no academic paper threat)

#### C5: Unknown Researcher
- **Status**: Unknown
- **Domain**: Unknown
- **Approach**: Unknown
- **Risk**: Always present; cannot be defended against without early publication
- **Threat level**: Unquantifiable; mitigated by speed

---

### Per-Idea Preemption Analysis

#### IDEA-NEW-2: T-Assess x StreamDQ Integration

| Competitor | Preemption Risk | Reasoning |
|------------|---------------|----------|
| **Stream DaQ** | LOW | Generic framework; no trajectory quality scoring; would need to independently discover T-Assess integration opportunity |
| **T-Assess Team** | **HIGH** | They built T-Assess (VLDB 2025). They could trivially extend it with rule-based DQ validation and publish "T-Assess v2" at SIGMOD/VLDB 2026. Their VLDB 2025 paper explicitly supports online evaluation — they have the infrastructure. |
| **Weever** | LOW | General database focus; no trajectory domain; no integration incentive |
| **Industry** | LOW | No academic publication trajectory; no T-Assess integration interest |
| **Unknown** | MEDIUM | Could be working on the same integration; most dangerous vector |

**Critical vulnerability**: The T-Assess team has the most direct path to preemption. They authored the first trajectory quality system. Extending it with rule-based DQ validation (SYN/SEM/CRS rules) is a natural next step that they are well-positioned to execute. Their VLDB 2025 paper already supports online evaluation — they just need to add rules.

**Timing sensitivity**: The T-Assess team publishing a streaming extension in September 2026 (5 months from now) would directly preempt IDEA-NEW-2. Even if they don't call it "T-Assess x StreamDQ," the integration of trajectory quality scoring + rule-based validation would be non-novel by December 2026 submission.

---

#### IDEA-07: Streaming Transportation DQ Benchmark

| Competitor | Preemption Risk | Reasoning |
|------------|---------------|----------|
| **Stream DaQ** | LOW | No interest in publishing a benchmark for a competitor's (StreamDQ's) evaluation; they have their own internal metrics |
| **T-Assess** | LOW | T-Assess has their own evaluation; no incentive to build a benchmark for the transportation DQ field |
| **Weever** | LOW | General database focus; no transportation domain interest |
| **Industry** | MEDIUM | Grab or Confluent could publish "Transportation Streaming DQ Benchmark" as a blog post, not a paper — but industry blogs don't preempt academic submissions |
| **Unknown** | LOW | Benchmark papers require significant infrastructure investment; low probability of independent parallel development |

**Assessment**: Benchmark preemption risk is LOW. No competitor has the incentive to build a transportation DQ benchmark specifically for StreamDQ's evaluation. The infrastructure investment is substantial and the academic payoff is modest (benchmarks are cited but rarely win best paper). Stream DaQ and T-Assess have no incentive to build a benchmark that primarily benefits StreamDQ's evaluation.

**Key insight**: The benchmark is **defensive infrastructure**, not a competitive idea. It enables the thesis to claim reproducibility and comparative evaluation. Preemption would require a competitor to independently invest in the same infrastructure for their own evaluation — unlikely given their generic domain focus.

---

#### IDEA-04: GTFS-RT Cross-Entity Validator

| Competitor | Preemption Risk | Reasoning |
|------------|---------------|----------|
| **Stream DaQ** | LOW | No GTFS-RT domain interest; would need significant domain expertise investment |
| **T-Assess** | MEDIUM | T-Assess targets trajectory data broadly; GTFS-RT is a trajectory data source; they could extend to GTFS-RT validation. But their focus is quality scoring, not cross-entity consistency. |
| **Weever** | LOW | General database focus; no GTFS-RT domain |
| **Industry** | LOW | CUTR validator exists (2018) but is batch/periodic; no streaming cross-entity. Grab/Confluent have no academic paper trajectory. |
| **Unknown** | MEDIUM | Could be working on GTFS-RT streaming validation; no known prior work |

**Assessment**: Preemption risk is LOW. The cross-entity consistency problem (VehiclePosition ↔ TripUpdate ↔ Alert correlation) is specific enough that no surveyed competitor is working on it. The CUTR validator (batch) and Wong 2025 (describes but doesn't detect) are the closest prior work, but neither implements streaming cross-entity validation.

**Defensive argument**: The domain specificity (GTFS-RT protobuf + cross-entity correlation) is a moat. Competitors would need GTFS-RT domain expertise, Protobuf parsing skills, and streaming infrastructure — a combination that is rare.

---

#### IDEA-02: Physics-Constrained Calibration

| Competitor | Preemption Risk | Reasoning |
|------------|---------------|----------|
| **Stream DaQ** | MEDIUM | Stream DaQ uses rolling μ±kσ (adaptive thresholds). They could extend to physics-constrained calibration as part of their adaptive threshold methodology. However, their current approach is statistical, not physics-constrained. |
| **T-Assess** | LOW | T-Assess uses statistical quality dimensions; no physics-constrained calibration interest |
| **Weever** | LOW | DC detection; no calibration interest |
| **Industry** | LOW | No academic publication trajectory |
| **Unknown** | MEDIUM | Adaptive threshold calibration is a known research area; unknown researcher could independently propose physics-constrained calibration |

**Assessment**: Preemption risk is MEDIUM. The concept (physics constraints + data-driven calibration) is generalizable enough that Stream DaQ or an unknown researcher could independently propose it. Stream DaQ already has adaptive thresholds — adding physics constraints is an incremental extension. The question is whether they have the transportation domain motivation to apply it to GPS/trajectory data specifically.

**Defensive argument**: The **transportation-specific application** is the differentiator. Generic adaptive threshold calibration (Stream DaQ's approach) is different from physics-constrained calibration for GPS data. The novelty is in the application, not the general method.

---

#### IDEA-05: Contextual Calibration

| Competitor | Preemption Risk | Reasoning |
|------------|---------------|----------|
| **Stream DaQ** | **HIGH** | Stream DaQ uses rolling μ±kσ — this IS contextual calibration by another name. They have adaptive thresholds with contextual adaptation. Adding "transportation-specific context" (rush hour, highway vs. urban) is a small extension. |
| **T-Assess** | LOW | Statistical quality dimensions; no threshold calibration focus |
| **Weever** | LOW | DC detection; no calibration interest |
| **Industry** | MEDIUM | Grab's LLM-based rule recommendation could extend to contextual threshold adaptation |
| **Unknown** | MEDIUM | Adaptive threshold calibration is well-studied; could be independently proposed |

**Assessment**: Preemption risk is HIGH for the generic concept, MEDIUM for the transportation-specific application. Stream DaQ's rolling μ±kσ is essentially contextual calibration — they have the adaptive threshold infrastructure. The specific transportation context (rush hour speed limits, highway vs. urban zones) is the differentiation, but it's a parameter choice, not a novel method.

**Critical vulnerability**: If Stream DaQ publishes "Contextual Adaptive Thresholds for Transportation" as a follow-up, or if a student at another university independently proposes "contextual calibration for streaming DQ," the idea becomes non-novel. This is the most vulnerable idea to Stream DaQ preemption specifically.

---

#### IDEA-NEW-3: Incremental DCs for GPS

| Competitor | Preemption Risk | Reasoning |
|------------|---------------|----------|
| **Stream DaQ** | LOW | No DC formalism; keyed checks are not DCs |
| **T-Assess** | LOW | No DC interest; quality scoring focus |
| **Weever** | **HIGH** | Weever (VLDB 2024) is the first incremental DC detection system. They could trivially extend to GPS-specific DCs — they have the incremental DC infrastructure, they just need GPS domain expertise. |
| **Industry** | LOW | No DC formalism; no academic trajectory |
| **Unknown** | MEDIUM | DC research community is active; unknown researcher could propose GPS-specific DCs |

**Assessment**: Preemption risk is HIGH from Weever. Weever published incremental DC detection at VLDB 2024 — the foundational work is done. GPS-specific adaptation is a straightforward domain extension that Weever's team is well-positioned to execute. They would need GPS domain expertise (Haversine distance, GTFS-RT data model), but that's achievable.

**Defensive argument**: The Weever team targets general databases. GPS-specific predicate optimization (Haversine distance, speed constraints) requires domain-specific engineering that may be outside their research agenda. But this is a weak defense — they could collaborate with transportation researchers.

---

## PHASE B — Preemption Risk Matrix

| Idea | Stream DaQ | T-Assess | Weever | Industry | Unknown | AVG RISK |
|------|:----------:|:--------:|:------:|:--------:|:-------:|:--------:|
| **IDEA-NEW-2** (T-Assess x StreamDQ) | LOW | **HIGH** | LOW | LOW | MEDIUM | **MEDIUM-HIGH** |
| **IDEA-07** (Benchmark) | LOW | LOW | LOW | MEDIUM | LOW | **LOW** |
| **IDEA-04** (GTFS-RT Cross-Entity) | LOW | MEDIUM | LOW | LOW | MEDIUM | **LOW-MEDIUM** |
| **IDEA-02** (Physics-Constrained) | MEDIUM | LOW | LOW | LOW | MEDIUM | **LOW-MEDIUM** |
| **IDEA-05** (Contextual Calibration) | **HIGH** | LOW | LOW | MEDIUM | MEDIUM | **MEDIUM** |
| **IDEA-NEW-3** (Incremental DCs) | LOW | LOW | **HIGH** | LOW | MEDIUM | **MEDIUM-HIGH** |

### Matrix Interpretation

| Risk Level | Ideas | Implication |
|------------|-------|-------------|
| **HIGH** | IDEA-05 (vs. Stream DaQ), IDEA-NEW-3 (vs. Weever), IDEA-NEW-2 (vs. T-Assess) | These specific competitor-idea pairs have direct preemption paths |
| **MEDIUM** | IDEA-NEW-2 (vs. Unknown), IDEA-02 (vs. Stream DaQ + Unknown), IDEA-05 (vs. Unknown + Industry), IDEA-NEW-3 (vs. Unknown), IDEA-04 (vs. T-Assess + Unknown) | Parallel independent development is plausible |
| **LOW** | IDEA-07, IDEA-04, IDEA-02 (vs. most competitors) | No direct preemption path identified |

### Key Findings

1. **IDEA-NEW-2 (T-Assess x StreamDQ)** is the most preemption-prone idea due to T-Assess team having the foundational component (T-Assess itself). The integration with rule-based DQ is novel, but the T-Assess team could extend their own system.

2. **IDEA-05 (Contextual Calibration)** is vulnerable to Stream DaQ extending their existing adaptive threshold approach. Stream DaQ's rolling μ±kσ is already contextual — transportation-specific context is an incremental extension.

3. **IDEA-NEW-3 (Incremental DCs for GPS)** is vulnerable to Weever extending to GPS-specific DCs. Weever has the foundational framework; GPS adaptation is domain-specific but not methodologically novel.

4. **IDEA-07 (Benchmark)** is the most defensible idea. No competitor has the incentive to build a transportation DQ benchmark for StreamDQ's evaluation.

---

## PHASE C — Defense Strategies

### HIGH Preemption Risk: IDEA-NEW-2 vs. T-Assess Team

#### Threat Assessment
The T-Assess team (ZJU-DAILY, VLDB 2025) has the most direct preemption path:
- They authored T-Assess (first trajectory quality scoring system)
- Their paper explicitly supports online/streaming evaluation
- Rule-based DQ validation is a natural extension of quality scoring
- They have the code infrastructure (GitHub: ZJU-DAILY/T-Assess)
- A "T-Assess v2 with Rule-Based DQ" could be submitted to SIGMOD/VLDB 2026

#### Defense Arguments

**DA1 — Integration Novelty**: The specific integration of T-Assess quality dimensions + StreamDQ SYN/SEM/CRS rules is not obvious from T-Assess alone. T-Assess provides statistical quality dimensions; it has no rule-based DQ validation. The mapping (SYN rules → Validity, CRS rules → Consistency) requires transportation domain knowledge that T-Assess (general trajectory focus) doesn't have.

**DA2 — Evaluation Methodology**: The synthetic ground truth + degradation curve evaluation is specific to StreamDQ's evaluation framework. T-Assess evaluates on real trajectory data without ground truth injection. The evaluation methodology is as much a contribution as the integration itself.

**DA3 — Transportation Focus**: T-Assess targets trajectory data broadly (mobility data, vehicle trajectories). The specific GTFS-RT validation (protobuf parsing, cross-entity consistency, NYC taxi domain rules) is outside T-Assess's scope.

#### Timing Advantage

- **Current position**: April 22, 2026 — 8 months to December submission
- **T-Assess timeline**: If they submit a streaming extension at SIGMOD 2026 (Feb 1 deadline) or VLDB 2026 (Mar 1 deadline), they would publish before the December submission
- **Critical window**: SIGMOD 2026 results (acceptance/rejection) typically announced April-May 2026. If T-Assess submits a streaming extension to SIGMOD, we would know by May 2026 whether they preempted the idea.
- **VLDB 2026**: March 2026 submission deadline, June 2026 conference. This overlaps with our submission timeline.

#### Mitigation Strategy

**MS1 — Race to Publish**: File a preprint (arXiv) by July 2026 at the latest. Establish priority. A preprint establishes priority without peer review and can be updated.

**MS2 — Scope the Integration Narrowly**: Don't claim "T-Assess x StreamDQ Integration" broadly. Claim specifically: "Rule-Based DQ Validation as a Dimension in Trajectory Quality Scoring." The framing as a dimension extension (not a full integration) is more defensible and harder to preempt.

**MS3 — Publish the Evaluation First**: Submit the evaluation methodology (synthetic injection, degradation curves) as a separate technical report or workshop paper. This establishes priority on the evaluation approach before the full integration is submitted.

**MS4 — Monitor T-Assess GitHub**: Set up alerts for ZJU-DAILY/T-Assess repository. Any addition of rule-based validation is an early warning signal. Check arXiv weekly for new submissions from ZJU-DAILY authors.

**MS5 — Seek Collaboration**: Consider reaching out to the T-Assess team (ZJU-DAILY) to discuss collaboration. A joint paper is less likely to preempt and more likely to be synergistic. This is ethically appropriate if disclosed.

---

### HIGH Preemption Risk: IDEA-05 vs. Stream DaQ

#### Threat Assessment
Stream DaQ (arXiv 2025) uses rolling μ±kσ adaptive thresholds. This IS contextual calibration by another name:
- Rolling statistical baselines adapt to temporal context
- Keyed checks (per-taxi) adapt to entity context
- Dynamic context checks adapt to historical patterns

Adding "transportation-specific context" (rush hour vs. night, highway vs. urban) is a parameter choice, not a novel method. If Stream DaQ publishes "Adaptive Thresholds for Transportation Data" as a follow-up, or if their code adds transportation-specific context parameters, IDEA-05 becomes non-novel.

#### Defense Arguments

**DA1 — Transportation Domain Specificity**: Stream DaQ's adaptive thresholds are generic. The transportation-specific context (speed limits by road type, rush hour patterns, weekend vs. weekday) requires domain knowledge that Stream DaQ doesn't have. The specific calibration methodology (physics-constrained search over transportation-specific context cells) is novel.

**DA2 — Constrained Hypothesis Space**: Stream DaQ optimizes k in μ±kσ over unconstrained ranges. Physics-constrained calibration restricts the search to physically valid ranges first. This is a principled methodology, not just parameter tuning.

**DA3 — Evaluation on Transportation Data**: Stream DaQ evaluates on generic streaming data (no specific domain). Transportation-specific evaluation (NYC TLC, GTFS-RT) is a differentiated contribution.

#### Timing Advantage

- **Stream DaQ status**: arXiv preprint (June 2025). No indication of follow-up paper planned.
- **Stream DaQ authors**: Papastergios & Gounaris — their focus is on the Pathway framework, not transportation domain.
- **Window**: If Stream DaQ submits a transportation extension to EDBT/ICDT 2026 (March deadline), it would publish June 2026 — before December submission.

#### Mitigation Strategy

**MS1 — Reframe as IDEA-02 (Physics-Constrained)**: IDEA-05 (Contextual Calibration) is more easily preempted than IDEA-02 (Physics-Constrained). The physics constraint is a principled methodological contribution; "contextual calibration" is too close to Stream DaQ's existing approach.

**MS2 — Focus on Evaluation Novelty**: The specific evaluation design (synthetic injection with ground truth, per-context-cell precision/recall, bootstrap CI) is StreamDQ's differentiated contribution. Stream DaQ has no ground-truth evaluation methodology.

**MS3 — Document the Distinction Clearly**: In the paper, explicitly contrast with Stream DaQ's rolling μ±kσ: "Stream DaQ (Papastergios & Gounaris, 2025) uses rolling statistical baselines. We extend this with physics-constrained calibration over transportation-specific context dimensions."

---

### HIGH Preemption Risk: IDEA-NEW-3 vs. Weever Team

#### Threat Assessment
Weever (VLDB 2024) is the first incremental DC detection system. The foundational work is done:
- Weever has incremental DC detection infrastructure
- GPS-specific DCs (speed constraints, Haversine distance) are straightforward to express as formal DCs
- The Weever team could collaborate with transportation researchers to extend to GPS

The threat is real but weaker than T-Assess → IDEA-NEW-2 because Weever targets general databases, not transportation.

#### Defense Arguments

**DA1 — Domain Gap**: Weever targets general databases. GPS-specific predicate optimization (Haversine distance, speed constraints) requires domain-specific engineering that is outside Weever's research agenda.

**DA2 — DC Expression of GPS Rules**: The novel contribution is not the DC formalism (Weever) but the specific DC expressions for GPS constraints. CRS001 (GPS jump) as `¬(∃t₁,t₂: vehicle_id = v ∧ |t₂.ts − t₁.ts| = 30s ∧ Haversine(p₁, p₂) > MAX_JUMP)` is a novel DC expression, not a novel detection algorithm.

**DA3 — Evaluation on GPS Data**: Weever evaluates on general database workloads. GPS-specific evaluation (NYC TLC, GTFS-RT) is a differentiated contribution.

#### Timing Advantage

- **Weever status**: Published VLDB 2024. No indication of GPS extension planned.
- **Weever team focus**: Database theory and systems. Transportation domain is not their focus.

#### Mitigation Strategy

**MS1 — Scope as DC Expression, Not DC Detection**: Frame the contribution as "Formal DC Expressions for GPS Trajectory Constraints" — the novel contribution is the DC formalization of GPS rules, not the detection algorithm (which uses Weever's framework).

**MS2 — Publish DC Expressions as a Technical Report**: Establish priority on the DC expressions (CRS001, CRS002 as formal DCs) before Weever or anyone else formalizes them.

**MS3 — Collaborate with Weever Authors**: Cite Weever's incremental DC detection as the enabling technology. Frame the contribution as "building on Weever" rather than competing with them.

---

### MEDIUM Preemption Risk: IDEA-02 (Physics-Constrained) vs. Stream DaQ + Unknown

#### Defense Arguments

**DA1 — Methodology Novelty**: Physics-constrained calibration is a principled methodology, not just parameter tuning. The constrained hypothesis space (physical limits as prior) is a novel contribution that Stream DaQ's rolling μ±kσ doesn't address.

**DA2 — Addressing Martin et al. (PVLDB 2025)**: The 95% false positive rate in unconstrained DC discovery (Martin et al.) is a known problem. Physics-constrained calibration directly addresses this — constrain the hypothesis space to physically valid ranges, then calibrate from data. This is a response to a published PVLDB paper, not a response to Stream DaQ.

**DA3 — Transportation Domain Application**: The specific physics constraints (max speed, Haversine distance, position plausibility) are transportation-specific. Stream DaQ's generic adaptive thresholds don't address the false positive crisis in DC discovery.

#### Mitigation Strategy

**MS1 — Cite Martin et al. (PVLDB 2025) as Motivation**: Frame the contribution as a response to the false positive crisis in DC discovery, not as an extension of Stream DaQ's adaptive thresholds. This reframes the novelty claim.

**MS2 — Emphasize the Constraint**: The constrained hypothesis space (physics as prior) is the novel component. Without the physics constraint, the method degenerates to naive calibration.

**MS3 — Combine with IDEA-05 as Refinement**: IDEA-05 (Contextual Calibration) is the implementation; IDEA-02 (Physics-Constrained) is the methodology. Submit IDEA-02 as the primary contribution; IDEA-05 as a refinement.

---

### LOW Preemption Risk: IDEA-07 (Benchmark)

#### Defense Arguments

**DA1 — No Competitor Incentive**: No competitor (Stream DaQ, T-Assess, Weever) has the incentive to build a transportation DQ benchmark specifically for StreamDQ's evaluation. The infrastructure investment is substantial and the academic payoff is modest.

**DA2 — Reproducibility Contribution**: The benchmark enables reproducible evaluation of streaming DQ frameworks. This is a methodological contribution that benefits the community, not just StreamDQ.

**DA3 — Defensive Infrastructure**: The benchmark is defensive infrastructure, not a competitive idea. Even if preempted (unlikely), it enables the thesis to claim reproducibility and comparative evaluation.

#### Mitigation Strategy

**MS1 — Open-Source the Benchmark**: Publish the benchmark infrastructure on GitHub with an open-source license. This establishes the benchmark as a community resource and makes preemption less attractive (why compete with a free benchmark?).

**MS2 — Submit to Reproducibility Track**: Submit the benchmark to the VLDB/SIGMOD reproducibility track. This establishes priority and provides peer review of the methodology.

---

## PHASE D — Submission Timeline Reality Check

### Timeline Overview

| Date | Event | Impact |
|------|-------|--------|
| April 22, 2026 | Today | 8 months to December submission |
| June 2026 | Stream DaQ hypothetical publication (2 months) | Could preempt IDEA-05 |
| September 2026 | T-Assess team hypothetical streaming extension (5 months) | Could preempt IDEA-NEW-2 |
| October 2026 | Submission deadline (SIGMOD, if targeted) | Must have paper ready |
| December 2026 | Target conference submission | 8 months from now |
| April 2027 | Thesis defense | 12 months from now |

### Scenario 1: Stream DaQ Publishes June 2026 (2 months from now)

Stream DaQ publishes a transportation-specific extension or a journal paper with adaptive threshold details.

**Impact on ideas:**

| Idea | Impact | Severity | Survives? |
|------|--------|----------|-----------|
| IDEA-05 (Contextual Calibration) | HIGH — rolling μ±kσ for transportation preempts the generic concept | CRITICAL | **CONDITIONAL** — must emphasize physics constraint as the novel element |
| IDEA-02 (Physics-Constrained) | MEDIUM — Stream DaQ doesn't address the false positive crisis (Martin et al.) | MAJOR | **YES** — physics constraint is a principled response to PVLDB 2025 paper |
| IDEA-NEW-2 (T-Assess x StreamDQ) | LOW — different components | MINOR | **YES** |
| IDEA-07 (Benchmark) | LOW — no incentive to preempt | NONE | **YES** |
| IDEA-04 (GTFS-RT Cross-Entity) | LOW — domain-specific | NONE | **YES** |
| IDEA-NEW-3 (Incremental DCs) | LOW — Weever owns DC detection | NONE | **YES** |

**Ideas that become non-novel or severely weakened**: IDEA-05 (Contextual Calibration)

**Survival strategy**: If Stream DaQ publishes transportation-specific adaptive thresholds by June 2026, abandon IDEA-05 as a primary contribution. Reframe IDEA-02 (Physics-Constrained) as the primary adaptive threshold contribution. The physics constraint is a principled response to Martin et al. (PVLDB 2025), not an extension of Stream DaQ.

### Scenario 2: T-Assess Team Publishes Streaming Extension September 2026 (5 months from now)

T-Assess team publishes "T-Assess v2: Rule-Based DQ Validation for Trajectory Quality Scoring" at VLDB 2026 (March 2026 deadline) or as a journal extension.

**Impact on ideas:**

| Idea | Impact | Severity | Survives? |
|------|--------|----------|-----------|
| IDEA-NEW-2 (T-Assess x StreamDQ) | **HIGH** — if they add SYN/SEM/CRS rules to T-Assess, the integration becomes non-novel | CRITICAL | **CONDITIONAL** — must scope narrowly and file arXiv preprint first |
| IDEA-07 (Benchmark) | LOW — no incentive to preempt | NONE | **YES** |
| IDEA-04 (GTFS-RT Cross-Entity) | MEDIUM — T-Assess targets trajectory data; GTFS-RT is a trajectory source | MODERATE | **YES** — but must emphasize cross-entity specificity |
| IDEA-02 (Physics-Constrained) | LOW | NONE | **YES** |
| IDEA-05 (Contextual Calibration) | LOW | NONE | **YES** |
| IDEA-NEW-3 (Incremental DCs) | LOW — Weever owns DC detection | NONE | **YES** |

**Ideas that become non-novel or severely weakened**: IDEA-NEW-2 (T-Assess x StreamDQ) — most at risk

**Survival strategy**: This is the most dangerous scenario. The T-Assess team has the foundational system and could trivially add rule-based validation. Mitigation steps:

1. **ArXiv preprint by July 2026** (3 months) — establish priority on the integration methodology
2. **Scope narrowly**: Don't claim "integration of T-Assess and StreamDQ." Claim "rule-based DQ validation as a dimension in trajectory quality scoring." The framing as a dimension extension is more defensible.
3. **Focus on evaluation**: The synthetic ground truth + degradation curve evaluation is specific to StreamDQ's evaluation framework. Even if T-Assess adds rules, the evaluation methodology is novel.
4. **Monitor T-Assess GitHub weekly**: Any rule-based validation addition is an early warning signal. If seen, accelerate the arXiv preprint.

### Combined Scenario: Both Stream DaQ (June) and T-Assess (September) Publish

| Idea | Stream DaQ Impact | T-Assess Impact | Combined | Survives? |
|------|-------------------|-----------------|----------|-----------|
| IDEA-NEW-2 (T-Assess x StreamDQ) | LOW | HIGH | CRITICAL | **CONDITIONAL** — must scope narrowly + arXiv first |
| IDEA-07 (Benchmark) | LOW | LOW | NONE | **YES** |
| IDEA-04 (GTFS-RT Cross-Entity) | LOW | MEDIUM | MODERATE | **YES** — cross-entity specificity is the moat |
| IDEA-02 (Physics-Constrained) | MEDIUM | LOW | MEDIUM | **YES** — physics constraint is principled response to Martin et al. |
| IDEA-05 (Contextual Calibration) | HIGH | LOW | HIGH | **CONDITIONAL** — abandon if Stream DaQ publishes; reframe as IDEA-02 |
| IDEA-NEW-3 (Incremental DCs) | LOW | LOW | LOW | **YES** — Weever owns DC detection |

---

## PHASE E — Ranked Recommendations

### Preemption Risk Ranking (Most to Least Vulnerable)

| Rank | Idea | Primary Threat | AVG Risk | Recommendation |
|------|------|---------------|----------|----------------|
| **1 (Most Vulnerable)** | IDEA-NEW-2 (T-Assess x StreamDQ) | T-Assess team extending their own system | MEDIUM-HIGH | **Race to publish; scope narrowly; arXiv by July** |
| **2** | IDEA-05 (Contextual Calibration) | Stream DaQ extending adaptive thresholds | MEDIUM | **Reframe as IDEA-02 (Physics-Constrained); deprioritize as primary** |
| **3** | IDEA-NEW-3 (Incremental DCs) | Weever extending to GPS domain | MEDIUM-HIGH | **Frame as DC expression, not DC detection; cite Weever** |
| **4** | IDEA-02 (Physics-Constrained) | Stream DaQ + unknown researcher | LOW-MEDIUM | **Primary adaptive threshold contribution; cite Martin et al. as motivation** |
| **5** | IDEA-04 (GTFS-RT Cross-Entity) | T-Assess team extending to GTFS-RT | LOW-MEDIUM | **Audit CUTR first; emphasize cross-entity specificity** |
| **6 (Most Defensible)** | IDEA-07 (Benchmark) | Industry blog post | LOW | **Open-source + reproducibility track submission** |

### Defensive Priority Actions

**Tier 1 (Do immediately — within 1 month):**
1. Monitor T-Assess GitHub (ZJU-DAILY/T-Assess) weekly for rule-based DQ additions
2. Set arXiv alerts for Papastergios & Gounaris (Stream DaQ) for follow-up papers
3. Draft arXiv preprint outline for IDEA-NEW-2 (T-Assess x StreamDQ Integration) — file by July 2026

**Tier 2 (Do within 3 months — by July 2026):**
4. File arXiv preprint on IDEA-NEW-2 to establish priority
5. Audit CUTR GTFS-rt Validator rule set for cross-entity absence
6. Open-source benchmark infrastructure (IDEA-07) on GitHub
7. Submit benchmark to VLDB/SIGMOD reproducibility track

**Tier 3 (Do within 6 months — by October 2026):**
8. Complete evaluation for IDEA-NEW-2 (synthetic injection + degradation curves)
9. Submit conference paper with strongest surviving idea
10. Prepare backup idea (IDEA-02 or IDEA-07) if primary is preempted

### Submission Strategy Recommendation

**Primary**: IDEA-NEW-2 (T-Assess x StreamDQ) with IDEA-07 (Benchmark) as evaluation infrastructure
- Highest novelty + highest feasibility (per brainstorming)
- Most at risk from T-Assess team preemption — but race conditions favor early mover
- File arXiv preprint by July 2026 to establish priority

**Backup**: If IDEA-NEW-2 is preempted by T-Assess in September 2026:
- Pivot to IDEA-02 (Physics-Constrained Calibration) as primary
- IDEA-07 (Benchmark) remains as infrastructure contribution
- IDEA-04 (GTFS-RT Cross-Entity) as domain-specific contribution

**Contingency**: If both Stream DaQ (June) and T-Assess (September) preempt IDEA-05 and IDEA-NEW-2:
- Abandon both
- Submit IDEA-02 (Physics-Constrained) + IDEA-07 (Benchmark) + IDEA-04 (GTFS-RT Cross-Entity)
- IDEA-04's domain specificity (cross-entity consistency) is the strongest remaining differentiator

---

## Appendix: Scientific-Critical-Thinking Audit of the Ideas

### IDEA-NEW-2 — Fatal Flaw Check

Applying the scope mismatch attack from the critical thinking framework:

> The paper (T-Assess, VLDB 2025) claims to assess trajectory data quality. However, their architecture uses statistical quality dimensions (validity, completeness, consistency, fairness) computed from trajectory features. It has no rule-based DQ validation. StreamDQ's SYN/SEM/CRS rules detect specific violations (null, range, speed, GPS jump) that statistical methods cannot detect. Therefore, by design, T-Assess CANNOT detect rule-based violations. We demonstrate this empirically in Section X.

**Counter-attack (competitor's response)**: "T-Assess v2 could trivially add rule-based validation as a module. Statistical quality scoring + rule-based DQ is an obvious composition."

**Defense**: The integration methodology (how violations map to quality scores, how to weight violations vs. statistical anomalies) is non-trivial. But this is a WEAK defense — the composition is obvious to any systems researcher.

**Honest assessment**: IDEA-NEW-2 is the most novel idea and the most at risk. The race condition is real. File arXiv by July 2026.

### IDEA-07 — Scope Mismatch Check

> The paper (NUMOSIM, SIGSPATIAL 2024) benchmarks anomaly detection. However, anomaly detection (detecting unusual patterns) is fundamentally different from DQ validation (detecting specification violations). NUMOSIM cannot evaluate DQ rule precision/recall because it has no ground truth for violations. Therefore, by design, NUMOSIM CANNOT be used for DQ benchmark evaluation.

**Assessment**: This attack is valid and helps IDEA-07. NUMOSIM benchmarks AD, not DQ. StreamDQ's benchmark fills a genuine gap.

### IDEA-05 — Claim vs. Reality Check

| Claim (paper) | Reality |
|--------------|---------|
| "Contextual calibration adapts to transportation context" | Stream DaQ already does rolling μ±kσ — same thing, different name |
| "Novel methodology" | Rolling statistics is well-established; transportation context is parameter choice |

**Assessment**: IDEA-05 is too close to Stream DaQ. Reframe as IDEA-02 (Physics-Constrained) to emphasize the principled methodology.

---

*Analysis by AGENT-5: THREAT using scientific-critical-thinking framework. All preemption assessments are honest estimates based on competitor publication status and domain focus. Risk levels reflect plausible preemption paths, not certainties.*
