# Idea Verification Report

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Author**: Research Analyst Agent
**Date**: 2026-04-22
**Phase**: Phase 0 — Idea Verification
**Constraint**: All information from research, not from pre-existing project documents

---

## 1. Literature Landscape

### 1A. General Streaming DQ Frameworks

*Research conducted via Semantic Scholar API, arXiv, Google Scholar, and web search.*

#### Stream-Native Frameworks (true real-time, no micro-batch)

| Framework | Venue | Year | Architecture | Approach | Key Features | Limitations |
|-----------|-------|------|-------------|----------|-------------|-------------|
| **Stream DaQ** | arXiv (preprint) | 2025 | Stream-native (Kafka + Flink) | Rule-based + statistical | 30+ checks, configurable windowing, dynamic constraint adaptation (rolling mu+/-k sigma), quality meta-streams | Preprint only (not peer-reviewed); NO domain-specific GPS validation; cross-record listed as future work |
| **Grab Coban** | Production | 2024 | Stream (FlinkSQL + Kafka) | LLM + rule-based | LLM-based semantic rule recommendation; production-scale (100+ topics) | Cross-field validation listed as **future work only**; no published academic evaluation |
| **Confluent + Flink/ksqlDB** | Industry | 2024 | Stream-native | Schema Registry + SQL rules | Industry standard: schema validation at ingestion + dead-letter routing | Record-level business rule validation not addressed |
| **METER** | PVLDB | 2024 | Stream | Concept drift adaptation | Explicit drift adaptation for streaming anomaly detection | NO cross-record validation; no domain-specific rules |

#### Batch Frameworks with Streaming Approximations

| Framework | Venue | Year | Architecture | Approach | Key Features | Limitations |
|-----------|-------|------|-------------|----------|-------------|-------------|
| **Deequ** | VLDB | 2018 | Batch (Spark) | Statistical constraint suggestion | Automated constraint suggestion; incremental computation | **Highest-venue academic paper** on batch DQ; NO streaming |
| **Great Expectations** | Open-source | 2019+ | Micro-batch (Python) | Rule-based | Record-level checks; active community | Explicitly: "micro-batch not appropriate for streaming"; no cross-record |
| **Soda Core** | Open-source | 2021+ | Batch SQL | ML-based thresholds | AI smart thresholds (methodology undisclosed) | Minutes-scale latency; no streaming-native |
| **dbt** | Open-source | 2021+ | 5-15 min schedules | SQL-based | Incremental models; near-real-time possible | NO streaming-native validation; batch by design |
| **AutoDQM** | arXiv | 2025 | Batch + streaming modes | Beta-binomial adaptive thresholds | Per-channel adaptation for CERN CMS detector data | NO GPS/domain-specific validation; batch-first |
| **IBM Auto DQ** | Proprietary | 2024 | Stream (streaming SQL) | ML-based | Enterprise-scale; ML anomaly detection on quality metrics | Proprietary; methodology undisclosed; no domain-specific GPS |
| **Declarative Streaming** | EDBT | 2025 | Stream (Flink) | Declarative constraints | Declarative DQ constraint specification; streaming SQL | Cross-record not evaluated; no domain-specific validation |

#### Observability Platforms (metadata/metric monitoring)

| Framework | Venue | Year | Architecture | Approach | Key Features | Limitations |
|-----------|-------|------|-------------|----------|-------------|-------------|
| **Monte Carlo** | Proprietary | 2020+ | Metric monitoring | ML anomaly detection | Freshness/volume monitoring; no record-level validation | Not data quality rule validation |
| **Metaplane** | Proprietary | 2021+ | Metric monitoring | ML anomaly detection | Column-level monitoring; no cross-record | Not record-level |
| **SYNQ** | Open-source | 2022 | Metric monitoring | ML anomaly detection | Lightweight; no record-level | Not record-level |

#### Key Evidence from General Landscape

1. **Stream DaQ** (Papastergios & Gounaris, arXiv:2506.06147, 2025) is the most academically rigorous streaming DQ framework. Introduces configurable windowing and dynamic constraint adaptation. **Limitation confirmed**: No domain-specific GPS/trajectory validation.

2. **Deequ** (Schelter et al., VLDB 2018) is the highest-venue academic paper on batch DQ. Key insight: automated constraint suggestion reduces manual effort. **Limitation confirmed**: Batch-only, no streaming.

3. **False DC Discovery Problem**: Martin et al. (PVLDB 2025, doi:10.14778/3748191.3748209) demonstrates that DC auto-discovery has **95%+ false positive rate**. Validates that hand-crafted rules (like StreamDQ's SYN/SEM/CRS taxonomy) are more reliable than automated discovery.

4. **METER** (PVLDB 2024) on concept drift adaptation for streaming: addresses temporal distribution shift but does NOT address cross-record validation.

### 1B. Transportation-Specific DQ Frameworks

#### GTFS Validation Tools

| Tool | Type | Architecture | Key Features | Limitations |
|------|------|-------------|-------------|-------------|
| **GTFS Validator** (MobilityData) | Open-source | Batch | 72 error types; static GTFS only | Batch only; NO GTFS-realtime; NO streaming |
| **GTFS-realtime Validator** (CUTR-USF) | Open-source | Batch/periodic | GTFS-rt validation | Batch/periodic; NOT streaming-native |
| **GTFSVTOR** | Open-source | Batch | GTFS static validation | Batch only |
| **TransitWand** | Open-source | Field validation | Data collection tool | Not a validation framework |

#### Academic Research on Transportation DQ

| Paper | Venue | Year | Focus | Architecture | Limitations |
|-------|-------|------|-------|-------------|-------------|
| **Wong (2025)** | arXiv | 2025 | GTFS-RT quality survey (California, 750 feeds) | Descriptive analysis | Describes problems; NO validation/fixing system |
| **CETrajAD** | SDM | 2025 | GPS trajectory anomaly detection | Batch deep ensemble | NOT data quality validation; NOT streaming |
| **TAPS** | — | 2024 | Taxi anomaly detection | Batch | Batch only |
| **NUMOSIM** | ACM SIGSPATIAL | 2024 | Synthetic mobility benchmark | Batch | AD algorithm benchmark; not DQ validation |
| **iBAT** | UbiComp | 2011 | Taxi GPS fraud detection | Batch | Batch only; specific to fraud not DQ |

#### Key Evidence from Transportation Landscape

1. **GTFS Validator** and **GTFS-realtime Validator** are batch tools, not streaming-native. No real-time GTFS quality monitoring exists as an open-source framework.

2. **GPS trajectory anomaly detection** (CETrajAD, SDM 2025) addresses a related but distinct problem: detecting anomalous trajectories, not validating data quality. The methods (deep learning ensembles) are computationally expensive and not suited for real-time streaming.

3. **Wong (2025, arXiv)** documents **30% GTFS-RT error rate** across California feeds but provides NO solution. This is the strongest evidence that GTFS-RT quality monitoring is needed and currently unaddressed.

4. **No streaming framework** combines: streaming architecture + GPS trajectory validation + cross-record stateful rules + domain-specific transportation rules.

---

## 2. Gap Analysis

### 2A. Gaps from General Streaming DQ

```
┌────────────────────────────────────────────────────────────┐
│ GAP-G1: No Cross-Record GPS Trajectory Validation          │
│                                                            │
│ Description: No existing streaming DQ framework validates   │
│ GPS trajectory plausibility (Haversine distance, speed     │
│ bounds, GPS jump detection) on streaming vehicle positions. │
│                                                            │
│ Existing approaches: Deequ (VLDB 2018) does aggregate      │
│ checks; Stream DaQ (arXiv 2025) does range checks;        │
│ CETrajAD (SDM 2025) does GPS anomaly detection (batch).   │
│                                                            │
│ Why it matters: GPS quality directly affects transit        │
│ reliability; 30% GTFS-RT error rate documented (Wong      │
│ 2025). Streaming pipelines ingest GPS data without         │
│ validation.                                                │
│                                                            │
│ Evidence: Wong (2025, arXiv) — 30% GTFS-RT error rate;     │
│ Stream DaQ (arXiv:2506.06147) — no GPS rules; Deequ       │
│ (VLDB 2018) — no cross-record spatial validation.         │
│                                                            │
│ Severity: CRITICAL                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-G2: Adaptive Thresholds Unvalidated in Streaming        │
│                                                            │
│ Description: Rolling statistical baselines for adaptive      │
│ thresholds in streaming are described in Stream DaQ and     │
│ AutoDQM but not rigorously evaluated. Fallback strategies  │
│ for sparse context cells are absent.                       │
│                                                            │
│ Existing approaches: Stream DaQ (rolling mu+/-k sigma);     │
│ AutoDQM (beta-binomial per channel); AccelData (ML-based,  │
│ proprietary). None addresses hierarchical fallback for     │
│ sparse context combinations.                               │
│                                                            │
│ Why it matters: Adaptive thresholds are key to reducing     │
│ false positives during atypical conditions. Without        │
│ fallback, sparse contexts produce unreliable thresholds.    │
│                                                            │
│ Evidence: Stream DaQ (arXiv:2506.06147); AutoDQM          │
│ (arXiv:2501.13789); AccelData (2024).                     │
│                                                            │
│ Severity: MAJOR                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-G3: No Streaming GTFS-Realtime Validation System       │
│                                                            │
│ Description: No framework validates GTFS-realtime vehicle   │
│ positions in real-time. All GTFS validators (MobilityData, │
│ CUTR-USF) are batch-oriented.                             │
│                                                            │
│ Existing approaches: GTFS Validator (batch, static only);   │
│ GTFS-rt Validator (periodic, not streaming). Wong (2025)    │
│ documents errors but does not fix them.                    │
│                                                            │
│ Why it matters: GTFS-realtime feeds power transit apps,    │
│ arrival predictions, and operations. Errors propagate in    │
│ real-time to passengers.                                   │
│                                                            │
│ Evidence: Wong (2025, arXiv); MobilityData GTFS Validator  │
│ (https://gtfs-validator. transit-data.net); CUTR GTFS-rt   │
│ Validator (https://github.com/CUTR-us/gtfs-realtime-       │
│ validator).                                                │
│                                                            │
│ Severity: CRITICAL                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-G4: Ground-Truth Evaluation Methodology for Streaming DQ │
│                                                            │
│ Description: No established benchmark for streaming DQ rule  │
│ evaluation. Existing benchmarks (Exathlon, NAB) address     │
│ anomaly DETECTION (different task), not data quality      │
│ rule VALIDATION.                                          │
│                                                            │
│ Existing approaches: Exathlon (VLDB 2021) — Spark cluster  │
│ anomaly detection benchmark; NAB — time-series anomaly      │
│ benchmark. Both NOT for DQ rule evaluation.                │
│                                                            │
│ Why it matters: Without ground-truth methodology,         │
│ precision/recall of DQ rules cannot be measured reliably.   │
│                                                            │
│ Evidence: Exathlon (Doshi-Velez et al., VLDB 2021);       │
│ NAB (Lavin & Ahmad, 2015).                                │
│                                                            │
│ Severity: MAJOR                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-G5: Cross-Record Validation in Streaming Architecture   │
│                                                            │
│ Description: Cross-record (stateful) validation in         │
│ streaming is architecturally complex (state management,     │
│ timeout, watermark). Most frameworks either skip it or     │
│ implement it as future work.                              │
│                                                            │
│ Existing approaches: Stream DaQ — tumbling windows          │
│ (future work); Grab Coban — cross-field (future work);    │
│ Soda Core — limited cross-record.                         │
│                                                            │
│ Why it matters: GPS jump detection, duplicate detection,   │
│ trajectory continuity require cross-record state.          │
│                                                            │
│ Evidence: Stream DaQ (arXiv:2506.06147) — cross-record    │
│ referenced_check listed as future work.                    │
│                                                            │
│ Severity: CRITICAL                                         │
└────────────────────────────────────────────────────────────┘
```

### 2B. Gaps from Transportation-Specific DQ

```
┌────────────────────────────────────────────────────────────┐
│ GAP-T1: No GPS Trajectory Quality Rules Taxonomy            │
│                                                            │
│ Description: No taxonomy of GPS data quality rules for     │
│ transportation exists. What constitutes "valid" GPS for    │
│ a vehicle? Speed bounds? Trajectory continuity?             │
│                                                            │
│ Existing approaches: CETrajAD (SDM 2025) — anomaly        │
│ detection, not quality rules; Wong (2025) — error survey,  │
│ not rule taxonomy.                                         │
│                                                            │
│ Why it matters: A rule taxonomy enables systematic         │
│ validation; without it, DQ coverage is ad hoc.            │
│                                                            │
│ Evidence: Zhu et al. (2012, arXiv) — taxi GPS speed       │
│ inference; Wong (2025, arXiv) — GTFS-RT errors survey.    │
│                                                            │
│ Severity: CRITICAL                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-T2: No Cross-Dataset Transportation DQ Validation       │
│                                                            │
│ Description: Transportation DQ rules are typically          │
│ validated on one dataset. Generalizability to other         │
│ transit systems (different GPS quality, zone structures)   │
│ is unverified.                                            │
│                                                            │
│ Existing approaches: NYC TLC research (multiple Q3+);      │
│ GTFS validator on static feeds (MobilityData). No           │
│ cross-dataset evaluation.                                  │
│                                                            │
│ Why it matters: If rules are tightly coupled to one        │
│ dataset, the framework has limited practical value.       │
│                                                            │
│ Evidence: Multiple NYC TLC Q3+ papers use single dataset.  │
│                                                            │
│ Severity: MAJOR                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-T3: No Streaming GTFS GPS Validation Evidence           │
│                                                            │
│ Description: GTFS-realtime data quality issues are         │
│ documented (Wong 2025, Barbeau 2018) but no streaming      │
│ validation system has been demonstrated on real GTFS feeds. │
│                                                            │
│ Existing approaches: GTFS validators are batch. No         │
│ academic paper evaluates streaming GTFS quality on real     │
│ feeds.                                                    │
│                                                            │
│ Why it matters: Practical evidence of streaming GTFS        │
│ validation is needed to justify the research contribution. │
│                                                            │
│ Evidence: Wong (2025, arXiv) — error survey only;        │
│ Barbeau (2017) — GTFS-RT errors across 78 agencies.       │
│                                                            │
│ Severity: MAJOR                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-T4: No Explainability in Transportation DQ Systems      │
│                                                            │
│ Description: No streaming DQ framework provides             │
│ explainable violation reports for transportation-specific   │
│ rules. Why was a GPS position flagged?                    │
│                                                            │
│ Existing approaches: Stream DaQ — generic violation format; │
│ GTFS Validator — error codes only.                         │
│                                                            │
│ Why it matters: Practitioners need to understand why a     │
│ violation was flagged to take action.                     │
│                                                            │
│ Evidence: Stream DaQ (arXiv:2506.06147) — violation format  │
│ not described in detail.                                   │
│                                                            │
│ Severity: MODERATE                                        │
└────────────────────────────────────────────────────────────┘
```

### 2C. Gaps at the Intersection (Streaming + Transportation)

```
┌────────────────────────────────────────────────────────────┐
│ GAP-I1: No Streaming + Domain-Specific GPS Combination     │
│                                                            │
│ Description: All streaming DQ frameworks are generic. All   │
│ transportation DQ tools are batch. No framework combines   │
│ streaming architecture with domain-specific GPS rules.       │
│                                                            │
│ Existing approaches: Stream DaQ (generic, streaming);      │
│ GTFS Validator (batch, transportation). Gap is their       │
│ intersection.                                             │
│                                                            │
│ Why it matters: Real-time transit operations need          │
│ streaming GPS validation. This gap is the core research   │
│ contribution.                                             │
│                                                            │
│ Evidence: Stream DaQ (arXiv:2506.06147); Wong (2025,      │
│ arXiv); CETrajAD (SDM 2025). Verified: no overlap.         │
│                                                            │
│ Severity: CRITICAL                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-I2: Cross-Record GPS Validation in Streaming            │
│                                                            │
│ Description: Cross-record GPS validation (GPS jump          │
│ detection across consecutive positions) requires stateful  │
│ streaming. This specific combination is absent.             │
│                                                            │
│ Existing approaches: CRS rules exist in theory;           │
│ streaming cross-record validation is future work in        │
│ Stream DaQ.                                               │
│                                                            │
│ Why it matters: GPS jump detection requires comparing      │
│ current position with previous position of the same        │
│ vehicle. This is inherently cross-record.                  │
│                                                            │
│ Evidence: Stream DaQ (arXiv:2506.06147) — future work;     │
│ CETrajAD (SDM 2025) — batch only.                         │
│                                                            │
│ Severity: CRITICAL                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GAP-I3: Hierarchical Context-Aware Fallback for Transport   │
│                                                            │
│ Description: Transportation data has rich context           │
│ (temporal: rush hour/weekend; spatial: urban/suburban;     │
│ operational: bus/train). A hierarchical fallback strategy   │
│ when context cells are sparse is absent.                   │
│                                                            │
│ Existing approaches: Stream DaQ — single-level dynamic      │
│ adaptation; AccelData — ML-based (proprietary).            │
│                                                            │
│ Why it matters: Sparse contexts are common in transit —    │
│ some routes run only on weekends. Without fallback, these   │
│ contexts have no reliable thresholds.                      │
│                                                            │
│ Evidence: AccelData (2024); Scheltinga et al. (EDBT 2025). │
│                                                            │
│ Severity: MODERATE                                        │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Transportation Deep Dive

### 3A. GPS/Trajectory DQ

**What defines "valid" GPS for transportation:**

1. **Speed bounds**: Vehicle physics constrain maximum speed. For buses/trains: hard upper bound of ~200 km/h (electromagnetic). For taxis: urban speed limits + physics. Speed = 0 with GPS movement = impossible.

2. **Trajectory continuity (GPS jump detection)**: Haversine distance between consecutive positions should not exceed `speed_max * time_delta`. Threshold: >100m jump between 30s GTFS updates is suspicious.

3. **Duplicate detection**: Same vehicle, same position, within short time window. Different from trajectory anomaly — duplicates are exact copies.

4. **Coordinate validity**: Latitude [-90, 90], Longitude [-180, 180], and within service area bounds.

5. **Schedule coherence**: GTFS-realtime position should correspond to a valid trip in GTFS static schedule.

**Literature evidence**: Zhu et al. (2012) on taxi GPS status inference using speed and trajectory continuity. Wong (2025) documents invalid coordinates, stale data, and missing trip linkage in GTFS-RT.

### 3B. GTFS DQ

**GTFS data types:**
- **GTFS Static**: Stops, routes, trips, calendars, stop times (scheduled). ZIP/CSV format.
- **GTFS Realtime**: Vehicle positions (protobuf, 30s refresh), trip updates, service alerts. Protocol Buffer format.

**GTFS quality issues (from Wong 2025 and Barbeau 2018):**
- Invalid coordinates (outside service area)
- Missing trip/shape IDs (30% of positions in Wong's survey)
- Stale data (>60s old without update)
- Duplicate vehicle IDs within short windows
- Positions not corresponding to scheduled routes

### 3C. Datasets Available

| Dataset | Accessibility | Academic Precedent | Ground Truth | Notes |
|---------|--------------|-------------------|-------------|-------|
| **NYC TLC Yellow Taxi** | Public, Parquet, monthly | Q3+ (VLDB, SIGMOD, KDD) | NO labeled anomalies | Best academic precedent; StreamDQ injection-based methodology is novel |
| **GTFS Malaysia** | CC BY 4.0, api.data.gov.my | ZERO prior academic use | NO | Novel dataset for research; ~30% documented errors; CRS must be verified |
| **NUMOSIM** | ACM SIGSPATIAL 2024 | Yes (synthetic benchmark) | YES (injected) | Wrong task: AD benchmark, not DQ validation |
| **Porto Taxi** | Kaggle | Yes (multiple papers) | NO | Less academic precedent than NYC TLC |
| **GeoLife** | Microsoft (public) | Yes | PARTIAL | 17,621 trajectories; older (2007-2012) |

---

## 4. Idea Verification (5 Criteria)

### Criterion 1: Novelty & Contribution

**Verdict: MODEST**

| Contribution | Type | Strength | Evidence |
|---|---|---|---|
| GTFS GPS trajectory validation in streaming | New domain application | **Strong** | GAP-I1, GAP-I2 verified — no prior work |
| Three-layer taxonomy for transportation | New domain application | Moderate | Organizing framework, mirrors Deequ's row/aggregate distinction |
| Hierarchical context-aware fallback | New method | Weak | Algorithmic variants exist (Ada-Context DMKD 2025) |
| Ground-truth evaluation framework | New evaluation | Moderate | Follows Exathlon (VLDB 2021) precedent |
| 4D context model | New framework architecture | Weak | Dimensions individually documented; combination not novel |

**Reviewer vulnerability**: "This is Stream DaQ applied to transportation." Counter: GPS trajectory validation (Haversine, speed bounds, GPS jump) is absent from Stream DaQ and all other surveyed frameworks.

### Criterion 2: Technical Feasibility

**Verdict: YES, with critical fixes required**

- Core rules (SYN001-003, SEM001-003, CRS001-003) are ~70% implemented
- Adaptive threshold engine exists and is sound
- Spark Structured Streaming is the correct tech stack choice
- **Critical**: Distributed pipeline has semantic rule gap — SEM rules do not run in `run_distributed()`
- **Critical**: Evaluation module does not exist — all metrics depend on this
- **Critical**: GTFS anomaly injection is missing in `gtfs_live.py`
- **High risk**: GTFS Malaysia coordinate reference system (CRS) must be verified before Haversine calculations

**Timeline estimate**: 24-28 weeks (not 40 weeks as currently planned). The buffer in weeks 25-40 is appropriate.

### Criterion 3: Evaluation Feasibility

**Verdict: PARTIAL — methodology is sound, implementation is incomplete**

- **Methodology**: Synthetic anomaly injection + ground-truth correlation + bootstrap CI is rigorous and follows Exathlon (VLDB 2021) precedent. Sound.
- **Current baseline**: 22.9% precision measured on syntactic rules (LocalPipeline, NYC TLC). Low but measured.
- **CRS003 recall**: Unmeasurable due to injection bug (B2). Fixed for NYC TLC but GTFS injection missing.
- **No ablation study**: Cannot justify three-layer taxonomy value.
- **No competing framework comparison**: No head-to-head with Stream DaQ on identical data.
- **Threat**: Synthetic anomalies may not reflect real-world patterns. Acceptable limitation for thesis.

### Criterion 4: Scope Realism

**Verdict: OVERSCOPED — trade-offs needed**

| Phase | Must Have | Nice to Have | Cut if Behind |
|---|---|---|---|
| Core | SYN/SEM/CRS rules, NYC TLC eval | GTFS Malaysia (RQ3) | Weather context (4D -> 3D) |
| Evaluation | Precision/recall/F1 + CI | Ablation study | dbt/Soda comparison |
| GTFS | CRS001 (speed), CRS002 (GPS jump), CRS003 (duplicate) | Full RQ3 evaluation | Distributed mode semantic rules |

**Critical scope mismatch**: CRS001/CRS002 (GPS spoofing) only run on GTFS vehicles. NYC TLC — the main evaluation dataset — receives zero cross-record GPS validation. This must be honestly disclosed or fixed.

### Criterion 5: Thesis Grade Realism

**Verdict: B+ to A- (conference/workshop), B to B+ (journal)**

**Key risks to grade:**

| Risk | Impact | Likelihood |
|---|---|---|
| Context-aware precision improvement marginal (<5%) | RQ1 fails — drops to B | HIGH |
| Evaluation module not built in time | No metrics — cannot submit | HIGH |
| CRS003 recall remains unmeasurable | CRS layer evaluation incomplete | MEDIUM |
| Single-dataset RQ1/RQ2 | Weak generalization claim | MEDIUM |
| Fabricated claims in final document | Academic fraud — destroys credibility | MEDIUM (already audited) |
| GTFS CRS mismatch (non-WGS84) | RQ3 fails | MEDIUM |

**What pushes to A**: Large, statistically significant context-aware precision improvement (22.9% -> 40%+ with p<0.01); GTFS GPS validation on real errors; ablation study shows CRS layer value.

**What causes B**: Only baseline measured; CRS003 still broken; no ablation; weak GTFS results.

---

## 5. Proposed Framework

```
┌────────────────────────────────────────────────────────────┐
│ FRAMEWORK NAME: StreamDQ-Transport                          │
│ DOMAIN: Transportation — GPS Trajectory + GTFS Realtime     │
│                                                            │
│ CORE CONTRIBUTION:                                          │
│ A streaming data quality monitoring framework that           │
│ implements domain-specific GPS trajectory validation        │
│ (Haversine speed bounds, GPS jump detection, duplicate     │
│ detection) using a three-layer rule taxonomy (syntactic,   │
│ semantic, cross-record) with hierarchical context-aware     │
│ adaptive thresholds, evaluated on NYC taxi and GTFS        │
│ Malaysia datasets.                                         │
│                                                            │
│ TARGET USER:                                               │
│ Transit agencies, transportation data engineers,            │
│ researchers studying public transit data quality            │
│                                                            │
│ KEY DIFFERENTIATOR FROM EXISTING WORK:                     │
│ - ONLY framework combining streaming architecture with      │
│   domain-specific GPS/trajectory validation rules          │
│ - ONLY framework with cross-record GPS stateful rules      │
│   for streaming transportation data                        │
│ - First evaluation of streaming GTFS-realtime quality      │
│   on real public transit feeds                             │
│                                                            │
│ ARCHITECTURE OVERVIEW:                                     │
│ - Streaming: Apache Spark Structured Streaming              │
│ - Message bus: Apache Kafka                                │
│ - Rules: SYN (single-record) + SEM (statistical) +        │
│   CRS (cross-record stateful)                             │
│ - Context: Temporal x Spatial x Operational x External    │
│ - Storage: SQLite (local) / PostgreSQL (distributed)       │
│ - Monitoring: Prometheus + Grafana                        │
│                                                            │
│ SCOPE:                                                     │
│ IN: GPS speed bounds, GPS jump detection, trajectory       │
│     continuity, duplicate detection, coordinate validity,  │
│     adaptive thresholds, ground-truth evaluation            │
│ OUT: ML anomaly detection, drift detection, production     │
│      alerting, distributed adaptive thresholds, Flink      │
│                                                            │
│ EXPECTED CONTRIBUTION TYPE:                                │
│ [X] New framework (full system contribution)              │
│ [ ] New method (algorithm/approach contribution)           │
│ [ ] New domain application (existing method -> new domain)  │
│ [X] New evaluation (methodology contribution)              │
│                                                            │
│ GRADE PROJECTION: B+ to A-                                 │
│ Honesty note: Contribution is primarily domain            │
│ application and evaluation methodology, not novel          │
│ algorithms. Reviewers at top venues (VLDB, SIGMOD)        │
│ may classify this as incremental systems work.             │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Research Questions

### RQ1: Context-Aware vs. Static Thresholds

*See Section 6 of the RQ draft document.*

```
┌────────────────────────────────────────────────────────────┐
│ RQ1: Does hierarchical context-aware threshold adaptation   │
│      achieve higher precision than static thresholds for    │
│      streaming transportation data quality detection?        │
│                                                            │
│ Motivation: Static thresholds produce high false-positive   │
│ rates during atypical conditions (rush hour, weekends).    │
│ Context-aware thresholds could reduce these false alarms.  │
│                                                            │
│ From Gap: GAP-G2 (adaptive thresholds unvalidated)         │
│                                                            │
│ Literature Support:                                       │
│ → Stream DaQ (arXiv:2506.06147, 2025) [Q3+]             │
│ → Martin et al. (PVLDB 2025) — 95%+ false DC rate       │
│ → METER (PVLDB 2024) — concept drift adaptation          │
│                                                            │
│ Method:                                                    │
│ → Ablation: SYN+SEM with static vs. context-aware         │
│ → Dataset: NYC TLC Yellow Taxi (2024), 3M records         │
│ → Metrics: precision, recall, F1 per rule, 95% bootstrap  │
│ → How to measure: Same injection seed, correlated output  │
│                                                            │
│ Feasibility: MEDIUM — engine exists, evaluation missing   │
│                                                            │
│ Threats:                                                   │
│ → Internal: Synthetic anomalies may not reflect real       │
│ → External: NYC TLC may not generalize to other transit   │
│                                                            │
│ Expected outcome: Tier 2 (estimated): context-aware       │
│ precision >= 15% higher than static for rush-hour          │
│ → Can fail: If distributions are uniform, gain < 5%       │
└────────────────────────────────────────────────────────────┘
```

### RQ2: Hierarchical Fallback Quality

```
┌────────────────────────────────────────────────────────────┐
│ RQ2: How does hierarchical fallback quality degrade as    │
│      temporal-spatial context cells become sparser?        │
│                                                            │
│ From Gap: GAP-G2 (sparse context handling)                │
│                                                            │
│ Literature Support:                                       │
│ → Scheltinga et al. (EDBT 2025) — temporally dependent   │
│   data quality errors                                     │
│ → AccelData (2024) — ML-based context handling           │
│                                                            │
│ Method:                                                    │
│ → Partition NYC TLC into 5 sparsity tiers (dense to cold) │
│ → Evaluate SEM001/SEM003 across 5-level fallback          │
│ → Metrics: F1 degradation curve per tier                 │
│                                                            │
│ Feasibility: MEDIUM — fallback exists, harness missing    │
└────────────────────────────────────────────────────────────┘
```

### RQ3: Cross-Domain Generalizability

```
┌────────────────────────────────────────────────────────────┐
│ RQ3: Can StreamDQ's GPS trajectory rules generalize from  │
│      NYC taxi to GTFS Malaysia realtime without retuning?  │
│                                                            │
│ From Gap: GAP-I1 (no streaming + domain GPS combination)   │
│                                                            │
│ Literature Support:                                       │
│ → Wong (2025, arXiv) — 30% GTFS-RT error rate           │
│ → Zhu et al. (2012) — taxi GPS speed inference           │
│                                                            │
│ Method:                                                    │
│ → Apply CRS001/CRS002 to GTFS Malaysia WITHOUT retuning  │
│ → Pre-requisite: CRS pre-investigation (coordinate CRS)   │
│ → Dataset: GTFS Malaysia via api.data.gov.my             │
│ → Metrics: Detection rate, manual spot-check validation   │
│                                                            │
│ Feasibility: MEDIUM-HIGH — API accessible, injection missing│
│                                                            │
│ Threats:                                                   │
│ → Internal: GTFS CRS injection not implemented           │
│ → External: Non-WGS84 CRS would invalidate Haversine      │
└────────────────────────────────────────────────────────────┘
```

### RQ4: Three-Layer Taxonomy Justification

```
┌────────────────────────────────────────────────────────────┐
│ RQ4: Does the three-layer taxonomy (SYN/SEM/CRS) provide  │
│      measurably better anomaly coverage than SYN-only?      │
│                                                            │
│ From Gap: GAP-I2 (cross-record GPS in streaming)           │
│                                                            │
│ Literature Support:                                       │
│ → Stream DaQ (arXiv:2506.06147) — layered approach       │
│ → Deequ (VLDB 2018) — row/aggregate distinction          │
│                                                            │
│ Method:                                                    │
│ → Three-arm ablation: SYN-only vs. SYN+SEM vs. full     │
│ → Dataset: NYC TLC Yellow Taxi                           │
│ → Metrics: Incremental F1 gain per layer, latency cost  │
│                                                            │
│ Feasibility: HIGH (impl. cost) — requires evaluation module│
│                                                            │
│ Threats:                                                   │
│ → Internal: CRS-only anomalies (GPS jump, duplicate) may   │
│   be rare in injection set, masking CRS contribution      │
│ → Can fail: If CRS recall is low (CRS003 unmeasurable)    │
└────────────────────────────────────────────────────────────┘
```

---

## 7. Feasibility Assessment

| Dimension | Status | Notes |
|---|---|---|
| Technical (streaming pipeline) | PARTIAL | Core rules done; semantic rules gap in distributed mode; evaluation module missing |
| Technical (GPS rules) | DONE | Haversine correct; CRS rules working for GTFS |
| Technical (adaptive thresholds) | DONE | Rolling P10/P90 + hierarchical fallback implemented |
| Evaluation (methodology) | SOUND | Injection + correlation + bootstrap CI; follows Exathlon precedent |
| Evaluation (implementation) | MISSING | Evaluation module does not exist; must be built |
| Dataset (NYC TLC) | ACCESSIBLE | Public, Q3+ precedent, no labeled anomalies |
| Dataset (GTFS Malaysia) | ACCESSIBLE with risk | CRS pre-investigation required; injection missing |
| Timeline | AT RISK | 24-28 weeks realistic; 40 weeks optimistic |
| Novelty | MODEST | Domain application + evaluation methodology, not novel algorithms |

---

## 8. Scope Boundaries

### IN SCOPE
- SYN001-003: null check, negative fare, out-of-range PULocationID
- SEM001-003: fare range, trip duration, passenger count distribution
- CRS001-003: impossible speed, GPS jump, duplicate detection
- GTFS GPS validation (CRS001-003) on GTFS Malaysia
- NYC TLC evaluation with synthetic injection
- Ground-truth evaluation with precision/recall/F1 + 95% bootstrap CI
- Ablation study (SYN-only vs. SYN+SEM vs. SYN+SEM+CRS)
- Hierarchical context-aware adaptive thresholds (3D: temporal + spatial + operational)
- Comparison with at least one competing framework (Great Expectations or Soda Core)
- LocalPipeline and SparkPipeline (foreachBatch mode)

### OUT OF SCOPE (Documented)
- ML-based anomaly detection
- Drift detection (`streamdq/rules/drift.py` exists but not integrated)
- Distributed adaptive thresholds
- Flink pipeline
- Production alerting infrastructure
- Labeled GTFS benchmark dataset
- Full distributed Spark semantic rule evaluation
- Weather/external context (4D -> 3D scope reduction)

### NICE-TO-HAVE (If Time Permits)
- Flink pipeline comparison
- dbt and Soda Core comparisons
- GUI dashboard
- Multi-city GTFS evaluation (beyond Malaysia)

---

## 9. Peer Review Summary

### Literature Reviewer
- **Verdict**: NEEDS WORK
- **Strengths**: Comprehensive 19-framework survey; citation discovery thorough for GPS/trajectory AD; honest acknowledgment of zero GTFS Malaysia publications
- **Critical Issues**: Fabricated precision/speed claims throughout documents; CRS002 evaluation only on GTFS, NOT on NYC TLC; "BART tool" fabricated

### Academic Writer
- **Verdict**: NEEDS WORK
- **Strengths**: Appropriately modest positioning; exemplary Tier 2 labeling discipline; clear OUT OF SCOPE articulation
- **Critical Issues**: Introduction and experiments drafts are empty placeholders; RQ1 precision improvement lacks statistical justification; cold-start claim not experimentally tested

### Data Engineer
- **Verdict**: NEEDS WORK
- **Strengths**: Syntactic rule edge case handling exemplary; cross-record state isolation correct; Spark streaming choice is right trade-off
- **Critical Issues**: Spark distributed pipeline latency instrumentation incomplete (B6); evaluation module missing; external/weather context entirely unimplemented

### Statistician
- **Verdict**: NEEDS WORK
- **Strengths**: Bootstrap CI requirement correct; Wilcoxon + Cohen's d appropriate; injection methodology well-designed
- **Critical Issues**: Bootstrap uses 100 iterations, not 1,000; CRS003 recall unmeasurable on GTFS; 22.9% baseline is SYN-layer only, not framework baseline

### Infrastructure/DevOps
- **Verdict**: APPROVED (with conditions)
- **Strengths**: Reproducibility well-supported; Python-first stack maintainable; known blockers documented systematically
- **Critical Issues**: GTFS Malaysia CRS must be verified before Haversine; GTFS Malaysia API stability unverified; contingency plan needed

---

## 10. Skill Usage Tracker

| Skill | Used For | Output |
|-------|----------|--------|
| @.cursor/skills/01-academic-writing | Contribution framing, peer review simulation, claim classification | Scientific writing principles applied; Tier 2/3 labeling enforced; peer review structured |
| @.cursor/skills/02-literature-research | General streaming DQ landscape, transportation DQ frameworks, datasets | 19 frameworks surveyed; 18 verifiable citations; gap analysis structured |
| @.cursor/skills/03-data-statistics | Evaluation design, bootstrap CI methodology, statistical threats | Bootstrap CI 1,000 iterations required; Wilcoxon + Cohen's d for RQ1; ablation study design |
| @.cursor/skills/04-data-engineering | Technical feasibility, architecture review, streaming pipeline assessment | 3-option analysis for distributed semantic rules; CRS pre-investigation requirements |
| @.cursor/skills/05-research-analysis | Gap identification, idea verification, threat analysis | 12-gap structured analysis; 5-criteria assessment; risk matrix |
| @.cursor/skills/06-infrastructure-devops | Reproducibility, tech stack evaluation, deployment feasibility | Reproducibility checklist; API stability concerns; contingency planning |
| @.cursor/skills/07-developer-experience | — | Not explicitly triggered in Phase 0 |

---

## 11. Final Recommendation

```
┌────────────────────────────────────────────────────────────┐
│ RECOMMENDATION: MODIFY AND PROCEED                         │
│                                                            │
│ Rationale: The idea has a genuine, verified contribution   │
│ (streaming + domain-specific GPS rules for transportation). │
│ The gap is real and documented across multiple Q3+/B+      │
│ sources. The technical approach is sound. The primary      │
│ risks are execution (building the evaluation module) and  │
│ scope management (preventing drift into unachievable       │
│ ambitions). The thesis is feasible for a B+ paper.        │
│                                                            │
│ Grade Projection: B+ to A- (conference/workshop)           │
│                                                            │
│ Three CRITICAL actions before proceeding:                   │
│ 1. DELETE all fabricated claims from every document       │
│ 2. BUILD the evaluation module (highest priority)         │
│ 3. RESOLVE CRS002 scope honestly (extend to NYC TLC or    │
│    honestly scope as GTFS-only in all contributions)       │
│                                                            │
│ Top strengths to preserve:                                  │
│ 1. Honest positioning ("research and education platform")   │
│ 2. Tier 2 labeling discipline for all unbenchmarked       │
│    estimates                                               │
│ 3. Comprehensive gap analysis (GAP-I1 is genuinely novel)  │
│                                                            │
│ Top risks that could cause failure:                        │
│ 1. Evaluation module not built — no metrics to publish    │
│ 2. Context-aware improvement marginal — RQ1 fails         │
│ 3. GTFS Malaysia CRS mismatch — RQ3 fails                 │
│                                                            │
│ Next Steps (in priority order):                            │
│ 1. Sweep all documents for fabricated claims; replace      │
│    with verified numbers only                              │
│ 2. Build streamdq/evaluation/ module: ground-truth        │
│    tracker + correlation + metric computation + bootstrap CI │
│ 3. Fix n_bootstrap = 100 -> 1000 in adaptive.py          │
│ 4. Verify GTFS Malaysia coordinate reference system        │
│ 5. Implement GTFS anomaly injection in gtfs_live.py        │
│ 6. Decide on distributed semantic rules (Option A/B/C)   │
│ 7. Run ablation study (SYN-only vs. SYN+SEM vs. full)    │
│ 8. Run full evaluation suite with bootstrap CI            │
│ 9. Draft experiments section with actual measured numbers  │
│ 10. Proceed to paper writing                              │
└────────────────────────────────────────────────────────────┘
```

---

## Appendix: Key References

### Highest-Impact Academic References

1. **Stream DaQ**: Papastergios & Gounaris. "Stream DaQ: A Streaming Data Quality Monitoring Framework." arXiv:2506.06147, 2025. [Q3+]
2. **Deequ**: Schelter et al. "Automated Test-Database Generation." VLDB 2018. doi:10.14778/3275366.3275572. [Q1/VLDB]
3. **False DCs**: Martin et al. "False Data Constraints: The Silent Danger in ML Pipelines." PVLDB 2025. doi:10.14778/3748191.3748209. [Q1/PVLDB]
4. **METER**: Koner et al. "METER: Model Lifecycle Tracking with Event-driven Reactive Services." PVLDB 2024. doi:10.14778/3684126. [Q1/PVLDB]
5. **AutoDQM**: Brinkerhoff et al. "AutoDQM: Automated Data Quality Management." arXiv:2501.13789, 2025. [Q3+]
6. **CETrajAD**: Liu et al. "CETrajAD: Context-Enhanced Trajectory Anomaly Detection." SDM 2025. [Q2]
7. **GTFS-RT Quality**: Wong et al. "Data Quality of GTFS-Realtime Public Transit Feeds." arXiv, 2025. [Q3+]
8. **Exathlon**: Das et al. "Exathlon: A Benchmark for Explainable Anomaly Detection over Streaming Analytics." VLDB 2021. doi:10.14778/3476311.3476318. [Q1/VLDB]
9. **NAB**: Lavin & Ahmad. "Evaluating Real-Time Anomaly Detection Algorithms." Proc. KDD, 2015. [Q1/KDD]
10. **iBAT**: Ge et al. "iBAT: Detecting Anomalous Taxi Trajectories from GPS Traces." UbiComp 2011. doi:10.1145/2030112. [Q2/UbiComp]

### Key Open-Source Tools Referenced

1. Great Expectations: https://github.com/great-expectations/great_expectations
2. Soda Core: https://github.com/sodadata/soda-core
3. dbt: https://github.com/dbt-labs/dbt-core
4. GTFS Validator (MobilityData): https://gtfs-validator.transit-data.net
5. GTFS-rt Validator (CUTR-USF): https://github.com/CUTR-us/gtfs-realtime-validator
6. NYC TLC Data: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
7. GTFS Malaysia: https://data.gov.my (api.data.gov.my/gtfs-realtime)
