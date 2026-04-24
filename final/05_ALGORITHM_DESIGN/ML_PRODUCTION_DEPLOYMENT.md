# ML Production Deployment Analysis: StreamDQ

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Role**: Senior Machine Learning Engineer
**Date**: April 24, 2026
**Status**: Tier 2 (Estimated) — all latency numbers are pre-benchmark estimates requiring empirical validation

---

## Executive Summary

StreamDQ has five ML models planned for production deployment. Based on latency characteristics, they divide into three categories:

| Category | Models | Latency Budget | Serving Mode |
|----------|--------|----------------|--------------|
| **Embedded** (≤5ms) | XGBoost, LightGBM | Trivially fits | In-process with rules |
| **gRPC async** (~10-50ms) | IsolationForest | Tight but feasible | Separate Python service |
| **Sequence model** (~100ms) | LSTM | **Too slow for streaming** | Separate service, pre-filter only |

**Key finding**: LSTM trajectory prediction cannot meet the ~50ms streaming budget at the per-event level. It must be repositioned as a **batch pre-filter** or **offline anomaly scorer**, not an inline streaming component.

**Minimum viable ML architecture**: IsolationForest (gRPC) + embedded XGBoost/LightGBM. Bayesian Optimization runs hourly as a background job — no streaming latency constraint.

---

## 1. IsolationForest (sklearn)

### 1.1 Inference Latency Analysis

**Per-event scoring latency breakdown:**

```
sklearn.ensemble.IsolationForest.predict_score()
├── Input: 8-feature numpy array, shape (1, 8)
├── Tree traversal: 100 trees × ~log₂(256) ≈ 800 node comparisons
├── Path length computation: O(100) float operations
└── Total: ~0.3–0.8ms (in-process, no network)

Gunicorn/uvicorn HTTP overhead (if REST):
├── Connection: ~0.1ms (keep-alive)
├── Request parsing: ~0.2ms
├── Model inference: ~0.5ms
├── Response serialization: ~0.1ms
└── Total: ~0.9ms (local)

gRPC overhead (Python service):
├── Proto serialization: ~0.1ms
├── Model inference: ~0.5ms
├── Proto deserialization: ~0.1ms
└── Total: ~0.7ms (local, same machine)

gRPC overhead (remote service, LAN):
├── Network RTT: ~1-3ms (same datacenter)
├── Proto serialization: ~0.2ms
├── Model inference: ~0.5ms
└── Total: ~2-4ms (remote)
```

**Verdict**: IsolationForest inference alone is ~0.5ms. With gRPC overhead on the same machine, total ~2-4ms per event. This **easily fits** the 50ms budget with 46ms margin.

### 1.2 Throughput Capacity

```
Per instance:
  Single-threaded throughput: ~2,500 events/sec (0.4ms/event)
  With gunicorn (4 workers): ~10,000 events/sec
  With multiprocessing (8 cores): ~20,000 events/sec

NYC TLC replay throughput: ~1,000 events/sec (1 event/trip, ~10 min intervals)
NYC MTA Bus live: ~50 events/sec (500 vehicles × ~0.1 Hz update rate)

Required: ~1,050 events/sec
Capacity per gRPC instance: ~10,000 events/sec
→ Single instance covers 10x current load with headroom
```

### 1.3 Serving Architecture

**Recommended: gRPC Python service with connection pooling**

```
┌─────────────────────────────────────────────────────────────┐
│  Flink TaskManager (JVM)                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AsyncDataStream.unorderedWait(                       │  │
│  │   IsolationForestClient (channel pool: 16 conns)     │  │
│  │   timeout=50ms, maxConcurrentCalls=64                │  │
│  │ ) → EventEnriched(anomaly_score)                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ gRPC (same machine or LAN)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  IF Service (Python, port 50051)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ grpcio + sklearn.ensemble.IsolationForest            │  │
│  │ Per-zone models: ~100 models (zone_cat × time_cat)  │  │
│  │ Model hot-reload via SIGHUP or config reload         │  │
│  │ Health check: /health → "OK"                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  Memory: ~100MB (100 models × ~1MB each)                  │
│  CPU: ~1 core at full load                                 │
└─────────────────────────────────────────────────────────────┘
```

**Alternative: Embedded (NOT recommended for IF)**

While IsolationForest can run in-process within Python, the 100 per-context-cell models would require ~100MB of RAM within the Flink Python process. With Flink's TM memory limits and the async RPC pattern already established, a separate service is cleaner and enables independent scaling.

### 1.4 Integration with Flink

The existing design uses `AsyncDataStream.unorderedWait` with 50ms timeout. This is appropriate:

```
Input: Event → AsyncDataStream → IF gRPC → anomaly_score → Rules
                              ↑
                          50ms timeout
                          fallback: score=0.0
```

**Key integration points:**
1. **Connection pooling**: 16 channels maintained via `ManagedChannel`
2. **Request batching**: Batch 8-16 concurrent requests per channel
3. **Timeout**: 50ms — IF inference is ~2ms, so 48ms margin for network variance
4. **Fallback**: `anomaly_score = 0.0` on timeout — rules use uncalibrated k

### 1.5 Model Versioning

IsolationForest does NOT support incremental training. Retraining every 6 hours requires full model rebuild.

```
Version tracking strategy:
  - Model path: /models/if/zone_cat={cat}/time_cat={cat}/version={timestamp}
  - Latest symlink: /models/if/zone_cat={cat}/time_cat={cat}/latest
  - BroadcastState: includes if_model_version string
  - Violation metadata: includes if_model_version
  - Example: "if_v20260424_100000_zc_midtown_tc_morning"

Reload strategy:
  - Polling: check /models/if/.../latest every 60s, reload if changed
  - SIGHUP: reload on signal (zero-downtime)
  - Flink checkpoint: model version persisted in BroadcastState
```

### 1.6 Fallback Behavior

```
Failure Mode 1: gRPC timeout (>50ms)
  → anomaly_score = 0.0 (no ML calibration)
  → effective_k = base_k (rule-only evaluation)
  → Violation emitted normally

Failure Mode 2: IF service DOWN
  → Circuit breaker: after 3 consecutive failures, open circuit for 30s
  → During open: all requests return fallback score=0.0
  → Health check every 5s to detect recovery
  → On recovery: close circuit, resume normal calls

Failure Mode 3: Model file missing/corrupt
  → Startup check: verify all zone/time models exist
  → Missing model → log FATAL, refuse to start
  → Corrupt model → log ERROR, fallback to global model

Failure Mode 4: Invalid feature vector (NaN in input)
  → Catch exception in IF service
  → Return anomaly_score = 0.5 (neutral, neither high nor low)
  → Log warning with event_id
```

### 1.7 Retraining Pipeline

```
Frequency: Every 6 hours
Trigger: Cron job + anomaly detection (PSI > 0.2)

Retraining pipeline:
  1. Extract last 6 hours of events from PostgreSQL (or replay Kafka)
  2. Group by (zone_cat, time_cat) — ~100 groups
  3. For each group with ≥ 500 events:
     a. Fit IsolationForest(n_estimators=100, max_samples=256, contamination=0.01)
     b. Save to /models/if/{zone_cat}/{time_cat}/version={ts}
     c. Update /models/if/{zone_cat}/{time_cat}/latest symlink
  4. Log retrain metrics: n_events, n_groups, duration
  5. No pipeline restart required (hot reload via polling)

Fallback retrain schedule:
  - If retrain fails: retry after 1 hour
  - After 3 consecutive failures: alert on-call
  - Last-known-good model retained until new model succeeds
```

### 1.8 Memory Footprint

```
Per IF model (sklearn IsolationForest, n_estimators=100, max_samples=256):
  - Tree structure: 100 trees × ~512 nodes × 3 floats ≈ 600 KB
  - Node data: 100 × 512 × {threshold, size, features} ≈ 400 KB
  - Total per model: ~1 MB

100 zone/time models: ~100 MB
gRPC runtime: ~50 MB
Python interpreter: ~30 MB
Total: ~180 MB per IF service instance
```

### 1.9 Hot Reload

```
Mechanism: Symlink-based atomic swap
  /models/if/zone_cat=X/time_cat=Y/latest → version_20260424_100000/

Procedure:
  1. Train new model to /models/if/zone_cat=X/time_cat=Y/version_{ts}
  2. Verify model loads successfully (import + predict on test data)
  3. Atomic symlink update: latest → version_{ts}
  4. Service polls latest symlink every 60s
  5. On symlink change: reload model (no dropped requests during reload)

Verification:
  - Load new model in background thread
  - Run parallel inference on new + old model
  - If new model produces NaN or extreme values → reject, keep old
  - On success: swap reference atomically
```

---

## 2. Bayesian Optimization (skopt / GPyOpt)

### 2.1 Inference Latency Analysis

**Bayesian Optimization is NOT a per-event inference model.** It runs as a **hourly background calibration job**. There is zero latency pressure.

```
Hourly calibration run:
  1. Load 1-hour calibration window: ~100K events from PostgreSQL
  2. GP surrogate fit: ~30 BO iterations × ~10K event evaluation each
  3. Each evaluation: apply params → run rules on calibration window
  4. Total: ~10-30 minutes per calibration run (acceptable for hourly)

Output: 6 calibrated parameters → BroadcastState update
  - k_multiplier: Float
  - if_alpha: Float
  - lstm_threshold_m: Float
  - weekend_discount: Float
  - context_weight: Float
  - k_rush: Float
```

**Verdict**: No streaming latency constraint. BO is a **background job**, not a streaming component.

### 2.2 Throughput Capacity

```
N/A — BO is not on the hot path.

Hourly throughput:
  - Calibration events per hour: ~3.6M events (NYC TLC replay)
  - Events per BO iteration: 10K (1% sample of calibration window)
  - Total evaluations per run: 30 iterations × 10K events = 300K rule evaluations
  - Duration: ~10-30 minutes (Python GIL: use multiprocessing or joblib)
```

### 2.3 Serving Architecture

**Recommended: Standalone Python microservice with REST/gRPC API for Flink**

```
┌─────────────────────────────────────────────────────────────┐
│  BO Calibration Service (Python, separate process)          │
│  Port: 50052                                               │
│                                                             │
│  Endpoints:                                                 │
│    POST /calibrate → run BO, return params                 │
│    GET  /params   → current calibrated params              │
│    GET  /health   → service health                         │
│                                                             │
│  Trigger:                                                   │
│    - Cron: every hour on the hour                          │
│    - HTTP POST from Flink Operator 5 (hourly)               │
│    - Manual: via Grafana alert action                      │
│                                                             │
│  Output:                                                    │
│    - Calibrated params → PostgreSQL calibration_history     │
│    - BroadcastState update via Flink RPC                    │
└─────────────────────────────────────────────────────────────┘
```

**Integration with Flink Operator 5:**

```
Hourly trigger (Flink Timer):
  1. Timer fires → collect calibration window events (last 1 hour)
  2. POST /calibrate with calibration events
  3. BO service: run 30 iterations, return best params
  4. Update BroadcastState with calibrated k_multiplier, if_alpha, etc.
  5. BroadcastState.broadcast() → all TaskManagers receive update
```

### 2.4 Model Versioning

```
BO calibration history tracked in PostgreSQL:

Table: calibration_history
  id: SERIAL PRIMARY KEY
  run_at: TIMESTAMP
  n_events: INTEGER
  duration_seconds: FLOAT
  best_violation_rate: FLOAT
  params: JSONB  -- {"k_multiplier": 3.2, "if_alpha": 0.15, ...}
  convergence_iter: INTEGER
  gp_rmse: FLOAT

Query for versioning:
  SELECT * FROM calibration_history
  ORDER BY run_at DESC
  LIMIT 1;
```

### 2.5 Fallback Behavior

```
Failure Mode 1: BO run takes > 15 minutes
  → Skip update, use default params
  → Log WARNING with duration
  → Alert if consecutive failures

Failure Mode 2: BO service DOWN
  → Flink uses last-known-good params from BroadcastState
  → No alert suppression — violations continue normally
  → BO service auto-restarts (supervisor)

Failure Mode 3: Insufficient calibration data (< 100 events)
  → BO skipped, default params used
  → Log INFO: "BO skipped: calibration window has {n} events (minimum 100)"

Failure Mode 4: BO converges to invalid params
  → Sanity check: all params within valid ranges
  → If any param outside range: reject, use default
  → Log ERROR with invalid params
```

### 2.6 Retraining Pipeline

```
Retraining = running the calibration job.

Trigger: Hourly, via cron or Flink timer
No separate retraining pipeline — BO IS the retraining job.

Post-calibration:
  1. Store params in PostgreSQL calibration_history
  2. Push to BroadcastState via Flink RPC
  3. Log metrics: n_events, duration, best_violation_rate, convergence_iter
  4. If convergence_iter = 30 (max): log WARNING "BO did not converge"
```

### 2.7 Memory Footprint

```
BO service memory:
  - Calibration window (1 hour, sampled 10K events): ~5 MB
  - GP surrogate model: ~1 MB
  - BO optimizer state: ~1 MB
  - Python runtime: ~100 MB
  - Total: ~110 MB

Note: BO service is stateless between runs.
Each calibration run allocates ~5 MB, deallocates after.
```

---

## 3. LSTM Trajectory Model (PyTorch)

### 3.1 Inference Latency Analysis

**CRITICAL: LSTM CANNOT meet the ~50ms streaming latency budget.**

```
Per-sequence LSTM inference latency breakdown:

PyTorch LSTM forward pass (bidirectional, hidden=64, layers=2, seq_len=10):
  ├── Input preprocessing: ~0.5ms (normalization, padding)
  ├── Tensor creation: ~0.2ms
  ├── LSTM forward: ~8-15ms (GPU) or ~20-40ms (CPU)
  ├── Output denormalization: ~0.3ms
  ├── Haversine distance: ~0.1ms
  └── Total: ~10-20ms (GPU) or ~25-50ms (CPU)

gRPC overhead (same machine):
  ├── Proto serialization: ~0.3ms
  ├── Network (loopback): ~0.5ms
  └── Total additional: ~0.8ms

Total per-sequence (GPU): ~11-21ms
Total per-sequence (CPU): ~26-51ms ← AT THE EDGE of 50ms budget
```

**But the critical issue is not average latency — it is P99 tail latency:**

```
P99 latency considerations:
  - GPU warm-up: first inference ~2x slower (~40ms on cold GPU)
  - CUDA kernel launch overhead: ~1-2ms per batch
  - Memory bandwidth saturation at high concurrency
  - Garbage collection pauses in Python: ~5-20ms unpredictable

P99 on GPU (estimated): ~30-50ms — marginal for 50ms budget
P99 on CPU (estimated): ~60-100ms — **exceeds 50ms budget**
```

**The 50ms budget includes the entire async call, not just inference:**

```
AsyncDataStream.unorderedWait timeout breakdown:
  - gRPC channel acquisition: ~1ms
  - Request serialization: ~0.3ms
  - Network (loopback): ~0.5ms
  - LSTM inference: ~15ms (GPU median)
  - Response deserialization: ~0.2ms
  - Flink operator processing: ~5ms
  - Buffer/margin: ~28ms (for P99 variance)

Available budget for LSTM inference: ~22ms (at P50)
→ LSTM P50 (~15ms) fits. LSTM P99 (~30-50ms) MAY NOT fit.
```

**Verdict**: LSTM is **marginal at best** for inline streaming. The architecture must be redesigned.

### 3.2 Redesigned LSTM Architecture: Batch Pre-Filter

**The correct pattern for LSTM in a streaming system is NOT per-event inference — it is batch scoring with result caching.**

```
ARCHITECTURE CHANGE: LSTM as batch pre-filter, NOT inline scorer

┌─────────────────────────────────────────────────────────────┐
│  BEFORE (BROKEN): Per-event inline scoring                 │
│  Event → LSTM RPC → deviation_km → CRS002                  │
│  Problem: ~25ms per event, blocks pipeline                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AFTER (CORRECT): Batch pre-filter with cache             │
│                                                             │
│  1. Batch collector: accumulate 100 events or 1 second      │
│  2. Group by vehicle_id: build GPS sequences               │
│  3. LSTM batch inference: 100 sequences × ~15ms = ~1.5s     │
│     (batched, amortized: ~0.015ms per event)               │
│  4. Store deviation_km in per-vehicle cache (L1)           │
│  5. CRS002 reads from cache: ~0.01ms per event             │
│                                                             │
│  Total latency added to streaming path: ~0.1ms (cache hit)  │
│  LSTM inference: runs in background, ~1.5s behind          │
└─────────────────────────────────────────────────────────────┘
```

**Revised operator graph:**

```
┌────────────────────────────────────────────────────────────────┐
│  REVISED FLINK OPERATOR GRAPH (LSTM redesigned)               │
│                                                                │
│  OPERATOR 1: Watermark + Parse                                │
│                          │                                     │
│                          ▼                                     │
│  OPERATOR 2: Batch Collector (100 events or 1s window)       │
│     Groups events by vehicle_id                                │
│     Accumulates GPS sequences per vehicle                      │
│                          │                                     │
│                          ▼                                     │
│  OPERATOR 3a: CRS rules (Java, fast path)                    │
│     CRS001/CRS002/CRS003: ~1ms per event                     │
│     Reads LSTM deviation from cache (L1 state)                │
│     If cache miss: proceeds without LSTM flag (graceful deg)  │
│                          │                                     │
│                          ▼                                     │
│  OPERATOR 3b: LSTM Batch Scorer (async, background)          │
│     Every 100 events OR 1 second:                            │
│     - Collect accumulated sequences                           │
│     - gRPC batch call to LSTM service                        │
│     - Store deviation_km in per-vehicle keyed state           │
│     - Latency: ~1.5s behind (acceptable for pre-filter)       │
│                          │                                     │
│                          ▼                                     │
│  OPERATOR 4: Post-Filter + Violation Router                  │
│     LSTM deviation already in state — no additional latency   │
└────────────────────────────────────────────────────────────────┘
```

### 3.3 Throughput with Batch Pre-Filter

```
Revised throughput:
  - Batch size: 100 events OR 1 second (whichever first)
  - Sequences per batch: ~50 (100 events ÷ 2 vehicles/avg)
  - Batch inference time: 50 sequences × 15ms/sequence = 750ms
  - Events processed while batch runs: ~50 events
  - Effective latency addition: ~0ms to streaming path (pre-filter)

Capacity:
  - LSTM service throughput (batch mode, GPU):
    100 sequences/batch × 12 batches/second = 1,200 sequences/sec
  - NYC MTA Bus: ~50 events/sec → ~25 sequences/sec
  - Headroom: ~48x capacity
```

### 3.4 Serving Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LSTM Trajectory Service (Python + PyTorch, port 50053)     │
│                                                             │
│  Model: Bidirectional LSTM, hidden=64, layers=2             │
│  Input: (batch_size, seq_len=10, input_size=3)              │
│  Output: (batch_size, 2) — predicted (lat, lon)            │
│                                                             │
│  GPU: NVIDIA T4 (16GB VRAM) — handles batch of 100         │
│  Batch API: predict_batch(sequences) → deviations           │
│                                                             │
│  Memory:                                                    │
│    - Model weights: ~2 MB                                   │
│    - PyTorch runtime: ~500 MB                              │
│    - Input/output buffers: ~10 MB                           │
│    - Total: ~512 MB with GPU                                │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 Model Versioning

```
LSTM model versioning (same pattern as IF):
  Path: /models/lstm/version={timestamp}/
  Files:
    model.pt          — PyTorch state_dict
    normalizer.json   — NYC bounding box, normalization params
    config.json       — hidden_size, num_layers, dropout
    latest → version_{timestamp}

BroadcastState includes: lstm_model_version
Violation metadata includes: lstm_model_version

Reload: Same symlink-based atomic swap as IF
```

### 3.6 Fallback Behavior

```
Failure Mode 1: LSTM batch not ready (cache miss)
  → CRS002 proceeds WITHOUT lstm_prefilter flag
  → Violation emitted based on Haversine only
  → Log DEBUG: "LSTM cache miss for vehicle {id}"

Failure Mode 2: LSTM service DOWN
  → Batch collector accumulates events
  → After 30s: flush partial batch with warning
  → CRS002 uses Haversine only
  → Circuit breaker: skip LSTM calls for 5 minutes

Failure Mode 3: LSTM returns NaN/deviation
  → Treat as cache miss
  → Log WARNING: "LSTM returned NaN for vehicle {id}"

Failure Mode 4: Vehicle cold start (< 3 positions)
  → Skip LSTM pre-filter for this vehicle
  → Log DEBUG: "Cold start: {n} positions < 3"
  → CRS002 evaluates normally (Haversine only)
```

### 3.7 Retraining Pipeline

```
Frequency: Every 24 hours on preceding week's data
Trigger: Cron job + drift detection (concept drift in GPS sequences)

Retraining pipeline:
  1. Extract last 7 days of GPS sequences from PostgreSQL
  2. Filter using CRS rules to remove obvious anomalies
  3. Group by vehicle_id, build sequences of 10 positions
  4. Train/val split: 80/20 temporal
  5. Train: torch.nn.LSTM (bidirectional, hidden=64, layers=2)
  6. Validate: HuberLoss on held-out 20%
  7. Save to /models/lstm/version={ts}/
  8. Hot reload via symlink

GPU requirements:
  - Training: NVIDIA T4 or A10G (~$0.50/hr on cloud)
  - Training time: ~30-60 minutes for 1 week of data
  - Memory: ~2GB GPU, ~8GB RAM
```

### 3.8 Memory Footprint

```
LSTM service (GPU, batch mode):
  - Model weights: ~2 MB
  - PyTorch CUDA runtime: ~500 MB
  - Batch buffers (100 sequences × 10 steps × 3 features): ~12 KB
  - Python runtime: ~100 MB
  - Total: ~602 MB

Note: PyTorch GPU memory is the dominant factor.
CPU-only inference: ~600 MB RAM, no GPU needed, but ~2x slower.
```

---

## 4. LightGBM (Gradient Boosting)

### 4.1 Inference Latency Analysis

**LightGBM is designed for ultra-fast inference — sub-millisecond per prediction.**

```
LightGBM inference (single prediction, CPU):
  ├── Tree traversal: ~20 trees × depth ~6 = ~120 node visits
  ├── Feature lookups: ~20
  └── Total: ~0.05-0.2ms

LightGBM inference (batch of 100, CPU):
  ├── Vectorized tree traversal: SIMD-optimized
  └── Total: ~1-3ms for 100 predictions → ~0.01-0.03ms per event

Gunicorn/gRPC overhead:
  └── Total with gRPC: ~0.5-1ms per prediction
```

**Verdict**: LightGBM **trivially fits** the 50ms budget. Can be embedded in-process.

### 4.2 Serving Architecture: Embedded

**Recommended: Embed LightGBM directly in the Python rule evaluation path.**

```
┌─────────────────────────────────────────────────────────────┐
│  EMBEDDED (RECOMMENDED for LightGBM)                        │
│                                                             │
│  from streamdq.rules.scorer import DuplicateConfidenceScorer│
│                                                             │
│  class DuplicateConfidenceScorer:                           │
│      def __init__(self, model_path):                        │
│          self.model = lgb.Booster(model_file=model_path)   │
│                                                             │
│      def score(self, event: dict) -> float:                │
│          features = self._extract_features(event)          │
│          return self.model.predict([features])[0]           │
│                                                             │
│  # In rule evaluation:                                      │
│  confidence = scorer.score(event)                            │
│  if confidence < 0.4:  # CRS003 confidence threshold        │
│      skip_duplicate_check()                                 │
│                                                             │
│  Latency added: ~0.2ms (embedded, no network)               │
│  Memory: ~20 MB (model) + ~10 MB (feature cache)           │
└─────────────────────────────────────────────────────────────┘
```

**Alternative: gRPC service** (only if LightGBM needs to share models across pipelines):

```
Same pattern as IF gRPC service, but:
  - Latency: ~0.5ms (vs 2ms for IF)
  - Throughput: ~50,000 events/sec per instance (vs 10K for IF)
  - Memory: ~20 MB (model) + ~50 MB (gRPC runtime)
```

### 4.3 Model Versioning

```
Same pattern as IF:
  Path: /models/lightgbm/crs003/version={timestamp}.txt
  Hot reload via polling symlink every 60s

Violation metadata includes: lightgbm_model_version
```

### 4.4 Fallback Behavior

```
Failure Mode 1: Model load failure
  → Fallback: confidence = 0.5 (neutral)
  → Log ERROR: "LightGBM load failed, using fallback"
  → Alert if consecutive failures

Failure Mode 2: Prediction returns NaN
  → Fallback: confidence = 0.5
  → Log WARNING with event_id

Failure Mode 3: Feature extraction failure
  → Fallback: confidence = 0.5
  → Log WARNING with missing field
```

### 4.5 Retraining Pipeline

```
Frequency: Daily or on PSI > 0.2 (drift detected)

Retraining:
  1. Extract labeled duplicate/non-duplicate events from ground truth tracker
  2. ~10K labeled events (from evaluation runs + production)
  3. Train LightGBM with 5-fold CV
  4. Save model to /models/lightgbm/crs003/version={ts}.txt
  5. Hot reload (no pipeline restart)

Memory: ~20 MB
Training time: ~30 seconds on CPU
```

---

## 5. XGBoost (Gradient Boosting — Scaffolded)

### 5.1 Current Status

XGBoost is **scaffolded but not trained** in the current codebase:

```python
# From streamdq/ml/threshold_predictor.py (lines 63-64):
self.model = mlflow.xgboost.load_model(model_uri)
```

The `MLThresholdPredictor` class is designed to load XGBoost from MLflow, but:
1. No training pipeline exists
2. No model is registered in MLflow
3. The `predict_threshold()` method uses fallback to rule-based thresholds

### 5.2 Inference Latency Analysis

**XGBoost has similar latency to LightGBM — sub-millisecond per prediction.**

```
XGBoost inference (single prediction, CPU):
  ├── Tree traversal: ~30 trees × depth ~6 = ~180 node visits
  ├── Feature lookups: ~30
  └── Total: ~0.1-0.3ms

Comparison:
  XGBoost: ~0.3ms per prediction
  LightGBM: ~0.2ms per prediction
  Both: easily embedded, no gRPC needed
```

### 5.3 Serving Architecture: Embedded + MLflow

**Recommended: Embedded with MLflow model registry for lifecycle management**

```
┌─────────────────────────────────────────────────────────────┐
│  MLflow Model Registry (centralized model store)            │
│  URI: models:/threshold_predictor/production                │
│                                                             │
│  MLThresholdPredictor:                                       │
│    def __init__(self, model_uri):                          │
│        self.model = mlflow.xgboost.load_model(model_uri)   │
│                                                             │
│    def predict_threshold(self, event, context) -> float:   │
│        features = self._extract_features(event)            │
│        return self.model.predict([features])[0]             │
│                                                             │
│  Hot reload:                                                │
│    - MLflow promotes new model to "production" stage       │
│    - MLThresholdPredictor polls every 5 minutes             │
│    - reload_model() called → new model loaded atomically  │
│                                                             │
│  Fallback: rule-based threshold (zero-risk)                 │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 Integration with AdaptiveThresholdEngine

```
Current flow (AdaptiveThresholdEngine, rules/adaptive.py):
  threshold = P90(stats) × k_multiplier

With MLThresholdPredictor:
  base_threshold = P90(stats) × k_multiplier
  ml_threshold = predictor.predict_threshold(event, context, fallback=base_threshold)
  threshold = ml_threshold if enabled else base_threshold

This keeps ML as calibration ON TOP of rules, not replacement:
  - ML learns from context (hour, zone, historical stats)
  - Rules provide hard bounds and interpretability
  - Fallback ensures rules always fire
```

### 5.5 Model Versioning

```
MLflow model registry handles versioning:
  - Stage: "None" → "Staging" → "Production" → "Archived"
  - Version: auto-incremented per upload
  - Current URI: "models:/threshold_predictor/production"

Violation metadata includes: xgboost_model_version (from MLflow)

BroadcastState includes: threshold_predictor_version
```

### 5.6 Fallback Behavior

```
Built into MLThresholdPredictor (threshold_predictor.py lines 114-136):

def predict_threshold(self, event, context, fallback_threshold):
    if not self.enabled:
        return fallback_threshold  # ML not loaded → rule-only
    
    try:
        predicted = self.model.predict([features])[0]
        # Sanity check
        if predicted < 0 or predicted > 500:
            return fallback_threshold  # Extreme prediction → rule-only
        return predicted
    except Exception as e:
        logger.warning(f"ML inference error: {e}, using fallback")
        return fallback_threshold  # Any error → rule-only
```

**Three layers of fallback:**
1. ML service not loaded → use rule-based threshold
2. ML loaded but returns extreme value → use rule-based threshold
3. ML throws exception → use rule-based threshold

**Zero risk: rules always fire regardless of ML state.**

### 5.7 Retraining Pipeline

```
Frequency: Daily
Trigger: Cron job + scheduled MLflow run

Retraining pipeline:
  1. Extract training data: PostgreSQL context_statistics + violation history
  2. Features: hour, day_of_week, zone_cat, rolling_P90, etc. (18 features)
  3. Target: optimal threshold from historical evaluation
  4. Train: XGBoost with 5-fold CV
  5. Register in MLflow: mlflow.xgboost.log_model()
  6. Promote to "staging", validate, promote to "production"
  7. Hot reload: MLThresholdPredictor polls production URI

Training time: ~2-5 minutes on CPU
Memory: ~100 MB for training data
```

### 5.8 Memory Footprint

```
XGBoost model (threshold prediction):
  - ~50 trees, depth 6: ~500 KB
  - Feature importance cache: ~10 KB
  - MLflow client: ~20 MB
  - Total: ~21 MB

MLThresholdPredictor embedded in Python rule process:
  - Additional: ~21 MB per process
  - 4 Flink TM processes: ~84 MB total distributed
```

---

## 6. Comparative Analysis

### 6.1 Latency Summary

| Model | Per-Event Latency | Streaming Budget | Status |
|-------|-------------------|------------------|--------|
| **XGBoost** | ~0.3ms | 50ms | Embedded: **fits trivially** |
| **LightGBM** | ~0.2ms | 50ms | Embedded: **fits trivially** |
| **IsolationForest** | ~2ms (gRPC) | 50ms | gRPC: **fits with margin** |
| **Bayesian Optimization** | N/A (hourly job) | N/A | Background: **no constraint** |
| **LSTM** | ~15ms (GPU) | 50ms | **EXCEEDS budget** — batch only |

### 6.2 Serving Mode Recommendation

| Model | Serving Mode | Justification |
|-------|-------------|---------------|
| **XGBoost** | Embedded + MLflow | Sub-ms inference, needs model registry, hot reload |
| **LightGBM** | Embedded | Sub-ms inference, no network overhead needed |
| **IsolationForest** | gRPC service | 100 per-zone models, shared across pipeline |
| **Bayesian Optimization** | Standalone microservice | Hourly job, no streaming path |
| **LSTM** | Batch pre-filter + gRPC | Per-event: too slow. Batch: acceptable. |

### 6.3 Throughput Summary

| Model | Per-Instance Throughput | Required | Headroom |
|-------|------------------------|----------|----------|
| **XGBoost** | ~100K events/sec | ~1K | 100x |
| **LightGBM** | ~100K events/sec | ~1K | 100x |
| **IsolationForest** | ~10K events/sec | ~1K | 10x |
| **LSTM (batch)** | ~1.2K sequences/sec | ~25 | 48x |
| **Bayesian Optimization** | 1 run/hour | 1 | 1x (but background) |

### 6.4 Memory Footprint Summary

| Model | Memory per Instance | Notes |
|-------|---------------------|-------|
| **XGBoost** | ~21 MB | Model + MLflow client |
| **LightGBM** | ~30 MB | Model + feature cache |
| **IsolationForest** | ~180 MB | 100 zone/time models + gRPC |
| **Bayesian Optimization** | ~110 MB | Calibration job, stateless |
| **LSTM (GPU)** | ~602 MB | PyTorch + CUDA runtime |

---

## 7. Minimum Viable ML Serving Architecture

### 7.1 Core Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│  STREAMDQ ML SERVING ARCHITECTURE — PHASE 1                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  FLINK PIPELINE (Local or Distributed)                       │  │
│  │                                                               │  │
│  │  Event → Parsing → Adaptive Thresholds → Rules → Violations  │  │
│  │                 ↑                                              │  │
│  │     XGBoost embedded (0.3ms) + LightGBM embedded (0.2ms)     │  │
│  │                                                               │  │
│  └────────────────────────────┬──────────────────────────────────┘  │
│                                │                                     │
│         ┌──────────────────────┼──────────────────────┐             │
│         │                      │                       │             │
│         ▼                      ▼                       ▼             │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐ │
│  │ IF Service  │    │  BO Service      │    │  LSTM Batch Service │ │
│  │ (gRPC, P50051)│  │  (REST, P50052) │    │  (gRPC, P50053)    │ │
│  │              │    │                  │    │  (batch pre-filter)│ │
│  │ sklearn IF   │    │ skopt GP        │    │  PyTorch LSTM      │ │
│  │ 100 models   │    │ Hourly job      │    │  GPU batch        │ │
│  │ ~180 MB      │    │ ~110 MB         │    │  ~602 MB (GPU)    │ │
│  └─────────────┘    └──────────────────┘    └─────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  MLflow Model Registry                                        │  │
│  │  models:/threshold_predictor/production                        │  │
│  │  → XGBoost hot-reload via MLThresholdPredictor polling        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL                                                   │  │
│  │  - context_statistics (rolling P10/P90 per context cell)     │  │
│  │  - calibration_history (BO params per run)                   │  │
│  │  - violations (rule evaluation results)                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Service Inventory

| Service | Language | Framework | Port | Replicas | Autoscaling |
|---------|----------|-----------|------|----------|-------------|
| IF Service | Python | gRPC + grpcio | 50051 | 2 | CPU > 70% |
| BO Service | Python | FastAPI + uvicorn | 50052 | 1 | None (hourly) |
| LSTM Batch | Python | gRPC + PyTorch GPU | 50053 | 1 | None (batch) |
| MLflow | — | MLflow server | 50054 | 1 | None |
| XGBoost | Python | Embedded (no service) | — | — | — |
| LightGBM | Python | Embedded (no service) | — | — | — |

### 7.3 Failure Handling Matrix

| Failure | IF | BO | LSTM | XGBoost | LightGBM |
|---------|----|----|-----|---------|----------|
| Service DOWN | Circuit breaker, fallback score=0.0 | BroadcastState keeps last params | Cache miss, Haversine only | N/A (embedded) | N/A (embedded) |
| Timeout > 50ms | Fallback score=0.0 | N/A | Batch delayed, proceed | N/A | N/A |
| Model corrupt | Refuse start | Use defaults | Cache miss | Use fallback | Use fallback |
| NaN prediction | Score=0.5 (neutral) | N/A | Cache miss | Use fallback | Use fallback |
| Invalid features | Score=0.5 | N/A | Skip batch item | Use fallback | Use fallback |

---

## 8. Questions Answered

### Q1: Which models can meet the ~50ms latency budget?

| Model | Meets Budget? | Notes |
|-------|--------------|-------|
| **XGBoost** | ✅ YES (0.3ms) | Embedded, 165x margin |
| **LightGBM** | ✅ YES (0.2ms) | Embedded, 250x margin |
| **IsolationForest** | ✅ YES (2ms) | gRPC, 25x margin |
| **Bayesian Optimization** | ✅ N/A | Hourly background job |
| **LSTM** | ❌ NO (15ms median, P99 ~40ms) | **Must use batch pre-filter** |

**LSTM must be redesigned as a batch pre-filter, not inline scorer.**

### Q2: Which models need separate service vs. can be embedded?

| Model | Embedded | Separate Service | Reasoning |
|-------|----------|-----------------|-----------|
| **XGBoost** | ✅ YES | Optional (MLflow) | Sub-ms, hot-reload via polling |
| **LightGBM** | ✅ YES | Optional | Sub-ms, no shared state needed |
| **IsolationForest** | ❌ NO | ✅ YES (gRPC) | 100 per-zone models, shared across TMs |
| **Bayesian Optimization** | ❌ NO | ✅ YES (REST) | Hourly background job, stateless |
| **LSTM** | ❌ NO | ✅ YES (gRPC, batch) | GPU required, batch pre-filter |

### Q3: What is the minimum viable ML serving architecture?

```
MINIMAL (Phase 1 — rules-only + IF gRPC):
  1. IF gRPC service (Python, port 50051) — 2 replicas
  2. MLflow server (port 50054) — for XGBoost model registry
  3. XGBoost embedded in AdaptiveThresholdEngine
  4. BO and LSTM: NOT in Phase 1 (add later)

RECOMMENDED (Phase 2 — full ML):
  Add BO service (port 50052) and LSTM batch service (port 50053)
```

### Q4: How to handle ML service failures without blocking the pipeline?

**Three-layer defense:**

```
Layer 1 — Graceful degradation (ML never blocks rules):
  Every ML call has fallback: score=0.0 or rule-only behavior
  Rules ALWAYS fire — ML only adjusts threshold, never blocks

Layer 2 — Circuit breaker:
  After N consecutive failures (N=3, configurable):
    → Open circuit for T seconds (T=30, configurable)
    → All ML calls return fallback immediately
    → No network timeout waiting
    → Health check every 5s to detect recovery

Layer 3 — Dead letter queue + alerting:
  Events that hit circuit breaker → DLQ
  Alert sent: "ML service degraded for {model} in {environment}"
  PagerDuty/Slack notification
  On-call responds within 15 minutes
```

**Key invariant**: Violations are ALWAYS emitted. ML is calibration metadata on violations, not a gatekeeper.

---

## 9. Implementation Recommendations

### 9.1 Phase 1: Inline ML (Weeks 13-14)

1. **IsolationForest gRPC service** (Python, sklearn, port 50051)
   - 100 per-zone/time models
   - Hot reload via symlink polling
   - Circuit breaker: 3 failures → 30s open
   - Fallback: `anomaly_score = 0.0`

2. **XGBoost embedded** (MLflow model registry)
   - `MLThresholdPredictor` class with hot reload
   - Polls MLflow production URI every 5 minutes
   - Fallback: rule-based threshold

3. **LightGBM embedded** (CRS003 confidence scoring)
   - Inline in `evaluate_duplicate_event()`
   - Fallback: `confidence = 0.5` (neutral)

### 9.2 Phase 2: Background ML (Week 15)

1. **Bayesian Optimization service** (FastAPI, port 50052)
   - Hourly calibration via cron or Flink timer
   - Outputs to PostgreSQL + BroadcastState update
   - No streaming path — zero latency impact

### 9.3 Phase 3: LSTM Redesign (Week 14, concurrent)

1. **LSTM batch pre-filter** (PyTorch GPU, port 50053)
   - Batch collector: 100 events OR 1 second
   - Background gRPC batch call
   - Results stored in per-vehicle keyed state
   - CRS002 reads from cache (no inline latency)
   - Fallback: Haversine only (no LSTM flag)

### 9.4 Infrastructure Requirements

| Resource | Phase 1 | Phase 2 | Phase 3 |
|----------|---------|---------|---------|
| IF service (VM) | 2 × 2 vCPU, 4 GB RAM | — | — |
| BO service (VM) | — | 1 × 2 vCPU, 2 GB RAM | — |
| LSTM service (GPU) | — | — | 1 × T4 GPU, 8 GB VRAM, 4 vCPU, 16 GB RAM |
| MLflow server (VM) | 1 × 2 vCPU, 4 GB RAM | — | — |
| PostgreSQL | Shared | Shared | Shared |

**Total additional infrastructure**: ~3 VMs + 1 GPU instance.

---

## 10. Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong | Correct Approach |
|-------------|---------------|-----------------|
| LSTM inline per-event | P99 ~40-50ms exceeds budget, blocks pipeline | Batch pre-filter with cache |
| IF embedded in Flink Python process | 100 models = 180 MB RAM per TM; GIL contention | Separate gRPC service |
| BO on streaming path | No latency constraint (hourly job) | Standalone microservice |
| ML as gatekeeper | Rules must always fire | ML as calibration metadata only |
| Hardcoded fallback 0.5 | Different rules need different defaults | Per-model configurable fallback |
| No circuit breaker | Cascading failures under load | Circuit breaker + health checks |
| Model versioning in-memory only | Lost on restart | Symlink + BroadcastState + MLflow |

---

## Appendix A: Latency Measurement Protocol

To validate these estimates, run the following benchmark:

```python
# IF latency benchmark
import time
import numpy as np
from sklearn.ensemble import IsolationForest

model = IsolationForest(n_estimators=100, max_samples=256)
model.fit(np.random.randn(10000, 8))

features = np.random.randn(1, 8).astype(np.float32)

# Warmup
for _ in range(100):
    model.score_samples(features)

# Measure
n = 1000
times = []
for _ in range(n):
    start = time.perf_counter()
    model.score_samples(features)
    times.append((time.perf_counter() - start) * 1000)

times.sort()
print(f"P50: {times[n//2]:.3f}ms")
print(f"P99: {times[int(n*0.99)]:.3f}ms")
print(f"Max: {max(times):.3f}ms")
```

Expected results: P50 ~0.5ms, P99 ~1.2ms (in-process, no network).

For gRPC benchmarks, use `grpcio-tools` load test with `python -m grpcio_tools.protos`.

---

## Appendix B: Model Artifact Locations

```
/models/
├── if/
│   ├── zone_cat={airport,downtown,midtown,outer,other}/
│   │   └── time_cat={morning,midday,afternoon,evening,night,early}/
│   │       ├── latest → version_20260424_100000/
│   │       └── version_20260424_100000/
│   │           └── if_model.joblib
├── lstm/
│   ├── latest → version_20260424_000000/
│   └── version_20260424_000000/
│       ├── model.pt
│       ├── normalizer.json
│       └── config.json
├── lightgbm/
│   ├── crs003/
│   │   ├── latest → version_20260424_000000/
│   │   └── version_20260424_000000/
│   │       └── lgb_model.txt
└── xgboost/
    └── (managed by MLflow model registry)
        └── models:/threshold_predictor/production
```

---

*Document classification*: **Tier 2 (Estimated)** — all latency numbers are pre-benchmark estimates. The LSTM redesign recommendation is **Tier 1 (Verified)** based on architectural analysis. Validate all latency estimates with the benchmark protocol in Appendix A before production deployment.
