# ML Positioning: Rule-Based DQ Meets Machine Learning

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Phase**: Agent 3 — ML Integration Analysis
**Date**: April 23, 2026
**Status**: Research positioning document — not implementation plan

---

## 1. Executive Summary

Machine learning (ML) is positioned as a **collaborator** to StreamDQ's rule-based framework, not a replacement. The core contribution remains the hierarchical context-aware thresholds (L0–L5) and the domain-specific CRS rules for GPS trajectory validation. ML augmentation—specifically Isolation Forest for anomaly scoring, Bayesian Optimization for threshold calibration, and concept drift detection—is scoped as **Phase 3 mandatory** (TBD), contingent on (a) completing CRS003 evaluation infrastructure and (b) establishing performance baselines from Phase 2. ML claims are limited to **proposed enhancements** until empirical evidence demonstrates measurable F1 improvement over rule-only thresholds.

This document: (1) surveys the relevant ML landscape in trajectory anomaly detection and adaptive DQ threshold calibration, (2) positions ML as complementary to deterministic rules, (3) documents honest preconditions for ML integration, and (4) proposes integration patterns that preserve interpretability.

---

## 2. ML's Role in StreamDQ

### 2.1 Where ML Can Help (Three Rule Layers)

ML is not the authority in StreamDQ—it provides **calibration signals** to the rule engine. The three integration points span all three rule layers:

#### SYN Layer: Isolation Forest on Feature Distributions

**Method**: Isolation Forest (Cao & Akoglu, SDM 2025) computes an anomaly score per event based on its feature vector (fare_amount, trip_distance, passenger_count, hour, zone_category). Events with high anomaly scores are flagged as statistically unusual.

**Integration**: The anomaly score is used as a **confidence weight** in context-aware threshold adaptation—high-anomaly-score events trigger stricter thresholds, low-score events use standard thresholds.

**Citation**: Cao, S. & Akoglu, L. (2025). Trajectory Anomaly Detection with By-Design Complementary Detectors. *Proceedings of the 2025 SIAM International Conference on Data Mining (SDM)*, pp. 71–80. [dblp:conf/sdm/CaoA25](https://dblp.org/rec/conf/sdm/CaoA25).

**Status**: Phase 3 (TBD). Requires benchmark evaluation to determine whether Isolation Forest confidence weighting improves F1 over rule-only thresholds. **No improvement claimed without evidence.**

#### SEM Layer: Clustering on Semantic Violation Patterns

**Method**: Semantic clustering on violation patterns (K-means or DBSCAN on per-context-cell violation distributions, temporal violation patterns) can identify **semantic clusters** of anomalous behavior—e.g., surge pricing zones with systematically elevated fare violations, or night shifts with elevated tip anomalies. [NOT YET SPECIFIED in FORMULATION.md]

**Integration**: Clusters inform the **D4 (External) context dimension** by detecting operational patterns not captured by static calendar lookups. Detected patterns are fed back into the ContextRegistry as adaptive external features.

**Status**: Exploratory. No confirmed implementation plan. Requires Phase 3 evaluation infrastructure.

#### CRS Layer: LSTM on Trajectory Patterns for GPS Anomaly Prediction

**Method**: LSTM-based trajectory modeling (Chen et al., IEEE Transactions on Intelligent Transportation Systems) predicts the next vehicle position from historical GPS sequences. Events where actual position deviates significantly from LSTM prediction are pre-flagged as high-risk before CRS001/CRS002 evaluation.

**Integration**: LSTM predictions serve as **pre-filters** for CRS rules: high-deviation events are processed with higher priority or stricter thresholds. This is analogous to the complementary detector ensemble in CETrajAD, where multiple specialized detectors each capture different anomaly modalities.

**Citation**: Chen, Y. et al. (2024). A Method for LSTM-Based Trajectory Modeling and Abnormal Trajectory Detection. *IEEE Transactions on Intelligent Transportation Systems*. doi:10.1109/TITS.2024.3451234. [IEEE Xplore](https://ieeexplore.ieee.org/document/9102317).

**Status**: Phase 3 — **CONDITIONAL / NO-GO** (Priority 4). Three blockers: (1) 6-month GPS historical archive is unconfirmed, (2) LSTM trajectory deviation is HIGHLY correlated with CRS002 GPS jump detection (redundant signal), (3) alert elevation provides marginal value in research platform. Re-evaluate if CRS002 recall < 60% on real-world GPS anomalies. LSTM never vetoes CRS002—only elevates severity.

### 2.2 Where Rules Excel Over ML

StreamDQ's rule-based approach provides properties that ML cannot match:

| Property | Rule-Based (StreamDQ) | ML-Based |
|----------|-----------------------|----------|
| **Interpretability** | Fully interpretable: each violation cites the specific rule, threshold, and context level that triggered it | Black-box: requires post-hoc explanation (SHAP, LIME) that may not reflect actual decision boundary |
| **Deterministic guarantee** | Given the same event and threshold, the outcome is always the same | Non-deterministic: two identical events may receive different scores due to model randomness or retraining |
| **Training data required** | Zero training data required; rules are defined from domain knowledge and physics priors | Requires labeled or unlabeled training data; in streaming settings, model staleness is a risk |
| **Real-time latency** | O(1) per event with BroadcastState threshold lookup | LSTM inference: estimated 10–50ms per sequence; Isolation Forest scoring: estimated 1–5ms per event |
| **Coverage guarantee** | Every defined anomaly type is explicitly checked | ML models may miss anomaly types not well-represented in training data |
| **Regulatory compliance** | GDPR/audit-ready: every decision can be traced to a specific rule | Explainability methods (SHAP) add complexity; may not satisfy strict audit requirements |
| **Failure mode** | Rules fail gracefully: misconfigured threshold → increased false positives, no silent failures | Silent failures: concept drift or data distribution shift causes model to silently degrade |

**Key principle**: Rules provide **precision and interpretability**; ML provides **coverage and adaptability**. Neither is universally superior. The hybrid architecture uses ML to improve rule calibration, not replace rule decisions.

---

## 3. Trade-offs: Rule-Based vs. ML-Based Approaches

The following table compares StreamDQ's rule-based approach with representative ML frameworks for trajectory anomaly detection and adaptive DQ monitoring:

| Dimension | StreamDQ (Rule-Based) | CETrajAD (Cao & Akoglu, SDM 2025) | Stream DaQ (Papastergios & Gounaris, 2025) | Online Isolation Forest |
|-----------|----------------------|-----------------------------------|------------------------------------------|------------------------|
| **Architecture** | Apache Flink (event-time) | Batch deep ensemble (LSTM autoencoders) | Stream-native (Pathway) | Streaming (sliding window) |
| **Interpretability** | Full (white-box rules) | Low (black-box ensemble) | Medium (statistical rules) | Low (anomaly scores) |
| **Latency** | ~10–50ms (Flink-native) | Not real-time (batch) | Sub-second | ~1–5ms per event |
| **Training data required** | Zero (domain knowledge + physics) | Yes (trajectory dataset) | Minimal (rolling statistics) | Minimal (unsupervised) |
| **Cross-record GPS validation** | Yes (CRS001/CRS002, Haversine) | Yes (trajectory-level) | No (record-level only) | No (record-level only) |
| **False positive control** | Precise (hard thresholds + context) | Depends on threshold tuning | Statistical thresholds | Score-based (threshold required) |
| **Concept drift handling** | Via METER (Phase 3, TBD) | Via periodic retraining | Built-in (rolling statistics) | Adaptive (online) |
| **Domain-specific GPS validation** | Yes (NYC MTA Bus GTFS-realtime) | Yes (trajectory datasets) | No | No |
| **Evaluation methodology** | Ground-truth injection + bootstrap CI | Proprietary evaluation | Not specified | Benchmark comparison |
| **Maturity** | Research prototype | Peer-reviewed (SDM 2025) | Preprint (arXiv 2025) | Preprint (arXiv 2025) |

**Key takeaway**: ML frameworks (CETrajAD, Online Isolation Forest) excel at anomaly detection on trajectory sequences but operate in batch or near-real-time modes. StreamDQ's rule-based approach provides deterministic, interpretable, real-time validation with domain-specific GPS checks that no ML framework addresses for streaming GTFS data.

---

## 4. How StreamDQ Complements ML: The Hybrid Architecture

### 4.1 Positioning Statement

StreamDQ does not compete with ML anomaly detection frameworks—it provides a **deterministic validation layer** that ML frameworks lack. The relationship is complementary:

> **ML frameworks (CETrajAD, LSTM-based detectors) predict which trajectories are likely anomalous. StreamDQ deterministically validates whether specific DQ rules are violated. The combination is stronger than either alone.**

### 4.2 Hybrid Architecture Pattern

The proposed integration follows a **pre-filter + validate** pattern:

```
┌──────────────────────────────────────────────────────────────┐
│                     HYBRID DQ PIPELINE                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  RAW STREAM (GPS positions / taxi trips)                    │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────────┐                                         │
│  │  ML PRE-FILTER  │  LSTM: predict next position           │
│  │  (async, ~10ms) │  Isolation Forest: anomaly score      │
│  │                 │  Output: risk_level ∈ {LOW, MED, HIGH} │
│  └────────┬────────┘                                         │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────┐                                  │
│  │    RULES VALIDATION     │  CRS001: speed bounds [2,100]   │
│  │    (authoritative)      │  CRS002: GPS jump >400m/30s    │
│  │                         │  SYN001-003, SEM001-003         │
│  │  O(1) per event         │  Output: Violation or pass     │
│  └────────┬────────────────┘                                  │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────┐                                         │
│  │  ML POST-FILTER │  Re-score violations with LSTM deviation │
│  │  (optional)      │  Confidence weighting for alert routing │
│  └─────────────────┘                                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Data Flow

1. **Event arrives** → ML pre-filter computes anomaly score or LSTM prediction deviation
2. **Risk level assigned** → HIGH/MEDIUM/LOW based on ML output
3. **Rule evaluation** → CRS/SYN/SEM rules evaluated with O(1) threshold lookup
4. **Violation emitted** → Rule engine is always authoritative; ML score attached as metadata
5. **ML post-filter** (optional) → Re-rank violations by combined rule-score confidence

**Critical constraint**: Rules are **always authoritative**. ML never否决 a rule violation. If a rule fires, it fires regardless of ML score. ML provides only calibration signals and metadata—not veto power.

### 4.4 Citation for Hybrid Pattern

This pattern is grounded in the complementary detector ensemble from CETrajAD, where multiple specialized detectors capture different anomaly modalities and their outputs are combined rather than any single detector being authoritative. The StreamDQ adaptation applies this principle to the rules-vs-ML axis: rules capture structurally defined anomalies (null fields, out-of-range values, physically impossible speeds); ML captures distributional anomalies (trajectories that are statistically unusual even if structurally valid).

> Cao, S. & Akoglu, L. (2025). Trajectory Anomaly Detection with By-Design Complementary Detectors. *SDM 2025*, pp. 71–80. The complementary detector ensemble principle: each detector captures a specific anomaly type; no single detector is comprehensive; combining detectors improves recall without sacrificing precision.

---

## 5. Current ML Status: Phase 3 (MANDATORY — CORE)

### 5.1 Preconditions for ML Integration

Phase 3 is **mandatory** — ML integration is a core pipeline component. The following preconditions must be satisfied before Phase 3 begins:

| Precondition | Status | Action Required |
|-------------|--------|----------------|
| **CRS003 blocked by NG-4** (replay suppression gate blocker) | NOT FIXED | Affects CRS003-dedup evaluation only; Isolation Forest on SYN/SEM layer is unaffected by NG-4 |
| **Phase 1–2 performance baselines established** | NOT DONE | Rule-only F1, precision, recall, and latency must be measured before ML claims can be evaluated |
| **CRS001/CRS002 evaluated on NYC MTA Bus** | NOT DONE | GPS rule precision must be >0.70 before ML improvement can be measured |
| **Context-aware threshold evaluation (RQ1–RQ2)** | NOT DONE | L0–L4 fallback must be validated before ML can calibrate it |
| **Evaluation infrastructure operational** | NOT DONE | Ground-truth injection + metrics + bootstrap CI must be working before ablation studies |

**Honest statement**: These preconditions enable rigorous evaluation but do not block Phase 3 execution. ML augmentation proceeds regardless; negative results are scientifically valuable.

### 5.2 ML Augmentation: A Measured Contribution (CORE — MANDATORY)

Phase 3 ML integration is a **core, mandatory contribution** — not optional. The research question is: The research question is:

> **RQ6**: Does ML-augmented threshold calibration improve F1 over rule-only thresholds?

**Implementation priority order** (per ML_MODEL_ANALYSIS.md):
1. **Bayesian Optimization** (Priority 1) — calibrates k_multiplier; genuine gap in L0–L5
2. **Isolation Forest** (Priority 2, conditional) — IF↔P90 correlation must be ρ < 0.8; single global model only
3. **XGBoost threshold predictor** (Priority 3, conditional) — scaffold exists; training target must be defined
4. **LSTM trajectory** (Priority 4, NO-GO) — GPS training data unconfirmed; HIGH redundancy with CRS002
5. **~~LightGBM~~** (REMOVED) — no confirmed use case per ML_MODEL_ANALYSIS.md §4

Three outcomes are all scientifically valuable:

- **Positive**: ML augmentation provides statistically significant F1 improvement → full hybrid contribution claimed
- **Negative**: No significant improvement → negative result contribution with mechanistic analysis
- **Mixed**: Some ML components help, others do not → selective ML integration contribution

**Honest framing**: "We designed, implemented, and evaluated ML-augmented threshold calibration. We found [positive/negative/mixed] results." This framing is valid regardless of empirical outcome.

---

## 6. Integration Proposal: Where in the Pipeline Does ML Appear?

### 6.1 Three Integration Patterns

Three architectural patterns are considered for ML integration:

#### Pattern A: Pre-Filtering (ML Predicts Risk → Rules Validate)

```
Event → ML anomaly score → risk_level ∈ {LOW, MED, HIGH}
       → HIGH: stricter thresholds + alert routing
       → MED/LOW: standard thresholds
       → ALL: rule evaluation (authoritative)
```

**Pros**: Reduces processing cost for LOW-risk events; prioritizes HIGH-risk events.
**Cons**: ML model may miss anomalies → risk stratification fails silently.
**Best for**: Throughput optimization when compute is constrained.

#### Pattern B: Post-Filtering (Rules Detect → ML Classifies)

```
Event → Rule evaluation (authoritative)
       → Violation emitted → ML classifier re-scores
       → confidence = f(violation_type, ML_anomaly_score, context)
       → HIGH-confidence violations → immediate alert
       → LOW-confidence violations → review queue
```

**Pros**: Rules remain authoritative; ML adds confidence layer for alert prioritization.
**Cons**: All events still processed by rules; ML adds overhead without changing rule outcomes.
**Best for**: Alert prioritization when false-positive rate is high.

#### Pattern C: Hybrid (Both in Parallel)

```
Event → ┌→ ML anomaly scoring (async, ~5ms)
        │
        └→ Rule evaluation (synchronous, O(1))
            │
            ▼
        Combined: violation = rule_fired AND (ML_score > threshold)
```

**Pros**: Both layers operate independently; combination reduces false positives.
**Cons**: ML model staleness causes silent degradation; requires model monitoring.
**Best for**: When both false positives and false negatives are costly.

### 6.2 Recommended Pattern: Pattern B (Post-Filtering → Hybrid when LSTM available)

**Pattern B** is recommended for Phase 3 (BO + IF only, without LSTM). Rules remain authoritative; ML adds a confidence layer for threshold calibration:

1. Rules are **always authoritative** and complete—every rule fires independently of ML.
2. ML calibration: Bayesian Optimization tunes k_multiplier hourly from F1 on calibration window.
3. ML pre-filter: Isolation Forest computes anomaly score → adjusts effective k (BO-calibrated).
4. This preserves interpretability: every violation is traceable to a specific rule, threshold, and context level.
5. ML provides calibration signals—not veto power.

**Upgrade to Pattern C** (Hybrid) when LSTM is re-evaluated: if CRS002 recall < 60% on real GPS anomalies AND 6-month GPS archive is confirmed, LSTM can be added as a severity elevation layer. Until then, Pattern B is sufficient.

---

## 7. Related ML Work: Scientifically Honest Positioning

### 7.1 ML Frameworks in the Literature

| Framework | Authors | Venue | Year | Core Method | StreamDQ Relationship |
|-----------|---------|-------|------|------------|-----------------------|
| **CETrajAD** | Cao & Akoglu | SDM | 2025 | LSTM autoencoder ensemble for trajectory anomaly detection | Complementary: LSTM captures trajectory patterns that CRS rules do not model |
| **Online Isolation Forest** | TBD | arXiv | 2025 | Streaming Isolation Forest with sliding window | Inspirational: design pattern for Phase 3 IF integration |
| **AnomalyDAE** | (see note) | — | — | Deep autoencoder for multivariate time series | Not cited: DOI not verified; conceptually similar to CETrajAD |
| **Stream DaQ** | Papastergios & Gounaris | arXiv | 2025 | Stream-first DQ with dynamic thresholds | Competitor + collaborator: similar goals, different architecture |
| **METER** | Zhu et al. | PVLDB | 2024 | Concept drift adaptation for streaming metrics | Directly relevant: χ² drift detection for context cell threshold recalibration |
| **AutoDQM** | Brinkerhmann et al. | arXiv | 2025 | Bayesian Optimization for threshold calibration | Inspirational: GP surrogate model design for Phase 3 k-multiplier optimization |
| **GPS Spoofing LSTM/GRU** | Chen et al. | IEEE T-ITS | 2024 | LSTM/GRU for GPS spoofing detection | Directly relevant: LSTM prediction deviation as pre-filter for CRS002 |

**Note on AnomalyDAE**: No verifiable DOI or publication venue was found for "AnomalyDAE" in the literature search. This framework is not cited in this document. The closest conceptually related work is CETrajAD (SDM 2025), which uses LSTM autoencoders for trajectory anomaly detection.

### 7.2 What Is NOT Claimed

The following claims are explicitly **not made** in this document or in the broader StreamDQ framework:

- ~~ML improves F1 by X%~~ — No benchmark evidence exists; claim removed.
- ~~ML augmentation is optional~~ — ML is Phase 3 mandatory per ML_MODEL_ANALYSIS.md analysis.
- ~~LSTM provides clear improvement over CRS rules~~ — LSTM is HIGHLY correlated with CRS002 GPS jump detection; training data unconfirmed.
- ~~Per-cell IF models~~ — Per-cell 10,000+ IF models are computationally infeasible; single global model used instead.
- ~~StreamDQ replaces ML anomaly detection~~ — StreamDQ complements ML frameworks; rules and ML address different anomaly modalities.
- ~~Isolation Forest + LSTM + Bayesian Optimization is novel~~ — All three are standard methods; novelty (if any) is in the integration design, not the methods.

---

## 8. Summary: ML is a Collaborator, Not a Competitor

StreamDQ's core value proposition is **deterministic, interpretable, real-time DQ validation** for streaming GPS trajectories in transportation. The rule-based framework—SYN/SEM/CRS rules with hierarchical context-aware thresholds—is the primary contribution. ML augmentation is a secondary enhancement that **may** improve threshold calibration and alert prioritization, but only if Phase 2 establishes baselines and Phase 3 demonstrates measurable improvement.

The positioning is intentionally conservative: **standard ML methods bolted together is not a contribution**. The integration design—rules as authoritative, ML as confidence signal—is the plausible novelty claim, but it requires empirical validation before it can be stated as a finding. This aligns with the PC reviewer assessment in NOVELTY_SCORES.md: Claim 2 (ML augmentation) scores BORDERLINE (6/12), and the path to WEAK ACCEPT requires benchmark evidence of F1 improvement.

**In the research and education platform framing**: StreamDQ teaches practitioners how to build streaming DQ pipelines with interpretable rules. ML augmentation demonstrates how to layer adaptive calibration on top of deterministic validation. The two are complementary—rules provide the foundation; ML provides the calibration. Neither replaces the other, and both are better together than apart.

**Phase 3 is now mandatory**: ML integration is a core contribution. The implementation architecture (BO → IF → XGBoost → LSTM) is specified in ML_INTEGRATION_REDESIGN.md and FORMULATION.md (Algorithms G, H, I), updated per ML_MODEL_ANALYSIS.md recommendations. LightGBM is removed. LSTM is conditional (Priority 4).

---

## Appendix A: ML Method Specifications (Phase 3 Planning)

### A.1 Isolation Forest Configuration

```
# ARCHITECTURE: Single global IF model (NOT per-cell)
# Per-cell models (10,000+) are computationally infeasible.
# ML_MODEL_ANALYSIS.md §1.4: use single global model with zone/hour as features.
# Profile after implementation; multi-cell only if single-model latency exceeds budget.

IsolationForest(
    n_estimators=100,      # SDM 2025 precedent
    max_samples=256,        # streaming-friendly
    contamination=0.01,      # prior: 1% anomalies — sweep {0.005,0.01,0.02,0.05}
    random_state=42,
    Behaviour.NEW           # streaming-compatible
)

Feature vector per event (single global model, zone/hour as features):
  - fare_amount (Z-score normalized from ThresholdStats)
  - trip_distance (Z-score normalized from ThresholdStats)
  - passenger_count (raw)
  - hour (cyclical: sin/cos encoding)
  - zone_category (one-hot: airport, downtown, midtown, outer — 4 features)
  - weekend (binary)
  - payment_type (raw integer)
  # Total: 11 features — single model for all contexts
```

### A.2 LSTM Trajectory Model Configuration

```
# STATUS: CONDITIONAL / NO-GO (Priority 4)
# ML_MODEL_ANALYSIS.md §3: GPS training data unconfirmed, HIGH redundancy with CRS002
# Only proceed if: (a) 6-month GPS archive confirmed, (b) CRS002 recall < 60%

LSTM(
    input_size=3,           # (lat_norm, lon_norm, t_norm)
    hidden_size=64,         # {32, 64, 128} — tuned by validation loss
    num_layers=2,           # {1, 2, 3} — tuned by validation loss
    dropout=0.2,            # {0.1, 0.2, 0.3} — tuned by validation loss
    bidirectional=True
)

Training: NYC MTA Bus historical trajectories (6 months) [UNCONFIRMED]
Prediction: next position from last 10 GPS positions
Deviation metric: haversine(actual, predicted) in km
Alert threshold: >lstm_threshold_m (calibrated by BO, default 100m)
Alert elevation: CRS002 severity max(MEDIUM, ELEVATED) — never vetoes rule
Cold start: vehicles with < 3 prior positions skip LSTM
```

### A.3 Bayesian Optimization Configuration

```
# CRITICAL FIX: objective = F1, not violation_rate (FPR)
# ML_MODEL_ANALYSIS.md §2.8: violation_rate (FPR) can diverge from F1.
# Optimizing FPR may worsen F1 — requires injected calibration data.

BayesianOptimization(
    f=f1_objective,          # maximize F1 on injected calibration data
    pbounds={
        'k_multiplier': (1.5, 5.0),    # for rolling μ±kσ thresholds
        'if_alpha': (0.0, 0.5),         # IF calibration sensitivity (only if IF deployed)
        'lstm_threshold_m': (50.0, 250.0),  # LSTM deviation threshold (only if LSTM deployed)
        'weekend_discount': (0.0, 0.5),  # k reduction for weekend
        'context_weight': (0.0, 1.0)    # weight for context vs. global thresholds
    },
    n_initial_random=10,
    n_iter=30,
    random_state=42,
    acq_func="EI",
    acq_optimizer="sampling"
)

Surrogate model: Gaussian Process (sklearn-based)
Acquisition: Expected Improvement (EI)
Calibration window: 1 hour (requires injection_rate > 0.0 for F1 computation)
Requires: ground_truth_tracker operational (Phase 1)
Staleness check: skip update if calibration takes > 15 minutes
```

---

## Appendix B: Honest Citation List

| # | Citation | Used In |
|---|----------|---------|
| 1 | Cao, S. & Akoglu, L. (2025). Trajectory Anomaly Detection with By-Design Complementary Detectors. *SDM 2025*, pp. 71–80. | Section 2.1 (SYN), Section 4.2 |
| 2 | Chen, Y. et al. (2024). A Method for LSTM-Based Trajectory Modeling and Abnormal Trajectory Detection. *IEEE T-ITS*. doi:10.1109/TITS.2024.3451234. | Section 2.1 (CRS), Section 7.1 |
| 3 | Zhu, X. et al. (2024). METER: Concept Drift Adaptation for Streaming Data. *PVLDB* 17(4). doi:10.14778/3636218.3636233. | Section 2.1, Section 7.1 |
| 4 | Papastergios, G. & Gounaris, A. (2025). Stream DaQ: Stream-First Data Quality Monitoring. arXiv:2506.06147. | Section 3, Section 7.1 |
| 5 | Brinkerhoff et al. (2025). AutoDQM: Automated Data Quality Monitoring. arXiv:2501.13789. | Section 3, Section 7.1 |
| 6 | — | Online Isolation Forest. arXiv:2505.09593, 2025. | Section 2.1, Section 7.1 |
| 7 | Martin, F. et al. (2025). False Discovery in Auto-DQ Constraint Detection. *PVLDB* 18. doi:10.14778/3748191.3748209. | Section 3 (rules > auto-discovery) |

---

*Document classification: Tier 2 (Estimated) for all ML performance claims. All F1 improvement projections are hypotheses requiring empirical validation. ML augmentation is Phase 3 mandatory — a measured contribution, not a guaranteed contribution.*
