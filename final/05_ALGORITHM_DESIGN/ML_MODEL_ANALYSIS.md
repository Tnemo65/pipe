# ML Model Analysis: StreamDQ — Technical Deep-Dive

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Analyst**: Senior Data Scientist + ML Engineer
**Date**: April 24, 2026
**Status**: Research platform analysis — all ML claims are Tier 2 (Estimated) or Tier 3 (Unmeasurable) until benchmark data is collected
**Scope**: `/final` documents only; codebase is reference, not implementation target

---

## Executive Summary

StreamDQ's ML layer has three components proposed across three design documents (FORMULATION.md Algorithms G/H/I, ML_INTEGRATION_REDESIGN.md, ML_POSITIONING.md). All are **NOT implemented** except a scaffold `MLThresholdPredictor` in `streamdq/ml/threshold_predictor.py` (XGBoost-based, scaffold only — no trained model). This analysis evaluates all five models across applicability, feature engineering, integration, training data, inference latency, redundancy with L0–L5, and recommendation.

**Critical finding**: The single most important redundancy question — "what does this model do that P10/P90 thresholds cannot?" — has a partially affirmative answer for only two models. The other three either duplicate L0–L5 signal or address problems StreamDQ does not have.

---

## 0. The L0–L5 Baseline (What ML Must Beat)

Before analyzing each model, establish what the rule-only baseline already provides:

| What L0–L5 Computes | What ML Must Add |
|--------------------|-------------------|
| Rolling P10/P90 of `fare_amount`, `trip_distance` per context cell | None for distributional anomaly capture |
| Hierarchical fallback: L0 (hour×zone×weekend) → L4 (global) → L5 (physics prior) | Cannot be replicated by ML alone |
| Z-score threshold: `μ + k·σ` with Bayesian-optimized k ∈ [1.5, 5.0] | ML could calibrate k, but BO already does this |
| Per-vehicle GPS speed bounds [2, 100] km/h via Haversine | ML could predict expected speed, but Haversine is physics-based and domain-correct |
| GPS jump >400m/30s via Haversine | ML could predict next position, but rule is deterministic and fast |

**Key insight**: L0–L5 is already a **context-conditioned statistical model**. Its effective model is: `threshold = f(context_key, field, rolling_window_stats)`. The question for each ML model is: what additional signal does it provide that this formula cannot capture?

---

## 1. Isolation Forest

**Library**: `sklearn.ensemble.IsolationForest` (scikit-learn ≥ 1.3)
**Status**: NOT implemented. Specified in FORMULATION.md Algorithm G, ML_INTEGRATION_REDESIGN.md §3.1.
**Implementation scaffold**: None in codebase (Algorithm G is pseudocode only).

### 1.1 Method Overview

Isolation Forest (Liu et al., 2008; SDM 2025 adaptation by Cao & Akoglu) isolates anomalies by recursive random partitioning of feature space. Anomalies require fewer splits to isolate, producing shorter average path lengths. The anomaly score `s(x, n) ∈ [-1, 1]` is:

```
s(x, n) = 2^(-E(h(x)) / c(n))

WHERE:
  h(x) = path length from root to isolation of x
  E(h(x)) = average path length over all trees
  c(n) = average path length for unsuccessful search in BST of size n
```

**Training requirements**: Unsupervised — no labels needed. Fit on historical NYC TLC events. Retrain every 6 hours.
**Inference output**: `anomaly_score ∈ [0, 1]` (transformed from `s(x,n)`).
**sklearn API**: `IsolationForest(n_estimators=100, max_samples=256, contamination=0.01).fit_predict(X)` → anomaly labels; `.score_samples(X)` → raw scores.

### 1.2 Applicability to StreamDQ

**Rating: MEDIUM**

Isolation Forest captures **multivariate distributional anomalies** that univariate P10/P90 thresholds miss. Specifically:

- **What it captures that rules don't**: A fare_amount of $45 is within P90 for a given context cell, but when combined with `trip_distance = 0.1 miles` and `passenger_count = 6`, this combination is statistically unusual even if each field individually passes its threshold. IF detects this multivariate outlier pattern.
- **What it does NOT capture**: Monotone anomalies (e.g., all fares are 10% too high) — these are within distribution so IF scores them as normal.

The proposed integration is: `effective_k = base_k × (1 + α × anomaly_score)` where α is calibrated by Bayesian Optimization. This is a **calibration signal, not a veto**. The rule still fires on the adjusted threshold.

**Redundancy risk**: HIGH. L0–L5 P10/P90 already conditions on context. IF's multivariate score on the same features (fare_amount, trip_distance, passenger_count, hour, zone, weekend) is likely correlated with the rolling statistics. The critical unknown is: how much additional information does IF provide over the P10/P90 statistics? This requires measurement.

### 1.3 Feature Engineering

**NYC TLC feature vector** (8 features, from FORMULATION.md Algorithm G):

```python
import numpy as np
from sklearn.preprocessing import StandardScaler

def build_if_features(event: dict, stats: ThresholdStats) -> np.ndarray:
    hour = extract_hour(event["ts"])
    zone_cat = zone_lookup(event["PULocationID"]).category  # airport/downtown/midtown/outer
    weekend = is_weekend(event["ts"])

    # Z-score normalization using context statistics (from ThresholdStats broadcast state)
    fare_z = (event["fare_amount"] - stats.mean) / (stats.std + 1e-8)
    dist_z = (event["trip_distance"] - stats.mean_dist) / (stats.std_dist + 1e-8)

    # Cyclical encoding for hour
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)

    # Zone category one-hot (4 categories: airport, downtown, midtown, outer)
    zone_onehot = {
        "airport":  [1, 0, 0, 0],
        "downtown": [0, 1, 0, 0],
        "midtown":  [0, 0, 1, 0],
        "outer":    [0, 0, 0, 1],
    }.get(zone_cat, [0, 0, 0, 0])

    features = np.array([
        fare_z,                    # f[0]: normalized fare
        dist_z,                    # f[1]: normalized distance
        float(event["passenger_count"]),  # f[2]: raw integer
        hour_sin,                  # f[3]: cyclical
        hour_cos,                  # f[4]: cyclical
        *zone_onehot,              # f[5-8]: one-hot zone
        float(weekend),            # f[9]: binary
        float(event.get("payment_type", 0)),  # f[10]: raw integer
    ], dtype=np.float32)

    return features

# Training: fit StandardScaler on calibration window first
# scaler = StandardScaler().fit(feature_matrix)  # transform all features
```

**NYC MTA Bus feature vector** (6 features):

```python
def build_gtfs_if_features(event: dict, speed_kmh: float) -> np.ndarray:
    hour = extract_hour(event["ts"])
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)

    # Normalize speed using context statistics
    speed_z = (speed_kmh - SPEED_MEAN) / (SPEED_STD + 1e-8)

    schedule_ordinal = {
        "SCHEDULED": 0, "ADDED": 1, "UNSCHEDULED": 2, "CANCELED": 3
    }.get(event.get("schedule_relationship", "SCHEDULED"), 0)

    return np.array([
        speed_z,                   # f[0]: normalized speed
        float(schedule_ordinal),    # f[1]: ordinal
        hour_sin,                  # f[2]: cyclical
        hour_cos,                  # f[3]: cyclical
        float(is_bus),             # f[4]: binary
        float(is_weekend(event["ts"])),  # f[5]: binary
    ], dtype=np.float32)
```

### 1.4 Integration Pattern

**Location**: Python gRPC service, separate process from Flink JVM.
**Flink integration**: `AsyncDataStream.unorderedWait` with timeout=50ms.
**Fallback**: `anomaly_score = 0.0` on timeout/error (no ML calibration; rule-only).
**BroadcastState update**: After BO calibration, `BroadcastState[key].ml_alpha` is set to calibrated value.

```
Event → AsyncDataStream.unorderedWait → IF gRPC → anomaly_score
       → effective_k = base_k × (1 + α × anomaly_score)
       → SYN002/SEM001 threshold adjusted
       → Rule evaluation (authoritative, always fires)
```

**Note on per-cell models**: FORMULATION.md §8.3 suggests "each NYC TLC zone-hour cell maintains its own IF model." This is computationally expensive (~10,000 models). The more practical approach is a single global IF model trained on all contexts, with zone/hour as features. **The per-cell model claim is unrealistic for a research platform** — implement a single global model first.

### 1.5 Training Data

| Dataset | Size | Availability | Labels Required |
|---------|------|-------------|-----------------|
| NYC TLC parquet | ~3M records (Jan 2024) | Yes (public) | No (unsupervised) |
| NYC MTA Bus GPS | Historical GPS traces needed | Partial (live feed only) | No (unsupervised) |

**Training schedule**: Retrain every 6 hours on preceding 6 hours of data.
**Ground truth**: None needed (unsupervised). BUT: the contamination parameter (default 0.01) is a design choice — it assumes 1% anomaly rate. This prior is not validated on NYC TLC.

### 1.6 Inference Latency

| Component | Estimated Time | Notes |
|-----------|:-------------:|-------|
| Feature extraction | ~0.1 ms | Pure Python dict lookups |
| sklearn IF `.score_samples()` | ~1–2 ms | 100 trees, 256 samples per tree |
| gRPC round-trip (Python→JVM→Python) | ~5–10 ms | Network + serialization overhead |
| **Total per event** | **~10–15 ms** | Within 50ms timeout budget |

**Streaming feasibility**: YES (under 50ms budget).
**Throughput**: ~1,000 events/sec per IF service instance [Tier 2 — Estimated].

### 1.7 Redundancy Analysis

| Question | Answer | Confidence |
|----------|--------|:----------:|
| Does IF detect anomalies that P10/P90 misses? | YES for multivariate patterns | Tier 1 (mechanistic) |
| Does IF correlate with L0–L5 thresholds? | LIKELY HIGH (same features) | Tier 2 (needs measurement) |
| Could P10/P90 achieve the same result? | PARTIALLY for univariate; NO for multivariate | Tier 1 (reasoned) |
| Is the effective_k adjustment measurable? | UNKNOWN — needs ablation study | Tier 2 |

**The key unknown**: IF's added value over L0–L5 is the **multivariate interaction** between fare, distance, passenger_count, and zone. If the correlation between IF_score and P90_threshold is ρ > 0.8, IF is redundant. This must be measured before claiming ML benefit.

### 1.8 Recommendation

**GO (conditional)** — Priority: **2nd**
- Conditional on: measure IF_score correlation with L0–L5 thresholds. If ρ > 0.8, downgrade to NO-GO.
- Key risk: IF_score redundancy with rolling statistics → no measurable F1 improvement.
- Evidence: Tier 1 (method is proven), Tier 2 (benefit to StreamDQ is unmeasured).

---

## 2. Bayesian Optimization

**Library**: `skopt` (scikit-learn based GP surrogate) or `GPyOpt`
**Status**: NOT implemented. Specified in FORMULATION.md Algorithm I, ML_INTEGRATION_REDESIGN.md §3.3.
**Implementation scaffold**: None in codebase.

### 2.1 Method Overview

Gaussian Process (GP) surrogate model with Expected Improvement (EI) acquisition function minimizes the violation rate on a 1-hour calibration window by tuning threshold parameters. GP models the mapping `f: params → violation_rate` with uncertainty estimates, enabling intelligent exploration.

**Training requirements**: Objective function evaluation (violation rate on calibration window). No labels needed — self-supervised from the running pipeline.
**Inference output**: Optimal parameter values (k_multiplier, if_alpha, lstm_threshold_m, weekend_discount, context_weight).
**skopt API**:

```python
from skopt import Optimizer

optimizer = Optimizer(
    dimensions=[
        (1.5, 5.0),      # k_multiplier
        (0.0, 0.5),      # if_alpha
        (50.0, 250.0),   # lstm_threshold_m
        (0.0, 0.5),      # weekend_discount
        (0.0, 1.0),      # context_weight
    ],
    n_initial_points=10,   # random exploration
    random_state=42,
    acq_func="EI",         # Expected Improvement
    acq_optimizer="sampling",
)

for i in range(30):
    params = optimizer.ask()
    violation_rate = evaluate_on_calibration_window(params)
    optimizer.tell(params, violation_rate)

best = optimizer.get_best()
```

### 2.2 Applicability to StreamDQ

**Rating: MEDIUM**

Bayesian Optimization addresses a **genuine gap** in the L0–L5 design: the k-multiplier in `threshold = μ + k·σ` is currently either hardcoded (k=3.0) or manually tuned. BO provides systematic calibration. However:

- **What it captures that L0–L5 doesn't**: Optimal k per context cell. Different context cells may have different k-optimal values (e.g., airport zone has higher variance → needs higher k).
- **What it does NOT address**: The fundamental question of whether context-aware thresholds work at all (that's RQ1, measured by ablation study).

**Critical design tension**: The objective function is `violation_rate on clean data (injection_rate=0.0)`. This optimizes for **false-positive rate minimization**, not **F1 maximization**. These can diverge: lowering FPR may raise FNR if anomalies are present. The ML_INTEGRATION_REDESIGN.md explicitly acknowledges this as HIGH likelihood risk: "Optimizing violation rate (FPR) may reduce recall."

**Redundancy risk**: LOW. BO calibrates parameters that the rules themselves cannot calibrate. No redundancy with L0–L5.

### 2.3 Feature Engineering

BO does not use event-level features. Its "features" are the 5–6 pipeline parameters being calibrated:

```python
parameter_space = {
    "k_multiplier": (1.5, 5.0),       # uniform k across all levels
    "k_rush": (1.0, 2.0),             # multiplicative rush-hour bonus
    "if_alpha": (0.0, 0.5),           # IF calibration sensitivity
    "lstm_threshold_m": (50.0, 250.0), # LSTM deviation threshold (meters)
    "weekend_discount": (0.0, 0.5),    # k reduction for weekend
    "context_weight": (0.0, 1.0),      # context vs. global weight
}
```

**Objective function**: `violation_rate = n_violations / n_events` on 1-hour calibration window with injection_rate=0.0.

### 2.4 Integration Pattern

**Location**: Separate Python background process, triggered hourly.
**Flink integration**: Writes calibrated parameters to BroadcastState via Flink RPC.
**Trigger**: Every 1 hour, after calibration window closes.
**Staleness check**: If calibration takes > 15 minutes, skip update.

```
Hourly trigger → Pull 1-hour calibration window (injection_rate=0.0)
               → BO.run(n_iterations=30)
               → Extract best_params
               → Write to BroadcastState (all TaskManagers)
               → Log calibration_version++
```

### 2.5 Training Data

| Requirement | Status |
|-------------|--------|
| 1-hour clean event window | Requires operational pipeline with injection_rate=0.0 |
| Minimum 100 events in window | Must check before running BO |
| Parameter evaluation (30 iterations × N events) | Computationally bounded |

**Data availability**: NYC TLC replay data is available. Running a clean replay with injection_rate=0.0 is feasible. [Tier 2 — Estimated feasibility].

### 2.6 Inference Latency

| Component | Estimated Time | Notes |
|-----------|:-------------:|-------|
| BO ask/tell loop (30 iterations) | ~1–5 seconds | GP surrogate evaluation is fast |
| Violation rate evaluation (per iteration) | ~30–60 seconds | Replaying 1-hour window through rules |
| **Total calibration run** | **~15–30 minutes** | [Tier 2 — Estimated] |
| Parameter broadcast to Flink | ~1–2 seconds | RPC call |

**Streaming feasibility**: N/A — this is a background job, not per-event inference. Runs hourly.
**Acceptable for streaming**: YES — hourly cadence is appropriate for threshold recalibration.

### 2.7 Redundancy Analysis

| Question | Answer | Confidence |
|----------|--------|:----------:|
| Does BO duplicate L0–L5 statistics? | NO — BO optimizes k, L0–L5 computes stats | Tier 1 |
| Could grid search achieve the same? | YES, but less efficiently | Tier 1 |
| Is hourly calibration appropriate? | YES — matches diurnal cycle | Tier 2 |

**The objective function problem is the real risk**: BO on violation_rate (FPR) may not maximize F1. The correct objective is `F1 = 2·P·R/(P+R)` on injected calibration data. This requires the evaluation infrastructure (Phase 1) to be operational first.

### 2.8 Recommendation

**GO (conditional)** — Priority: **1st** (if Phase 1 infrastructure exists) / **3rd** (if Phase 1 not ready)
- Conditional on: (a) Phase 1 evaluation infrastructure operational, (b) objective function uses F1 not violation_rate.
- Key risk: BO converges to local minimum; GP surrogate mis-specified.
- Evidence: Tier 1 (method is proven), Tier 2 (optimal objective is disputed — FPR vs F1).

---

## 3. LSTM Trajectory Model

**Library**: `PyTorch` (bidirectional LSTM)
**Status**: NOT implemented. Specified in FORMULATION.md Algorithm H, ML_INTEGRATION_REDESIGN.md §3.2.
**Implementation scaffold**: None in codebase.

### 3.1 Method Overview

Bidirectional LSTM predicts the next vehicle position from the last 10 GPS positions. Events where the actual position deviates significantly from the prediction are pre-flagged with elevated severity for CRS002 evaluation.

**Training requirements**: Historical NYC MTA Bus GPS trajectories. Supervised: input = sequence of (lat, lon, ts), output = next (lat, lon).
**Inference output**: Predicted next (lat, lon), deviation_km (Haversine distance from actual).
**Architecture** (from FORMULATION.md Algorithm H):

```python
import torch
import torch.nn as nn

class LSTMTrajectoryModel(nn.Module):
    def __init__(self, input_size=3, hidden_size=64, num_layers=2,
                 dropout=0.2, output_size=2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,    # (lat_norm, lon_norm, t_norm)
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size * 2, output_size)  # *2 for bidirectional

    def forward(self, x):
        # x: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Use last time step
        last_output = lstm_out[:, -1, :]
        prediction = self.fc(last_output)  # (batch, 2) = (lat_norm, lon_norm)
        return prediction
```

### 3.2 Applicability to StreamDQ

**Rating: MEDIUM**

LSTM provides a **trajectory-level anomaly signal** that per-event rules cannot capture. CRS001 and CRS002 evaluate single-step GPS measurements. LSTM evaluates the **trajectory shape** — whether the sequence of positions is consistent with expected bus routes.

**What it captures that CRS rules don't**:
- A single position jump of 300m (below CRS002 threshold of 400m) may be part of a larger pattern of deviation from expected route
- The **direction** of movement relative to expected trajectory (LSTM captures this; CRS does not)
- **Route context**: LSTM implicitly learns typical bus routes from training data; CRS001/CRS002 are purely physics-based

**What it does NOT capture that CRS rules do**:
- Absolute speed bounds (CRS001 is physics-correct and simpler)
- Exact GPS jump magnitude (CRS002 threshold is deterministic)
- Anomalies that don't deviate from the predicted route

**Redundancy risk**: HIGH. CRS002 GPS jump detection and LSTM trajectory deviation are **measuring the same phenomenon** (deviation from expected movement). The critical unknown: what fraction of CRS002 violations does LSTM pre-filter catch that CRS002 wouldn't catch on its own? If the answer is "none," LSTM is purely redundant.

FORMULATION.md §9.3 explicitly states: "CRS002 evaluation always proceeds — ML never vetoes a rule." So LSTM pre-filtering is **alert elevation only**, not detection replacement. This is honest but raises the question: what does elevated severity achieve that the rule itself doesn't?

### 3.3 Feature Engineering

**Input representation** (per vehicle, last 10 positions):

```python
import torch

# NYC bounding box normalization
NYC_BOX = {
    "lat_min": 40.5, "lat_max": 41.0,
    "lon_min": -74.3, "lon_max": -73.7,
}

def build_lstm_sequence(vehicle_positions: list[dict]) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Build input tensor for LSTM from last 10 vehicle positions.

    Args:
        vehicle_positions: List of dicts with keys: lat, lon, ts
                          Ordered oldest → newest (at least 3 positions required)

    Returns:
        (input_tensor, mask) where:
        - input_tensor: (1, seq_len, 3) — normalized lat, lon, time
        - mask: (1, seq_len) — 1.0 for valid, 0.0 for padded
    """
    seq_len = 10
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Pad sequence if fewer than 10 positions
    padded = vehicle_positions[-seq_len:] if len(vehicle_positions) >= seq_len \
             else [{"lat": 0, "lon": 0, "ts": 0}] * (seq_len - len(vehicle_positions)) + vehicle_positions

    # Normalize
    lat_min, lat_max = NYC_BOX["lat_min"], NYC_BOX["lat_max"]
    lon_min, lon_max = NYC_BOX["lon_min"], NYC_BOX["lon_max"]
    ts_start = padded[0]["ts"]

    lat_norm = [(p["lat"] - lat_min) / (lat_max - lat_min) for p in padded]
    lon_norm = [(p["lon"] - lon_min) / (lon_max - lon_min) for p in padded]
    # Normalize timestamps to 30-minute window
    dt_norm = [min((p["ts"] - ts_start) / (30 * 60 * 1000), 1.0) for p in padded]

    # Build mask (1 for valid, 0 for padded)
    mask = torch.tensor(
        [1.0 if p["lat"] != 0 else 0.0 for p in padded],
        dtype=torch.float32,
    ).unsqueeze(0)  # (1, seq_len)

    # Stack: (1, seq_len, 3)
    tensor = torch.tensor(
        [[lat_norm[i], lon_norm[i], dt_norm[i]] for i in range(seq_len)],
        dtype=torch.float32,
    ).unsqueeze(0).to(device)

    return tensor, mask

# Inference
def predict_deviation(model, vehicle_positions: list[dict], actual_lat: float,
                       actual_lon: float) -> float:
    if len(vehicle_positions) < 3:
        return None  # Cold start — skip LSTM

    input_tensor, _ = build_lstm_sequence(vehicle_positions)
    model.eval()
    with torch.no_grad():
        pred_norm = model(input_tensor).squeeze(0).cpu().numpy()

    # Denormalize
    pred_lat = pred_norm[0] * (NYC_BOX["lat_max"] - NYC_BOX["lat_min"]) + NYC_BOX["lat_min"]
    pred_lon = pred_norm[1] * (NYC_BOX["lon_max"] - NYC_BOX["lon_min"]) + NYC_BOX["lon_min"]

    # Haversine deviation
    deviation_km = haversine(actual_lat, actual_lon, pred_lat, pred_lon)
    return deviation_km
```

### 3.4 Integration Pattern

**Location**: Python gRPC service, separate from Flink JVM.
**Flink integration**: `AsyncDataStream.unorderedWait`, timeout=50ms, `lstm_deviation_km` returned.
**CRS002 integration**: After LSTM scoring:

```
CRS002 violation detected → LSTM deviation_km available?
                         → deviation_km > lstm_threshold_m?
                            → severity ← max(severity, ELEVATED)
                            → metadata["lstm_deviation_m"] ← deviation_km × 1000
                         → Violation emitted (CRS002 is authoritative)
```

**Note**: LSTM never vetoes CRS002. CRS002 always fires if its condition is met.

### 3.5 Training Data

| Dataset | Size | Availability | Labels Required |
|---------|------|-------------|-----------------|
| NYC MTA Bus historical GPS trajectories | Unknown | Partial (live feed replay only; no historical archive confirmed) | No (self-supervised: predict next position from sequence) |

**Critical gap**: FORMULATION.md §9.2 states "Training: NYC MTA Bus historical GPS trajectories (pre-collected, at least 6 months)." **No 6-month historical GPS archive is confirmed to exist.** The live feed replays recent data, but a 6-month archive for LSTM training may not be available. This is a **Tier 2 — Estimated** feasibility issue. If only 1–2 weeks of data are available, LSTM training will be underfitted.

**Training schedule**: Retrain every 24 hours on preceding week's data.
**Loss function**: `nn.HuberLoss(delta=0.1)` — robust to GPS noise.

### 3.6 Inference Latency

| Component | Estimated Time | Notes |
|-----------|:-------------:|-------|
| LSTM forward pass (seq_len=10, hidden=64, 2 layers) | ~2–5 ms | GPU: ~1ms; CPU: ~5ms |
| gRPC round-trip | ~5–10 ms | Network + serialization |
| Feature building (per-vehicle position lookup) | ~1 ms | KeyedState read |
| **Total per sequence** | **~10–15 ms** | Within 50ms timeout budget |

**Streaming feasibility**: YES (under 50ms budget per sequence, not per event).
**Throughput**: ~100 sequences/sec per LSTM service instance [Tier 2 — Estimated].

### 3.7 Redundancy Analysis

| Question | Answer | Confidence |
|----------|--------|:----------:|
| Does LSTM catch what CRS002 misses? | POSSIBLY — trajectory patterns vs. single-step jumps | Tier 2 |
| Is LSTM deviation correlated with CRS002 violation? | LIKELY — both measure GPS deviation | Tier 2 — needs measurement |
| Could LSTM replace CRS002? | NO — LSTM is less interpretable; rules must remain | Tier 1 |
| Does LSTM add value beyond alert elevation? | UNKNOWN — elevation doesn't change detection | Tier 3 |

**The alert elevation problem**: FORMULATION.md §9.3 says LSTM only elevates severity, never vetoes. If a CRS002 violation fires, it fires. The only difference is whether it's routed as HIGH vs. MEDIUM priority. **For a research platform with no production alerting system, this benefit is marginal.** There is no confirmed downstream system that would treat ELEVATED differently from a normal CRS002 violation.

### 3.8 Recommendation

**NO-GO (for now)** — Priority: **4th**
- Rationale: (a) Training data availability uncertain (6-month GPS archive unconfirmed), (b) LSTM–CRS002 redundancy is HIGH (same signal), (c) alert elevation provides marginal value in a research platform, (d) cold-start problem is HIGH (vehicles with < 3 prior positions cannot use LSTM).
- **Exception**: GO if CRS002 recall < 60% on real-world GPS anomalies — LSTM trajectory prediction could capture what CRS002 misses. This requires real GPS anomaly data (not synthetic injection) to evaluate.
- Evidence: Tier 2 (method proven), Tier 2 (training data unconfirmed), Tier 3 (downstream value unconfirmed).

---

## 4. LightGBM

**Library**: `lightgbm` (Microsoft gradient boosting)
**Status**: NOT implemented. Referenced in `streamdq/ml/__init__.py` ("Duplicate confidence scoring (LightGBM)") but no implementation.
**Implementation scaffold**: None in codebase.

### 4.1 Method Overview

LightGBM (Ke et al., 2017) is a gradient boosting decision tree framework optimized for speed and memory efficiency. The proposed use in `streamdq/ml/__init__.py` is for "duplicate confidence scoring" — predicting whether a potential duplicate event is a true duplicate or a legitimate re-occurrence.

**Training requirements**: Labeled data (true duplicates vs. false duplicates). Requires ground-truth duplicate labels.
**Inference output**: Probability of being a true duplicate.

### 4.2 Applicability to StreamDQ

**Rating: LOW**

**Critical problem**: The stated use case ("duplicate confidence scoring") addresses a problem CRS003 does not have. CRS003 uses SHA256 hashing — if the hash matches, it's a duplicate by construction. There is no "confidence" question for hash-based deduplication.

The confusion likely arises from the CRS003 ground truth tracking problem (NG-4: replay suppression gate blocks synthetic duplicates). But fixing NG-4 does not require LightGBM — it requires `synthetic_injector.py` to emit two records. LightGBM would be useful for:

1. **Predicting which context cells will have high violation rates** (cross-context prediction)
2. **Predicting TQS score from event features** (regression)
3. **Classifying violation severity from event metadata**

None of these are in the FORMULATION.md or ML_INTEGRATION_REDESIGN.md specifications. The mention in `__init__.py` appears to be a design artifact, not a planned feature.

**Redundancy risk**: N/A — no confirmed use case.

### 4.3 Feature Engineering

**Proposed feature vector for duplicate confidence** (if use case is clarified):

```python
def build_duplicate_features(event1: dict, event2: dict) -> np.ndarray:
    """
    Features for predicting duplicate confidence between two events.

    NOTE: This use case is not confirmed in the FORMULATION.md specification.
    LightGBM for duplicate confidence is NOT in the approved ML architecture.
    """
    dt_ms = abs(event2["ts"] - event1["ts"])

    features = np.array([
        dt_ms / 1000.0,  # time delta in seconds
        float(event1.get("PULocationID") == event2.get("PULocationID")),  # same pickup
        float(event1.get("DOLocationID") == event2.get("DOLocationID")),  # same dropoff
        float(event1.get("vehicle_id") == event2.get("vehicle_id")),  # same vehicle
        abs(event1.get("fare_amount", 0) - event2.get("fare_amount", 0)),  # fare diff
        abs(event1.get("trip_distance", 0) - event2.get("trip_distance", 0)),  # dist diff
    ], dtype=np.float32)

    return features
```

### 4.4 Integration Pattern

No integration pattern specified in design documents. `streamdq/ml/__init__.py` lists it as a planned component but provides no specification.

### 4.5 Training Data

| Requirement | Status |
|------------|--------|
| Labeled duplicate data (true/false) | UNKNOWN — no labeled duplicate dataset confirmed |
| Ground truth for duplicates | TIER 3 — CRS003 recall is unmeasurable (NG-4 not fixed) |

### 4.6 Redundancy Analysis

| Question | Answer | Confidence |
|----------|--------|:----------:|
| Does LightGBM address a real gap in StreamDQ? | UNCONFIRMED | Tier 3 |
| Is the use case ("duplicate confidence") valid? | NO for hash-based dedup; POSSIBLY for other tasks | Tier 2 |
| Is this specified in FORMULATION.md? | NO | Tier 1 |

### 4.7 Recommendation

**NOT APPLICABLE** — No confirmed use case in the approved architecture.
- The mention in `streamdq/ml/__init__.py` should be removed or clarified.
- If a use case is identified (e.g., TQS score prediction), revisit with concrete specification.
- Evidence: Tier 3 (no confirmed use case).

---

## 5. XGBoost

**Library**: `xgboost` (dmlc)
**Status**: Scaffold exists in `streamdq/ml/threshold_predictor.py` but **NO trained model**. The `MLThresholdPredictor` class attempts to load an MLflow model but falls back gracefully to rule-based thresholds when the model is unavailable.
**Implementation scaffold**: Partial — the scaffolding is present, model training pipeline is NOT.

### 5.1 Method Overview

XGBoost (Chen & Guestrin, 2016) is a gradient boosting framework. The `MLThresholdPredictor` class proposes using XGBoost to predict optimal `fare_amount` thresholds from event features:

```python
# From streamdq/ml/threshold_predictor.py
def _extract_features(self, event: Dict, context: Any) -> np.ndarray:
    """Extract 18 features for threshold prediction."""
    # Features: hour, day_of_week, is_weekend, is_peak_hour, is_late_night,
    #          pickup_region, dropoff_region, is_same_region,
    #          passengers, distance, fare_per_mile, fare_per_passenger,
    #          fare_mean, fare_std, fare_p90,
    #          fare_rolling_mean, fare_rolling_std, fare_rolling_p90
    # ...
```

**Training requirements**: Historical events with ground-truth optimal thresholds (from domain expert or backtest).
**Inference output**: Predicted optimal threshold value.
**Current status**: Model loading from MLflow fails gracefully (`self.enabled = False`), pipeline continues with rule-based thresholds.

### 5.2 Applicability to StreamDQ

**Rating: MEDIUM (potential) / LOW (current design)**

The XGBoost threshold predictor addresses a different problem than L0–L5: it learns a **direct mapping from features to optimal threshold**, whereas L0–L5 computes thresholds from rolling statistics. The key distinction:

| Approach | Method | Pros | Cons |
|----------|--------|------|------|
| L0–L5 (rolling stats) | `threshold = P90(rolling_window)` | No training needed; adapts to distribution | Only uses univariate statistics |
| XGBoost (threshold predictor) | `threshold = f(features)` | Can learn multivariate interactions; explicit feature importance | Requires labeled training data; may not generalize across time |

**What XGBoost could capture that L0–L5 doesn't**:
- Non-linear relationships between features and optimal threshold (e.g., surge pricing pattern that depends on interaction of hour × zone × day_of_week)
- Explicit feature importance for interpretability
- Transfer of threshold knowledge from well-sampled cells to poorly-sampled cells

**Redundancy risk**: MEDIUM. The feature set overlaps with L0–L5 inputs. If the optimal threshold is well-approximated by rolling P90, XGBoost adds little.

### 5.3 Feature Engineering

**Feature vector** (18 features, from `threshold_predictor.py`):

```python
# Reproduced from streamdq/ml/threshold_predictor.py
features = np.array([
    hour,                           # f[0]: 0-23
    day_of_week,                   # f[1]: 0-6
    is_weekend,                    # f[2]: 0/1
    is_peak_hour,                  # f[3]: 0/1
    is_late_night,                 # f[4]: 0/1
    pickup_region,                  # f[5]: 0-26 (PULocationID // 10)
    dropoff_region,                 # f[6]: 0-26
    is_same_region,                 # f[7]: 0/1
    passengers,                    # f[8]: 1-6
    distance,                      # f[9]: miles
    fare_per_mile,                 # f[10]: USD/mile
    fare_per_passenger,            # f[11]: USD/person
    fare_mean,                     # f[12]: from context.stats
    fare_std,                      # f[13]: from context.stats
    fare_p90,                      # f[14]: from context.stats
    fare_rolling_mean_100,          # f[15]: rolling mean (placeholder)
    fare_rolling_std_100,           # f[16]: rolling std (placeholder)
    fare_rolling_p90_100,          # f[17]: rolling p90 (placeholder)
], dtype=np.float32)
```

**Note**: Features f[15-17] are marked as "placeholder" in the code. This is a scaffold, not a working implementation.

### 5.4 Integration Pattern

**Current**: `MLThresholdPredictor` wraps the XGBoost model and provides a fallback:

```python
# From streamdq/ml/threshold_predictor.py
def predict_threshold(self, event, context, fallback_threshold):
    if not self.enabled:
        return fallback_threshold  # Rule-based fallback
    # ML inference
    features = self._extract_features(event, context)
    predicted = float(self.model.predict([features])[0])
    # Sanity check
    if predicted < 0 or predicted > 500:
        return fallback_threshold
    return predicted
```

**Proposed integration** (if model is trained):
```
Event → predict_threshold(event, context, fallback=P90_threshold)
      → XGBoost predicted threshold
      → Compare: if |predicted - P90| > tolerance, flag for review
      → Use P90 as authoritative threshold (rules remain authoritative)
```

### 5.5 Training Data

| Requirement | Status |
|------------|--------|
| Historical NYC TLC events with known optimal thresholds | UNKNOWN — "optimal threshold" is not ground-truth observable |
| Feature values for each event | YES (from context.stats and event fields) |
| Labels: what is the target variable? | **UNDEFINED** — the code does not specify what XGBoost should predict |

**Critical design gap**: What does "optimal threshold" mean as a training label? Options:
1. **Backtest-based**: Find thresholds that maximize F1 on historical injected anomalies — requires ground truth labels
2. **Expert-annotated**: Domain expert labels "correct threshold" per context cell — subjective, not scalable
3. **Regression on P90**: Target = P90 from rolling window — this just reproduces L0–L5, no new signal

The `threshold_predictor.py` scaffold does not define the training target. This is a **Tier 3 — Unmeasurable** issue until the training objective is clarified.

### 5.6 Inference Latency

| Component | Estimated Time | Notes |
|-----------|:-------------:|-------|
| Feature extraction (18 features) | ~0.1 ms | Dict lookups |
| XGBoost prediction | ~0.5 ms | Single tree ensemble, very fast |
| **Total per event** | **< 1 ms** | Fastest of all ML models |

**Streaming feasibility**: YES (far under 50ms budget).

### 5.7 Redundancy Analysis

| Question | Answer | Confidence |
|----------|--------|:----------:|
| Does XGBoost learn something P10/P90 can't? | UNKNOWN — training objective undefined | Tier 3 |
| Are features overlapping with L0–L5? | YES — fare_mean, fare_std, fare_p90 are same as L0–L5 | Tier 1 |
| Could XGBoost replace L0–L5? | NO — rules remain authoritative; XGBoost is calibration only | Tier 1 |

### 5.8 Recommendation

**CONDITIONAL GO** — Priority: **3rd (if use case clarified)**
- Rationale: (a) Scaffold exists but model is not trained, (b) training objective undefined — must clarify what "optimal threshold" means as a label, (c) features f[15-17] are placeholders, (d) current fallback to rule-based thresholds is correct behavior.
- Required before implementation: Define training target. Recommended: maximize F1 on backtest with synthetic injection. Do not use P90 as label (circular).
- Evidence: Tier 2 (scaffold exists), Tier 3 (training objective undefined).

---

## 6. Comparison Table

| Model | Type | Training Data | Output | Latency | Streaming OK | Redundancy Risk | Recommendation |
|-------|------|-------------|--------|---------|:-----------:|-----------|:--------------:|
| **IsolationForest** | Unsupervised anomaly detection | NYC TLC parquet (~3M records, no labels) | anomaly_score ∈ [0, 1] | ~10–15 ms/event | **YES** | **HIGH** — correlated with L0–L5 features | **GO (conditional)** — Priority 2 |
| **BayesianOpt** | GP surrogate optimization | 1-hour clean event window (self-supervised) | calibrated k, α, thresholds | ~15–30 min/run (hourly) | **YES** (background) | **LOW** — optimizes params L0–L5 can't | **GO (conditional)** — Priority 1 (if Phase 1 ready) |
| **LSTM** | Sequence prediction (PyTorch) | 6-month NYC MTA Bus GPS traces [UNCONFIRMED] | deviation_km | ~10–15 ms/sequence | **YES** (50ms budget OK) | **HIGH** — correlated with CRS002 GPS jump | **NO-GO** — Priority 4; training data unconfirmed |
| **LightGBM** | Gradient boosting (supervised) | Labeled duplicate data [NO USE CASE] | duplicate probability | N/A | N/A | **N/A** — no confirmed use case | **NOT APPLICABLE** — remove from __init__.py |
| **XGBoost** | Gradient boosting (supervised, scaffold) | Optimal threshold labels [UNDEFINED] | threshold value | < 1 ms/event | **YES** | **MEDIUM** — overlapping features | **CONDITIONAL GO** — Priority 3; training target must be defined |

---

## 7. FINAL RANKING

### Priority 1: Bayesian Optimization
**Rationale**: BO addresses a genuine gap (k-multiplier calibration) that no other model covers. L0–L5 computes rolling statistics but cannot optimize the k parameter. BO provides this calibration with a GP surrogate. It runs hourly as a background job — no per-event latency concern. The main risk (wrong objective function) is addressable by using F1 instead of violation_rate. **Start here if Phase 1 evaluation infrastructure exists.**

### Priority 2: Isolation Forest
**Rationale**: IF provides a multivariate anomaly signal that L0–L5 univariate thresholds cannot capture. The critical unknown (IF_score correlation with P10/P90) must be measured, but the method is proven and latency is acceptable. **Measure IF–P90 correlation first; if ρ < 0.8, proceed with implementation.** If ρ > 0.8, IF is redundant with L0–L5.

### Priority 3: XGBoost (threshold predictor)
**Rationale**: The scaffold exists but the training objective is undefined. If the objective is clarified (maximize F1 on backtest, not reproduce P90), XGBoost could learn non-linear threshold patterns that L0–L5 misses. **Do not implement until training target is defined.** The current fallback-to-rules behavior is correct and should be preserved.

### Priority 4: LSTM Trajectory Model
**Rationale**: Training data availability is unconfirmed (6-month GPS archive not confirmed). LSTM–CRS002 redundancy is HIGH. Alert elevation (the only LSTM output) provides marginal value in a research platform without a production alerting system. **Re-evaluate if CRS002 recall on real-world data is < 60%.**

### Priority 5: LightGBM
**Rationale**: No confirmed use case in the approved architecture. The "duplicate confidence scoring" use case does not map to a real problem in CRS003 (hash-based dedup has no confidence question). **Remove from `streamdq/ml/__init__.py` or re-scope to a concrete use case.**

---

## 8. Concrete Feature Vectors by Dataset

### NYC TLC Yellow Taxi

| Model | Feature Vector (8–18 features) | Normalization |
|-------|------------------------------|---------------|
| **IsolationForest** | `[fare_z, dist_z, passenger_count, hour_sin, hour_cos, is_airport, is_downtown, is_midtown, is_outer, is_weekend, payment_type]` | Z-score (fare/dist from ThresholdStats; others raw) |
| **XGBoost** | `[hour, day_of_week, is_weekend, is_peak_hour, is_late_night, pickup_region, dropoff_region, is_same_region, passengers, distance, fare_per_mile, fare_per_passenger, fare_mean, fare_std, fare_p90, rolling_mean, rolling_std, rolling_p90]` | Mixed (raw + from context.stats) |
| **BayesianOpt** | Parameters: `[k_multiplier, if_alpha, lstm_threshold_m, weekend_discount, context_weight]` — no event features | N/A |

### NYC MTA Bus GTFS-realtime

| Model | Feature Vector (6 features) | Normalization |
|-------|---------------------------|---------------|
| **IsolationForest** | `[speed_z, schedule_ordinal, hour_sin, hour_cos, is_bus, is_weekend]` | Z-score (speed from context stats; schedule_ordinal raw) |
| **LSTM** | Sequence of 10 `(lat_norm, lon_norm, t_norm)` tuples + position mask | NYC bounding box normalization + 30-min window |
| **BayesianOpt** | Same as NYC TLC (operates on pipeline parameters, not event features) | N/A |

---

## 9. Evidence Tier Summary

| Model | Overall Tier | Key Uncertainties |
|-------|:------------:|-------------------|
| IsolationForest | **Tier 2** | IF_score ↔ P90 correlation unmeasured; per-cell model feasibility |
| BayesianOpt | **Tier 2** | Optimal objective function (FPR vs F1); BO convergence on 6-param space |
| LSTM | **Tier 2/3** | Training data unconfirmed (6-month GPS archive); CRS002 redundancy |
| LightGBM | **Tier 3** | No confirmed use case |
| XGBoost | **Tier 2/3** | Training target undefined; scaffold has placeholder features |

**No model achieves Tier 1 (Verified)** — all ML claims are estimated pending benchmark data.

---

## 10. Architectural Red Flags

### Flag 1: Per-Cell IF Models Are Unscalable
FORMULATION.md Algorithm G suggests "each NYC TLC zone-hour cell maintains its own IF model (10,000+ models)." This is computationally infeasible for a research platform. **Implement a single global IF model with zone/hour as features. Profile first; multi-model only if single-model latency exceeds budget.**

### Flag 2: LSTM Alert Elevation Is Low-Value in Research Platform
LSTM pre-filtering elevates CRS002 severity from MEDIUM to HIGH. In a research platform with no production alerting integration, this elevation has no downstream effect. **Either implement a concrete alerting use case or deprioritize LSTM.**

### Flag 3: BO Objective Function Mismatch
Bayesian Optimization minimizes violation_rate on clean data (FPR). The desired outcome is F1 maximization on injected data. These can diverge: a threshold optimized for low FPR may have poor recall. **Use F1 as the BO objective, not violation_rate.**

### Flag 4: XGBoost Training Target Is Undefined
The `threshold_predictor.py` scaffold does not define what XGBoost should predict as a label. Without this, model training is impossible. **Define the training target: maximize F1 on backtest with synthetic injection is the recommended approach.**

### Flag 5: LightGBM Use Case Is Absent
`streamdq/ml/__init__.py` lists LightGBM for "duplicate confidence scoring" but no design document specifies this use case. Hash-based deduplication has no confidence question. **Remove from `__init__.py` or define a concrete use case.**

---

*Analysis classification: All ML performance claims are Tier 2 (Estimated) until benchmark data is collected. IsolationForest, LSTM, and XGBoost method claims are Tier 1 (verified from scikit-learn/PyTorch documentation). BayesianOpt method claim is Tier 1. LightGBM use case is Tier 3 (no confirmed application).*
