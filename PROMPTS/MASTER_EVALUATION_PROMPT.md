# STREAMDQ MASTER EVALUATION & ENHANCEMENT PROMPT
### Self-Checking, Literature-Grounded, MCP-Verified

**Version:** 2.0 — Upgraded from `PROMPTS/MASTER_EVALUATION_PROMPT.md`
**Project:** StreamDQ — "A Context-Aware Framework for Streaming Data Quality Monitoring"
**Workspace:** `d:\dtl\pipeline_real\`
**Date:** April 19, 2026

---

## PART 0: PREAMBLE — HOW TO USE THIS PROMPT

This prompt is a **self-checking, iterative evaluation system** that follows the WAVES Research Agent Rules
(`@.cursor/rules/agent-rules.mdc`) and StreamDQ Master Rules (`@.cursor/rules/streamdq-master.mdc`).

### Execution Loop

```
EVALUATE → DIAGNOSE → PLAN → VERIFY → REPEAT
    ↑                                   │
    └───────────────────────────────────┘
```

### Required Skills Per Step

| Step | Skill(s) |
|------|---------|
| Research | `research-lookup`, `paper-lookup`, `literature-review` |
| Architecture Analysis | `scientific-critical-thinking` |
| Statistical Analysis | `statistical-analysis` |
| Paper Writing | `scientific-writing`, `peer-review` |
| Hypothesis Generation | `hypothesis-generation` |

### MCP Tools Available

| MCP | Tool | Use For |
|-----|------|---------|
| `user-kafka` | Kafka MCP | Verify topics, consumer lag, GTFS vehicle count |
| `user-duckdb` | DuckDB MCP | Query violations, compute real precision/recall |

### Context Files (DO NOT Repeat — Reference Directly)

| File | Purpose | Key Findings |
|------|---------|------------|
| `CODE_AUDIT.md` | 10 issues, 2 CRITICAL | B1 NaN pass, B2 duplicate no-op |
| `STREAMDQ_TECHNICAL_ANALYSIS.md` | 14 Q&A, 11 missing features | P0-P2 priority matrix |
| `LITERATURE_REVIEW.md` | 17 papers, 2024-2026 | Stream DaQ (2025) is primary competitor |
| `COMPETITIVE_ANALYSIS.md` | 8 tools analyzed | Stream DaQ wins on architecture |
| `HYPOTHESES.md` | 7 hypotheses | H1-H7 with experiment designs |
| `CONTRIBUTIONS.md` | Positioning | Research/education platform, not production |
| `PAPER_SECTIONS/*.md` | Paper drafts | Intro, RelatedWork, Evaluation, Limitations |
| `SPEC.md` | Product requirements | F1-F10 functional, NF1-NF5 non-functional |

---

## PART 1: DECONSTRUCT THE TITLE

Before anything else, decompose every word in "**A Context-Aware Framework for Streaming Data Quality Monitoring**" and demand evidence for each.

---

### 1.1 "Context-Aware" — VERIFY WITH CODE EVIDENCE

Ask: *"How does context-awareness actually work? Is it real or a label?"*

#### Evidence Required (Read These Files First)

| File | Lines | What to Verify |
|------|-------|---------------|
| `streamdq/rules/adaptive.py` | 1-191 | How are thresholds computed? Only P10/P90? |
| `streamdq/rules/base.py` | 15-53 | What does `external_context` contain? Is it populated? |
| `streamdq/rules/semantic.py` | 35-83 | How does SEM001 use `historical_stats`? |
| `streamdq/pipeline/local_pipeline.py` | 96-101 | Is `external_context` passed as `{}`? |
| `streamdq/pipeline/spark_pipeline.py` | 205-209 | Same question for Spark pipeline |

#### Grading Rubric

| Score | Definition | Evidence |
|-------|-----------|----------|
| **8-10** | Real context: time-of-day, day-of-week, weather, geographic, seasonal | Contexts populated, rules use them |
| **5-7** | Partial: `historical_stats` used but `external_context` empty | Adaptive threshold only |
| **0-4** | Label only: "context-aware" but only static thresholds | No context integration |

#### Current Assessment (Pre-Analysis)

The codebase shows:

- `external_context` is always `{}` — **no real external context**
- Only 2 fields tracked (`fare_amount`, `trip_distance`) — **limited adaptive scope**
- Percentile uses `int()` truncation — **imprecise** (see B8 in CODE_AUDIT)
- Driver-only computation — **not distributed**

**Current Score: 6/10 — WEAK Context-Awareness**

#### Specific Research to Verify

- [ ] Use `literature-review` to verify: "What does context-aware mean in streaming DQ? Are there papers defining it formally?"
- [ ] Use `research-lookup` to find: Stream DaQ's "dynamic constraint adaptation" vs StreamDQ's rolling P10/P90 — what's the difference?
- [ ] Search: "beta-binomial thresholds streaming data quality" (AutoDQM) — could StreamDQ use this?

#### Questions to Answer Before Proceeding

1. Does `RuleContext.external_context` get populated anywhere? Search all files.
2. What would "real" context-awareness look like for NYC Taxi? (time-of-day fare peaks, weekend patterns, weather events)
3. What is the minimum viable context (MVP): just `historical_stats` + `external_context`?

---

### 1.2 "Streaming" — VERIFY WITH CODE EVIDENCE

Ask: *"Is this truly streaming or micro-batch? What does 'streaming' mean here?"*

#### Evidence Required

| File | Lines | What to Verify |
|------|-------|---------------|
| `streamdq/pipeline/spark_pipeline.py` | 249-304 | Is it micro-batch or continuous? |
| `docker-compose.yml` | 48 | Dockerfile.spark referenced but missing |
| `streamdq/rules/cross_record.py` | 52-183 | CRS rules use global dicts — streaming or batch? |
| `streamdq/evaluation/run_evaluation.py` | 183 | LocalPipeline used, NOT SparkPipeline |

#### Grading Rubric

| Score | Definition | Evidence |
|-------|-----------|----------|
| **8-10** | True streaming: event-by-event, sub-second, continuous | Flink/Pathway-level |
| **5-7** | Micro-batch: Spark micro-batch, 500ms+ interval | Current StreamDQ |
| **0-4** | Pseudo-streaming: batch dressed as streaming | LocalPipeline only |

#### Current Assessment

- **Micro-batch only** — `outputMode: "complete"` with `foreachBatch`
- **Dockerfile.spark missing** — full pipeline cannot start
- **GTFS topic not wired** — CRS001/CRS002 inactive for GTFS data
- **LocalPipeline used in evaluation** — NOT actual streaming

**Current Score: 4/10 — PSEUDO-STREAMING (Blocking Issues)**

#### Specific Research

- [ ] Use `research-lookup`: "Spark Structured Streaming vs Apache Flink latency comparison 2024-2025"
- [ ] Use `paper-lookup`: Stream DaQ (arXiv:2506.06147) — how do they achieve sub-second?
- [ ] Compare: Spark micro-batch trigger interval vs true streaming event-time processing

#### Questions to Answer

1. Can StreamDQ claim "streaming" if it uses micro-batch? What is the minimum latency floor?
2. What would true streaming require? (Flink migration? Pathway integration?)
3. Is "micro-batch streaming" acceptable for the research/education positioning?

---

### 1.3 "Framework" — VERIFY WITH CODE EVIDENCE

Ask: *"Is this a framework (extensible, reusable) or a one-off application?"*

#### Evidence Required

| File | Lines | What to Verify |
|------|-------|---------------|
| `streamdq/rules/base.py` | 1-105 | Is DataQualityRule ABC clean and extensible? |
| `streamdq/rules/registry.py` | 1-120 | Can new rules be registered easily? |
| `streamdq/rules/syntactic.py` | 1-291 | Is adding a new rule just subclassing? |
| `tests/test_*.py` | 1-500 | Are there tests for each rule category? |

#### Grading Rubric

| Score | Definition | Evidence |
|-------|-----------|----------|
| **8-10** | Extensible: new rules, new sources, new sinks with minimal code | Registry pattern, ABC, tests |
| **5-7** | Partially extensible: rules extensible, sources/sinks hardcoded | Limited registry |
| **0-4** | Monolithic: adding rules requires modifying core | No clear extension points |

#### Current Assessment

- **Good ABC design** — `DataQualityRule` is clean
- **Registry pattern** — `RuleRegistry.evaluate_all()` works
- **Unit tests exist** — 4 test files, SYN/SEM/CRS covered
- **Missing: Dockerfile.spark, Prometheus endpoint, GTFS wiring** — infrastructure not extensible

**Current Score: 7/10 — GOOD Framework Architecture, Weak Infrastructure**

---

### 1.4 "Data Quality Monitoring" — VERIFY WITH CODE EVIDENCE

Ask: *"What data quality dimensions are monitored? How comprehensive is coverage?"*

#### Evidence Required

| File | Lines | What to Verify |
|------|-------|---------------|
| `SPEC.md` | 139-168 | 9 rules defined — are they all implemented and tested? |
| `streamdq/rules/syntactic.py` | 1-291 | SYN001-003: completeness, validity, freshness |
| `streamdq/rules/semantic.py` | 1-276 | SEM001-003: accuracy, plausibility |
| `streamdq/rules/cross_record.py` | 1-329 | CRS001-003: consistency, uniqueness |
| `CODE_AUDIT.md` | 1-497 | B1-B10 issues with rule implementations |

#### DQ Dimensions Coverage Matrix

| Dimension | Rule(s) | Coverage | Issue |
|-----------|---------|---------|-------|
| Completeness | SYN001 only | Partial | Only `fare_amount` has completeness rule |
| Validity | SYN002, SYN003 | Good | Type and range checks |
| Consistency | CRS001-003 | Partial | CRS002 scope narrow, CRS003 broken |
| Accuracy | SEM001-003 | Good | Domain-specific checks |
| Freshness | SYN003 | Partial | Only "not in future", not "not stale" |
| Uniqueness | CRS003 | Broken | Duplicate injection no-op |

#### Grading Rubric

| Score | Definition | Evidence |
|-------|-----------|----------|
| **8-10** | All 6 DQ dimensions covered, rules for each | Comprehensive |
| **5-7** | 4-5 dimensions covered | Most important covered |
| **0-4** | <4 dimensions, major gaps | Incomplete coverage |

**Current Score: 5/10 — PARTIAL Coverage (Major Gaps in Completeness, Consistency)**

---

## PART 2: COMPONENT-BY-COMPONENT GRADING

Grade each major component on a 1-10 scale. Cite specific file:line evidence.

---

### 2.1 Rule Engine (SYN/SEM/CRS)

| Component | Score | Evidence | Issue |
|-----------|-------|----------|-------|
| SYN001 (Fare validity) | 8/10 | `syntactic.py:40-118` | NaN fix applied but verify |
| SYN002 (Location validity) | 9/10 | `syntactic.py:134-193` | Clean, correct |
| SYN003 (Timestamp) | 8/10 | `syntactic.py:229-290` | Good edge case handling |
| SEM001 (Fare range) | 7/10 | `semantic.py:35-83` | Adaptive but only 2 fields |
| SEM002 (Trip duration) | 8/10 | `semantic.py:119-178` | Clean implementation |
| SEM003 (Speed) | 7/10 | `semantic.py:213-275` | Fixed threshold, not adaptive |
| CRS001 (GPS speed) | 8/10 | `cross_record.py:52-183` | Haversine correct |
| CRS002 (GPS spoofing) | 4/10 | `cross_record.py:148` | Speed threshold too narrow |
| CRS003 (Duplicates) | 2/10 | `run_evaluation.py:102-104` | **CRITICAL: injection broken** |

**Subtotal: 61/90 = 6.8/10**

---

### 2.2 Adaptive Threshold Engine

| Aspect | Score | Evidence | Issue |
|--------|-------|----------|-------|
| Rolling percentile computation | 6/10 | `adaptive.py:101-107` | Integer truncation, no interpolation |
| Recompute frequency | 7/10 | `adaptive.py:83-84` | Every 1000 events is reasonable |
| Override mechanism | 8/10 | `adaptive.py:175-182` | Clean human override |
| Distributed computation | 1/10 | `spark_pipeline.py:176` | **Driver-only — not distributed** |
| Context integration | 2/10 | `base.py:31-35` | `external_context` always `{}` |
| Drift detection | 0/10 | N/A | **Completely absent** |

**Subtotal: 24/60 = 4/10 — WEAK**

---

### 2.3 Streaming Pipeline

| Aspect | Score | Evidence | Issue |
|--------|-------|----------|-------|
| Spark micro-batch | 6/10 | `spark_pipeline.py:249-304` | Works but micro-batch only |
| Rule evaluation | 5/10 | `spark_pipeline.py:203-218` | Python for-loop, single-threaded |
| GTFS routing | 0/10 | `spark_pipeline.py:150-304` | GTFS topic never read |
| Kafka violation sink | 0/10 | `spark_pipeline.py:221-222` | **NOT implemented** |
| Prometheus metrics | 3/10 | `spark_pipeline.py:26-82` | Stub metrics only, no HTTP endpoint |
| State checkpointing | 2/10 | `cross_record.py:264-328` | Save/load exist but not wired |

**Subtotal: 16/60 = 2.7/10 — POOR (Blocking Issues)**

---

### 2.4 Evaluation Framework

| Aspect | Score | Evidence | Issue |
|--------|-------|----------|-------|
| Ground truth tracking | 7/10 | `metrics.py:1-175` | Design is sound, one bug |
| Anomaly injection | 5/10 | `run_evaluation.py:48-106` | 7/8 types work, duplicate broken |
| Metric computation | 7/10 | `metrics.py:108-154` | Precision/recall/detection rate correct |
| Comparison vs baselines | 5/10 | `comparison.py:1-200` | All numbers are estimates |
| Latency measurement | 2/10 | `spark_pipeline.py:225` | **Hardcoded to 0** |
| Bootstrap CI | 0/10 | N/A | **Not implemented** |

**Subtotal: 26/60 = 4.3/10 — WEAK**

---

### 2.5 Documentation & Paper

| Aspect | Score | Evidence | Issue |
|--------|-------|----------|-------|
| Paper sections | 7/10 | `PAPER_SECTIONS/*.md` | Well-structured, honest limitations |
| README | 8/10 | `README.md:1-308` | Clear, good diagrams |
| SPEC | 8/10 | `SPEC.md:1-216` | Comprehensive requirements |
| Literature review | 8/10 | `LITERATURE_REVIEW.md` | 17 papers, 2024-2026 |
| Competitive analysis | 8/10 | `COMPETITIVE_ANALYSIS.md` | 8 tools, honest positioning |
| Code audit | 9/10 | `CODE_AUDIT.md` | 10 issues, scientific rigor |

**Subtotal: 48/60 = 8/10 — STRONG**

---

### 2.6 Overall Scorecard

| Component | Score | Weight | Weighted |
|-----------|-------|--------|---------|
| Rule Engine | 6.8/10 | 25% | 1.70 |
| Adaptive Threshold | 4.0/10 | 20% | 0.80 |
| Streaming Pipeline | 2.7/10 | 20% | 0.54 |
| Evaluation Framework | 4.3/10 | 15% | 0.65 |
| Documentation/Paper | 8.0/10 | 20% | 1.60 |
| **OVERALL** | | **100%** | **5.28/10** |

**Grade: 5.3/10 — PROTOTYPE WITH SIGNIFICANT GAPS**

---

## PART 3: RESEARCH AGenda (Use Skills)

### 3.1 Critical Research Questions

Before any enhancement work, research these:

#### RQ1: "What does 'context-aware' mean in streaming DQ literature?"

```
Use: research-lookup + paper-lookup
Search: "context-aware data quality streaming", "adaptive threshold streaming DQ 2024-2026"
Verify: Is StreamDQ's approach novel or just a label?
Expected: Stream DaQ has "dynamic constraint adaptation", AutoDQM has beta-binomial
Gap: StreamDQ has neither → need to research what to add
```

#### RQ2: "How does Stream DaQ (2025) compare to StreamDQ?"

```
Use: paper-lookup for arXiv:2506.06147
Verify: Their 30+ quality checks vs StreamDQ's 9 rules
Verify: Their Pathway-based state management vs StreamDQ's global dicts
Verify: Their drift detection vs StreamDQ's rolling percentile
Action: Should StreamDQ adopt Pathway? Or is Spark micro-batch acceptable for research platform?
```

#### RQ3: "What adaptive threshold approaches exist beyond rolling percentiles?"

```
Use: literature-review
Papers: strAEm++DD (arXiv:2305.08977), Adaptive NAD (arXiv:2410.22967), AutoDQM (arXiv:2501.13789)
Compare: beta-binomial vs rolling percentile vs autoencoder vs two-layer
Action: Which is simplest to implement for MVP? Which gives best improvement?
```

#### RQ4: "What are the 5 most impactful fixes for StreamDQ?"

```
Use: scientific-critical-thinking on CODE_AUDIT.md
Prioritize: CRITICAL issues first (B1 NaN, B2 duplicate)
Then: MAJOR issues that block demo (Dockerfile.spark, Prometheus)
Then: Quality improvements (CRS002, percentile precision, SQLite WAL)
```

### 3.2 Research Output Format

For each RQ, produce:

```markdown
## RQ-X: [Question]

### Findings
- [Citation 1] — [Key finding]
- [Citation 2] — [Key finding]

### Gap Identified
- [What StreamDQ lacks]

### Recommendation
- [Concrete action: add/remove/change X]

### Confidence
- High/Medium/Low (based on evidence quality)
```

---

## PART 4: DIAGNOSE — Apply Scientific Critical Thinking

### 4.1 Claim Decomposition Checklist

For EVERY claim in the project, verify:

- [ ] **"Context-aware"** — Does code prove it? (NO: `external_context = {}`)
- [ ] **"P50 ~150ms"** — Measured or estimated? (ESTIMATED: `comparison.py` hardcoded)
- [ ] **"P99 ~890ms"** — Measured or estimated? (ESTIMATED: same)
- [ ] **"82% recall"** — Can CRS003 recall be measured? (NO: duplicate injection no-op)
- [ ] **"85% precision"** — Measured on what dataset? (LocalPipeline only)
- [ ] **"400x faster than GE"** — Measured or calculated? (ESTIMATED: architecture comparison)
- [ ] **"1,700+ GTFS vehicles"** — Verified in code? (NO: claim in docs only)
- [ ] **"Adaptive thresholds"** — Working in distributed mode? (NO: driver-only)
- [ ] **"Fault-tolerant"** — Layer 2 state checkpointed? (NO: global dicts)
- [ ] **"5,000+ events/sec"** — Measured or claimed? (NOT MEASURED)

### 4.2 Known Blockers (From streamdq-master.mdc)

| Blocker | Severity | File:Line | Fix Status |
|---------|---------|-----------|-----------|
| B1: NaN silent pass-through | CRITICAL | `syntactic.py:59` | **Verify if fixed** |
| B2: Duplicate injection no-op | CRITICAL | `run_evaluation.py:102` | **NOT FIXED** |
| B3: CRS002 speed range gap | MAJOR | `cross_record.py:148` | **NOT FIXED** |
| B4: foreachBatch driver bottleneck | MAJOR | `spark_pipeline.py:176` | **Known limitation** |
| B5: SQLite no WAL mode | MAJOR | `violation_store.py` | **NOT FIXED** |
| B6: processing_latency_ms = 0 | CRITICAL | `syntactic.py:56` | **NOT FIXED** |

**Action for each: Read the code → Verify if issue exists → Decide: fix or document as limitation**

### 4.3 Self-Diagnosis Questions

Apply `scientific-critical-thinking` to these:

1. **Is StreamDQ's "streaming" claim honest?** — Micro-batch is NOT streaming. Can the paper claim streaming at all?
2. **Is the adaptive threshold claim honest?** — Rolling P10/P90 is adaptive, but drift detection is absent. Is "adaptive" accurate?
3. **Is the 82% recall claim honest?** — CRS003 cannot be measured. Realistic ceiling: 87.5% (excluding duplicate).
4. **Is the positioning claim honest?** — "Research and education platform" vs "production-ready" — is this consistently stated?
5. **Are benchmark numbers honest?** — Every number is estimated. Is the paper honest about this?

---

## PART 5: PLAN — Prioritized Enhancement Roadmap

### 5.1 Critical Fixes (Before Any New Feature)

| Priority | Task | Bug ID | Files | Verification |
|----------|------|--------|-------|-------------|
| P0-1 | Verify B1 (NaN) fix applied | B1 | `syntactic.py` | Run: `python -c "import math; print(math.isnan(float('nan')))"` |
| P0-2 | Fix B2 (duplicate injection) | B2 | `run_evaluation.py:102` | Inject two records, verify CRS003 fires |
| P0-3 | Fix B6 (latency = 0) | B6 | All rule files | Verify `processing_latency_ms` computed |
| P0-4 | Create Dockerfile.spark | N/A | New file | `docker compose up` succeeds |
| P0-5 | Wire GTFS topic → CRS | N/A | `spark_pipeline.py` | GTFS violations appear |

### 5.2 Quality Improvements (After Critical Fixes)

| Priority | Task | Bug ID | Files | Impact |
|----------|------|--------|-------|--------|
| P1-1 | Fix B3 (CRS002 speed) | B3 | `cross_record.py:148` | +15% GPS spoofing recall |
| P1-2 | Fix B5 (SQLite WAL) | B5 | `violation_store.py` | +60% storage throughput |
| P1-3 | Add percentile interpolation | B8 | `adaptive.py:101` | Statistical rigor |
| P1-4 | Implement Kafka violation sink | N/A | `spark_pipeline.py` | Architecture complete |
| P1-5 | Add Prometheus metrics HTTP | N/A | `spark_pipeline.py` | Grafana works |

### 5.3 Enhancement Research (Requires Literature First)

| Priority | Task | Source | Expected Impact |
|----------|------|--------|---------------|
| P2-1 | Drift detection in adaptive engine | RQ3 research | Reduce false positives |
| P2-2 | Beta-binomial thresholds (SEM001) | AutoDQM paper | Better warmup behavior |
| P2-3 | External context injection (time-of-day) | RQ1 research | Genuine context-awareness |
| P2-4 | Bootstrap CI for metrics | `statistical-analysis` | Honest confidence bounds |
| P2-5 | Pandas UDF rule evaluation | B4 fix | +40% throughput |

---

## PART 6: VERIFY WITH MCP TOOLS

### 6.1 Kafka MCP Verification

After implementing critical fixes, verify with Kafka MCP:

```bash
# Verify 1: Check topics exist
kafka_topics_list → "nyc-taxi-events", "gtfs-vehicle-pos", "quality-violations"

# Verify 2: Check GTFS vehicle count
kafka_consume messages="gtfs-vehicle-pos" limit=1000
→ Count unique vehicle_id values → should be ~1700+

# Verify 3: Verify anomaly injection → violation appears
produce test event with fare_amount=-50 → consume "quality-violations" 
→ should see SYN001 violation

# Verify 4: Check consumer lag
kafka_get_consumer_group_info group="streamdq-consumer"
→ lag should be < 1000 for healthy pipeline
```

### 6.2 DuckDB MCP Verification

After running evaluation, verify metrics:

```sql
-- Verify 1: Real precision/recall from actual run
SELECT 
    anomaly_type,
    COUNT(*) as total_injected,
    SUM(CASE WHEN detected THEN 1 ELSE 0 END) as detected,
    ROUND(SUM(CASE WHEN detected THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as recall_pct
FROM evaluation_results
GROUP BY anomaly_type;

-- Verify 2: Latency percentiles
SELECT 
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) as p50,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99
FROM violations;

-- Verify 3: False positive analysis
SELECT rule_id, COUNT(*) as violations 
FROM violations 
WHERE entity_index NOT IN (SELECT entity_index FROM injected_anomalies)
GROUP BY rule_id
ORDER BY violations DESC;
```

---

## PART 7: GRADING RUBRIC FOR FINAL OUTPUT

### 7.1 Paper Readiness Score (per Section)

| Section | Min Score | Max Score | Current | Gap |
|---------|-----------|-----------|---------|-----|
| Introduction | 7 | 10 | 7 | Honesty about streaming vs batch |
| Related Work | 8 | 10 | 8 | Need to add Flink comparison papers |
| Architecture | 6 | 10 | 6 | Micro-batch acknowledgment |
| Evaluation | 4 | 10 | 4 | MUST measure before publishing |
| Limitations | 8 | 10 | 8 | Already honest |
| **Total** | **40** | **60** | **~40** | **CRITICAL: Evaluation must be measured** |

### 7.2 Demo Readiness Checklist

Before claiming "working demo":

- [ ] `docker compose up` starts full pipeline → BLOCKED by Dockerfile.spark missing
- [ ] Grafana shows data → BLOCKED by Prometheus endpoint not exposed
- [ ] NYC TLC events flow through Kafka → Works (producer exists)
- [ ] GTFS violations detected → BLOCKED by GTFS topic not wired
- [ ] SQLite has violation records → Partially works

**Demo Readiness: 2/5 — NOT DEMO-READY**

### 7.3 Production Readiness Checklist

Before claiming "production-ready":

- [ ] Fault-tolerant state → BLOCKED by no checkpointing
- [ ] Horizontal scaling → BLOCKED by single-threaded rule eval
- [ ] Real benchmark validated → BLOCKED by LocalPipeline only
- [ ] Monitoring/alerting → BLOCKED by Prometheus not exposed
- [ ] Multi-broker Kafka → BLOCKED by single broker RF=1

**Production Readiness: 0/5 — RESEARCH PLATFORM ONLY**

---

## PART 8: MASTER PROMPT — THE SELF-EVALUATION LOOP

### How to Run This Prompt (for the AI Agent)

```
PHASE 1 — DECOMPOSE (1 research iteration)
├── Read: STREAMDQ_TECHNICAL_ANALYSIS.md + CODE_AUDIT.md
├── Research: RQ1-RQ4 using research-lookup + paper-lookup
└── Output: Graded components (Part 2) + Research findings (Part 3)

PHASE 2 — DIAGNOSE (1 analysis iteration)
├── Apply: scientific-critical-thinking to every claim
├── Verify: B1-B6 in code (read actual files)
├── Grade: Each component (Part 2 scorecard)
└── Output: Diagnosis report with specific evidence

PHASE 3 — PLAN (1 planning iteration)
├── Prioritize: CRITICAL > MAJOR > MINOR
├── Sequence: Fix blocking first, then enhance
├── Resource: Map to skills + MCP tools available
└── Output: Roadmap (Part 5) with verification criteria

PHASE 4 — VERIFY (1 verification iteration)
├── Execute: DuckDB queries on violation data
├── Execute: Kafka MCP topic inspection
├── Execute: Run evaluation and compare to claims
└── Output: Verified vs claimed gap analysis

PHASE 5 — DECIDE (1 decision iteration)
├── Based on: All evidence above
├── Decide: Is the project ready to publish? What must be fixed first?
├── Scope: What can be done in 1 week? 1 month? 1 quarter?
└── Output: Decision memo with go/no-go recommendations
```

### Output Format for Each Phase

#### Phase 1 Output: Component Grades + Research Summary

```markdown
## Phase 1: Component Evaluation

### Scores (X/Y)
| Component | Score | Key Evidence | Key Gap |
|-----------|-------|-------------|---------|
| Rule Engine | X/Y | [file:line] | [specific issue] |
| Adaptive Threshold | X/Y | [file:line] | [specific issue] |
| Streaming Pipeline | X/Y | [file:line] | [specific issue] |
| Evaluation Framework | X/Y | [file:line] | [specific issue] |
| Documentation | X/Y | [file:line] | [specific issue] |
| **OVERALL** | X/Y | | |

### Research Findings
#### RQ1: Context-Aware
- [Finding 1 with citation]
- [Finding 2 with citation]
- Gap: [what StreamDQ lacks]

#### RQ2: Stream DaQ Comparison
- [Finding]
- Recommendation: [adopt/adapt/ignore]

...etc for RQ3, RQ4

### Self-Evaluation: [X/10]
- Strengths: [top 3]
- Weaknesses: [top 3]
- Blocking issues: [top 3]
```

#### Phase 2 Output: Diagnosis Report

```markdown
## Phase 2: Diagnosis

### Claim Verification
| Claim | Status | Evidence | Action |
|-------|--------|---------|--------|
| "Context-aware" | OVERCLAIM | `base.py:31` external_context={} | Downgrade or implement |
| "P50 ~150ms" | UNVERIFIED | `comparison.py:144` hardcoded | Must measure |
| "82% recall" | OVERCLAIM | B2: CRS003 injection broken | Fix B2 first |
...etc

### Bug Status
| Bug | Verified? | File:Line | Fix Applied? |
|-----|-----------|-----------|--------------|
| B1 | [YES/NO] | [ref] | [YES/NO] |
| B2 | [YES/NO] | [ref] | [YES/NO] |
...etc

### Root Cause Analysis
[For each blocking issue, trace to the code-level cause]
```

#### Phase 3 Output: Prioritized Roadmap

```markdown
## Phase 3: Enhancement Roadmap

### Week 1 (Critical Fixes)
| # | Task | Files | Verification | Owner |
|---|------|-------|-------------|-------|
| 1 | Fix B2 duplicate injection | run_evaluation.py | Test CRS003 fires | AI |
| 2 | Create Dockerfile.spark | Dockerfile.spark | docker compose up works | AI |
...etc

### Week 2-4 (Quality)
| # | Task | Expected Impact | Research Needed |
|---|------|----------------|-----------------|
| 1 | Fix B3 CRS002 speed | +15% recall | None |
| 2 | Add drift detection | -X% FPR | literature-review |
...etc

### Month 2+ (Enhancement)
| # | Task | Complexity | Literature Source |
|---|------|-----------|------------------|
| 1 | Beta-binomial thresholds | Medium | AutoDQM |
| 2 | External context | High | RQ1 research |
...etc
```

#### Phase 4 Output: Verification Report

```markdown
## Phase 4: MCP Verification Results

### Kafka Verification
- Topics: [list]
- GTFS vehicle count: [number] (expected: ~1700)
- Consumer group lag: [number]
- Anomaly injection test: [PASS/FAIL]

### DuckDB Verification
- Total violations: [N]
- Precision: [X%] (claimed: Y%)
- Recall by type: [table]
- Latency P50/P99: [Xms / Yms] (claimed: 150ms / 890ms)

### Verdict
- [X] claims can be verified
- [Y] claims remain unverified
- [Z] claims are FALSE (contradicted by data)
```

#### Phase 5 Output: Decision Memo

```markdown
## Phase 5: Decision Memo

### Current State
- Overall Grade: [X/10]
- Demo Ready: [YES/NO — N/5 checkpoints]
- Production Ready: [YES/NO — N/5 checkpoints]
- Paper Ready: [YES/NO — sections scored]

### Go/No-Go for Publication
[Based on evidence above, recommend one of:]
- GO: All claims verified, all critical bugs fixed
- CONDITIONAL GO: Major claims verified, minor gaps documented
- NO-GO: Critical gaps remain, benchmark not measured

### Must-Fix Before Publication (Non-Negotiable)
1. [Critical fix with deadline]
2. [Critical fix with deadline]
3. [Critical fix with deadline]

### Can-Do After Publication (Optional)
1. [Enhancement]
2. [Enhancement]

### Positioning Adjustment
[Based on findings, recommend specific language changes to paper positioning]
```

---

## PART 9: LITERATURE GAPS TO FILL

### Papers That Need Verification

| Paper | Citation | Claim to Verify |
|-------|---------|----------------|
| Stream DaQ (2025) | arXiv:2506.06147 | Sub-second latency, 30+ checks, drift detection |
| AutoDQM (2025) | arXiv:2501.13789 | Beta-binomial thresholds for DQ |
| strAEm++DD (2023) | arXiv:2305.08977 | Autoencoder + drift detection |
| Adaptive NAD (2024) | arXiv:2410.22967 | Two-layer self-adaptive thresholds |
| StreamShield (2026) | arXiv:2602.03189 | Production resiliency for Flink |

### New Research Needed

1. **"What is the state-of-the-art for streaming DQ in 2026?"** — Update LITERATURE_REVIEW.md
2. **"How do commercial tools (Monte Carlo, Anomalo) implement adaptive thresholds?"** — Update COMPETITIVE_ANALYSIS.md
3. **"Is there a benchmark dataset for streaming cross-record DQ?"** — Gap identification
4. **"What are the theoretical foundations of streaming DQ metrics?"** — Gap: no unified theory

---

## PART 10: ANTI-PATTERNS TO AVOID

Based on CODE_AUDIT.md and agent-rules.mdc:

| Anti-Pattern | Example in StreamDQ | How to Avoid |
|-------------|--------------------|--------------|
| **Unverified claims** | P50=150ms, P99=890ms | Measure before publishing |
| **Missing implementation** | Dockerfile.spark | Reference only existing files |
| **Silent failures** | NaN pass-through (B1) | Guard every field access |
| **Magic numbers** | `speed_kmh < 20.0` | Named constants with comments |
| **Scope mismatch** | CRS002 narrow coverage | Map all attack vectors |
| **Overclaiming** | "400x faster" unverified | Architecture ≠ measurement |
| **Missing CI** | No bootstrap confidence intervals | statistical-analysis skill |
| **State not checkpointed** | Global dicts for CRS | Implement save/load wiring |

---

## PART 11: THE LOOP — How to Use This Prompt Iteratively

### First Pass (Current State)

```
Goal: Grade the project honestly
Output: This document (scores, research, diagnosis)
Trigger: User asks "evaluate my project" or "is this ready to publish?"
```

### Subsequent Passes (After Fixes)

```
Goal: Re-grade after implementing fixes
Output: Updated scores + verification evidence
Trigger: User reports "I fixed B2" → re-evaluate CRS003 coverage
```

### Research Pass (Before Enhancement)

```
Goal: Decide what to enhance based on literature
Output: RQ answers + recommendation (from Part 3)
Trigger: User asks "should I add drift detection?"
```

### Publication Pass (Before Submit)

```
Goal: Final verification checklist
Output: Phase 4 + Phase 5 output
Trigger: User asks "is this paper ready?"
```

---

## EXECUTION CHECKLIST

Before responding to any user query about StreamDQ, the agent must:

- [ ] Read CODE_AUDIT.md (10 issues, must reference B1-B10)
- [ ] Read STREAMDQ_TECHNICAL_ANALYSIS.md (P0-P2 priorities)
- [ ] Check bug status in actual source files
- [ ] Use `scientific-critical-thinking` on every claim
- [ ] Verify with DuckDB/Kafka MCP when data exists
- [ ] Apply grading rubric from Part 2
- [ ] Reference existing analysis docs (don't repeat work)
- [ ] Follow WAVES Research Agent Rules (agent-rules.mdc)
- [ ] Follow StreamDQ Master Rules (streamdq-master.mdc)

---

## FINAL VERDICT (Pre-Analysis)

Based on the existing analysis documents, StreamDQ scores:

**Overall: 5.3/10 — RESEARCH PROTOTYPE WITH SIGNIFICANT GAPS**

| Tier | Score | Reason |
|------|-------|--------|
| **Claims vs Reality** | 4/10 | Most benchmark numbers are estimates |
| **Technical Correctness** | 7/10 | Haversine correct, rules mostly right, B2 critical bug |
| **Evaluation Framework** | 4/10 | Design good, B2 blocks CRS003 measurement |
| **Infrastructure** | 2/10 | Dockerfile missing, Prometheus broken, GTFS unwired |
| **Literature/Positioning** | 8/10 | Well-researched, honest limitations, good comparison |
| **Innovation** | 5/10 | Domain-specific rules good, adaptive threshold weak |

### Top 3 Actions Required Before Any Publication

1. **FIX B2** (duplicate injection no-op) — CRS003 recall unmeasurable
2. **MEASURE** (real benchmark) — P50/P99/precision/recall all unverified
3. **CREATE Dockerfile.spark** — Full pipeline cannot start

### Top 3 Enhancements After Critical Fixes

1. **Drift detection** in adaptive engine — Literature shows this is table stakes
2. **GTFS → CRS wiring** — Domain-specific strength is currently inactive
3. **External context** — "Context-aware" is currently a label, not reality

---

## PART 12: IBM + PRECISELY RESEARCH FINDINGS (April 2026)

**Sources:**
- IBM: https://www.ibm.com/think/topics/data-quality
- Precisely: https://www.precisely.com/data-quality/big-data-quality-mastering-data-quality-in-the-age-of-big-data/

### 12.1 IBM — 7 Data Quality Dimensions

IBM defines 7 DQ dimensions that StreamDQ must cover:

| Dimension | IBM Definition | StreamDQ Status | Gap |
|-----------|---------------|----------------|-----|
| **Completeness** | Amount of usable/complete data; null rates | SYN001 (partial: `fare_amount` only) | Need per-field null rate monitoring |
| **Uniqueness** | Absence of duplicate data (e.g., unique `trip_id`) | CRS003 (**broken**: duplicate injection no-op) | Must fix B2 first |
| **Validity** | Conformance to format/business rules | SYN002, SYN003 (type + range checks) | ✅ Covered |
| **Timeliness** | Readiness within expected timeframe | SYN003 (partial: "not in future" only) | Missing: stale data detection |
| **Accuracy** | Correctness vs. agreed source of truth | SEM001-003 | ✅ Covered |
| **Consistency** | Cross-record coherence | CRS001-003 (CRS002 narrow, CRS003 broken) | Partial coverage |
| **Fitness for purpose** | Data meets business need | ❌ **Missing entirely** | Must add new rule category |

**IBM's AI-readiness framing**: "30% of genAI projects will be abandoned due to poor data quality" (Gartner). StreamDQ's positioning should include pre-ML data validation — validating data BEFORE it feeds ML pipelines.

### 12.2 IBM — Key Insights for StreamDQ

1. **DQ governance is enterprise-critical**: Poor data quality costs organizations an average of USD 12.9M/year (Gartner). StreamDQ must be positioned as a tool that reduces this cost.
2. **Data integrity vs. data quality**: IBM distinguishes data integrity (accuracy, consistency, completeness — from a security lens) from data quality (broader: includes timeliness, validity, uniqueness, fitness for purpose).
3. **Data profiling**: IBM defines profiling as "reviewing and cleansing data to maintain quality standards" — this is the **Discover** phase of Precisely's framework.
4. **Gartner Market Guide for Data Observability** (referenced): StreamDQ should be compared against data observability tools, not just DQ tools.

### 12.3 Precisely — 5-Step Framework for Data in Motion

Precisely's operational framework for big data quality:

```
1. Discover   → Profile data, identify critical flows, set baselines
2. Define     → Assess DQ risks, pain points, prioritize
3. Design     → Design analysis/exception processes, rules independent of data
4. Deploy     → Deploy controls, workflow for results
5. Monitor    → Automated, continuous monitoring
```

### 12.4 Precisely vs. Confluent 6-Step Comparison

|| Step | Precisely | Confluent |
|------|----------|-----------|
| 1 | Discover (profiling) | Ingest (Kafka-native) |
| 2 | Define (risk assessment) | Schema Validate (Schema Registry) |
| 3 | Design (rules) | Business Rules (Flink/ksqlDB) |
| 4 | Deploy (controls) | Quarantine (dead-letter queue) |
| 5 | Monitor (automated) | Monitor (Grafana/Datadog) |
| 6 | — | Alert (Slack/PagerDuty) |

**Insight**: Precisely adds explicit "Discover" and "Define" phases (upstream governance). Confluent adds explicit "Alert" phase (downstream action). StreamDQ currently implements only Confluent's steps 3-4 (rules + quarantine) partially.

### 12.5 Precisely — Data-in-Motion Specific Challenges

1. **Speed/volume/variety**: Data in motion is most vulnerable — not stored, constantly changing, hard to monitor
2. **Schema evolution**: Silent schema changes shift acceptable ranges (Acceldata warning)
3. **Data lineage**: Track which systems/consumers are affected by violations
4. **Proactive vs. reactive**: "Shift from reactive to proactive data quality. Define and enforce data contracts in real-time."

### 12.6 StreamDQ Gap Analysis vs. IBM + Precisely

| Feature | IBM / Precisely | StreamDQ Status |
|---------|-----------------|-----------------|
| Completeness monitoring (null rates per field) | IBM: core dimension | ❌ Missing: only `fare_amount` |
| Fitness for purpose evaluation | IBM: core dimension | ❌ Missing entirely |
| Stale data detection | Precisely: timeliness | ❌ Missing: SYN003 only checks "not in future" |
| Discover phase (auto-profiling) | Precisely Step 1 | ❌ Missing |
| Define phase (DQ risk assessment) | Precisely Step 2 | ❌ Missing |
| Design phase (rules as contracts) | Precisely Step 3 | ⚠️ Partial: rules exist but no contract YAML |
| Monitor phase (automated alerts) | Precisely Step 5 | ⚠️ Weak: SQLite only, no Grafana |
| AI-readiness framing | IBM: core positioning | ❌ Not discussed |
| Data lineage for violations | Precisely: root cause | ❌ Missing |

### 12.7 NEW: Precisely's "5 Steps to Master Big Data Quality"

From Precisely's blog:

1. **Discover**: Identify critical information flows, set metric baselines, profile data sources
2. **Define**: Assess DQ risks, pain points, prioritize by cost/impact
3. **Design**: Design analysis/exception processes. Rules must be independent of the data they analyze
4. **Deploy**: Deploy controls based on criticality. Include people + process + technology
5. **Monitor**: Automated, continuous monitoring. Most cost-effective approach.

**StreamDQ maps to**:
- Steps 1-2: MISSING (upstream governance)
- Step 3: PARTIAL (rule authoring exists)
- Step 4: MISSING (no deployment workflow)
- Step 5: WEAK (SQLite violations, no Grafana)

### 12.8 Industry Research Status Update

| Research Type | Before | After |
|-------------|--------|-------|
| Academic papers | ✅ Done | ✅ Done |
| Industry blogs (general) | ✅ Done | ✅ Done |
| Production case studies | ✅ Done | ✅ Done |
| IBM DQ framework | ❌ Missing | ✅ **ADDED** (7 dimensions, AI-readiness) |
| Precisely 5-step | ❌ Missing | ✅ **ADDED** (Discover-Define-Design-Deploy-Monitor) |

### 12.9 Recommended Actions from IBM + Precisely

#### P1-A: Completeness Monitoring (IBM Dimension #1)

**IBM**: "Completeness = amount of usable data. High null rates lead to biased analysis."
**Precisely**: "Discover phase = profile data, identify null rates per field."

```python
# New rule: SYN000 — Field Completeness Monitor
# Track null rate per field per sliding window (e.g., 5-min)
# Fire violation when null rate > contract SLA (e.g., >2% null)
@dataclass
class CompletenessStats:
    field_name: str
    total_count: int
    null_count: int
    null_rate: float  # null_count / total_count
    window_start: datetime
    window_end: datetime

# RuleConfig should include:
# - target_field: str
# - completeness_sla: float  # e.g., 0.98 = 98% complete required
```

#### P1-B: Fitness for Purpose (IBM Dimension #7 — Currently Missing)

**IBM**: "Fitness for purpose = data asset meets business need. Difficult to evaluate for new datasets."

```python
# New rule category: FIT001 — Business Fitness
# Check if data distribution matches business expectations
# e.g., NYC taxi: mean fare should be within [10, 80] USD for 95% of trips
# e.g., GTFS: vehicle_count should be > 1000 during peak hours

# Config includes:
# - business_profile: dict  # {field: (min_acceptable, max_acceptable, confidence_pct)}
# - evaluation_window: int  # events to evaluate
# - violation_threshold: float  # % of events outside range to trigger
```

#### P1-C: Stale Data Detection (IBM Timeliness — Currently Partial)

**IBM**: "Timeliness = data ready within expected timeframe."
**Precisely**: "Data in motion is most vulnerable."

```python
# Extend SYN003 to also check:
# - record_age_ms: current_time - event_timestamp > staleness_threshold_ms
# - gap_detection: if no events for > X seconds, fire alert
SYN003_STALENESS_THRESHOLD_MS = 60_000  # 1 minute for GTFS
```

#### P1-D: Auto-Profiling (Precisely Step 1 — Discover)

```python
# New class: SchemaProfiler
# Run on first N events to auto-generate rule suggestions
class SchemaProfiler:
    def profile(self, events: list[dict]) -> ProfilingReport:
        report = ProfilingReport()
        for event in events:
            for field, value in event.items():
                report.update(field, value)
        return report

    def suggest_rules(self, report: ProfilingReport) -> list[RuleConfig]:
        # Generate SYN001 (null check) for all fields
        # Generate SYN002 (type/range) from observed types/ranges
        # Generate SYN003 (timestamp freshness) for timestamp fields
        # Return list of suggested RuleConfig objects
```

#### P1-E: Data Contract Definition (Precisely Step 2-3 — Define + Design)

```yaml
# data_contracts/nyc_taxi.yaml
topic: nyc-taxi-events
version: "1.0"
completeness_sla:
  trip_id: 1.0      # 100% required (PK)
  fare_amount: 0.98 # 98% required
  pickup_datetime: 1.0
validity:
  fare_amount:
    type: float
    min: 0.0
    max: 500.0
  trip_distance:
    type: float
    min: 0.0
    max: 100.0  # miles
timeliness:
  max_event_age_ms: 5000  # events older than 5s are stale
fitness:
  mean_fare_expected: [10.0, 80.0]  # USD
  mean_distance_expected: [1.0, 15.0]  # miles
```

#### P1-F: Alert Routing (Precisely Step 5 — Monitor)

```python
# New: AlertRouter
class AlertRouter:
    def send(self, violation: Violation):
        for channel in self.channels:
            channel.send(violation)

# Slack webhook
class SlackChannel:
    def __init__(self, webhook_url: str, channel: str):
        self.webhook_url = webhook_url

    def send(self, violation: Violation):
        payload = {
            "channel": self.channel,
            "text": f"🚨 StreamDQ Violation: {violation.rule_id}",
            "blocks": [
                {"type": "section", "text": {
                    "type": "mrkdwn",
                    "text": f"*{violation.rule_id}* | {violation.severity}\n"
                            f"Field: {violation.details.get('field')}\n"
                            f"Value: {violation.details.get('actual_value')}\n"
                            f"Entity: {violation.entity_id}"
                }}
            ]
        }
        requests.post(self.webhook_url, json=payload)
```

### 12.10 Updated Research Agenda (NEW RQ5-RQ6)

```markdown
#### RQ5: "How does IBM's 'fitness for purpose' dimension map to quantifiable metrics?"

Use: literature-review + research-lookup
Search: "data quality fitness for purpose evaluation metrics"
Expected: Distribution-based evaluation, business profile matching
Gap: StreamDQ has no fitness-for-purpose rule category

#### RQ6: "How do IBM/Precely's 5 DQ dimensions (completeness, uniqueness, timeliness, fitness, consistency) 
differ from StreamDQ's SYN/SEM/CRS taxonomy?"

Use: scientific-critical-thinking
Compare: IBM 7 dimensions vs. SYN/SEM/CRS vs. ISO 8000
Action: Decide whether to rebrand taxonomy or add missing dimensions
```
