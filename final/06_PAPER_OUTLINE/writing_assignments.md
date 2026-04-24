# Writing Assignments

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Step**: Step 11 — Writing Assignments
**Date**: April 24, 2026
**Purpose**: Assign sections to writers based on expertise and dependencies

---

## Overview

Each section has: word count target, source documents, key claims to include, and writing standards. Every claim must cite a source. Every number must be labeled [TIER-1/2/3] or [NEEDS BENCHMARK].

---

## Assignment 1: Abstract (500 words total: 250 EN + 250 VI)

**Assigned to**: Writing specialist
**Deadline**: After all other sections drafted
**Dependencies**: None (write last)

### Abstract (English) — ~250 words

1. **Problem** (2–3 sentences): Transportation systems generate continuous GPS records; existing DQ tools lack streaming GPS validation
2. **Approach** (3–4 sentences): StreamDQ — Flink-native, hierarchical context-aware thresholds (L0–L5), GPS cross-record rules (CRS001–CRS003)
3. **Contributions** (3 bullets):
   - First streaming GPS trajectory validation on real GTFS-realtime feeds
   - Hierarchical context-aware thresholds with graceful L0–L5 fallback
   - Ground-truth evaluation methodology with explicit measurement limitations
4. **Results** (1–2 sentences): [TIER-2] Rule precision [ESTIMATED], context-aware ΔF1 [ESTIMATED], ML augmentation [MEASURED CONTRIBUTION]
5. **Keywords**: streaming data quality, GPS trajectory, context-aware thresholds, Apache Flink, GTFS-realtime

**Sources**: `final/04_NOVELTY_CONTRIBUTION/CONTRIBUTIONS.md` Part I; `thesis_outline.md` §2.2

### Abstract (Vietnamese) — ~250 words

Same structure, translated. Use Vietnamese academic writing conventions.

---

## Assignment 2: Introduction (~2,000 words)

**Assigned to**: Writing specialist
**Deadline**: Week 1
**Dependencies**: None

### §I.1 Motivation & Problem Statement (~600 words)

**Sources**: `final/03_IDEA_SELECTION/report.md` §1; `final/00_IDEA_VERIFICATION/report.md`

**Content**:
- Transportation data is GPS-rich and high-velocity (bus, taxi, transit)
- Data quality issues: GPS spoofing, sensor errors, duplicate reports
- Batch DQ tools miss real-time anomalies
- **Gap**: No streaming framework validates GPS trajectory quality

**Claims to include**:
- NYC MTA Bus generates continuous GPS positions every ~30s [VERIFIED: public GTFS feed]
- Great Expectations and Soda Core are batch-only [VERIFIED: documented]
- Stream DaQ lacks GPS cross-record validation [VERIFIED: COMPETITIVE_TABLE.md]
- GPS spoofing in transportation is documented threat [VERIFIED: Martin et al. PVLDB 2025]

**Writing standard**: Active voice, concrete numbers where available, cite every claim

### §I.2 Research Objectives (~200 words)

**Sources**: `final/05_ALGORITHM_DESIGN/HYPOTHESES.md`; `final/03_IDEA_SELECTION/report.md`

**Content**:
- RQ1: Context-aware thresholds improve F1 over static? (Wilcoxon signed-rank, ΔF1 ≥ 5pp at L0 cells, α_adj=0.0083)
- RQ2: L4 global fallback TQS correlates with L0 TQS? (Pearson ρ > 0.5)
- RQ3: TQS correlates with injection rate? (Pearson ρ > 0.7)
- RQ4: CRS layer adds incremental F1 over SYN+SEM? (Wilcoxon signed-rank, ΔF1 ≥ 5pp)
- RQ5: CRS001/CRS002 precision > 0.70 on NYC MTA Bus? (GPS injection)
- RQ6: ML augmentation improves F1? (Phase 3 ablation, IF←P90 correlation prerequisite)

### §I.3 Contributions (~400 words)

**Sources**: `final/04_NOVELTY_CONTRIBUTION/CONTRIBUTIONS.md` Part II

**Content** (4 contributions, each ~100 words):
- **C1**: GPS trajectory validation — first streaming implementation on real GTFS feeds
- **C2**: Hierarchical context-aware thresholds — L0–L5 fallback, graceful degradation
- **C3**: Ground-truth evaluation methodology — synthetic injection + bootstrap CI + honest limitations
- **C4**: ML-augmented calibration — measured contribution, Phase 3 mandatory

**Writing standard**: "We implement X" not "X is proposed." Cite evidence, don't praise.

### §I.4 Thesis Structure (~150 words)

**Content**: Chapter 1 → literature review. Chapter 2 → architecture. Chapter 3 → evaluation. Conclusion.

---

## Assignment 3: Chapter 1 — Fundamentals (~4,500 words)

**Assigned to**: Writing specialist
**Deadline**: Week 1–2
**Dependencies**: §I.1 (Introduction motivation)

### §1.2 Streaming DQ Frameworks (~1,200 words)

**Sources**: `final/01_LITERATURE_REVIEW/AUDITS/audit_streaming_dq_frameworks.md`

**Content**:
1. DQ dimensions: Redman, Otto et al.
2. Streaming vs. batch DQ challenges
3. Survey table: GE, Soda, Stream DaQ, METER, Ada-Context, Deequ, GTFS Validator
4. Gap: none survey GPS trajectory validation in streaming

**Tables needed**: Survey comparison table (use T5 from `table_specifications.md`)
**Figures needed**: None (prose + table)

**Writing standard**: Use comparison table T5 for systematic comparison; cite each framework's publication

### §1.3 Context-Aware DQ (~1,200 words)

**Sources**: `final/05_ALGORITHM_DESIGN/FORMULATION.md` §2; `final/01_LITERATURE_REVIEW/AUDITS/audit_streaming_dq_frameworks.md`

**Content**:
1. 5D context decomposition (temporal, spatial, operational, external, data char.)
2. Context-aware thresholds: rolling P10/P90 conditioned on context
3. L0–L5 hierarchical fallback (table T3)
4. Comparison with Stream DaQ, Ada-Context, METER

**Tables needed**: T2 (5D), T3 (L0–L5)
**Figures needed**: F2 (L0–L5 hierarchy) — order from designer

**Writing standard**: Mathematical notation for context key construction; cite every claim about prior work

### §1.4 GPS Trajectory Validation (~1,000 words)

**Sources**: `final/01_LITERATURE_REVIEW/AUDITS/audit_transportation_datasets.md`; `final/01_LITERATURE_REVIEW/AUDITS/audit_transportation_dq_literature.md`

**Content**:
1. GTFS-realtime data model (VehiclePosition, TripUpdate)
2. GPS quality issues: speed spikes, jumps, duplicates
3. CETrajAD (SDM 2025), GPS spoofing detection (IEEE T-ITS 2024)
4. Gap: no streaming GPS validation for transit

**Figures needed**: None (prose + table)
**Writing standard**: Cite CETrajAD and GPS spoofing work; distinguish batch (CETrajAD) from streaming (StreamDQ)

### §1.5 ML for DQ Calibration (~800 words)

**Sources**: `final/04_NOVELTY_CONTRIBUTION/ML_POSITIONING.md` §7; `final/05_ALGORITHM_DESIGN/ML_MODEL_ANALYSIS.md`

**Content**:
1. Rule-based vs. ML trade-off table (from ML_POSITIONING.md §2.2)
2. Hybrid architecture: rules authoritative, ML calibration
3. Three ML components: BO (Priority 1), IF (Priority 2), XGBoost (Priority 3)
4. Why LSTM is NO-GO: GPS data unconfirmed, HIGH redundancy

**Tables needed**: T6 (ML model comparison)
**Figures needed**: None

**Writing standard**: Be explicit about conditional status; "Isolation Forest (Priority 2, conditional)" not "Isolation Forest"

---

## Assignment 4: Chapter 2 — Architecture (~5,500 words)

**Assigned to**: Writing specialist + system architect
**Deadline**: Week 2–3
**Dependencies**: Chapter 1 (§1.2–§1.5), F1, F2, F3

### §2.2 System Overview (~600 words)

**Sources**: `final/05_ALGORITHM_DESIGN/FORMULATION.md` §1

**Content**:
- Architecture diagram description (F1)
- Two data sources: NYC TLC (parquet replay), NYC MTA Bus (live)
- Design principles: rules authoritative, no silent failures
- What StreamDQ IS NOT: not batch, not ML-only, not production

**Figures needed**: F1 (system architecture)
**Writing standard**: Reference F1 explicitly; describe each pipeline stage

### §2.3 Rule Taxonomy (~1,500 words)

**Sources**: `final/05_ALGORITHM_DESIGN/FORMULATION.md` §3–§7

**Content**:
- SYN layer: SYN001, SYN002, SYN003
- SEM layer: SEM001, SEM002, SEM003, GTFSSem002
- CRS layer: CRS001, CRS002, CRS003 (Java)
- Rule sequencing (from QUALITY_AUDIT.md)

**Tables needed**: T1 (rule taxonomy)
**Figures needed**: F3 (rule pipeline)
**Writing standard**: Each rule has: what it checks, why the bound is chosen, dataset scope

### §2.4 Hierarchical Thresholds (~1,000 words)

**Sources**: `final/05_ALGORITHM_DESIGN/FORMULATION.md` §2; `final/05_ALGORITHM_DESIGN/DATA_STRUCTURES.md`

**Content**:
- Context key composition with formula
- Rolling P10/P90 computation
- Fallback chain with min-sample thresholds
- BroadcastState implementation

**Figures needed**: F2 (L0–L5 hierarchy)
**Writing standard**: Mathematical notation; cite power analysis for min-sample values

### §2.5 Trajectory Quality Scoring (~600 words)

**Sources**: `final/05_ALGORITHM_DESIGN/FORMULATION.md` §5

**Content**:
- Five TQS dimensions with formulas
- V2 weights and selection rationale
- Non-circular design: raw properties only
- TQS vs. injection rate correlation (RQ3)

**Tables needed**: T4 (TQS weights)
**Figures needed**: F6 (TQS computation)
**Writing standard**: Explicit formula for each dimension; cite T-Assess (VLDB 2025) for attribution idea

### §2.6 ML Augmentation (~800 words)

**Sources**: `final/05_ALGORITHM_DESIGN/ML_INTEGRATION_REDESIGN.md`; `final/05_ALGORITHM_DESIGN/FORMULATION.md` Algorithms G–I

**Content**:
- BO: GP surrogate, F1 objective, hourly calibration
- IF: single global model, anomaly_score, effective_k
- XGBoost: conditional, training target undefined
- LSTM: NO-GO, GPS data unconfirmed

**Tables needed**: T6 (ML comparison)
**Figures needed**: F5 (ML hybrid architecture)
**Writing standard**: Be explicit about conditional status; "Bayesian Optimization (Priority 1)" not "ML calibration"

---

## Assignment 5: Chapter 3 — Experiments (~4,500 words)

**Assigned to**: Writing specialist + data scientist
**Deadline**: Week 3–4
**Dependencies**: All other chapters; benchmark data

### §3.2 Experimental Setup (~800 words)

**Sources**: `final/05_ALGORITHM_DESIGN/STATISTICAL_PLAN.md` §2

**Content**:
- Datasets: NYC TLC (parquet), NYC MTA Bus (live GTFS-realtime)
- Infrastructure: LocalPipeline + Flink
- Synthetic injection: types, rates, reproducibility protocol
- Warmup: 10,000 events; measurement: 600s; trials: 3

**Writing standard**: Be explicit about what's estimated vs. verified; LocalPipeline ≠ Flink

### §3.3 Evaluation Methodology (~1,000 words)

**Sources**: `final/05_ALGORITHM_DESIGN/STATISTICAL_PLAN.md` §3; `final/04_NOVELTY_CONTRIBUTION/ML_INTEGRATION_REDESIGN.md` §6

**Content**:
- Ground-truth tracking: `ground_truth_events` table
- Metrics: precision, recall, F1 with 95% bootstrap CI (10,000 iterations, percentile method for F1; BCa for skewed latency)
- Ablation studies: RQ1, RQ4, RQ6
- Statistical tests: Wilcoxon signed-rank on per-event binary detection; Holm-Bonferroni within RQ families; McNemar mid-p as sensitivity analysis

**Tables needed**: T8 (evaluation metrics), T10 (statistical tests)
**Writing standard**: Every metric has CI method specified; cite Exathlon (VLDB 2021)

### §3.4–§3.7 Results (~1,800 words)

**Status**: TIER-2 ESTIMATED — write with placeholders

**Content**:
- Six experiment scenarios referenced (F7): S1/S2 (SYN001), S3 (GTFSSem002), S4 (volume), S5 (SEM rules), S6 (CRS rules)
- SYN/SEM results: T6a table (S1–S5, TIER-2 placeholders)
- CRS results: T6a table (S6 GPS rules, TIER-2 placeholders; CRS003 = Tier 3 UNMEASURABLE)
- Context-aware ablation: T6b table
- ML ablation: T6c table (Phase 3)

**Writing standard**: Every number labeled [TIER-2 ESTIMATED]; every Tier-3 claim labeled [TIER-3 UNMEASURABLE]; never present estimated as verified

**Figures needed**: F7 (experimental pipeline, describes how all 6 scenarios are injected)
**Tables needed**: T6a, T6b, T6c (benchmark results)

**Writing standard**: Every number labeled [TIER-2 ESTIMATED]; every Tier-3 claim labeled [TIER-3 UNMEASURABLE]; never present estimated as verified

### §3.9 Limitations (~400 words) — **MANDATORY**

**Sources**: `final/04_NOVELTY_CONTRIBUTION/CONTRIBUTIONS.md` Part IV

**Content** (list all 7 limitations explicitly):
1. CRS003 recall = Tier 3 UNMEASURABLE (NG-4)
2. L0 coverage sparse (2–5%) → aggregate ΔF1 small
3. ML augmentation = Tier 2 ESTIMATED
4. Single dataset (NYC TLC + NYC MTA Bus)
5. LocalPipeline ≠ distributed Flink
6. L4 dilution effect
7. D4 External context is stub

**Writing standard**: This section MUST be present. Every limitation stated explicitly, not buried. This is a quality standard.

---

## Assignment 6: Conclusion (~800 words)

**Assigned to**: Writing specialist
**Deadline**: Week 4
**Dependencies**: All other sections

### §C.1 Summary (~300 words)
- Restate C1, C2, C3, C4
- State results honestly: [TIER-2] for all numbers

### §C.2 Key Findings (~300 words)
- GPS rules work as designed [TIER-2]
- Context-aware value depends on L0 coverage [TIER-2]
- ML: measured contribution [TIER-2]

### §C.3 Future Work (~200 words)
- Fix NG-4 (replay suppression gate)
- Implement D4 (External context)
- Deploy Flink cluster
- Re-evaluate LSTM if GPS data available

---

## Writing Standards Checklist

| Standard | Requirement | Check |
|----------|-------------|--------|
| Active voice | "We implement" not "X is proposed" | |
| Citation every claim | Every factual claim has DOI/URL | |
| Tier labeling | Every number labeled Tier 1/2/3 or ESTIMATED | |
| Limitations section | Must be present, explicit | |
| Comparison tables | Use T5, T6 from specifications | |
| Figure captions | Descriptive, not just label | |
| No self-praise | Cite evidence, don't say "excellent" | |
| Tables over prose | Use T1–T10 as specified | |
| Related work | GE, Soda, Stream DaQ, METER, Deequ, CETrajAD | |

---

## Section Dependencies Graph

```
Introduction
  └── Ch.1 Fundamentals
        ├── §1.2 Streaming DQ → needs T5
        ├── §1.3 Context-Aware → needs T2, T3, F2
        ├── §1.4 GPS Validation → needs literature review
        └── §1.5 ML → needs T6
  └── Ch.2 Architecture
        ├── §2.2 Overview → needs F1
        ├── §2.3 Rules → needs T1, F3
        ├── §2.4 Thresholds → needs T3, F2
        ├── §2.5 TQS → needs T4, F6
        └── §2.6 ML → needs T6, F5
  └── Ch.3 Experiments
        ├── §3.2 Setup → needs benchmark
        ├── §3.3 Methodology → needs T8, T10
        ├── §3.4–§3.7 Results → needs T9a, T9b, T9c
        └── §3.9 Limitations → MANDATORY
  └── Conclusion
        └── All chapters
```
