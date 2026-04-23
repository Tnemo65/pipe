# ContextAware-DQ — Final Research Document

**Project**: "A Context-Aware Framework for Streaming Data Quality Monitoring"
**Domain**: Transportation — GPS Trajectory + GTFS Realtime
**Phase**: Phase 0 — Idea Verification (COMPLETE)
**Generated**: 2026-04-22

---

## Folder Structure

```
final/
  README.md                          -- This file
  00_IDEA_VERIFICATION/
    report.md                        -- Phase 0: full idea verification report
    gap_analysis.md                   -- 12-gap analysis from literature research
  01_LITERATURE_REVIEW/
    AUDITS/                          -- Research audit reports
      audit_streaming_dq_frameworks.md   -- General streaming DQ landscape (19 frameworks)
      audit_transportation_dq_literature.md -- Transportation-specific DQ literature
      audit_transportation_datasets.md     -- Dataset analysis (NYC TLC, GTFS Malaysia)
  02_IDEA_BRAINSTORM/
    report.md                        -- Phase 2: 12 ideas, 5-agent parallel brainstorm
    AGENT_TRANSCRIPTS/               -- 8 agent transcripts (brainstorm phase)
  03_IDEA_SELECTION/
    report.md                        -- Phase 3: idea selection report
    context_aware_upgrade.md         -- Phase 3B: context-aware upgrade evaluation
    AGENT_TRANSCRIPTS/               -- 7 agent transcripts (selection + upgrade phases)
  04_LAYER_INTEGRATION/             -- Phase 4: Storage (Layer 5) + Alerting (Layer 6) + ML Layer
```

---

## What's Here

### Phase 0 Output (Idea Verification — COMPLETE)

**Verdict**: MODIFY AND PROCEED

The idea is feasible for a **B+ to A- paper**. The contribution (streaming + domain-specific GPS trajectory rules for transportation) is genuine and verified. Three critical actions are required before proceeding.

- `00_IDEA_VERIFICATION/report.md` — Full report: literature landscape, gap analysis, 5-criteria assessment, proposed framework, 4 research questions, feasibility, peer review
- `00_IDEA_VERIFICATION/gap_analysis.md` — 12 gaps identified and structured with evidence
- `01_LITERATURE_REVIEW/AUDITS/` — Supporting research from 3 parallel literature searches

### What Was Deleted

- `CONFLICT_RESOLUTION.md` — Old file, resolved conflicts between non-existent `finalsystem/` and `finalsystem2/`
- `08_DRAFTS/` — Empty placeholder skeletons (23-33 lines), replaced by real drafts when Phase 1 begins

---

## Research Summary

### Key Finding

No existing framework combines streaming architecture with domain-specific GPS/trajectory validation rules for transportation. This is the central verified gap (GAP-01 and GAP-07, severity: CRITICAL).

### Literature Survey

- **19 frameworks** surveyed across 3 categories: stream-native (Stream DaQ, Grab Coban, METER), batch-approximation (Deequ (Schelter et al., PVLDB 2018, doi:10.14778/3229863.3229867), GE, Soda, dbt, AutoDQM), observability (Monte Carlo, Metaplane)
- **Transportation DQ**: GTFS Validator (MobilityData), GTFS-rt Validator (CUTR-USF) are batch-only; Wong (2025) documents 30% GTFS-RT error rate
- **GPS trajectory AD**: CETrajAD (SDM 2025), TAPS, NUMOSIM (SIGSPATIAL 2024) — related but distinct task (anomaly detection, not data quality validation)
- **Key reference**: Martin et al. (PVLDB 2025) — 95%+ false positive rate for DC auto-discovery. Validates that hand-crafted rules (like ContextAware-DQ's SYN/SEM/CRS taxonomy) are more reliable than automated discovery.

### Datasets

| Dataset | Accessibility | Academic Precedent | Status |
|---------|--------------|-------------------|--------|
| NYC TLC Yellow Taxi | Public, Parquet | Q3+ (VLDB, SIGMOD, KDD) | Ready |
| GTFS Malaysia | CC BY 4.0, api.data.gov.my | None (novel use) | CRS verification needed |

---

## Proposed Framework

**ContextAware-DQ-Transport**: Streaming DQ monitoring for transportation with:
- Three-layer rule taxonomy: SYN (syntactic) + SEM (semantic) + CRS (cross-record)
- Domain-specific GPS rules: Haversine speed bounds, GPS jump detection, duplicate detection
- Hierarchical context-aware thresholds (3D: temporal + spatial + operational)
- **ML-augmented threshold calibration** (Isolation Forest + Bayesian Optimization + METER drift detection)
- Datasets: NYC TLC + GTFS Malaysia

### Research Questions

| RQ | Question | Gap | Key Metric |
|----|----------|-----|------------|
| RQ1 | Does context-aware threshold adaptation improve F1 over static thresholds? | GAP-03 | ΔF1 ≥ 5pp, 95% CI |
| RQ2 | Does hierarchical fallback maintain quality on sparse context cells? | GAP-03 | Fallback accuracy < 10% error |
| RQ3 | Does context-decomposed TQS correlate with ground truth better than aggregate TQS? | GAP-10 | Pearson ρ > 0.7 |
| RQ4 | Does TQS accurately quantify quality degradation with injection rate? | TQS calibration | |ΔTQS − Δinjection| < 5pp, ρ > 0.9 |
| RQ5 | Do CRS rules achieve precision > 0.70 on GTFS Malaysia? | GAP-06 | P > 0.70, 95% CI |
| RQ6 | Does ML-augmented threshold calibration (Isolation Forest + Bayesian Opt) improve F1 over rule-only thresholds? | GAP-03 | ΔF1 ≥ 5pp, 95% CI |

---

## 3 CRITICAL Actions Before Phase 1

| # | Action | Why |
|---|--------|-----|
| **1** | DELETE all fabricated claims from every document | "94.2%", "13x GE", "91.8%", "245K events/sec" are fabricated. Academic fraud if published. |
| **2** | BUILD evaluation module (`streamdq/evaluation/`) | Every thesis metric depends on this. Currently missing. |
| **3** | RESOLVE CRS002 scope honestly | CRS001/CRS002 only run on GTFS, NOT on NYC TLC. Main dataset gets zero cross-record GPS validation. |

---

## Grade Projection

**B+ to A-** (conference/workshop). Achieievable if:
- Context-aware precision shows significant improvement over static
- Evaluation module is built and ablation study is run
- GTFS GPS validation is demonstrated on real errors
- All fabricated claims are purged

**B** if: marginal improvement, incomplete evaluation, unresolved CRS scope.

---

## Skill Usage Tracker

| Skill | Used For |
|-------|----------|
| @.cursor/skills/01-academic-writing | Contribution framing, peer review simulation |
| @.cursor/skills/02-literature-research | General streaming DQ, transportation DQ, datasets |
| @.cursor/skills/03-data-statistics | Evaluation design, bootstrap CI methodology |
| @.cursor/skills/04-data-engineering | Technical feasibility, architecture assessment |
| @.cursor/skills/05-research-analysis | Gap identification, idea verification, threat analysis |
| @.cursor/skills/06-infrastructure-devops | Reproducibility, tech stack evaluation |

---

## Phase 4: Layer Integration (Storage + Alerting)

**Decision**: Selective integration of Layer 5 (Storage) + Layer 6 (Alert) from old `StreamDQ v2.0` proposal into `ContextAware-DQ`.

### Storage: PostgreSQL Schema (5 Tables)

The current proposal has minimal sink layer (Kafka + PostgreSQL + Prometheus). These tables are **ADDED** to support RQ2-RQ5 evaluation:

| Table | Purpose | Retention |
|-------|---------|-----------|
| `violations` (extended) | All SYN/SEM/CRS violations with context + fallback level | 90 days |
| `context_statistics` | L0-L5 rolling stats per context cell (threshold calibration) | 365 days |
| `metrics_summary` | Time-window aggregations (TQS scores, throughput) | 365 days |
| `ground_truth_events` | Injected anomalies with ground truth labels (P/R/F1 matching) | 90 days |
| `evaluation_results` | Per-run P/R/F1 with bootstrap 95% CI (permanent research artifact) | Permanent |

**Deferred**: `alert_history`, `anomaly_violations`, S3, Redis, PagerDuty/Slack (out of scope for research platform).

**Rejected**: S3 raw events (Kafka stores them), Redis cache (BroadcastState is O(1)), PagerDuty/Slack (production only).

### Alerting: Prometheus + Grafana (Research Platform)

Severity-based routing simplified for research (no PagerDuty/Slack):

| Severity | Research Action |
|:--------:|:----------------|
| CRITICAL | Grafana red alert + log |
| HIGH | Grafana orange alert |
| MEDIUM | Grafana yellow alert |
| LOW | Grafana grey (info) |

**Grafana: 4 essential panels** (thesis presentation):
1. Violations by Rule (stacked bar — shows which rules fire most)
2. TQS Score Trend (time series + threshold — RQ3/RQ4 evaluation)
3. Context Fallback Distribution (stacked bar — RQ2, shows L0-L5 distribution)
4. Violations by Severity (pie chart — alert prioritization)

**Additional panels** (nice-to-have): Processing Latency, Throughput, CRS State Size.

**Prometheus alert rules** extend `prometheus_alerts.yml` with:
- `StreamDQExcessiveFallback`: >50% events falling to L4 global fallback
- `StreamDQLowTQS`: TQS drops below 0.80
- `StreamDQGPSSpoofingDetected`: GPS jump violations > 0.1/sec
- `StreamDQHighNullRate`: NULL violation rate > 5%
- `StreamDQNoEvents`: No events processed for 2 minutes
- `StreamDQStateSizeWarning`: CRS state > 500 MB

### Updated Architecture (Storage Layer Integrated)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Apache Flink (Streaming Engine)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  KAFKA INPUT STREAM                                                     │
│  ├── nyc-taxi-events (NYC TLC Parquet replay → Kafka)                  │
│  └── gtfs-vehicle-positions (GTFS Malaysia live feed)                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ FLINK PIPELINE                                                    │   │
│  │  1. Watermark Generation (event-time, bounded out-of-order 60s)  │   │
│  │  2. Parse & Route (Java ProcessFunction)                         │   │
│  │  3. Rule Evaluation (SYN/SEM → async Python; CRS → Java)       │   │
│  │  4. Context-Aware Threshold Engine (Broadcast State, L0-L5)       │   │
│  │     ┌────────────────────────────────────────────────────────┐ │   │
│  │     │  ML CALIBRATION (async, periodic every 1h):            │ │   │
│  │     │  • Isolation Forest: anomaly score → confidence weight  │ │   │
│  │     │  • Bayesian Optimization: k-multiplier per context cell  │ │   │
│  │     │  • METER: concept drift detection per context cell       │ │   │
│  │     └────────────────────────────────────────────────────────┘ │   │
│  │  5. TQS Aggregation                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  SINK LAYER                                                             │
│  ├── Kafka: quality-violations (real-time alerting)                      │
│  ├── PostgreSQL (PERSISTENT): violations, context_statistics,             │
│  │   metrics_summary, ground_truth_events, evaluation_results         │
│  └── Prometheus (STREAMING): violations per rule/severity,              │
│      TQS score, context fallback, CRS counters, throughput/latency    │
│                                                                         │
│  OBSERVABILITY LAYER                                                     │
│  ├── Grafana: 4 essential dashboard panels                              │
│  └── Prometheus alerting rules                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Updated Rule Taxonomy (11 Rules)

| Rule | Check | Dataset | Source |
|------|-------|--------|--------|
| SYN001 | Null/missing required fields | NYC TLC + GTFS | `syntactic.py` |
| SYN002 | Fare amount range | NYC TLC | `syntactic.py` |
| SYN003 | Location validity | NYC TLC + GTFS | `syntactic.py` |
| SEM001 | Fare plausibility (adaptive) | NYC TLC | `semantic.py` |
| SEM002 | Trip duration sanity (adaptive) | NYC TLC | `semantic.py` |
| SEM003 | Passenger count plausibility | NYC TLC | `semantic.py` |
| **GTFSSem002** | **Vehicle position stale > 5 min** | **GTFS** | **`gtfs_rules.py`** |
| CRS001 | GPS speed bounds [2, 120] km/h | GTFS | `cross_record.py` |
| CRS002 | GPS position jump >100m/30s | GTFS | `cross_record.py` |
| CRS003 | Event deduplication (300s window) | NYC TLC + GTFS | `cross_record.py` |

> GTFSSem002 closes the Timeliness DQ dimension gap (Section 5.2). Already implemented in `gtfs_rules.py`, added to taxonomy.

### ML Layer: Adaptive Context Calibration (Core Contribution)

Three ML integration points embedded in the Context-Aware Threshold Engine (step 4 of the Flink pipeline):

1. **Isolation Forest** (Cao & Akoglu, SDM 2025): Anomaly scoring per event feature vector → confidence weight for threshold adaptation. Events with high anomaly scores trigger stricter thresholds.

2. **Bayesian Optimization** (AutoDQM, arXiv 2025): Gaussian Process surrogate model optimizes k-multiplier per context cell on a held-out calibration window. Optimized thresholds written to Broadcast State every 1 hour.

3. **METER** (Zhu et al., PVLDB 2024): Concept drift detection per context cell via χ² test on feature distributions. When drift is detected, context statistics are reset and threshold recalibration is triggered.

**Positioning**: ML models provide calibration signals; rule engine remains authoritative. Violations are always determined by rule thresholds, never by ML predictions.

### Implementation Effort Summary

| Priority | Effort | Components |
|:--------:|:------:|-----------|
| P0 (Must have) | **4 days** | 5 PostgreSQL tables |
| P1 (Should have) | **3 days** | 4 Prometheus metrics + 4 Grafana panels |
| P2 (Nice to have) | **3 hours** | GTFSSem002 taxonomy + Prometheus alerts |
| **Total** | **~7 days** | |

**Week 1**: PostgreSQL schema (violations, context_statistics, metrics_summary)
**Week 2**: PostgreSQL tables (ground_truth_events, evaluation_results) + Prometheus metrics
**Week 3**: Grafana dashboard (4 panels)
**Week 4**: Prometheus alerts + GTFSSem002 taxonomy

---

## Next Phase

**Phase 1**: Implementation — Build `streamdq/evaluation/` module, fix bugs, run benchmarks.
