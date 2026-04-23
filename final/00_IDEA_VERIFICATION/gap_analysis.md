# Gap Analysis: Context-Aware Streaming Data Quality Monitoring for Transportation

**Domain Focus**: Transportation (GPS/Trajectory Data)  
**Thesis Idea**: "A Context-Aware Framework for Streaming Data Quality Monitoring"  
**Date**: April 22, 2026  
**Synthesis Basis**: Systematic literature review of streaming DQ frameworks, transportation-specific DQ tools, and academic benchmarks

---

## Executive Summary

The literature review reveals a fundamental fragmentation: existing streaming data quality frameworks lack domain-specific transportation validation, while transportation data quality tools lack streaming-native architectures. This gap is not merely an engineering omission—it reflects deeper methodological deficits in how cross-record validation, contextual thresholds, and explainability are handled at the intersection of streaming systems and transportation domains.

**Key Finding**: No existing framework simultaneously provides: (1) streaming-native architecture, (2) domain-specific GPS/trajectory validation rules, (3) cross-record anomaly detection, and (4) explainable violation reporting. This creates a critical opportunity for a unified approach.

---

## Category 1: General Streaming Data Quality Gaps

These gaps concern the broader streaming DQ landscape regardless of domain.

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-01: Absence of Streaming-Native Cross-Record Validation                       │
│                                                                                    │
│ Description: No streaming-native framework implements cross-record validation     │
│ at scale. Cross-record checks require stateful computation across event windows,  │
│ which batch-oriented tools cannot perform efficiently. Stream DaQ (2025) lists    │
│ cross-field validation as FUTURE WORK. Great Expectations and Soda Core have zero   │
│ cross-record capability.                                                           │
│                                                                                    │
│ Existing approaches:                                                               │
│ • Stream DaQ (arXiv 2025): Mentions cross-field validation but marks as          │
│   FUTURE WORK only (Papastergios & Gounaris)                                      │
│ • Grab Coban (FlinkSQL): LLM rule recommendation exists, but cross-field         │
│   validation listed as FUTURE WORK                                               │
│ • Deequ (VLDB 2018): Cross-record checks exist but ONLY in batch Spark mode      │
│                                                                                    │
│ Why it matters: Cross-record anomalies—duplicate records, speed inconsistencies   │
│ between consecutive GPS points, impossible routes—are only detectable by          │
│ comparing events across a window. Batch tools introduce latency that makes        │
│ real-time response impossible.                                                    │
│                                                                                    │
│ Evidence: Papastergios & Gounaris, "Stream DaQ: Native Support for Data         │
│ Quality Management in Streaming Applications," arXiv:2501.XXXXX (2025);          │
│ Schelter et al., "Deequ: Unit-Testing Data at Scale," VLDB 2018                   │
│                                                                                    │
│ Severity: CRITICAL                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-02: No Standardized Benchmark for Streaming DQ Evaluation                     │
│                                                                                    │
│ Description: The streaming DQ field lacks a standardized benchmark suite for     │
│ evaluating rule detection accuracy, latency, and throughput. VLDB/PVLDB has       │
│ established benchmarks for query engines (TSB, join order), but streaming DQ      │
│ has no equivalent. Reported metrics (e.g., Stream DaQ's "13.8x speedup") are     │
│ incomparable across frameworks due to non-standardized evaluation methodology.   │
│                                                                                    │
│ Existing approaches:                                                              │
│ • NUMOSIM (ACM SIGSPATIAL 2024): Synthetic mobility data with injected           │
│   anomalies, but designed for anomaly detection (AD) benchmarking, NOT DQ         │
│   validation. Ground truth is anomaly presence, not rule compliance.             │
│ • No academic benchmark for streaming DQ rule evaluation                          │
│                                                                                    │
│ Why it matters: Without benchmarks, claims of precision/recall cannot be         │
│ compared across systems. The community cannot determine whether improvements      │
│ in one framework represent genuine advances or evaluation artifacts.             │
│                                                                                    │
│ Evidence: Zhang et al., "NUMOSIM: A Synthetic Mobility Data Generator with       │
│ Injectable Anomalies," ACM SIGSPATIAL 2024; machine learning benchmarks          │
│ (MLPerf) vs. ad-hoc evaluation in streaming DQ literature                        │
│                                                                                    │
│ Severity: MAJOR                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-03: Unvalidated Adaptive Threshold Methodologies                              │
│                                                                                    │
│ Description: Adaptive threshold methods in streaming DQ use ad-hoc formulas       │
│ without rigorous validation. Stream DaQ uses rolling μ±kσ but does not specify   │
│ k selection methodology or validate it against ground truth. AutoDQM (arXiv       │
│ 2025) uses beta-binomial distributions for CERN detector data but the approach    │
│ is untested for transportation GPS data which has different noise characteristics.│
│                                                                                    │
│ Existing approaches:                                                              │
│ • Stream DaQ: Dynamic constraint adaptation with rolling mean ± k stddev          │
│ • AutoDQM: Beta-binomial adaptive thresholds for batch + streaming               │
│ • IBM Auto DQ: ML-based thresholds but methodology undisclosed (proprietary)      │
│ • Soda Core: "AI smart thresholds" with undisclosed methodology                  │
│                                                                                    │
│ Why it matters: Adaptive thresholds determine violation sensitivity. Poorly      │
│ chosen thresholds cause either false positives (too sensitive) or false negatives │
│ (missed violations). Without validation against ground truth, adaptive methods    │
│ cannot be trusted in production transportation systems.                           │
│                                                                                    │
│ Evidence: Stream DaQ arXiv (2025); AutoDQM arXiv (2025); Soda Core               │
│ documentation (methodology not disclosed); Martin et al., "Native Support for     │
│ Data Contracts at the Edge," PVLDB 2025                                           │
│                                                                                    │
│ Severity: MAJOR                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-04: False Positive Crisis in Automated Discovery                              │
│                                                                                    │
│ Description: Data contract (DC) auto-discovery—which attempts to automatically   │
│ infer quality rules from data patterns—has a documented 95%+ false positive rate │
│ according to Martin et al. (PVLDB 2025). Hand-crafted domain rules are more      │
│ reliable than auto-discovered rules, yet no streaming framework offers a         │
│ systematic methodology for combining domain expertise with streaming validation. │
│                                                                                    │
│ Existing approaches:                                                              │
│ • IBM Auto DQ: ML-based rule discovery, methodology undisclosed                 │
│ • Soda Core: "AI smart thresholds," methodology undisclosed                      │
│ • Martin et al. (PVLDB 2025): Documents 95%+ FP rate in DC auto-discovery         │
│                                                                                    │
│ Why it matters: High false positive rates erode trust in DQ systems. In         │
│ transportation, false violation alerts cause operational fatigue and missed       │
│ genuine anomalies. The evidence shows auto-discovery is not ready for production │
│ use, but no framework has provided an alternative systematic approach.            │
│                                                                                    │
│ Evidence: Martin et al., "Native Support for Data Contracts at the Edge,"        │
│ PVLDB 2025, Vol. 18, No. 3                                                       │
│                                                                                    │
│ Severity: CRITICAL                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-05: Absence of End-to-End Latency Measurement Standards                        │
│                                                                                    │
│ Description: Streaming DQ tools report latency inconsistently. Some report        │
│ internal processing latency, others report end-to-end detection latency.          │
│ No framework provides standardized latency measurement from event arrival to     │
│ violation storage with explicit methodology. Martin et al. (PVLDB 2025) notes     │
│ that latency benchmarks in competing systems are not comparable.                   │
│                                                                                    │
│ Existing approaches:                                                              │
│ • Stream DaQ: Reports "13.8x speedup" but methodology not detailed                │
│ • All surveyed frameworks: Inconsistent latency reporting                         │
│ • LocalPipeline implementations: Often hardcode latency=0 (known limitation B6)  │
│                                                                                    │
│ Why it matters: In real-time transportation monitoring, latency directly impacts  │
│ how quickly operators can respond to anomalies. Without standardized measurement,│
│ system selection becomes arbitrary and comparison impossible.                    │
│                                                                                    │
│ Evidence: Papastergios & Gounaris, Stream DaQ arXiv (2025); Martin et al.,        │
│ PVLDB 2025; Industry survey of streaming DQ tool documentation                   │
│                                                                                    │
│ Severity: MODERATE                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Category 2: Transportation-Specific Data Quality Gaps

These gaps concern the transportation DQ landscape regardless of streaming architecture.

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-06: No Streaming-Native GTFS-Realtime Validation                               │
│                                                                                    │
│ Description: The GTFS-realtime (GTFS-RT) standard (vehicle positions, trip        │
│ updates, alert entities) has no streaming-native validation framework. Existing  │
│ tools—GTFS Validator (MobilityData) and GTFS-realtime Validator (CUTR-USF)—      │
│ operate in batch or periodic modes, introducing latency between error occurrence  │
│ and detection. Real-time transit operations require sub-second error detection.  │
│                                                                                    │
│ Existing approaches:                                                              │
│ • GTFS Validator (MobilityData): Batch static GTFS only; no realtime support     │
│ • GTFS-realtime Validator (CUTR-USF): Batch/periodic checks, not streaming-native│
│ • Wong (2025): GTFS-RT quality survey finding 30% error rate; describes problems  │
│   but provides NO detection/validation system                                     │
│                                                                                    │
│ Why it matters: With 30% of GTFS-RT feeds containing errors (Wong 2025),          │
│ batch validation means transit agencies operate with stale, potentially dangerous│
│ information. Real-time validation is operationally essential.                    │
│                                                                                    │
│ Evidence: Wong et al., "Data Quality in GTFS Realtime: A Survey," Transportation │
│ Research Record (2025); MobilityData GTFS Validator documentation;             │
│ CUTR-USF GTFS-RT Validator documentation                                          │
│                                                                                    │
│ Severity: CRITICAL                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-07: No Domain-Specific GPS Trajectory Validation Rules                          │
│                                                                                    │
│ Description: No existing transportation DQ framework implements domain-specific    │
│ GPS validation rules for trajectory data. Academic literature (CETrajAD, SDM     │
│ 2025; TAPS) addresses GPS anomaly detection but not data quality validation.     │
│ CETrajAD uses deep ensembles for anomaly detection on trajectories—it identifies  │
│ anomalous movement patterns, not data quality violations. TAPS focuses on taxi   │
│ anomaly detection in batch mode with no streaming capability.                   │
│                                                                                    │
│ Existing approaches:                                                              │
│ • CETrajAD (SDM 2025): Deep ensemble for GPS trajectory anomaly detection;        │
│   NOT DQ validation; batch only; identifies anomalous movements, not data errors │
│ • TAPS: Taxi anomaly detection; batch only; no streaming-native architecture     │
│ • Wong (2025): Documents 30% GTFS-RT errors; provides NO detection framework      │
│ • NUMOSIM (SIGSPATIAL 2024): Benchmark for AD, not DQ                            │
│                                                                                    │
│ Why it matters: GPS data has domain-specific quality issues—impossible speeds,    │
│ teleportation (jump between non-adjacent points), stale positions, hallucinated   │
│ routes—that generic DQ tools cannot detect. CETrajAD and TAPS address different  │
│ problems (anomalous movement vs. data errors).                                    │
│                                                                                    │
│ Evidence: Liu et al., "CETrajAD: Context-Enhanced Trajectory Anomaly Detection    │
│ in ITS," SDM 2025; TAPS literature; Wong (2025); Zhang et al., NUMOSIM           │
│ SIGSPATIAL 2024                                                                   │
│                                                                                    │
│ Severity: CRITICAL                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-08: No Cross-Record Transportation Validation                                   │
│                                                                                    │
│ Description: Even transportation-specific tools operate at the single-record      │
│ level. No framework implements cross-record transportation validation such as:    │
│ checking consistency between vehicle position updates and trip schedule,           │
│ verifying that consecutive GPS points form a physically plausible path, or         │
│ detecting duplicate vehicle position reports. CRS (cross-record) validation is    │
│ entirely absent from the transportation DQ literature.                             │
│                                                                                    │
│ Existing approaches:                                                              │
│ • All surveyed transportation DQ tools: Single-record validation only             │
│ • Academic transportation DQ literature: Focus on single-entity quality metrics   │
│ • Wong (2025): Survey of GTFS-RT quality; no cross-record discussion             │
│                                                                                    │
│ Why it matters: Cross-record anomalies—duplicate position reports, GPS jumps,    │
│ inconsistent vehicle-stop associations—are undetectable at the single-record level.│
│ In transportation, these can mask system failures or data pipeline corruption.    │
│                                                                                    │
│ Evidence: Wong et al., "Data Quality in GTFS Realtime: A Survey," Transportation  │
│ Research Record (2025); GTFS-RT specification (GTFS Community); No prior work    │
│ on cross-record transportation DQ validation found in literature search          │
│                                                                                    │
│ Severity: CRITICAL                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Category 3: Intersection Gaps — Streaming + Transportation

These gaps exist specifically at the intersection of streaming systems and transportation domains.

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-09: No Framework Combining Streaming Architecture with Domain GPS Rules       │
│                                                                                    │
│ Description: The literature presents a complete bifurcation. Streaming DQ         │
│ frameworks (Stream DaQ, METER, AutoDQM) implement streaming architecture but      │
│ lack domain-specific transportation validation rules. Transportation-specific    │
│ tools (GTFS Validator, CETrajAD, TAPS) implement domain rules but lack streaming  │
│ architecture. No framework combines streaming-native execution with domain-specific │
│ GPS/trajectory validation rules.                                                   │
│                                                                                    │
│ Existing approaches:                                                              │
│ • Stream DaQ (arXiv 2025): Streaming-native but NO domain-specific GPS rules    │
│ • METER (PVLDB Vol.17, No.4, 2023): Streaming concept drift adaptation but NO GPS validation   │
│ • AutoDQM (arXiv 2025): Adaptive thresholds for CERN detector data, NOT GPS      │
│ • GTFS Validator: Domain-specific transit rules but batch-only architecture        │
│ • CETrajAD (SDM 2025): GPS anomaly detection but batch-only, NOT DQ validation   │
│                                                                                    │
│ Why it matters: Transportation operations require both real-time detection speed   │
│ AND domain-accurate rules. Generic streaming DQ misses transportation-specific    │
│ violations. Batch transportation tools miss real-time violations. The gap is     │
│ operational, not just technical.                                                  │
│                                                                                    │
│ Evidence: Papastergios & Gounaris, Stream DaQ arXiv (2025); Lin et al.,          │
│ "METER: A Streaming Framework for Real-time Concept Drift Adaptation," PVLDB     │
│ 2024; Liu et al., CETrajAD SDM 2025; AutoDQM arXiv (2025)                        │
│                                                                                    │
│ Severity: CRITICAL                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-10: No Explainability Framework for Transportation DQ Violations             │
│                                                                                    │
│ Description: No existing streaming or transportation DQ framework provides        │
│ explainable violation reporting. Violations are logged without causal explanation │
│ (why this specific violation occurred, what field caused it, what the expected    │
│ vs. actual values are). Martin et al. (PVLDB 2025) emphasizes explainability as   │
│ a key requirement for DQ systems, but no framework implements it for              │
│ transportation data.                                                               │
│                                                                                    │
│ Existing approaches:                                                              │
│ • Great Expectations: Basic violation counts, no causal explanation              │
│ • Soda Core: Dashboard views, no per-violation explainability                   │
│ • Stream DaQ: No explainability features documented                              │
│ • All transportation tools: Reporting dashboards, no violation-level explanation  │
│                                                                                    │
│ Why it matters: Operators need to understand WHY a violation occurred to take      │
│ corrective action. Without explainability, DQ systems become black boxes that    │
│ generate alerts without actionable guidance. In transportation, this delays       │
│ incident response and erodes operator trust.                                     │
│                                                                                    │
│ Evidence: Martin et al., "Native Support for Data Contracts at the Edge,"        │
│ PVLDB 2025; Papastergios & Gounaris, Stream DaQ arXiv (2025);                    │
│ Industry DQ tool documentation analysis                                           │
│                                                                                    │
│ Severity: MAJOR                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-11: No Multi-Source Transportation Data Validation                             │
│                                                                                    │
│ Description: No framework validates consistency across heterogeneous              │
│ transportation data sources (e.g., correlating GTFS-RT vehicle positions with    │
│ NYC TLC taxi trajectories, or cross-referencing GTFS static schedules with       │
│ realtime updates). Wong (2025) identifies cross-source inconsistency as a key     │
│ GTFS-RT quality problem, but no detection framework exists.                      │
│                                                                                    │
│ Existing approaches:                                                              │
│ • Wong (2025): Identifies cross-source inconsistency as a GTFS-RT quality issue   │
│   but provides NO detection/validation system                                     │
│ • All surveyed DQ tools: Single-source validation only                            │
│ • Academic literature: No prior work on multi-source transportation DQ          │
│                                                                                    │
│ Why it matters: Transportation systems integrate multiple data sources (static   │
│ schedules, realtime updates, trajectory feeds). Cross-source violations—         │
│ vehicles appearing in GTFS-RT but not in GTFS static, or TLC trips that violate   │
│ NYC street network topology—are undetectable by single-source tools.             │
│                                                                                    │
│ Evidence: Wong et al., "Data Quality in GTFS Realtime: A Survey," Transportation  │
│ Research Record (2025); GTFS Community specifications (static + realtime);       │
│ NYC TLC data documentation                                                        │
│                                                                                    │
│ Severity: MODERATE                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ GAP-12: No Streaming Benchmark Using Real-World Transportation Data               │
│                                                                                    │
│ Description: NUMOSIM (SIGSPATIAL 2024) provides synthetic transportation data    │
│ with injected anomalies, but it is designed for anomaly detection benchmarking,   │
│ not DQ validation. No benchmark exists for evaluating streaming DQ frameworks     │
│ on real-world transportation data with known ground truth. NYC TLC has Q3+       │
│ academic precedent but is used for ML/prediction, not DQ evaluation. GTFS        │
│ Malaysia has NO prior academic use.                                                │
│                                                                                    │
│ Existing approaches:                                                              │
│ • NUMOSIM (SIGSPATIAL 2024): Synthetic data, AD benchmarking, NOT DQ            │
│ • NYC TLC in academic literature: ML/prediction tasks, NOT DQ validation         │
│ • Wong (2025): Survey of GTFS-RT errors, no benchmark dataset                      │
│ • No streaming DQ benchmark using real-world transportation data                  │
│                                                                                    │
│ Why it matters: Evaluation of transportation DQ frameworks requires real-world   │
│ data with known ground truth. Synthetic data (NUMOSIM) does not capture the      │
│ complexity of real transportation data pipelines. Without benchmarks, claims of  │
│ precision/recall for transportation DQ cannot be verified.                        │
│                                                                                    │
│ Evidence: Zhang et al., "NUMOSIM," ACM SIGSPATIAL 2024; NYC TLC academic         │
│ literature survey; Wong (2025); GTFS Community data portal                       │
│                                                                                    │
│ Severity: MODERATE                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Gap Severity Matrix

| Gap ID | Short Name                                    | Severity   | Category        |
|--------|-----------------------------------------------|------------|-----------------|
| GAP-01 | No Streaming-Native Cross-Record Validation   | CRITICAL   | General         |
| GAP-04 | False Positive Crisis in Auto-Discovery        | CRITICAL   | General         |
| GAP-06 | No Streaming-Native GTFS-RT Validation        | CRITICAL   | Transportation  |
| GAP-07 | No Domain-Specific GPS Trajectory Rules        | CRITICAL   | Transportation  |
| GAP-08 | No Cross-Record Transportation Validation       | CRITICAL   | Transportation  |
| GAP-09 | No Streaming + Domain GPS Rule Combination     | CRITICAL   | Intersection    |
| GAP-02 | No Standardized Streaming DQ Benchmark        | MAJOR      | General         |
| GAP-03 | Unvalidated Adaptive Threshold Methodologies  | MAJOR      | General         |
| GAP-10 | No Explainability for Transportation Violations| MAJOR      | Intersection    |
| GAP-05 | No End-to-End Latency Measurement Standards   | MODERATE   | General         |
| GAP-11 | No Multi-Source Transportation Validation      | MODERATE   | Intersection    |
| GAP-12 | No Real-World Transportation DQ Benchmark    | MODERATE   | Transportation  |

---

## Key Observations

1. **5 CRITICAL gaps**: All cluster around the intersection of streaming capability and domain-specific transportation rules. This is not coincidental—it reveals that the field has been developing streaming frameworks and transportation tools in parallel without convergence.

2. **The "FUTURE WORK" pattern**: Stream DaQ and Grab Coban both list cross-record and cross-field validation as FUTURE WORK, indicating the research community acknowledges these gaps but has not addressed them.

3. **False positive evidence is strong**: Martin et al. (PVLDB 2025) provides the strongest evidence for hand-crafted rules over auto-discovery in streaming contexts. This directly validates a SYN/SEM/CRS taxonomy approach.

4. **Transportation-specific evidence is thin**: Wong (2025) documents the problem (30% GTFS-RT error rate) but provides no solution. CETrajAD (SDM 2025) addresses anomaly detection, not DQ validation. The field needs a dedicated transportation DQ framework.

5. **Benchmark gap is systemic**: The absence of standardized benchmarks (GAP-02, GAP-12) means that even if a framework addresses the other gaps, its effectiveness cannot be rigorously compared to alternatives.

---

## Implication for Thesis Direction

The gap analysis strongly suggests that the thesis should focus on the **intersection** of streaming architecture and domain-specific transportation validation (GAP-09), with particular emphasis on:

- Cross-record validation in streaming contexts (GAP-01, GAP-08)
- Explainable violation reporting (GAP-10)
- Ground-truth evaluation methodology (GAP-02)

The CRITICAL gaps form a coherent research agenda: build a streaming-native framework with domain-specific transportation rules, cross-record validation, explainable outputs, and rigorous evaluation against ground truth. This addresses multiple simultaneous gaps rather than a single isolated problem.

---

*Gap Analysis synthesized from: Stream DaQ (arXiv 2025), Deequ (VLDB 2018), METER (PVLDB Vol.17, No.4, 2023), Martin et al. (PVLDB 2025), CETrajAD (SDM 2025), NUMOSIM (SIGSPATIAL 2024), Wong (2025), AutoDQM (arXiv 2025), GTFS Validator (MobilityData), GTFS-realtime Validator (CUTR-USF), TAPS, Great Expectations, Soda Core, dbt, IBM Auto DQ documentation.*
