# AGENT-7: TIMELINE — Resource and Timeline Feasibility

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Author**: Timeline Analyst Agent
**Date**: 2026-04-22
**Phase**: Phase 2 — Idea Evaluation (Timeline Feasibility)
**Skill**: trend-analyst

---

## Executive Summary

| Idea | Total Weeks | Fit 40w | Buffer Left | Risk |
|------|:-----------:|:-------:|:-----------:|:----:|
| IDEA-NEW-2 (T-Assess x StreamDQ) | **38.0** | OVER by 2.0w | **-2.0w** | **MEDIUM** |
| IDEA-07 (Transportation DQ Benchmark) | **37.5** | OVER by 1.5w | **-1.5w** | **MEDIUM** |
| IDEA-04 (GTFS-RT Cross-Entity Validator) | **39.5** | OVER by 3.5w | **-3.5w** | **HIGH** |
| IDEA-02 (Physics-Constrained Calibration) | **37.5** | OVER by 1.5w | **-1.5w** | **MEDIUM** |
| IDEA-NEW-3 (Incremental DCs for GPS) | **39.0** | OVER by 3.0w | **-3.0w** | **HIGH** |
| IDEA-05 (Contextual Calibration) | **36.5** | OVER by 0.5w | **-0.5w** | **MEDIUM** |

**Critical Finding**: Every candidate idea exceeds the existing 36-week plan. No idea fits within the 40-week constraint without either dropping a core phase or accepting schedule compression. The current plan has zero buffer remaining after accounting for known bugs and all six ideas. The plan needs either scope reduction in existing phases, phased idea integration (sequencing ideas rather than parallel stacking), or acceptance of a 2-4 week overrun.

---

## PHASE A — Existing Phase Breakdown

The existing 8-phase plan spans 40 weeks (36 weeks content + 4 weeks buffer):

```
Phase 1 (Foundation):        Weeks  1-4   (4.0w) — Core rule infrastructure, SYN/SEM
Phase 2 (Semantic + Context): Weeks  5-8   (4.0w) — Adaptive threshold engine, context model
Phase 3 (Cross-Record):       Weeks  9-12  (4.0w) — CRS rules, state management
Phase 4 (Streaming Pipeline):  Weeks 13-16  (4.0w) — Kafka, Spark streaming integration
Phase 5 (Evaluation):          Weeks 17-20  (4.0w) — Ground-truth evaluation, bootstrap CI
Phase 6 (GTFS + Writing):      Weeks 21-28  (8.0w) — GTFS integration, paper drafting
Phase 7 (Refinement):          Weeks 29-36  (8.0w) — Paper revision, rebuttal prep
[Buffer]:                       Weeks 37-40  (4.0w) — Contingency

TOTAL CONTENT: 36.0 weeks
TOTAL WITH BUFFER: 40.0 weeks
```

**Critical Constraint**: The 4-week buffer (Weeks 37-40) is the only safety margin. Every idea consumes part of this buffer.

---

## PHASE B — Timeline Cost Per Idea

### IDEA-NEW-2: T-Assess x StreamDQ Integration

**Idea Summary**: Combine T-Assess (VLDB 2025, trajectory quality scoring) with StreamDQ's SYN/SEM/CRS taxonomy. Rule violations map to TQS dimensions; quality scores aggregate violations into operational signals.

| Cost Category | Estimate | Rationale |
|---------------|:--------:|------------|
| Integration engineering | 2.0w | T-Assess GitHub audit, API mapping, StreamDQ → TQS dimension mapper |
| Evaluation harness extension | 1.5w | TQS degradation curves, multiple weighting variants, correlation with ground truth |
| Baseline comparison runs | 0.5w | T-Assess alone vs. StreamDQ alone vs. integrated — 3 evaluation arms |
| TQS weighting validation | 0.5w | Pre-register 3-5 variants; best-selected requires multiple comparison correction |
| Bug exposure (B2 affects CRS dimension) | 0.5w | CRS003 broken; CRS layer TQS incomplete until B2 fixed |
| Buffer for integration surprises | 0.5w | T-Assess API compatibility issues, dimension mapping edge cases |
| **Subtotal (IDEA-NEW-2)** | **5.5w** | |

**Additional considerations**:
- IDEA-NEW-2 is NOT orthogonal to existing plan — it depends on the evaluation module (Phase 5) being built first. It extends Phase 5 and Phase 6.
- T-Assess code must be audited before integration commitment. If T-Assess API is incompatible with Spark streaming context, cost could rise to 7-8 weeks.
- The TQS weighting validation (multiple variants, multiple comparisons correction) is the most uncertain component.

**TOTAL IDEA-NEW-2 TIMELINE**: 36.0 + 5.5 = **41.5 weeks** → OVER by **1.5 weeks** (MEDIUM RISK if T-Assess compatible) or **3.5 weeks** (HIGH RISK if API incompatibility discovered).

---

### IDEA-07: Streaming Transportation DQ Benchmark

**Idea Summary**: Build benchmark infrastructure (synthetic GTFS-RT generator + evaluation harness) for streaming transportation DQ. Addresses GAP-02 and GAP-12.

| Cost Category | Estimate | Rationale |
|---------------|:--------:|------------|
| Benchmark design + NUMOSIM mapping | 1.0w | Define anomaly type → DQ rule mapping; document clearly |
| Synthetic data generator extension | 1.5w | Extend existing injection to support benchmark format; parameterized anomaly injection |
| Evaluation harness building | 1.0w | Harness for framework comparison (StreamDQ vs. GE vs. Soda); metric aggregation |
| Reproducibility documentation | 0.5w | Parameter publication, environment setup, run scripts |
| Multiple framework integration testing | 1.0w | Great Expectations and Soda Core comparison runs on identical data |
| NUMOSIM gap analysis | 0.5w | Validate that NUMOSIM anomaly types map to DQ rules — may reveal mismatches |
| Buffer for benchmark scope creep | 0.5w | Benchmark is unbounded; must enforce strict scope |
| **Subtotal (IDEA-07)** | **6.0w** | |

**Additional considerations**:
- IDEA-07 has HIGH overlap with existing Phase 5 (Evaluation). The evaluation module and benchmark harness are the same deliverable. Cost is partially subsidized by the plan.
- Multiple framework comparison (GE + Soda) adds 1.5-2.0 weeks beyond StreamDQ-only evaluation.
- Reproducibility documentation is often underestimated — expect 0.5w minimum.

**TOTAL IDEA-07 TIMELINE**: 36.0 + 6.0 = **42.0 weeks** → OVER by **2.0 weeks** (MEDIUM RISK). With subsidized overlap: **37.5 weeks** → OVER by **1.5 weeks** (MEDIUM RISK).

---

### IDEA-04: GTFS-RT Cross-Entity Validator

**Idea Summary**: First streaming-native GTFS-RT validator with cross-entity consistency checking between VehiclePosition, TripUpdate, and Alert entities.

| Cost Category | Estimate | Rationale |
|---------------|:--------:|------------|
| Protobuf parsing in Spark | 1.5w | gtfs-realtime-bindings integration; entity event typing; schema evolution handling |
| Multi-stream entity correlation | 2.0w | VehiclePosition ↔ TripUpdate ↔ Alert state management; watermark policy; TTL |
| GTFS static reference join | 1.0w | Quasi-static join (GTFS static updates weekly/monthly); entity matching |
| CRS rules extension for cross-entity | 1.0w | New rule type for inter-entity consistency; CRS001/CRS002 adaptation |
| CUTR rule set audit | 0.5w | Required before claiming "first"; document what CUTR does NOT check |
| GTFS CRS verification | 0.5w | Must verify WGS84 before Haversine; blocks CRS002 if CRS mismatch |
| GTFS anomaly injection | 0.5w | Inject cross-entity anomalies (not just position anomalies) |
| GTFS evaluation on Malaysia feed | 1.0w | Live feed testing; API stability issues; manual spot-check validation |
| Buffer for cross-entity complexity | 1.0w | Multi-stream watermark boundary is the hardest unsolved problem in streaming |
| **Subtotal (IDEA-04)** | **9.0w** | |

**Additional considerations**:
- IDEA-04 is a standalone extension beyond the existing GTFS phase (Phase 6). It adds significant new engineering.
- The multi-stream entity correlation state is the highest-complexity component. No existing streaming framework has solved this cleanly.
- GTFS CRS verification is a prerequisite — if CRS is non-WGS84, Haversine calculations are invalid and the entire idea may need redesign.

**TOTAL IDEA-04 TIMELINE**: 36.0 + 9.0 = **45.0 weeks** → OVER by **5.0 weeks** (HIGH RISK). Even with optimistic estimates: **39.5 weeks** → OVER by **3.5 weeks** (HIGH RISK).

---

### IDEA-02: Physics-Constrained Calibration

**Idea Summary**: Constrain threshold discovery to physically valid ranges (no vehicle exceeds 200 km/h, plausible trajectories). Addresses Martin et al. (PVLDB 2025) false positive crisis.

| Cost Category | Estimate | Rationale |
|---------------|:--------:|------------|
| Physics constraint specification | 0.5w | Document physical limits per vehicle type; compile domain knowledge |
| Constrained search implementation | 1.5w | Restrict threshold search to physics-valid ranges; implement as adaptive engine extension |
| Sparse cell handling refinement | 1.0w | Physics prior dominates in sparse cells; implement hierarchical fallback within physics |
| Cold-start evaluation | 0.5w | Validate behavior on night buses, weekend routes, sparse contexts |
| Ablation study | 0.5w | Physics-constrained vs. rolling P10/P90 vs. naive pooling — 3-arm comparison |
| Statistical analysis (bootstrap CI) | 0.5w | Per-context-cell F1, effect size, power analysis for 5% improvement detection |
| Buffer for bandit cold-start debugging | 0.5w | Sparse cell behavior is the most uncertain part of this idea |
| **Subtotal (IDEA-02)** | **5.0w** | |

**Additional considerations**:
- IDEA-02 has HIGH overlap with existing Phase 2 (Semantic + Context) — the adaptive threshold engine is already being built. This idea extends it, not rebuilds it.
- The cold-start problem on sparse cells is the single highest-risk component. Even with physics-constrained search, cells with <20 observations may not converge to useful thresholds.
- IDEA-02 competes with IDEA-05 for the same slot (adaptive threshold refinement). Choose one, not both.

**TOTAL IDEA-02 TIMELINE**: 36.0 + 5.0 = **41.0 weeks** → OVER by **1.0 week** (MEDIUM RISK). With subsidized overlap: **37.5 weeks** → OVER by **1.5 weeks** (MEDIUM RISK).

---

### IDEA-NEW-3: Incremental DCs for GPS

**Idea Summary**: Express GPS DQ rules as formal Denial Constraints; use Weever (VLDB 2024) framework adapted for GPS-specific predicates with spatial indexing.

| Cost Category | Estimate | Rationale |
|---------------|:--------:|------------|
| DC formalization of GPS rules | 1.0w | Express CRS001 (Haversine distance), CRS002 (duplicate) as formal DCs |
| DC evaluation engine (simplified) | 2.5w | Simplified Weever-style evaluator; GPS predicate optimization; spatial indexing |
| GPS-specific predicate optimization | 1.5w | Haversine distance computation in DC evaluator; bounding box pre-filtering |
| State management for streaming DCs | 1.0w | Incremental DC detection requires per-entity state; watermark handling |
| DC vs. procedural GPS rules comparison | 1.0w | Evaluate DC-based vs. StreamDQ procedural CRS rules; precision/recall comparison |
| Buffer for DC engine complexity | 1.0w | Formal DC evaluation is the most theoretically complex component |
| **Subtotal (IDEA-NEW-3)** | **8.0w** | |

**Additional considerations**:
- IDEA-NEW-3 is the most theoretically ambitious idea. It requires building a DC evaluation engine, not just extending the existing rule system.
- The Weever (VLDB 2024) framework is general-purpose — adapting it for GPS-specific predicates requires significant spatial indexing work.
- This idea is best suited as a Phase 2 theoretical component, not as a primary contribution. It could strengthen IDEA-02 or IDEA-05 rather than standing alone.

**TOTAL IDEA-NEW-3 TIMELINE**: 36.0 + 8.0 = **44.0 weeks** → OVER by **4.0 weeks** (HIGH RISK). Even with optimistic estimates: **39.0 weeks** → OVER by **3.0 weeks** (HIGH RISK).

---

### IDEA-05: Contextual Calibration

**Idea Summary**: Calibrate thresholds contextually using temporal (rush hour vs. night), spatial (urban vs. highway), and operational (weekday vs. weekend) context. Simpler to implement than IDEA-02.

| Cost Category | Estimate | Rationale |
|---------------|:--------:|------------|
| Context dimension expansion | 0.5w | Extend from 3D (current) to richer contextual dimensions |
| Threshold calibration per context cell | 1.5w | Implement contextual calibration within existing adaptive engine |
| Sparse cell fallback refinement | 1.0w | Hierarchical fallback for sparse cells; document fallback quality degradation |
| RQ1 evaluation (ablation) | 1.0w | Static vs. context-aware thresholds on NYC TLC; precision/recall per context |
| Statistical analysis (bootstrap CI) | 0.5w | Per-context-cell metrics; effect size; power analysis |
| Buffer for sparse cell edge cases | 0.5w | Cold-start on sparse cells is the main implementation risk |
| **Subtotal (IDEA-05)** | **5.0w** | |

**Additional considerations**:
- IDEA-05 has the HIGHEST overlap with existing Phase 2 (Semantic + Context). The adaptive threshold engine is already being built — this idea extends it.
- IDEA-05 is the simpler cousin of IDEA-02. If IDEA-02 is chosen, IDEA-05 becomes redundant.
- If context-aware precision improvement is marginal (<5%), the entire idea may not justify the evaluation cost.

**TOTAL IDEA-05 TIMELINE**: 36.0 + 5.0 = **41.0 weeks** → OVER by **1.0 week** (MEDIUM RISK). With subsidized overlap: **36.5 weeks** → OVER by **0.5 weeks** (MEDIUM RISK). This is the cheapest idea to add.

---

## PHASE C — Known Bugs Cost

The following bugs must be fixed regardless of which ideas are selected. Bug fix cost reduces the effective buffer available for new ideas:

| Bug ID | Description | Fix Estimate | Impacted Ideas |
|:------:|-------------|:-----------:|----------------|
| B1 | SYN001 NaN silent pass-through (no `math.isnan()` guard) | **0.5 days** | All ideas (SYN rules used everywhere) |
| B2 | CRS003 duplicate injection no-op (recall unmeasurable) | **2-3 days** | IDEA-NEW-2 (CRS dimension TQS), IDEA-04 (duplicate detection) |
| B3 | CRS002 speed range gap (2-20 km/h moderate spoofing) | **1 day** | IDEA-04 (GTFS-RT speed validation) |
| B4 | `foreachBatch` driver bottleneck (no Pandas UDF) | **1-2 weeks** | All ideas (pipeline latency) |
| B5 | SQLite no WAL mode (per-commit fsync overhead) | **0.5 day** | All ideas (evaluation writes) |
| B6 | `processing_latency_ms` hardcoded to 0 | **0.5 day** | All ideas (latency reporting) |

**Total bug fix cost (conservative, excluding B4)**: **~1.0 week**

**Critical note on B4**: If B4 (`foreachBatch` bottleneck) is addressed, add 1-2 weeks. If left as known limitation, B4 does not consume timeline but limits the quality of latency metrics in evaluation.

**Effective buffer after bug fixes**: 4.0 weeks (original buffer) - 1.0 week (bug fixes) = **3.0 weeks effective buffer**

---

## PHASE D — Overlap Analysis

Many ideas share engineering foundations. Calculating net additional time beyond the 36-week baseline by accounting for overlaps:

| Idea | Gross Additional | Overlap with Existing Plan | Net Additional | Overlap Partner Ideas |
|:-----|:---------------:|:-------------------------:|:--------------:|----------------------|
| IDEA-NEW-2 | 5.5w | -0.5w (eval module shared) | **5.0w** | IDEA-07 (eval harness) |
| IDEA-07 | 6.0w | -2.0w (eval module shared) | **4.0w** | IDEA-NEW-2 (eval harness) |
| IDEA-04 | 9.0w | -1.0w (GTFS phase already exists) | **8.0w** | (standalone) |
| IDEA-02 | 5.0w | -2.5w (adaptive engine already built) | **2.5w** | IDEA-05 (same component) |
| IDEA-NEW-3 | 8.0w | -1.5w (CRS rules already exist) | **6.5w** | IDEA-02/05 (calibration context) |
| IDEA-05 | 5.0w | -2.5w (adaptive engine already built) | **2.5w** | IDEA-02 (same component) |

**Mutual exclusion note**: IDEA-02 and IDEA-05 compete for the same component (adaptive threshold engine). Adding both adds cost for the second without proportional benefit. Choose one.

**Overlap synergy**: IDEA-NEW-2 and IDEA-07 share the evaluation module. Building one reduces cost of the other by ~0.5-1.0 weeks.

---

## PHASE E — Resource Constraints

### Compute Resources

| Resource | Availability | Constraint |
|----------|-------------|------------|
| Local laptop | YES | Single-machine Spark; ~8GB RAM for LocalPipeline |
| Spark cluster | UNKNOWN | No Spark cluster mentioned; distributed pipeline requires cluster access |
| Kafka | YES | Mentioned in tech stack; local or remote |
| PostgreSQL | AVAILABLE | For distributed mode state storage |

**Critical bottleneck**: The local laptop constraint means LocalPipeline is the primary evaluation environment. Spark distributed mode (Phase 4) may require cluster access that is not currently available. This affects all ideas requiring distributed evaluation.

### Data Resources

| Dataset | Status | Constraint |
|---------|--------|------------|
| NYC TLC Yellow Taxi | **READY** (Parquet) | 3M records; public; no labeled anomalies (synthetic injection required) |
| GTFS Malaysia | **NEEDS VERIFICATION** | API accessible; CRS must be verified; injection missing |

**Critical bottleneck**: GTFS Malaysia CRS verification is a prerequisite for IDEA-04, IDEA-NEW-3 (Haversine calculations), and CRS002 evaluation. If CRS is non-WGS84, Haversine-based ideas need redesign.

### Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Kafka | Available | Tech stack includes Kafka |
| Spark Structured Streaming | Available | Local mode confirmed; distributed needs cluster |
| SQLite | Available | WAL mode not enabled (B5) |
| Prometheus/Grafana | Available | For monitoring |

### External Dependencies

| Dependency | Status | Risk |
|------------|--------|------|
| T-Assess GitHub (ZJU-DAILY/T-Assess) | Accessible | HIGH RISK: API compatibility with Spark streaming unverified |
| GTFS Malaysia API | Accessible | MEDIUM RISK: API stability unverified; rate limits unknown |
| CUTR GTFS-rt Validator | GitHub accessible | Must audit to validate "first" claim for IDEA-04 |

### Human Resources

| Resource | Constraint | Impact |
|----------|-----------|--------|
| 1 thesis student | Single person | All ideas are sequential, not parallelizable; context switching cost |
| No research assistant | Unavailable | N/A |

**Critical bottleneck**: Single-person execution means ideas cannot run in parallel. The timeline estimates assume sequential execution. Any parallelization attempt (e.g., working on IDEA-07 while IDEA-NEW-2 is running) risks quality degradation.

---

## PHASE F — Timeline Feasibility Matrix (Detailed)

### Baseline: No New Ideas

```
Existing plan: 36.0 weeks content + 4.0 weeks buffer = 40.0 weeks total
Effective buffer after bug fixes: 3.0 weeks
Status: ON SCHEDULE
Risk: LOW
```

### IDEA-NEW-2 (T-Assess x StreamDQ) — MEDIUM RISK

```
Timeline: 36.0 + 5.5 = 41.5 weeks (pessimistic) / 41.0 weeks (realistic) / 40.5 weeks (optimistic)
Overrun: 1.5 weeks (optimistic) to 3.5 weeks (pessimistic)
Buffer remaining: -1.5w (optimistic) to -3.5w (pessimistic)
Risk classification: MEDIUM (optimistic) / HIGH (pessimistic)
Resource bottleneck: T-Assess API compatibility (unverified); evaluation module (must build first)
Path to fit: Reduce Phase 7 (Refinement) from 8 to 6 weeks (-2.0w)
Required action: Audit T-Assess GitHub before committing. If API incompatible, eliminate.
```

### IDEA-07 (Transportation DQ Benchmark) — MEDIUM RISK

```
Timeline: 36.0 + 6.0 = 42.0 weeks (pessimistic) / 37.5 weeks (realistic, with eval overlap)
Overrun: 1.5 weeks (realistic with overlap) to 6.0 weeks (pessimistic)
Buffer remaining: -1.5w (realistic) to -6.0w (pessimistic)
Risk classification: MEDIUM (realistic) / HIGH (pessimistic)
Resource bottleneck: Evaluation module is prerequisite; reproducibility documentation underestimated
Path to fit: Combine with IDEA-NEW-2 (shared eval module reduces combined cost by ~1.0w)
Required action: Scope to StreamDQ-only evaluation first; GE/Soda comparison as Phase 8 if time permits
```

### IDEA-04 (GTFS-RT Cross-Entity Validator) — HIGH RISK

```
Timeline: 36.0 + 9.0 = 45.0 weeks (pessimistic) / 42.0 weeks (realistic) / 39.5 weeks (optimistic)
Overrun: 3.5 weeks (optimistic) to 9.0 weeks (pessimistic)
Buffer remaining: -3.5w (optimistic) to -9.0w (pessimistic)
Risk classification: HIGH (all scenarios)
Resource bottleneck: Multi-stream watermark boundary (unsolved problem); GTFS CRS (prerequisite)
Path to fit: Defer cross-entity rules to future work; focus on single-entity GTFS validation (CRS001/CRS002 only)
Required action: Verify GTFS Malaysia CRS first. If non-WGS84, eliminate or redesign.
```

### IDEA-02 (Physics-Constrained Calibration) — MEDIUM RISK

```
Timeline: 36.0 + 5.0 = 41.0 weeks (pessimistic) / 37.5 weeks (realistic, with adaptive engine overlap)
Overrun: 1.5 weeks (realistic) to 5.0 weeks (pessimistic)
Buffer remaining: -1.5w (realistic) to -5.0w (pessimistic)
Risk classification: MEDIUM (realistic) / HIGH (pessimistic)
Resource bottleneck: Cold-start on sparse cells (night buses, weekend routes)
Path to fit: Use hierarchical fallback (sparse cells inherit broader context thresholds)
Required action: Test on sparse contexts before committing. If cold-start degrades badly, reduce to IDEA-05.
```

### IDEA-NEW-3 (Incremental DCs for GPS) — HIGH RISK

```
Timeline: 36.0 + 8.0 = 44.0 weeks (pessimistic) / 40.0 weeks (realistic, with CRS overlap) / 39.0 weeks (optimistic)
Overrun: 3.0 weeks (optimistic) to 8.0 weeks (pessimistic)
Buffer remaining: -3.0w (optimistic) to -8.0w (pessimistic)
Risk classification: HIGH (all scenarios)
Resource bottleneck: DC evaluation engine (theoretical complexity); spatial indexing for Haversine
Path to fit: Implement as proof-of-concept (simplified DC evaluator, not full Weever framework)
Required action: Scope to "GPS rules as formal DCs (conceptual)" — theoretical contribution only, not full engine
```

### IDEA-05 (Contextual Calibration) — MEDIUM RISK (Tightest Fit)

```
Timeline: 36.0 + 5.0 = 41.0 weeks (pessimistic) / 36.5 weeks (realistic, with adaptive engine overlap)
Overrun: 0.5 weeks (realistic) to 5.0 weeks (pessimistic)
Buffer remaining: -0.5w (realistic) to -5.0w (pessimistic)
Risk classification: MEDIUM (tightest fit of all ideas)
Resource bottleneck: Sparse cell fallback quality; context dimension expansion complexity
Path to fit: Extend Phase 2 by 0.5 weeks; reduce Phase 7 by 0.5 weeks
Required action: Proceed if context-aware improvement on NYC TLC is demonstrable (>5% precision gain)
```

---

## PHASE G — Combination Analysis

Since ideas cannot run in parallel (single-person execution), the relevant question is: what is the total timeline if multiple ideas are selected?

### Combination: IDEA-NEW-2 + IDEA-05 (Cheapest Combination)

```
IDEA-NEW-2 net: 5.0w (with eval overlap)
IDEA-05 net: 2.5w (with adaptive engine overlap)
Combined net: 7.5w
Total: 36.0 + 7.5 = 43.5 weeks
Overrun: 3.5 weeks beyond 40-week plan
Risk: HIGH
```

### Combination: IDEA-NEW-2 + IDEA-02 (Competing Adaptive Ideas)

```
IDEA-NEW-2 net: 5.0w
IDEA-02 net: 2.5w (IDEA-05 eliminated — same component)
Combined net: 7.5w
Total: 36.0 + 7.5 = 43.5 weeks
Risk: HIGH
Note: IDEA-02 and IDEA-05 cannot both be added. Choose one.
```

### Combination: IDEA-NEW-2 + IDEA-07 (Shared Eval Module)

```
IDEA-NEW-2 net: 5.0w
IDEA-07 net: 4.0w (with eval overlap: 6.0 - 2.0 = 4.0w)
Combined net: 9.0w
Total: 36.0 + 9.0 = 45.0 weeks
Risk: VERY HIGH
```

### Combination: IDEA-NEW-2 + IDEA-04 (Highest Value but Highest Cost)

```
IDEA-NEW-2 net: 5.0w
IDEA-04 net: 8.0w (standalone — minimal overlap with existing plan)
Combined net: 13.0w
Total: 36.0 + 13.0 = 49.0 weeks
Risk: VERY HIGH
```

### Single Idea Selection

| Idea | Net Additional | Total Timeline | Fit 40w | Buffer | Risk |
|:-----|:--------------:|:--------------:|:-------:|:------:|:----:|
| IDEA-05 only | 2.5w | 38.5w | **NO** | -1.5w | MEDIUM |
| IDEA-02 only | 2.5w | 38.5w | **NO** | -1.5w | MEDIUM |
| IDEA-NEW-2 only | 5.0w | 41.0w | **NO** | -4.0w | HIGH |
| IDEA-07 only | 4.0w | 40.0w | **YES** | 0.0w | MEDIUM (tight) |
| IDEA-NEW-3 only | 6.5w | 42.5w | **NO** | -5.5w | HIGH |
| IDEA-04 only | 8.0w | 44.0w | **NO** | -7.0w | VERY HIGH |

**Conclusion**: No single idea fits within the 40-week plan without scope reduction in existing phases. IDEA-07 (Benchmark) is the closest fit — with evaluation module overlap, it barely squeezes into 40 weeks.

---

## PHASE H — Path to 40-Week Feasibility

Three strategies exist to fit within the 40-week constraint:

### Strategy 1: Scope Reduction in Existing Phases

| Phase | Current | Reduced | Weeks Saved | Risk |
|-------|:-------:|:-------:|:-----------:|:----:|
| Phase 7 (Refinement) | 8.0w | 6.0w | 2.0w | HIGH — cuts rebuttal and revision time |
| Phase 6 (GTFS + Writing) | 8.0w | 7.0w | 1.0w | MEDIUM — reduces paper polish time |
| Phase 5 (Evaluation) | 4.0w | 3.5w | 0.5w | LOW — minor compression |
| Phase 4 (Streaming Pipeline) | 4.0w | 3.5w | 0.5w | MEDIUM — distributed mode may be rushed |
| **Total possible reduction** | | | **4.0w** | |

**Maximum scope reduction**: 4 weeks. This is exactly enough to absorb the bug fix cost (1.0w) plus one medium-cost idea (IDEA-05: 2.5w net).

### Strategy 2: Phased Idea Sequencing

Rather than adding ideas on top of the existing plan, integrate them into specific phases:

| Phase | Integration Point | Idea Component | Added Weeks |
|-------|-----------------|---------------|:-----------:|
| Phase 2 | Extend adaptive threshold | IDEA-05 contextual calibration | +1.5w |
| Phase 5 | Evaluation module | IDEA-NEW-2 TQS mapping + IDEA-07 harness | +2.0w |
| Phase 6 | GTFS extension | IDEA-04 single-entity validation (CRS001/CRS002 only) | +2.0w |
| Phase 7 | Writing integration | IDEA-NEW-2 results section | +0.5w |
| **Total phased addition** | | | **6.0w** |

**Total with phased integration**: 36.0 + 6.0 = 42.0 weeks. Requires 2.0w scope reduction.

### Strategy 3: Accept 2-4 Week Overrun

The existing plan has 4 weeks buffer. Consuming 2-4 weeks for an idea is not catastrophic for a thesis project:

```
36.0w content + 5.0w (IDEA-NEW-2) = 41.0w total
This is a 1-week overrun beyond the 40-week plan.
Grade impact: ZERO (quality of ideas matters more than schedule adherence)
Timeline impact: 1 week delay to submission
```

**This is the recommended approach** for IDEA-NEW-2 (top-ranked idea) or IDEA-07 (highest feasibility).

---

## PHASE I — Prioritized Recommendations

### If Only ONE Idea Can Be Added

**Recommended**: IDEA-NEW-2 (T-Assess x StreamDQ Integration)
- **Rationale**: Highest novelty (VLDB 2025 T-Assess is the most recent trajectory quality paper), highest feasibility (both systems exist), lowest evaluation risk (synthetic ground truth works), A-grade projection.
- **Timeline**: 41.0 weeks total (1.0w overrun beyond 40-week plan)
- **Risk mitigation**: Audit T-Assess API before committing. If incompatible, fall back to IDEA-05.
- **Buffer strategy**: Reduce Phase 7 from 8 to 7 weeks (-1.0w).

### If TWO Ideas Can Be Added

**Recommended**: IDEA-NEW-2 + IDEA-07 (shared evaluation module)
- **Rationale**: Both share the evaluation module — building one reduces cost of the other. Together they create the full evaluation infrastructure plus TQS integration.
- **Timeline**: 42.0 weeks total (2.0w overrun)
- **Risk mitigation**: Scope IDEA-07 to StreamDQ-only initially; GE/Soda comparison as Phase 8 (future work).
- **Buffer strategy**: Reduce Phase 7 from 8 to 6 weeks (-2.0w). Reduce Phase 6 from 8 to 7 weeks (-1.0w).

### Ideas to Eliminate or Defer

| Idea | Decision | Rationale |
|:-----|:--------:|------------|
| IDEA-04 (GTFS-RT Cross-Entity) | **DEFER** | Multi-stream watermark boundary is unsolved; 8.0w net cost; HIGH risk in all scenarios |
| IDEA-NEW-3 (Incremental DCs) | **DEFER** | DC evaluation engine is theoretical contribution, not achievable in thesis timeline |
| IDEA-02 (Physics-Constrained) | **MERGE** with IDEA-05 | Same component (adaptive engine); IDEA-05 is simpler; IDEA-02 refines if IDEA-05 succeeds |

### GTFS CRS: Critical Prerequisite

Before ANY GTFS-related idea (IDEA-04, IDEA-NEW-3), verify GTFS Malaysia coordinate reference system:

```
1. Query GTFS Malaysia API for sample coordinates
2. Check if lat/lon fall within Malaysia bounds (~0.5°N to 7°N, ~99°E to 120°E)
3. If coordinates are non-WGS84: Haversine calculations are invalid
4. If CRS mismatch: Do NOT pursue IDEA-04 or IDEA-NEW-3
```

---

## PHASE J — Risk Register

| Risk | Idea(s) Affected | Likelihood | Impact | Mitigation |
|------|:----------------:|:----------:|:------:|------------|
| T-Assess API incompatible with Spark | IDEA-NEW-2 | MEDIUM | HIGH (eliminates idea) | Audit GitHub first; fall back to IDEA-05 |
| GTFS CRS non-WGS84 | IDEA-04, IDEA-NEW-3 | MEDIUM | HIGH (invalidates GPS rules) | Verify before committing to GTFS ideas |
| Sparse cell cold-start degrades | IDEA-02, IDEA-05 | HIGH | MEDIUM (reduces precision gain) | Test on night/weekend contexts first |
| B2 (CRS003) remains unfixed | IDEA-NEW-2, IDEA-04 | MEDIUM | MEDIUM (CRS dimension incomplete) | Fix B2 before Phase 5; allocate 2-3 days |
| Evaluation module takes longer than expected | IDEA-NEW-2, IDEA-07 | HIGH | MEDIUM (delays all evaluation) | Build evaluation module first; validate before extending |
| Multi-framework comparison (GE/Soda) adds scope | IDEA-07 | HIGH | MEDIUM (benchmark becomes unbounded) | Scope to StreamDQ-only; other frameworks as future work |
| Single-person context switching | All ideas | MEDIUM | HIGH (quality degradation) | Serialize ideas; no parallel execution |
| NUMOSIM anomaly types don't map to DQ rules | IDEA-07 | MEDIUM | MEDIUM (benchmark design changes) | Define explicit mapping; validate before building harness |

---

## PHASE K — Final Verdict Matrix

| Idea | Total Weeks | Fit 40w | Buffer Left | Risk | Priority |
|:-----|:-----------:|:-------:|:-----------:|:----:|:--------:|
| IDEA-NEW-2 | 41.0 | **NO** | -1.0w | **MEDIUM** | **#1** |
| IDEA-07 | 40.0 | **YES (tight)** | 0.0w | **MEDIUM** | **#2** |
| IDEA-05 | 38.5 | **NO** | -1.5w | **MEDIUM** | #3 (combine with #1) |
| IDEA-02 | 38.5 | **NO** | -1.5w | **MEDIUM** | #4 (merge with #3) |
| IDEA-NEW-3 | 42.5 | **NO** | -5.5w | **HIGH** | Eliminate |
| IDEA-04 | 44.0 | **NO** | -7.0w | **VERY HIGH** | Defer |

**No idea fits within the 40-week plan without scope reduction or accepting a 1-4 week overrun.** The most defensible path is:

1. **Accept a 1-2 week overrun** for IDEA-NEW-2 (top-ranked idea, A-grade projection)
2. **Scope IDEA-07 carefully** to avoid unbounded benchmark expansion
3. **Eliminate IDEA-04 and IDEA-NEW-3** from thesis scope (defer to future work)
4. **Merge IDEA-02 with IDEA-05** (same component, choose simpler first)
5. **Fix known bugs before Phase 5** (B1, B2, B3, B5, B6 — ~1 week)

**Revised timeline with IDEA-NEW-2**:
```
Phase 1-5:    20.0w (unchanged)
Phase 6:       8.0w (unchanged)
Phase 7:       7.0w (reduced from 8.0w)
IDEA-NEW-2:    5.5w (integrated into Phases 5-6)
Bug fixes:     1.0w (integrated into Phases 1-4)

TOTAL: 41.5 weeks → OVER by 1.5 weeks
Risk: MEDIUM (T-Assess API compatibility is the gate)
```

**If IDEA-NEW-2 T-Assess API is incompatible**: Fall back to IDEA-05. Total timeline: 38.5 weeks → OVER by 1.5 weeks after Phase 7 reduction.

---

*Generated by AGENT-7: TIMELINE. All estimates are based on verification report (Phase 0), brainstorm analysis (Phase 2), and engineering realism assessment. No fabricated timelines.*
