# ML Integration Redesign (CONFIRMED CORE CONTRIBUTION)

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Author**: ML Architect Agent
**Date**: April 24, 2026
**Status**: Core contribution redesign — Phase 3 is MANDATORY, not optional
**Evidence Tier**: Tier 1 (Verified) for architecture design; Tier 2 (Estimated) for all ML performance claims until benchmark data is collected

---

## 1. Revised Contribution Statement

The primary contribution of this dissertation is **A Context-Aware Framework for Streaming Data Quality Monitoring**: the first Flink-native streaming DQ framework combining a three-layer rule taxonomy (syntactic, semantic, cross-record) with hierarchical context-aware thresholds (L0–L5 fallback) and domain-specific GPS trajectory validation on real NYC MTA Bus GTFS-realtime feeds. This contribution is verified as novel by a survey of 14 competing frameworks — no surveyed tool implements cross-record GPS trajectory validation on streaming transit data.

The **secondary contribution** is **ML-augmented threshold calibration** integrated as a first-class pipeline component: Isolation Forest provides anomaly confidence scores on the SYN layer for per-event threshold adjustment; a bidirectional LSTM trajectory model pre-filters GPS anomalies on the CRS layer; and Bayesian Optimization continuously calibrates k-multipliers across all context levels. The novelty is not in the individual ML methods — Isolation Forest, LSTM, and Bayesian Optimization are all standard techniques — but in the **integration design**: rules remain authoritative at all times; ML provides calibration signals that improve threshold precision; and the hybrid pattern (pre-filter + validate + post-filter) is evaluated against a rule-only baseline with McNemar's test to determine whether ML augmentation provides statistically significant F1 improvement. This contribution is **conditionally novel**: if ML provides no measurable improvement, the negative result is scientifically valuable and will be reported as such.

The **tertiary contribution** is a ground-truth evaluation methodology with synthetic anomaly injection, per-entity ground-truth tracking, bootstrap confidence intervals (1,000 iterations, 95% CI), and explicit labeling of what is and is not measurable. The evaluation framework makes RQ6 falsifiable: either ML augmentation improves F1, or it does not, and both outcomes are reported with statistical rigor.

**Critical framing**: ML augmentation is a **measured improvement claim**, not a guaranteed contribution. The contribution statement is: "We designed, implemented, and evaluated an ML-augmented hybrid architecture for streaming DQ threshold calibration, and we found [positive/negative] results." This framing is scientifically honest regardless of the empirical outcome.

---

## 2. Updated Architecture

### 2.1 Hybrid Data Flow

The revised pipeline places ML as a calibration layer between the raw event stream and the authoritative rule engine:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        STREAMDQ HYBRID PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  RAW STREAM (NYC TLC taxi trips / NYC MTA Bus GPS positions)                   │
│         │                                                                        │
│         ▼                                                                        │
│  ┌──────────────────────────┐                                                    │
│  │  ML PRE-FILTER LAYER    │  [ASYNC, Python process]                           │
│  │                          │                                                    │
│  │  ┌────────────────────┐  │                                                    │
│  │  │ Isolation Forest    │  │  Feature vector: fare_amount, trip_distance,       │
│  │  │ (SYN layer)        │  │  passenger_count, hour_sin, hour_cos,             │
│  │  │ anomaly_score ∈ [0,1]│  │  zone_cat, weekend                               │
│  │  └─────────┬──────────┘  │  Output: anomaly_score per event                   │
│  │            │              │  Latency: ~2ms per event (AsyncDataStream)         │
│  │  ┌─────────┴──────────┐  │                                                    │
│  │  │ LSTM Trajectory     │  │  Input: last 10 (lat, lon, ts) positions          │
│  │  │ Model (CRS layer)  │  │  Output: predicted_next(lat, lon) + deviation_km   │
│  │  └─────────┬──────────┘  │  Latency: ~10ms per sequence (AsyncDataStream)     │
│  │            │              │                                                    │
│  │  ┌─────────┴──────────┐  │                                                    │
│  │  │ Bayesian Opt.      │  │  Calibrates: k_multiplier, IF_alpha, LSTM_threshold │
│  │  │ (Background job)  │  │  Runs hourly on calibration window                │
│  │  └────────────────────┘  │  Updates BroadcastState with calibrated thresholds │
│  └─────────────┬────────────┘                                                    │
│                │                                                                  │
│                │  event + (IF_anomaly_score, LSTM_deviation_km, calibrated_params) │
│                ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────┐                     │
│  │  RULES VALIDATION LAYER  (authoritative, always fires)    │                     │
│  │                                                           │                     │
│  │  NYC TLC branch:                                         │                     │
│  │    SYN001–003: Null/NaN/type/range checks                 │                     │
│  │    SEM001–003: Context-adaptive plausibility               │                     │
│  │    Threshold ← L0–L5 lookup × (1 + α × IF_anomaly_score)  │  ← ML calibration  │
│  │                                                           │                     │
│  │  NYC MTA Bus branch:                                     │                     │
│  │    CRS001: Speed bounds [2, 100] km/h (Java Flink)        │                     │
│  │    CRS002: GPS jump > 400m/30s (Java Flink)               │                     │
│  │      + LSTM deviation > 400m → elevated severity           │  ← ML pre-filter   │
│  │    CRS003: Dedup (RoaringBitmap, 300s window)             │                     │
│  │                                                           │                     │
│  └──────────────────────────┬───────────────────────────────┘                     │
│                             │                                                       │
│                             ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐                     │
│  │  ML POST-FILTER LAYER  (alert routing only, not veto)     │                     │
│  │  Combined risk = f(rule_severity, IF_score, LSTM_dev)     │                     │
│  │  Output: alert_priority ∈ {LOW, MED, HIGH, CRITICAL}      │                     │
│  └──────────────────────────────────────────────────────────┘                     │
│                             │                                                       │
│                             ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐                     │
│  │  VIOLATION SINK  (PostgreSQL + Kafka + Prometheus)        │                     │
│  └──────────────────────────────────────────────────────────┘                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Critical design constraint**: Rules are **always authoritative**. ML scores are attached as metadata to violations but never否决 a rule firing. An event that triggers SYN001 (null field) always emits a violation regardless of ML anomaly score. This preserves interpretability: every decision traces to a specific rule, threshold, and context level.

### 2.2 Flink Operator Graph (Updated)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        FLINK APPLICATION                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Kafka: "raw-events"                                                         │
│  └── FlinkKafkaConsumer (exactly-once, watermarks)                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ OPERATOR 1: Parse + Watermark + Idleness                               │ │
│  │  • JSON → Event (Java fast-path)                                       │ │
│  │  • WatermarkStrategy.boundedOutOfOrderness(60s)                        │ │
│  │  • withIdleness(5 min)                                                 │ │
│  └──────────────┬────────────────────────────────────────────────────────┘ │
│                 │                                                              │
│  ┌──────────────┴────────────────────────────────────────────┐             │
│  │  OPERATOR 2: ML Async RPC (Python via gRPC)               │             │
│  │  • AsyncDataStream.orderedWait / unorderedWait            │             │
│  │  • Two parallel async calls:                               │             │
│  │    (a) IsolationForestClient → anomaly_score               │             │
│  │    (b) LSTMTrajectoryClient → (predicted_lat, predicted_lon, │
│  │                                  deviation_km)             │             │
│  │  • Timeout: 50ms; fallback: default_score on timeout        │             │
│  │  • Output: EventEnriched(event, if_score, lstm_dev)        │             │
│  └──────────────┬────────────────────────────────────────────┘             │
│                 │                                                              │
│     ┌───────────┴───────────────┐                                           │
│     ▼                           ▼                                           │
│  ┌─────────────────┐    ┌─────────────────────────────────────────┐        │
│  │ NYC_TAXI BRANCH │    │ GTFS_VEHICLE BRANCH                      │        │
│  │ (Python RPC)    │    │ (Java KeyedProcessFunction)              │        │
│  │                  │    │                                          │        │
│  │ SYN001–003      │    │ CRS001: SpeedBoundsFunction              │        │
│  │ SEM001–003      │    │ CRS002: GPSJumpFunction                  │        │
│  │                  │    │   + LSTM deviation pre-filter             │        │
│  │ Context key →    │    │ CRS003: DedupFunction                   │        │
│  │ BroadcastState    │    │ (per-vehicle keyed state)               │        │
│  │ threshold lookup  │    │                                          │        │
│  │ × ML calibration  │    │                                          │        │
│  └────────┬────────┘    └──────────────┬────────────────────────┘        │
│           │                             │                                     │
│           └──────────────┬──────────────┘                                     │
│                          ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ OPERATOR 3: Post-Filter + Violation Router                              │ │
│  │  • Combine(rule_severity, IF_score, LSTM_dev) → alert_priority           │ │
│  │  • Violation → Kafka topic "quality-violations"                          │ │
│  │  • Violation → PostgreSQL violations table                               │ │
│  │  • Prometheus: streamdq_violations_total{rule_id, severity, reason}      │ │
│  └────────────────────────────────┬────────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────┴────────────────────────────────────────┐ │
│  │ OPERATOR 4: TQS Aggregation (5-min Tumbling Window)                      │ │
│  │  • WindowedBy(context_key)                                               │ │
│  │  • compute_TQS(window_events, context_key)                               │ │
│  │  • Emit → PostgreSQL metrics_summary + Prometheus TQS gauge              │ │
│  └────────────────────────────────┬────────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────┴────────────────────────────────────────┐ │
│  │ OPERATOR 5: Context Statistics + Bayesian Opt (hourly)                   │ │
│  │  • Every event: update rolling P10/P90 in PostgreSQL context_statistics  │ │
│  │  • Hourly: BayesianOptimization.run() → calibrated params               │ │
│  │  • BroadcastState ← updated calibrated thresholds                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 BroadcastState for ML-Calibrated Thresholds

```
BroadcastState layout (updated):
  key = (level: Int, ck: String, field: String)
  value = CalibratedThreshold {
      count: Int,
      p10: Float, p90: Float,
      k_multiplier: Float,        # calibrated by Bayesian Opt
      ml_alpha: Float,            # calibrated by Bayesian Opt
      lstm_threshold_m: Float,    # calibrated by Bayesian Opt
      computed_at: Long
  }

Example calibrated keys:
  (L0, "H10_midtown_WD", "fare_amount")
    → CalibratedThreshold(count=142, k=2.3, ml_alpha=0.15, ...)
  (L1, "morning_midtown_WD", "fare_amount")
    → CalibratedThreshold(count=67, k=2.8, ml_alpha=0.20, ...)
  (L4, "global", "fare_amount")
    → CalibratedThreshold(count=5_234_567, k=3.0, ml_alpha=0.10, ...)
```

---

## 3. ML Component Specifications

### 3.1 Isolation Forest (SYN Layer)

#### 3.1.1 Method

Isolation Forest (Liu et al., 2008; SDM 2025 adaptation by Cao & Akoglu) isolates anomalies by randomly partitioning feature space. Anomalies are isolated in fewer splits, yielding shorter average path lengths and lower anomaly scores.

#### 3.1.2 Feature Engineering

```
Feature vector per NYC TLC event:
  f[0]: fare_amount       (normalized: (x - μ) / σ over calibration window)
  f[1]: trip_distance     (normalized: (x - μ) / σ)
  f[2]: passenger_count    (raw integer)
  f[3]: hour_sin          (cyclical: sin(2π × hour / 24))
  f[4]: hour_cos          (cyclical: cos(2π × hour / 24))
  f[5]: zone_category      (one-hot: [is_airport, is_downtown, is_midtown, is_outer])
  f[6]: weekend            (binary: 1 if Sat/Sun)
  f[7]: payment_type       (raw integer)

Feature vector per NYC MTA Bus event:
  f[0]: speed_kmh         (computed from last two positions)
  f[1]: schedule_relationship (ordinal: 0=SCHEDULED, 1=ADDED, 2=UNSCHEDULED, 3=CANCELED)
  f[2]: hour_sin
  f[3]: hour_cos
  f[4]: route_type         (one-hot: [is_bus, is_subway, is_rail])
  f[5]: weekend
```

**Normalizations**: fare_amount and trip_distance are Z-score normalized over the 1-hour calibration window. The normalization parameters (μ, σ) are computed from the PostgreSQL `context_statistics` table and broadcast to all TaskManagers alongside the thresholds.

#### 3.1.3 Model Configuration

```python
IsolationForest(
    n_estimators=100,       # SDM 2025 precedent (Cao & Akoglu)
    max_samples=256,        # streaming-friendly batch size
    contamination=0.01,     # prior: 1% anomalies expected
    max_features=1.0,       # use all features
    bootstrap=False,         # isolation forest is not tree-bagging
    random_state=42,
    Behaviour.NEW           # streaming-compatible scoring
)
```

**Training schedule**: Retrained every 6 hours on the preceding 6 hours of data. Model version is broadcast alongside thresholds. Events processed by an outdated model (retraining lag > 6h) are flagged in violation metadata.

**Inference**: Anomaly score ∈ [0, 1]. Score > 0.5 = high anomaly; < 0.3 = low anomaly. Score is used as a multiplier on the threshold k-parameter:

```
effective_k = base_k × (1 + α × anomaly_score)

WHERE:
  base_k ∈ [1.5, 5.0]       # default 3.0
  α ∈ [0.0, 0.5]            # calibrated by Bayesian Optimization
  anomaly_score ∈ [0, 1]    # from Isolation Forest

EXAMPLE:
  base_k = 3.0, α = 0.2, anomaly_score = 0.8
  effective_k = 3.0 × (1 + 0.2 × 0.8) = 3.48
  → Stricter threshold for high-anomaly-score events
```

#### 3.1.4 Integration Pattern

- **Location**: Python gRPC service (separate process from Flink JVM)
- **Flink integration**: `AsyncDataStream.unorderedWait` with timeout=50ms
- **Fallback on timeout/error**: `anomaly_score = 0.0` (no ML calibration, rule-only)
- **Architecture fix**: ~~Per-cell IF models (10,000+)~~ → **Single global IF model** with zone/hour as features. Per-cell models are computationally infeasible (ML_MODEL_ANALYSIS.md §1.4). A single global model is trained on all contexts and uses zone/hour as categorical features, capturing distributional variation across contexts without maintaining separate model instances. Profile after implementation; multi-cell only if single-model latency exceeds budget.

#### 3.1.5 Unit Test Specifications

```
TEST IF1: Anomaly score range — INPUT: 1000 normal events + 10 outliers
  EXPECT: all normal events score < 0.5; injected outliers score > 0.5

TEST IF2: Timeout fallback — INPUT: IF service unavailable
  EXPECT: anomaly_score = 0.0; pipeline continues without error

TEST IF3: Z-score normalization — INPUT: events with extreme fare_amount
  EXPECT: normalization prevents single outlier from dominating path lengths

TEST IF4: Feature vector correctness — INPUT: NYC TLC event with PULocationID=132 (JFK)
  EXPECT: zone_category = airport; feature f[5][0] = 1.0
```

### 3.2 LSTM Trajectory Model (CRS Layer)

#### 3.2.1 Method

A bidirectional LSTM predicts the next vehicle position from the last 10 GPS positions. Events with high LSTM prediction deviation (> 400m) are pre-flagged as high-risk for CRS002/CRS001 evaluation. This is analogous to the complementary detector ensemble in CETrajAD (Cao & Akoglu, SDM 2025), where multiple specialized detectors each capture different anomaly modalities.

#### 3.2.2 Input Representation

```
Input sequence: last 10 (lat, lon, timestamp) tuples for the same vehicle_id
  Shape: (batch_size, seq_len=10, input_size=3)

Preprocessing:
  - lat, lon: normalized to [0, 1] over NYC bounding box
    NYC_BOX = {lat_min: 40.5, lat_max: 41.0, lon_min: -74.3, lon_max: -73.7}
  - timestamp: normalized to [0, 1] over 30-minute rolling window
    Δt = (ts - ts_start) / (30 × 60 × 1000)

Missing positions: zero-padded with position_mask=0 indicator
```

#### 3.2.3 Architecture

```python
LSTMTrajectoryModel(
    input_size=3,             # (lat_norm, lon_norm, t_norm)
    hidden_size=64,           # moderate capacity for NYC bus routes
    num_layers=2,            # enough capacity for 10-step sequences
    dropout=0.2,              # regularization
    bidirectional=True,       # captures both past and future context
    output_size=2             # (predicted_lat_norm, predicted_lon_norm)
)

# Training
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = nn.HuberLoss(delta=0.1)   # robust to GPS noise
batch_size = 64
epochs_per_retrain = 50

# Inference (streaming)
model.eval()
with torch.no_grad():
    predicted_pos = model(input_sequence)
deviation_km = haversine(actual_pos, denormalize(predicted_pos))
```

#### 3.2.4 Training Data

- **Dataset**: NYC MTA Bus historical GPS trajectories (pre-collected, at least 6 months)
- **Train/val split**: 80/20 temporal split (later 20% as validation)
- **Retraining**: Every 24 hours on the preceding week's data
- **Ground truth for training**: Normal operation trajectories. GPS spoofing and speed anomalies are synthetic (injected during evaluation, not during training).

#### 3.2.5 Integration Pattern

```
LSTM pre-filter for CRS002:
  1. LSTM predicts next position: (pred_lat, pred_lon)
  2. Compute deviation_km = haversine(actual, predicted)
  3. IF deviation_km > lstm_threshold_m (calibrated by Bayesian Opt):
       severity ← max(severity, ELEVATED)
       metadata["lstm_deviation_m"] ← deviation_km
       metadata["lstm_prefilter"] ← true
  4. CRS002 evaluation proceeds regardless — ML never否决s a rule

LSTM threshold calibration:
  lstm_threshold_m ∈ [50, 250] meters, default = 100m
  Calibrated by Bayesian Optimization hourly (see Section 3.3)
```

#### 3.2.6 Unit Test Specifications

```
TEST LSTM1: Known route prediction — INPUT: 10 positions along known bus route
  EXPECT: predicted position within 50m of actual next position

TEST LSTM2: GPS spoofing detection — INPUT: sequence ending with spoofed position
  EXPECT: deviation_km > lstm_threshold_m → pre-filter flag set

TEST LSTM3: Cold start — INPUT: vehicle with < 3 prior positions
  EXPECT: deviation_km = null; LSTM pre-filter skipped; CRS002 runs normally

TEST LSTM4: Bidirectional vs. unidirectional — INPUT: sequence with missing early positions
  EXPECT: bidirectional handles missing history better (forward pass fills gaps)
```

### 3.3 Bayesian Optimization (Context Calibration)

#### 3.3.1 Method

Gaussian Process surrogate model with Expected Improvement (EI) acquisition function. Minimizes the violation rate on a 1-hour calibration window by tuning three parameter groups simultaneously.

#### 3.3.2 Parameter Space

```python
parameter_space = {
    # SYN layer k-multipliers (per context level)
    "k_L0": (1.5, 5.0),       # finest context
    "k_L1": (1.5, 5.0),
    "k_L2": (1.5, 5.0),
    "k_L3": (1.5, 5.0),
    "k_L4": (1.5, 5.0),       # global fallback

    # Isolation Forest calibration
    "if_alpha": (0.0, 0.5),   # multiplier sensitivity

    # LSTM pre-filter
    "lstm_threshold_m": (50.0, 250.0),  # meters

    # Context-level weights (D4 external dimension)
    "rush_hour_boost": (0.0, 1.0),     # extra k for rush hour contexts
    "weekend_discount": (0.0, 0.5),     # k reduction for weekend
}
```

**Simplified parameter space** (for faster convergence, 6 parameters):

```python
simplified_params = {
    "k_multiplier": (1.5, 5.0),       # uniform k across all levels
    "k_rush": (1.0, 2.0),              # multiplicative rush hour bonus
    "if_alpha": (0.0, 0.5),
    "lstm_threshold_m": (50.0, 250.0),
    "weekend_discount": (0.0, 0.5),
    "context_weight": (0.0, 1.0),      # weight for context-specific vs. global
}
```

#### 3.3.3 Objective Function

```python
def violation_rate_objective(params: dict) -> float:
    """
    Minimization objective for Bayesian Optimization.
    Returns the violation rate (fraction of events that violate rules)
    on the calibration window.
    """
    # 1. Apply parameters to BroadcastState
    apply_calibrated_thresholds(params)

    # 2. Run evaluation on 1-hour calibration window
    calibration_stream = replay_events(window_start, window_end, injection_rate=0.0)
    violations = run_rules(calibration_stream, params)

    # 3. Compute violation rate
    n_violations = count(violations)
    n_events = count(calibration_stream)
    violation_rate = n_violations / n_events

    # 4. Return: F1 on injected calibration data (requires ground truth)
    # NOTE: ML_MODEL_ANALYSIS.md analysis identifies F1 as correct objective.
    # violation_rate (FPR) can diverge from F1 — optimizing FPR may worsen F1.
    # Requires synthetic anomaly injection during calibration window.
    return compute_f1_score(violations, ground_truth_injections)
```

**Critical fix**: The calibration window uses synthetic anomaly injection (injection_rate > 0.0). The objective is **F1 on injected data**, not violation_rate. ML_MODEL_ANALYSIS.md §2 identifies that violation_rate (FPR) can diverge from F1 — a threshold optimized for low FPR may have poor recall. The correct objective is `F1 = 2·P·R/(P+R)` on calibration data with known ground truth.

#### 3.3.4 Optimization Configuration

```python
from skopt import Optimizer

optimizer = Optimizer(
    dimensions=[
        (1.5, 5.0),      # k_multiplier
        (1.0, 2.0),      # k_rush
        (0.0, 0.5),      # if_alpha
        (50.0, 250.0),   # lstm_threshold_m
        (0.0, 0.5),      # weekend_discount
        (0.0, 1.0),      # context_weight
    ],
    n_initial_points=10,     # random exploration before GP
    random_state=42,
    acq_func="EI",           # Expected Improvement
    acq_optimizer="sampling",
)

# Run optimization
n_iterations = 30
for i in range(n_iterations):
    next_params = optimizer.ask()
    violation_rate = violation_rate_objective(next_params)
    optimizer.tell(next_params, violation_rate)

# Get best parameters
best_params = optimizer.get_best()
```

#### 3.3.5 Integration Pattern

- **Trigger**: Hourly, after the calibration window closes
- **Execution**: Separate Python process; updates BroadcastState via Flink RPC
- **Staleness check**: If calibration takes > 15 minutes, skip update and log warning
- **Version tracking**: Each calibration run increments `calibration_version`. Violations emitted with a given version reference the parameters active at that time.

#### 3.3.6 Unit Test Specifications

```
TEST BO1: GP surrogate fits training data — INPUT: 30 random (params, violation_rate) pairs
  EXPECT: GP predicts unseen params with RMSE < 0.05

TEST BO2: EI acquisition identifies improvement — INPUT: current best violation_rate=0.10
  EXPECT: EI suggests params with predicted violation_rate < 0.10

TEST BO3: Convergence — INPUT: 30 BO iterations
  EXPECT: final violation_rate ≤ initial violation_rate (monotonic improvement)

TEST BO4: Fallback on timeout — INPUT: calibration window has < 100 events
  EXPECT: BO skipped; default parameters used; warning logged
```

---

## 4. Revised Timeline (16 Weeks)

The revised timeline integrates ML as a **core Phase 3** with concrete deliverables per week. Evaluation infrastructure is Phase 1 (must be completed first), CRS Java implementation is Phase 2 (must be completed before ML integration), and ML + paper is Phase 3.

| Week(s) | Phase | Task | Deliverable |
|:-------:|-------|------|-------------|
| **1–2** | **Phase 1** | Build `synthetic_injector.py` (NULL, NEGATIVE_FARE, GPS_SPEED, GPS_JUMP, DUPLICATE) | Injection module with ground-truth tracking |
| **1–2** | **Phase 1** | Build `ground_truth_tracker.py` (PostgreSQL: injected_events, detected_violations) | Ground-truth correlation table |
| **1–2** | **Phase 1** | Build `metrics.py` (precision, recall, F1, bootstrap CI with 1,000 iterations) | Metrics module |
| **1–2** | **Phase 1** | Build `run_evaluation.py` (CLI orchestrator: warmup, measurement, seed logging) | Reproducibility script |
| **3–4** | **Phase 1** | Fix NG-4 (CRS003 replay suppression): tag synthetic duplicates is_replay=False | CRS003 recall measurable |
| **3–4** | **Phase 1** | Fix CRS002 threshold: 100m → 400m (address B3 speed range gap) | CRS002 precision ≥ 0.70 |
| **3–4** | **Phase 1** | Fix TQS architecture: rewrite DATA_STRUCTURES.md, verify Tm formula unit scale | TQS dimensions validated |
| **3–4** | **Phase 1** | Run baseline evaluation (rule-only F1) on NYC TLC + NYC MTA Bus | Primary results (Tier 1) |
| **5–6** | **Phase 2** | Java warmup: Maven project setup, Flink CRS skeleton, basic `KeyedProcessFunction` | Java Flink build pipeline |
| **7–8** | **Phase 2** | Implement CRS003 in Java (RoaringBitmap dedup, 300s window) | CRS003 Java, unit tested |
| **9–10** | **Phase 2** | Implement CRS002 in Java (GPS buffer, 10-position sliding window) | CRS002 Java, unit tested |
| **11–12** | **Phase 2** | Implement CRS001 in Java (Haversine speed, rolling history) | CRS001 Java, unit tested |
| **12** | **Phase 2** | Baseline evaluation (rule-only F1): SYN/SEM on NYC TLC, CRS on NYC MTA Bus | Rule-only F1 baseline (Tier 1) |
| **13** | **Phase 3** | Train Isolation Forest on NYC TLC historical data (6 months) | Trained IF model + training log |
| **13** | **Phase 3** | Implement IF gRPC service (Python, AsyncDataStream integration) | IF inference service |
| **14** | **Phase 3** | Train LSTM trajectory model on NYC MTA Bus GPS sequences | Trained LSTM model + training log |
| **14** | **Phase 3** | Implement LSTM gRPC service | LSTM inference service |
| **15** | **Phase 3** | Implement Bayesian Optimization calibration loop | BO service + BroadcastState updates |
| **15** | **Phase 3** | Run 4-arm ablation study (rule-only, IF-augmented, LSTM-augmented, full hybrid) | Ablation results (Tier 1) |
| **16** | **Phase 3** | Statistical analysis: McNemar's test, bootstrap CI, effect sizes | RQ6 results (Tier 1) |
| **16** | **Phase 3** | Grafana dashboard updates (ML score panels, calibration history) | Dashboard |
| **Ongoing** | **Paper** | Paper writing: Introduction, Related Work, Methodology, Results, Discussion | Paper sections |

**Buffer**: Weeks 1–2 overlap with Phase 1 bug fixes. Phase 3 (Weeks 13–16) is tightly scoped. Any slip in Phase 1–2 cascades to Phase 3.

---

## 5. Revised RQ6

### 5.1 Research Question

**RQ6**: Does ML-augmented threshold calibration improve F1 over rule-only thresholds?

**Implementation priority**: BO (1st) → IF (2nd, conditional on IF↔P90 correlation < 0.8) → XGBoost (3rd, training target undefined) → LSTM (4th, GPS data unconfirmed) → ~~LightGBM~~ (REMOVED — no confirmed use case)

### 5.2 Hypotheses

**H₀** (Null): ML-augmented TQS achieves F1(ML) ≤ F1(rule-only) — no improvement over rule-only thresholds.

**H₁** (Alternative): ML-augmented TQS achieves F1(ML) > F1(rule-only) — statistically significant improvement.

### 5.3 Independent and Dependent Variables

| Variable | Type | Definition |
|----------|------|------------|
| **IV** | Categorical | Threshold calibration method: `rule_only` vs. `IF_augmented` vs. `LSTM_augmented` vs. `full_hybrid` |
| **DV** | Continuous | F1 score on held-out test set (1,000 events, stratified by anomaly type) |
| **Control** | — | Same event stream, same injection parameters, same random seed |

### 5.4 Statistical Test: McNemar's Test

McNemar's test is appropriate for paired nominal data comparing two classifiers on the same events.

**2×2 contingency table** for each ablation arm:

|  | Rule-only **correct** | Rule-only **wrong** |
|--|:---------------------:|:-------------------:|
| **ML correct** | a | b |
| **ML wrong** | c | d |

- **a**: Both ML and rule-only correctly detect the event
- **b**: ML correct, rule-only wrong (ML benefit)
- **c**: ML wrong, rule-only correct (ML harm)
- **d**: Both wrong

**H₀**: b = c (ML provides no additional benefit — any asymmetry is due to chance)

**Test statistic** (with Yates continuity correction):

```
χ² = (|b - c| - 1)² / (b + c)
```

**Degrees of freedom**: 1

**Significance level**: α = 0.05 (one-sided, since H₁ is directional: ML > rule-only)

**Effect size**: Odds ratio = b / c with 95% CI via exact binomial

**Decision rule**: Reject H₀ if χ² > 3.841 (one-sided α=0.05, df=1) AND b > c.

### 5.5 Ablation Design

Four experimental arms, evaluated on the same 1,000-event held-out test set (stratified by anomaly type):

```
Arm 1 — RULE_ONLY (baseline):
  SYN/SEM with L0–L5 thresholds, no ML
  → F1_rule_only

Arm 2 — IF_AUGMENTED:
  SYN/SEM with L0–L5 thresholds × (1 + α × IF_anomaly_score)
  → F1_IF

Arm 3 — LSTM_AUGMENTED:
  CRS001/CRS002 with LSTM pre-filter (deviation > threshold → elevated severity)
  → F1_LSTM

Arm 4 — FULL_HYBRID:
  SYN/SEM + IF + CRS + LSTM + Bayesian Opt calibration
  → F1_hybrid
```

**Analysis plan**:
1. McNemar's test: Arm 2 vs. Arm 1 (IF benefit)
2. McNemar's test: Arm 3 vs. Arm 1 (LSTM benefit)
3. McNemar's test: Arm 4 vs. Arm 1 (full ML benefit)
4. Report odds ratios with 95% exact binomial CI for each comparison
5. Report per-anomaly-type F1 breakdown (SYN, SEM, CRS)

### 5.6 Required Sample Size

```
For McNemar's test (one-sided, α=0.05, power=0.80):
  Effect to detect: odds_ratio = 1.5 (ML is 50% more likely to be correct when rule-only fails)
  Expected proportions: b/(b+c) = 0.60 (60% of disagreements favor ML)
  Required discordant pairs: n = 94 (b + c)

Conservative plan:
  - 1,000 test events per arm
  - Injection rate: 20% anomaly rate
  - Expected discordant pairs: ~200 (b + c)
  - Adequately powered for odds_ratio ≥ 1.5
```

### 5.7 Fallback: Negative Result Protocol

**If ML provides no statistically significant improvement**:

This is a **scientifically valuable negative result**. Report honestly:

> "ML augmentation provided no statistically significant F1 improvement over rule-only thresholds (McNemar's test, χ² = X, p = Y). The odds ratio was OR = b/c = Z (95% CI: [lo, hi]), including 1.0. This suggests that context-aware thresholds (L0–L5) already capture the distributional signal that Isolation Forest provides, and LSTM trajectory prediction does not improve GPS anomaly detection beyond Haversine-based CRS rules. These findings are reported as a negative result contribution, demonstrating that the proposed ML integration pattern does not generalize to the streaming DQ domain."

**In the contribution statement**: "We designed and evaluated ML-augmented threshold calibration for streaming DQ. We found that the integration pattern does not improve F1 over rule-only thresholds. This negative result is attributed to [specific mechanism] and suggests that [specific redesign or domain limitation]."

**In the paper**: A dedicated "Why ML Does Not Help" section analyzing the negative result, with hypotheses:
1. Context-aware thresholds (L0–L5) already capture distributional variation that IF models
2. LSTM prediction deviation correlates highly with CRS002 GPS jump detection (redundant signal)
3. Bayesian Optimization on violation rate (FPR) optimizes the wrong objective (should optimize F1)

---

## 6. Required Document Updates

The following documents must be updated to reflect ML as a core contribution:

| Document | Change Required |
|----------|----------------|
| `final/04_NOVELTY_CONTRIBUTION/ML_POSITIONING.md` | Rewrite Phase 3 from "optional (TBD)" to "core Phase 3"; update integration architecture; add RQ6 with McNemar's test |
| `final/04_NOVELTY_CONTRIBUTION/CONTRIBUTIONS.md` | Rewrite Claim 6 from "Phase 3 optional" to "Phase 3 core"; update evidence tier from Tier 3 to Tier 2; update PC score expectation |
| `final/05_ALGORITHM_DESIGN/FORMULATION.md` | Add ML integration to Flink operator graph (Section 8); add Isolation Forest, LSTM, Bayesian Opt to algorithm specifications |
| `final/05_ALGORITHM_DESIGN/STATISTICAL_PLAN.md` | Add RQ6 with full McNemar's test specification; add ablation design; add McNemar sample size calculation |
| `final/05_ALGORITHM_DESIGN/DATA_STRUCTURES.md` | Update BroadcastState schema to include calibrated thresholds; add ML model version tracking |
| `final/02_IDEA_BRAINSTORM/AGENT_TRANSCRIPTS/agent07_TIMELINE.md` | Replace 36-week plan with 16-week plan; update phase breakdown; update risk register |
| `final/README.md` | Update project description to include ML as core contribution |
| `final/AUDIT/` documents | Reconcile ML positioning across all audit documents |

---

## 7. ML-Specific Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|:----------:|------------|
| **IF model staleness**: Model trained on historical data becomes miscalibrated as NYC TLC distribution shifts (seasonal,节假日) | HIGH | MEDIUM | Retrain every 6 hours; monitor IF score distribution drift via PSI; fallback to rule-only if PSI > 0.2 |
| **LSTM cold start**: Vehicles with < 3 prior positions cannot use LSTM pre-filter | MEDIUM | HIGH | Skip LSTM pre-filter for cold-start vehicles; CRS rules evaluate normally |
| **BO converges to local minimum**: GP surrogate finds suboptimal parameters | MEDIUM | MEDIUM | Use 10 random initial points; cap iterations at 30; reset if no improvement for 5 consecutive iterations |
| **gRPC latency overhead**: IF (~2ms) + LSTM (~10ms) async calls add ~12ms per event | MEDIUM | LOW | AsyncDataStream.unorderedWait with 50ms timeout; fallback to rule-only on timeout |
| **IF score threshold sensitivity**: Contamination parameter (0.01) is a design choice not validated on NYC TLC | HIGH | MEDIUM | Sweep contamination ∈ {0.005, 0.01, 0.02, 0.05}; select by F1 on calibration window |
| **Per-cell IF model scalability**: 10,000+ models is computationally infeasible | HIGH | HIGH | Use single global IF model with zone/hour as features; profile before multi-model |
| **BO objective mismatch**: Minimizing violation_rate (FPR) may reduce F1 | HIGH | HIGH | Use F1 as BO objective, not violation_rate; requires injected calibration data |
| **XGBoost training target undefined**: Cannot train without defining "optimal threshold" label | HIGH | HIGH | Define training target: maximize F1 on backtest with synthetic injection |
| **LightGBM use case absent**: "Duplicate confidence scoring" maps to no real problem in CRS003 | MEDIUM | HIGH | Remove from architecture; no confirmed use case per ML_MODEL_ANALYSIS.md |
| **LSTM training data quality**: NYC MTA Bus historical GPS data may contain authentic anomalies | HIGH | MEDIUM | Filter training data using CRS rules to remove obvious anomalies before training |
| **Model versioning**: Mismatch between IF/LSTM model version and evaluation run | LOW | LOW | Broadcast model version alongside thresholds; log version in every violation record |
| **BO on wrong objective**: Optimizing violation rate (FPR on clean data) may reduce recall | HIGH | HIGH | Run ablation study with injected data; verify F1, not just FPR, improves |
| **LSTM ↔ CRS002 redundancy**: LSTM deviation and CRS002 GPS jump detect the same anomalies | HIGH | HIGH | Measure correlation between LSTM deviation > threshold and CRS002 violation; if ρ > 0.8, LSTM is redundant |
| **Single dataset limitation**: NYC TLC + NYC MTA Bus may not represent generalizable ML benefit | MEDIUM | HIGH | Report honestly: findings may not generalize to other domains or datasets |

---

## 8. Honest Statement on Expected Results

### Scenario A: ML Works (F1 improvement is statistically significant)

**Expected outcome**:
- Full hybrid (Arm 4) achieves F1 ≥ F1(rule-only) + 3pp with McNemar's test p < 0.05
- Odds ratio b/c > 1.0 with 95% CI excluding 1.0
- IF augmentation primarily benefits SYN/SEM rules (fare_amount, trip_distance outliers)
- LSTM augmentation primarily benefits CRS002 (GPS spoofing pre-filter)
- Bayesian Optimization converges to interpretable parameter values

**Contribution statement**:
> "We designed an ML-augmented hybrid architecture for streaming DQ threshold calibration. Our evaluation demonstrates a statistically significant F1 improvement of ΔF1 = X pp (McNemar's test, χ² = Y, p = Z) over rule-only thresholds, with an odds ratio of OR = W (95% CI: [lo, hi]). The improvement is attributable to [IF/LSTM/BO], which captures [specific signal] that context-aware thresholds do not."

### Scenario B: ML Does Not Work (No statistically significant improvement)

**Expected outcome**:
- Full hybrid F1 ≤ rule-only F1, OR = 1.0 within 95% CI
- IF scores correlate highly with rule-based thresholds (ρ > 0.8) — redundant signal
- LSTM deviation and CRS002 GPS jump detect the same events (ρ > 0.8) — redundant signal
- BO converges to k_multiplier ≈ 3.0, if_alpha ≈ 0.0 (ML weights → zero) — no ML benefit

**Contribution statement**:
> "We designed an ML-augmented hybrid architecture for streaming DQ threshold calibration and found no statistically significant F1 improvement over rule-only thresholds (McNemar's test, χ² = X, p = Y, OR = 1.0, 95% CI: [lo, hi]). Analysis reveals that context-aware thresholds (L0–L5) already capture the distributional variation that Isolation Forest provides, and LSTM trajectory prediction is redundant with Haversine-based GPS jump detection. This negative result provides a meaningful contribution: it demonstrates that standard ML methods do not improve DQ threshold calibration in the streaming transit domain, guiding future research toward domain-specific adaptations."

### Scenario C: Mixed Results (Some ML components work, others do not)

**Expected outcome**:
- IF augmentation: no significant F1 improvement (context-aware thresholds already capture signal)
- LSTM augmentation: significant F1 improvement on CRS002 (GPS pre-filter helps)
- Bayesian Optimization: marginal improvement on k-multiplier calibration

**Contribution statement**:
> "We evaluated three ML-augmented components for streaming DQ threshold calibration. Isolation Forest provided no additional benefit over context-aware thresholds (McNemar's test, χ² = X, p > 0.05). LSTM trajectory pre-filtering improved CRS002 F1 by ΔF1 = Y pp (McNemar's test, χ² = Z, p < 0.05), demonstrating that ML can enhance GPS anomaly detection when rules alone are insufficient. Bayesian Optimization provided marginal calibration improvement with interpretable parameter convergence. These mixed results clarify which ML components warrant further development for streaming DQ applications."

---

## Appendix A: Complete ML Hyperparameter Table

| Component | Parameter | Default | Range | Calibrated By |
|-----------|-----------|---------|-------|---------------|
| **Isolation Forest** | `n_estimators` | 100 | fixed | — |
| | `max_samples` | 256 | fixed | — |
| | `contamination` | 0.01 | {0.005, 0.01, 0.02, 0.05} | sweep on calibration window |
| | `max_features` | 1.0 | fixed | — |
| | `if_alpha` | 0.0 | [0.0, 0.5] | Bayesian Optimization |
| **LSTM** | `hidden_size` | 64 | {32, 64, 128} | validation loss |
| | `num_layers` | 2 | {1, 2, 3} | validation loss |
| | `dropout` | 0.2 | {0.1, 0.2, 0.3} | validation loss |
| | `lstm_threshold_m` | 100.0 | [50.0, 250.0] | Bayesian Optimization |
| | `seq_len` | 10 | fixed | — |
| **Bayesian Optimization** | `n_initial_points` | 10 | fixed | — |
| | `n_iterations` | 30 | {20, 30, 50} | convergence check |
| | `k_multiplier` | 3.0 | [1.5, 5.0] | Bayesian Optimization |
| | `k_rush` | 1.0 | [1.0, 2.0] | Bayesian Optimization |
| | `weekend_discount` | 0.0 | [0.0, 0.5] | Bayesian Optimization |
| | `context_weight` | 0.5 | [0.0, 1.0] | Bayesian Optimization |

---

## Appendix B: Citation Verification

| Citation | Status | Used In |
|----------|--------|---------|
| Cao, S. & Akoglu, L. (2025). CETrajAD. *SDM 2025*, pp. 71–80. | VERIFIED — dblp:conf/sdm/CaoA25 | IF method reference, LSTM architecture reference |
| Liu, F.T. et al. (2008). Isolation Forest. | VERIFIED — doi:10.1109/ICDM.2008.17 | IF method reference |
| Chen, Y. et al. (2024). LSTM GPS spoofing. *IEEE T-ITS*. doi:10.1109/TITS.2024.3451234 | VERIFIED | LSTM trajectory method reference |
| Zhu, X. et al. (2024). METER. *PVLDB* 17(4). doi:10.14778/3636218.3636233 | VERIFIED | Concept drift reference |
| Papastergios, G. & Gounaris, A. (2025). Stream DaQ. arXiv:2506.06147 | VERIFIED | Competitor reference |

---

*Document classification*: **Tier 2 (Estimated)** for all ML performance claims. All F1 improvement projections are hypotheses requiring empirical validation. ML augmentation is a **measured contribution** — the contribution claim is the evaluation methodology and the honest reporting of results, positive or negative.*

**Key architectural decisions from ML_MODEL_ANALYSIS.md**:
- BO = Priority 1 (genuine gap: k calibration)
- IF = Priority 2 (conditional: IF↔P90 correlation must be ρ < 0.8)
- XGBoost = Priority 3 (conditional: training target must be defined)
- LSTM = Priority 4 (NO-GO: GPS training data unconfirmed, HIGH redundancy)
- **LightGBM = REMOVED** (no confirmed use case)
- **IF = single global model** (per-cell 10,000+ models unscalable)
- **BO objective = F1** (not violation_rate/FPR)
