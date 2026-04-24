# Writing Plan — Phase A Output

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Phase**: Step 12 — Phase A: Orchestrator Preparation
**Date**: April 24, 2026
**Orchestrator**: research-orchestrator
**Input**: All 11 source documents (thesis_outline.md, writing_assignments.md, table_specifications.md, figure_specifications.md, abbreviations.md, references.bib, all 5 chapter .tex files, thesis_template.tex, FORMULATION.md, STATISTICAL_PLAN.md, CONTRIBUTIONS.md)

---

## 1. Template Commands (VNU-UET LaTeX)

All chapters use these commands exclusively:

| Command | Usage |
|---------|-------|
| `\chapter{...}` | Top-level chapter (numbered) |
| `\chapter*{...}` | Unnumbered chapter (intro, conclusion) |
| `\section{...}` | Major section within chapter |
| `\subsection{...}` | Sub-section |
| `\citep{key}` | Citation in parentheses |
| `\citet{key}` | Citation in running text |
| `\autoref{fig:id}` | Auto-reference figure/table/section |
| `\cref{fig:id,tab:id}` | Multiple cross-references |
| `\input{path}` | Include sub-file |
| `\ac{abbr}` | Acronym expansion (first use) |

**Babel**: `\usepackage[vietnamese,english]{babel}` — main text in English; VNU-UET bilingual front/back matter uses Vietnamese.

**Citation style**: `\setcitestyle{square,numbers,sort&compress}` (natbib). Use `\citep{}` for parenthetical citations.

**No `\begin{enumerate}` bullet lists** in academic writing — use `\begin{itemize}` for simple lists, or numbered lists only for sequential steps.

---

## 2. Cross-Reference Map

Every section must reference its supporting figures and tables explicitly:

| Figure/Table | Referenced In |
|---|---|
| T1 (Rule Taxonomy) | §1.5 ML, §2.3 Rule Taxonomy |
| T2 (Context Types) | §1.3 Context-Aware |
| T3 (Comparison) | §1.2 Streaming DQ Frameworks |
| T4 (TQS Weights) | §2.5 TQS |
| T5 (Evaluation Metrics) | §3.3 Evaluation Methodology |
| F1 (System Architecture) | §2.2 System Overview |
| F2 (L0–L5 Hierarchy) | §2.4 Hierarchical Thresholds |
| F3 (Rule Pipeline) | §2.3 Rule Taxonomy |
| F4 (Context Decision Flow) | §2.4 Hierarchical Thresholds |
| F5 (ML Hybrid Architecture) | §2.6 ML Augmentation |
| F6 (Sequence Diagram) | §2.3 Rule Taxonomy |
| F7 (Experimental Pipeline) | §3.2 Setup |
| F8 (Dashboard Mockup) | §3.2 Setup |

**All figures** use `\centering \fbox{\parbox{...}{...}}` as placeholder — no `\includesvg` until F1–F4 are created in Phase B.

---

## 3. Section-by-Section Writing Plan

### Introduction (`introduction.tex`)

**File**: `thesis_template/chapters/introduction.tex` — **COMPLETELY REWRITE** (delete all KG/DF content)

#### §Motivation and Problem Statement (~600 words)
- **Source**: thesis_outline.md §I.1; writing_assignments.md §I.1
- **Content**: Transportation GPS data, DQ issues (spoofing, sensor errors, duplicates), batch vs streaming gap, no streaming GPS validation framework
- **Key claim**: "No surveyed streaming framework implements cross-record GPS trajectory validation on GTFS-realtime feeds" [TIER-1 VERIFIED — from literature review]
- **Gap framing**: GTFS Validator (batch), Stream DaQ (no GPS rules), Great Expectations/Soda Core (batch)
- **Citations**: `\citep{paulheim2017knowledge}` REMOVE, use `\citep{streamdaq2025}`, `\citep{soda-core}`, `\citep{great_expectations}`, `\citep{gtfs_validator}`, `\citep{meter2024}`
- **Tier label**: `[TIER-1 VERIFIED]` for gap claim
- **Active voice**: "We implement" not "X is proposed"

#### §Research Objectives (~200 words)
- **Source**: thesis_outline.md §I.2; writing_assignments.md §I.2; STATISTICAL_PLAN.md
- **6 RQs** (use writing_assignments.md RQ1–RQ6, NOT thesis_outline.md RQ1–RQ9 — see Conflict #1):
  - RQ1: Context-aware thresholds improve F1? (Wilcoxon, ΔF1 ≥ 5pp at L0 cells, α_adj=0.0083)
  - RQ2: L4↔L0 TQS correlation? (Pearson ρ > 0.5)
  - RQ3: TQS↔injection rate correlation? (Pearson ρ > 0.7) — NOTE: must use non-circular redesign from STATISTICAL_PLAN.md §2
  - RQ4: CRS layer incremental F1? (Wilcoxon, ΔF1 ≥ 5pp)
  - RQ5: CRS precision > 0.70 on NYC MTA Bus? (GPS injection)
  - RQ6: ML augmentation improves F1? (Phase 3 ablation)
- **Tier label**: `[TIER-2 ESTIMATED]` for all RQ targets
- **Note**: "This is a research platform, not a production system"

#### §Contributions (~400 words)
- **Source**: thesis_outline.md §I.3; writing_assignments.md §I.3; CONTRIBUTIONS.md Part I
- **4 contributions** (C1–C4):
  - **C1**: First streaming GPS trajectory validation on real GTFS-realtime feeds [TIER-2 ESTIMATED]
  - **C2**: Hierarchical context-aware thresholds L0–L5 fallback [TIER-2 ESTIMATED]
  - **C3**: Ground-truth evaluation methodology [TIER-1 VERIFIED — methodology sound, results pending]
  - **C4**: ML-augmented calibration [TIER-2 ESTIMATED — Phase 3 mandatory]
- **Active voice throughout**: "We implement X" not "X is proposed"
- **No self-praise**: cite evidence, don't say "our framework is excellent"

#### §Thesis Structure (~150 words)
- Chapter 1: Literature review and background
- Chapter 2: System architecture and algorithm design
- Chapter 3: Evaluation methodology and results
- Conclusion: summary and future work

---

### Chapter 1: Fundamentals (`chapter01.tex`)

**File**: `thesis_template/chapters/chapter01.tex` — **COMPLETELY REWRITE** (delete all KG/DF content)

#### §1.1 Introduction to Chapter (~100 words)
- Roadmap: §1.2 → §1.3 → §1.4 → §1.5
- What this chapter covers: streaming DQ, context-aware DQ, GPS validation, ML calibration
- Forward: Chapter 2 designs the system

#### §1.2 Streaming Data Quality: Definitions and Frameworks (~1,200 words)
- **Source**: thesis_outline.md §1.2; table_specifications.md T1
- **T1 DQ Dimensions** (Redman 1998; Otto et al.): completeness, validity, timeliness, consistency, uniqueness
- Streaming vs batch DQ challenges: latency, state management, continuous quality assessment
- **Survey table**: Use T3 (comparison table) — include: GE, Soda Core, Stream DaQ, METER, Ada-Context, Deequ, GTFS Validator
- **Gap**: none survey GPS trajectory validation in streaming
- **Tier label**: `[TIER-1 VERIFIED]` for framework comparison (from audit)
- **Citations**: `\citep{redman1998}`, `\citep{otto2011}`, `\citep{streamdaq2025}`, `\citep{meter2024}`, `\citep{adacontext2025}`, `\citep{deequ2018}`

#### §1.3 Context-Aware Data Quality (~1,200 words)
- **Source**: thesis_outline.md §1.3; table_specifications.md T2
- **5D context decomposition**: D1 Temporal, D2 Spatial, D3 Operational, D4 External*, D5 Data characteristics
  - **IMPORTANT**: D4 is a stub — holiday indicator not implemented. Label explicitly: "D4 is a stub (holiday indicator not implemented; planned future work)"
- **Context-aware thresholds**: rolling P10/P90 conditioned on context key
- **L0–L5 hierarchical fallback**: use T2 and T3
  - L0: hour × zone × WE|WD (≥100 samples, ~2–5% coverage)
  - L1: bucket_zone_WE|WD (≥50)
  - L2: bucket_boro_WE|WD (≥25)
  - L3: time_category (≥10)
  - L4: global (≥5)
  - L5: physics priors (≥0)
- **Comparison**: Stream DaQ (single-level), Ada-Context (fixed grid, no fallback), METER (drift detection, no context decomposition)
- **Citations**: `\citep{adacontext2025}`, `\citep{meter2024}`, `\citep{streamdaq2025}`

#### §1.4 GPS Trajectory Validation for Transportation (~1,000 words)
- **Source**: thesis_outline.md §1.4; FORMULATION.md §3–§4; audit_transportation_dq_literature.md
- **GTFS-realtime data model**: VehiclePosition, TripUpdate, Alert
- **GPS quality issues**: speed spikes, jumps, duplicates
- **NYC TLC note**: zone-level data only (PULocationID/DOLocationID) — **no GPS coordinates**. CRS rules cannot be evaluated on NYC TLC.
- **Prior work**: CETrajAD (SDM 2025) — LSTM batch; GPS spoofing detection (IEEE T-ITS 2024)
- **Gap**: no streaming GPS validation for transit
- **Citations**: `\citep{cetrajad2025}`, `\citep{gpsspoof2024}`, `\citep{gtfsrt2017}`

#### §1.5 Machine Learning for Data Quality Calibration (~800 words)
- **Source**: thesis_outline.md §1.5; CONTRIBUTIONS.md Part III; ML_MODEL_ANALYSIS.md
- **Rule-based vs ML trade-off**: rules authoritative, ML calibration only
- **Three ML components**:
  - Bayesian Optimization (Priority 1, GO): GP surrogate, hourly calibration
  - Isolation Forest (Priority 2, conditional): ρ < 0.8 required
  - XGBoost (Priority 3, conditional): training target undefined
- **LSTM (Priority 4, NO-GO)**: GPS training data unconfirmed, HIGH redundancy with CRS002
- **Use T6** from table_specifications.md for ML comparison
- **Citations**: `\citep{bayesian2023}`

#### §1.6 Chapter Summary (~100 words)
- Summary of §1.2–§1.5
- Forward: Chapter 2 designs the system

---

### Chapter 2: Proposed System Architecture (`chapter02.tex`)

**File**: `thesis_template/chapters/chapter02.tex` — **COMPLETELY REWRITE** (delete all KG/DF content)

#### §2.1 Introduction to Chapter (~100 words)
- Roadmap: §2.2 Overview → §2.3 Rules → §2.4 Thresholds → §2.5 TQS → §2.6 ML
- What this chapter covers: system design, rule taxonomy, context-aware thresholds, TQS, ML integration

#### §2.2 System Overview (~600 words)
- **Architecture description** (reference F1)
- **Two data sources**:
  - NYC TLC Yellow Taxi: Jan 2024 parquet (~3M records), replayed via Kafka. Note: zone-level only — no GPS coordinates.
  - NYC MTA Bus GTFS-realtime: live public feed, no API key required. Note: GPS coordinates available — CRS rules evaluated here.
- **Design principles**: rules authoritative, no silent failures, context-aware thresholds
- **What StreamDQ IS NOT**: not batch, not ML-only, not production-ready
- **References**: F1 (system architecture diagram), F2 (layered architecture)
- **Citations**: `\citep{apache_flink}` (Apache Flink documentation)

#### §2.3 Rule Taxonomy: SYN / SEM / CRS (~1,500 words)
- **Source**: thesis_outline.md §2.3; FORMULATION.md §1.3
- **IMPORTANT — CRS001 BOUNDS**: Use `[2.0, 100.0] km/h` from FORMULATION.md §3.1 (violation if speed < 2.0 OR > 100.0). The 0.5 km/h + 60s requirement is a secondary condition — flag GPS jitter risk but use 2.0 km/h as primary threshold.
  - See Conflict #2 in §6 below
- **CRITICAL — CRS rules require Java**: JVM↔Python overhead too high for PyFlink stateful operations. State explicitly.
- **SYN layer**: SYN001 (NULL/NaN), SYN002 (negative fare), SYN003 (out-of-bound coords)
- **SEM layer**: SEM001–SEM003 (context-aware thresholds), GTFSSem002 (staleness > 5 min)
- **CRS layer**: CRS001 (GPS speed), CRS002 (GPS jump), CRS003 (dedup — TIER-3 UNMEASURABLE due to NG-4)
- **Rule sequencing**: SYN → SEM → CRS (parallel) → TQS aggregation
- **Use T1** from table_specifications.md
- **References**: F3 (rule pipeline), F6 (sequence diagram for CRS Java integration)

#### §2.4 Hierarchical Context-Aware Thresholds: L0–L5 (~1,000 words)
- **Source**: thesis_outline.md §2.4; FORMULATION.md §2; DATA_STRUCTURES.md
- **Context key composition**: formula from FORMULATION.md §2.1
- **Rolling P10/P90 computation**: 1-hour window
- **Fallback chain**: L0 ≥ 100 → L1 ≥ 50 → L2 ≥ 25 → L3 ≥ 10 → L4 ≥ 5 → L5 (physics)
- **BroadcastState implementation**: O(1) amortized lookup
- **Expected L0 coverage**: 2–5% (most NYC zones have < 100 samples per hour) — CRITICAL caveat
- **Use F2** and **T3** from table_specifications.md
- **Power analysis citation**: min_samples from power analysis (Cohen's d=0.30, α=0.01, power=0.80)

#### §2.5 Trajectory Quality Scoring (~600 words)
- **Source**: thesis_outline.md §2.5; FORMULATION.md §6; CONTRIBUTIONS.md Part I
- **5 dimensions** (use FORMULATION.md names, NOT thesis_outline §2.5 names):
  - Tm (Timeliness): inter-event time variance
  - Cn (Completeness): field null/NaN ratio
  - Ac (Accuracy): raw field plausibility ranges
  - Cs (Consistency): GPS coherence, timestamp monotonicity
  - Uv (Uniqueness): duplicate rate via hash
- **V2 weights** (from FORMULATION.md §6.3): ω_Tm=0.20, ω_Cn=0.25, ω_Ac=0.20, ω_Cs=0.25, ω_Uv=0.10
  - See Conflict #3 in §6 below
- **Non-circular design**: TQS computed from raw event properties, NOT from rule violations
- **TQS = α·Tm + β·Cn + γ·Ac + δ·Cs + ε·Uv** (use these Greek letters, consistent with FORMULATION.md)
- **Draws from**: T-Assess (VLDB 2025) with modifications for streaming GPS
- **Use T4** from table_specifications.md
- **Citations**: `\citep{tassess2025}`

#### §2.6 ML-Augmented Threshold Calibration (~800 words)
- **Source**: thesis_outline.md §2.6; ML_INTEGRATION_REDESIGN.md; FORMULATION.md Algorithms G–I
- **BO (Priority 1, GO)**: GP surrogate maximizes F1 on calibration window, hourly run
- **Isolation Forest (Priority 2, conditional)**: ρ < 0.8 required, adjusts effective_k
- **XGBoost (Priority 3, conditional)**: training target undefined, scaffold exists
- **LSTM (Priority 4, NO-GO)**: GPS training data unconfirmed, HIGH redundancy with CRS002
- **Rules remain AUTHORITATIVE**: ML never vetoes violations
- **Use F5** (ML architecture diagram) and **T6** from table_specifications.md

#### §2.7 Chapter Summary (~100 words)
- Summary of §2.2–§2.6
- Forward: Chapter 3 evaluates the system

---

### Chapter 3: Experiments and Evaluation (`chapter03.tex`)

**File**: `thesis_template/chapters/chapter03.tex` — **COMPLETELY REWRITE** (delete all integration/screenshot content)

#### §3.1 Introduction to Chapter (~100 words)
- Roadmap: §3.2 Setup → §3.3 Methodology → §3.4–§3.8 Results → §3.9 Limitations
- Forward: evaluation validates (or challenges) the claims in Chapter 2

#### §3.2 Experimental Setup (~800 words)
- **Datasets**:
  - NYC TLC Yellow Taxi: Jan 2024 parquet (~3M records), replayed via Kafka. Note: zone-level only — no GPS. CRS rules not applicable.
  - NYC MTA Bus GTFS-realtime: live public feed, no API key. GPS available — CRS rules evaluated here.
- **Infrastructure**:
  - LocalPipeline: in-process Python, development/unit tests
  - Flink pipeline: distributed engine, benchmark evaluation
  - Kafka, PostgreSQL, Prometheus
- **IMPORTANT**: LocalPipeline ≠ Flink. Label all latency results as "LocalPipeline profiling only"
- **Synthetic anomaly injection**:
  - Types: NULL (SYN001), NEGATIVE_FARE (SYN002), GPS_SPEED (CRS001), GPS_JUMP (CRS002), DUPLICATE (CRS003)
  - Rates: 0.5%, 1%, 2%, 5%
  - NG-4 NOTE: CRS003 recall = `[TIER-3 UNMEASURABLE]` — replay suppression gate blocks synthetic duplicates
- **Reproducibility**: seed, warmup (10,000 events), measurement window (600s), 3 trials
- **References**: F7 (experimental pipeline), F8 (dashboard mockup)
- **All screenshots**: use `\fbox{\parbox{...}{[TODO: screenshot after system deployment]}}`

#### §3.3 Evaluation Methodology (~1,000 words)
- **Source**: STATISTICAL_PLAN.md; table_specifications.md T5
- **Ground-truth tracking**: ground_truth_events table in PostgreSQL
- **Metrics**: precision, recall, F1 per rule with 95% bootstrap CI (1,000 iterations)
  - **Bootstrap upgrade**: mark as `[TODO: increase to 10,000 iterations for publication]`
- **Latency**: P50/P95/P99 processing latency (event arrival → violation stored)
- **Ablation studies**:
  - RQ1: static (global) vs. L0–L4 context-aware
  - RQ4: SYN-only vs. SYN+SEM vs. SYN+SEM+CRS
  - RQ6: rule-only vs. rule+ML (BO only)
- **Statistical tests**: Wilcoxon signed-rank, Holm-Bonferroni correction (α_adj=0.0083 between families)
- **Use T5** (evaluation metrics table)
- **Citations**: `\citep{exathlon2021}` (evaluation methodology precedent)

#### §3.4 Results: SYN/SEM Rules (~400 words + table)
- **Table**: T9a-style from table_specifications.md
- **All cells**: `[TIER-2 ESTIMATED — benchmark required]`
- Write prose introducing the table structure
- **No actual numbers** until benchmarks run

#### §3.5 Results: CRS Rules (~400 words + table)
- **Table**: T9b-style
- **CRS003 row**: `[TIER-3 UNMEASURABLE — NG-4 blocker]`
- **CRS001/CRS002 rows**: `[TIER-2 ESTIMATED]`
- Write prose introducing the table
- **CRS001 bounds in table**: use [2.0, 100.0] km/h (from FORMULATION.md)

#### §3.6 Results: Context-Aware Threshold Ablation (~400 words + table)
- Write prose about RQ1 ablation design
- Include T9c-style table for L0–L4 vs. static
- **CRITICAL caveat**: L0 coverage is 2–5%. Aggregate ΔF1 will be smaller than L0-specific ΔF1.
- **Power analysis caveat**: RQ1 is underpowered for aggregate ΔF1 at n=90 windows. Report L0-specific separately.

#### §3.7 Results: ML Augmentation (~400 words)
- Write prose about RQ6 ablation design
- Note: Bayesian Optimization only. Isolation Forest conditional.
- **This is a measured contribution**: positive, negative, or mixed results all valid

#### §3.8 Latency and Throughput (~300 words)
- Write prose about latency measurement methodology
- **Table with**: P99 latency ~500ms–1s, Throughput 5,000+ events/sec
- **Labels**: `[TIER-2 ESTIMATED — LocalPipeline profiling only]`
- **CRITICAL**: LocalPipeline results NOT equivalent to distributed Flink results

#### §3.9 Limitations (~600 words) — **MANDATORY**
- **Write ALL 7 limitations explicitly** (from thesis_outline.md §3.9):
  1. CRS003 recall = `[TIER-3 UNMEASURABLE]` (NG-4)
  2. L0 coverage sparse (2–5%) → aggregate ΔF1 likely 1–2pp, not 5pp
  3. ML augmentation = `[TIER-2 ESTIMATED]` — all numbers need benchmark
  4. Single dataset (NYC TLC + NYC MTA Bus) — may not generalize
  5. LocalPipeline ≠ distributed Flink — distributed latency unknown
  6. L4 global fallback masks context-specific patterns
  7. D4 External context is a stub — holiday indicator not implemented

#### §3.10 Chapter Summary (~100 words)

---

### Conclusion (`conclusion.tex`)

**File**: `thesis_template/chapters/conclusion.tex` — **COMPLETELY REWRITE** (delete all placeholder content)

#### §Summary of Contributions (~300 words)
- Restate C1–C4 with honest results
- C1: First streaming GPS trajectory validation — `[TIER-2 ESTIMATED]`
- C2: Hierarchical context-aware thresholds (L0–L5) — `[TIER-2 ESTIMATED]`
- C3: Ground-truth evaluation methodology — VERIFIED methodology (sound design)
- C4: ML-augmented calibration — `[TIER-2 ESTIMATED]`, positive/negative/mixed results all valid

#### §Key Findings (~300 words)
- CRS001 (GPS speed bounds) and CRS002 (GPS jump detection) designed as specified — `[TIER-2 ESTIMATED]`
- Context-aware thresholds provide value at L0 cells (2–5% coverage) — `[TIER-2 ESTIMATED]`
- L4 global fallback necessary but dilutes context-specific patterns
- ML augmentation: `[TIER-2 ESTIMATED]` — measured contribution
- TQS correlation with injection rate: `[TIER-2 ESTIMATED]`

#### §Future Work (~200 words)
1. Fix NG-4: replay suppression gate blocks CRS003 synthetic injection
2. Implement D4: External context (holiday indicator)
3. Deploy Flink cluster for distributed benchmarks
4. Re-evaluate LSTM if GPS training data becomes available
5. Extend CRS rules to other GTFS feeds beyond NYC

---

## 4. Placeholder Summary

| Item | Status | After Phase B (Figures) |
|-------|--------|---------------------------|
| F1–F4 figures | Needed | Reference in text after Phase B |
| F5–F8 figures | Needed | Reference in text after Phase B |
| T1–T6 tables | Ready | Insert after Phase B |
| T9a–T9c (benchmark results) | Placeholder only | Fill after implementation |
| Abstract | Write last | Write after all chapters |
| All result numbers | Placeholder | Fill after benchmark |

---

## 5. Tier Label Placement Guide

| Context | Label | Example |
|---------|-------|---------|
| Gap claim (no prior work) | `[TIER-1 VERIFIED]` | "No surveyed framework implements GPS cross-record validation" |
| Benchmark result | `[TIER-1 VERIFIED]` after run | "SYN001 precision: 0.91 (95% CI: 0.89–0.93)" |
| Estimated metric | `[TIER-2 ESTIMATED]` | "Context-aware ΔF1: [TIER-2 ESTIMATED]" |
| Benchmark result (before run) | `[TIER-2 ESTIMATED]` | "CRS001 precision: [TIER-2 ESTIMATED]" |
| Known blocker | `[TIER-3 UNMEASURABLE]` | "CRS003 recall: [TIER-3 UNMEASURABLE — NG-4]" |
| Methodology | `[TIER-1 VERIFIED]` | "Bootstrap CI with 1,000 iterations" |
| Latency (LocalPipeline) | `[TIER-2 ESTIMATED — LocalPipeline only]` | "P99 latency: ~500ms–1s" |

**Minimum occurrences in Ch.3**: ≥ 20 `TIER` labels (1 per metric cell + section headers)

---

## 6. Identified Conflicts — Flag for Phase D

| # | Conflict | Documents | Resolution |
|---|----------|-----------|-----------|
| **1** | RQ count: 6 in writing_assignments.md vs. 9 in thesis_outline.md | thesis_outline.md §I.2 vs. writing_assignments.md §I.2 | **Keep RQ1–RQ6 from writing_assignments.md**. Drop RQ7–RQ9 from thesis_outline.md. RQ2–RQ3 in thesis_outline use old circular TQS design (STATISTICAL_PLAN.md redesigned RQ3 non-circularly). |
| **2** | CRS001 bounds: [0.5, 100] km/h in thesis_outline.md §2.3 vs. [2.0, 100.0] km/h in FORMULATION.md §3.1 | thesis_outline.md §2.3 vs. FORMULATION.md §3.1 | **Use FORMULATION.md**: violation if speed < 2.0 OR > 100.0 km/h. The 0.5 km/h + 60s condition is a secondary guard against GPS jitter. Cite FORMULATION.md §3.1 for the [2.0, 100.0] primary threshold. |
| **3** | TQS weight notation: α=0.25, β=0.20, γ=0.25, δ=0.10, ε=0.20 in thesis_outline.md §2.5 vs. ω_Tm=0.20, ω_Cn=0.25, ω_Ac=0.20, ω_Cs=0.25, ω_Uv=0.10 in FORMULATION.md §6.3 | thesis_outline.md §2.5 vs. FORMULATION.md §6.3 | **Use FORMULATION.md** V2 weights: ω_Tm=0.20, ω_Cn=0.25, ω_Ac=0.20, ω_Cs=0.25, ω_Uv=0.10. Update thesis_outline.md §2.5 to match. FORMULATION.md §6.3 is the authoritative algorithm spec. |
| **4** | TQS dimension names: thesis_outline.md §2.5 lists Validity (Vl) as 5th dimension; FORMULATION.md §6 uses Uniqueness (Uv) | thesis_outline.md §2.5 vs. FORMULATION.md §6 | **Use FORMULATION.md**: 5 dimensions are Tm, Cn, Ac, Cs, Uv. Remove Validity (Vl) from thesis_outline.md. Validity was from original circular TQS design. |
| **5** | RQ2–RQ3 definitions: thesis_outline.md §I.2 uses "L4↔L0 correlation" and "TQS↔injection rate" — old circular design | thesis_outline.md §I.2 vs. STATISTICAL_PLAN.md §2 | **Use STATISTICAL_PLAN.md** non-circular redesign for RQ3. RQ2 (L4↔L0 correlation) is valid but use new dimension names. Update thesis_outline.md §I.2 to match writing_assignments.md RQ2. |
| **6** | T7–T10 don't exist in table_specifications.md | thesis_outline.md §6 vs. table_specifications.md | These are referenced in thesis_outline but embedded in text/subsections. **T7** (CRS bounds) = embedded in thesis_outline §2.3 text. **T8** (evaluation metrics) = embedded in thesis_outline §3.3. **T9** (benchmark results) = placeholder tables (T9a, T9b, T9c). **T10** (statistical tests) = embedded in thesis_outline §3.3. No separate table files needed. |
| **7** | Figure F4–F10 missing from figure_specifications.md | thesis_outline.md §6 vs. figure_specifications.md | F4–F8 exist in figure_specifications.md (F4=Context Decision, F5=Rule Taxonomy, F6=Sequence, F7=Pipeline, F8=Dashboard). F9–F10 in thesis_outline §6 are "BO calibration traces" and "latency histogram" — these need specs added. **Add F9, F10 to figure_specifications.md** in Phase B or Phase D. |

---

## 7. Citation Key Mapping

These keys must exist in `references.bib` (created in Phase C):

| Key | Reference |
|-----|-----------|
| `redman1998` | Redman, T.C. (1998). Data Quality: The Field Guide |
| `otto2011` | Otto et al. — Organizational data quality |
| `streamdaq2025` | Papastergios & Gounaris, arXiv 2025 |
| `soda-core` | Soda Core documentation |
| `great_expectations` | Great Expectations OSS |
| `gtfs_validator` | GTFS Validator |
| `gtfsrt2017` | GTFS-realtime specification |
| `meter2024` | METER (Zhu et al.), VLDB 2024, doi:10.14778/3636218.3636233 |
| `adacontext2025` | Ada-Context (DMKD 2025) |
| `deequ2018` | Schelter et al., VLDB 2018, doi:10.14778/3229863.3229867 |
| `tassess2025` | T-Assess, VLDB 2025, PVLDB Vol.18, No.3, pp.666-674 |
| `cetrajad2025` | Cao & Akoglu, SDM 2025 |
| `gpsspoof2024` | GPS spoofing (IEEE T-ITS 2024) |
| `exathlon2021` | Exathlon (Palpanas & Ilyas), VLDB 2021 |
| `martin2025` | Martin et al., PVLDB 2025, doi:10.14778/3748191.3748209 |
| `apache_flink` | Apache Flink documentation |
| `haversine` | Haversine formula reference |
| `bayesian2023` | Bayesian Optimization reference |
| `nyc_tlc` | NYC TLC Yellow Taxi dataset |
| `nyc_mta_bus` | NYC MTA Bus GTFS-realtime dataset |

---

## 8. Files to Create/Modify in Phase E

| File | Action | Phase |
|------|--------|-------|
| `thesis_template/chapters/introduction.tex` | REWRITE | E1 |
| `thesis_template/chapters/chapter01.tex` | REWRITE | E1 |
| `thesis_template/chapters/chapter02.tex` | REWRITE | E1 |
| `thesis_template/chapters/chapter03.tex` | REWRITE | E2 |
| `thesis_template/chapters/conclusion.tex` | REWRITE | E3 |
| `thesis_template/references.bib` | REWRITE | C |
| `final/06_PAPER_OUTLINE/figures/F1_System_Architecture.excalidraw.md` | CREATE | B |
| `final/06_PAPER_OUTLINE/figures/F2_L0_L5_Hierarchy.excalidraw.md` | CREATE | B |
| `final/06_PAPER_OUTLINE/figures/F3_Rule_Pipeline.excalidraw.md` | CREATE | B |
| `final/06_PAPER_OUTLINE/figures/F4_CRS_Java_Integration.excalidraw.md` | CREATE | B |
| `final/06_PAPER_OUTLINE/CROSS_CHECK/report.md` | CREATE | D |
| `thesis_template/chapters/appendix_results.tex` | Placeholder | E (after impl.) |
| `thesis_template/chapters/appendix_config.tex` | Placeholder | E (after impl.) |

---

*Document classification: Tier 1 (Verified) for template commands and cross-reference map; Tier 2 (Estimated) for all benchmark-dependent content.*
