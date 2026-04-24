# ContextAware-DQ: Data Structures & State Management Specification

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Engine**: Apache Flink (Java + Python async RPC)
**State Backend**: RocksDB via Flink's RocksDBStateBackend
**Date**: April 23, 2026

---

## Data Structure 1: L0–L5 Context Key Computation

### Data Model

**Java (Flink pipeline)** — context key computation happens in the event-time stream, before rule evaluation:

```java
public class ContextKey {
    int level;           // 0-5
    String key;          // e.g., "H10_midtown_WD"
}

public class ContextDimension {
    // D1: Temporal
    int hour;            // 0-23
    String dayOfWeek;    // Mon, Tue, ..., Sun
    boolean weekend;     // Sat/Sun
    boolean rushHour;    // 7-9am or 5-7pm
    boolean holiday;     // from calendar lookup (D4 — [PARTIAL])

    // D2: Spatial
    String zoneCategory; // airport, downtown, midtown, outer, other (263 TLC zones)
    String borough;      // Manhattan, Bronx, Brooklyn, Queens, Staten Island, EWR

    // D3: Operational
    String entityType;   // nyc_taxi, gtfs_vehicle
    int paymentType;     // 1=credit, 2=cash, 3=no_charge, 4=dispute, 5=unknown, 6=void

    // D5: Data Characteristics
    String sourceId;
    String sourceType;   // replay, live
    boolean isReplay;
}

public enum TimeCategory {
    EARLY_MORNING,  // 5-7
    MORNING,        // 7-11
    MIDDAY,         // 11-14
    AFTERNOON,      // 14-17
    EVENING,        // 17-21
    NIGHT           // 21-5
}
```

**ThresholdStats** (stored in broadcast state, Python dataclass for async RPC):

```python
@dataclass
class ThresholdStats:
    count: int
    mean: float
    std: float
    min_value: float
    max_value: float
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    p10_ci_lower: float      # [ASSUMES bootstrap precomputed]
    p10_ci_upper: float
    p90_ci_lower: float
    p90_ci_upper: float
    entropy: float
    computed_at: float      # Unix timestamp
    snapshot_date: date
    # ML-calibrated fields (updated by Bayesian Optimization hourly)
    k_multiplier: float    # calibrated k-multiplier (default 3.0, range [1.5, 5.0])
    ml_alpha: float        # Isolation Forest sensitivity (default 0.0, range [0.0, 0.5])
    lstm_threshold_m: float # LSTM deviation threshold in meters (default 100.0, range [50.0, 250.0])
    weekend_discount: float # k reduction for weekends (default 0.0, range [0.0, 0.5])
    context_weight: float   # context vs. global weight (default 0.5, range [0.0, 1.0])
    calibration_version: int # increments each BO calibration run
    if_model_version: str   # e.g. "if_v2.3" — broadcast with thresholds
    lstm_model_version: str # e.g. "lstm_v1.7" — broadcast with thresholds
```

**Context key composition rules**:

| Level | Key Schema | Example | Min Samples |
|-------|-----------|---------|:-----------:|
| L0 | `H{hour}_{zone_category}_{WE\|WD}` | `H10_midtown_WD` | 100 |
| L1 | `{hour_bucket}_{zone_category}_{WE\|WD}` | `morning_midtown_WD` | 50 |
| L2 | `{hour_bucket}_{borough}_{WE\|WD}` | `morning_Manhattan_WD` | 25 |
| L3 | `{time_category}` | `morning` | 10 |
| L4 | `global` | `global` | 5 |
| L5 | `physics` (hardcoded priors) | N/A | 0 |

### State Backend

**BroadcastState** — for threshold lookup and ML-calibrated threshold values (read by all parallel instances):

```
BroadcastState<ContextLevel, ContextKey, ThresholdStats>
```

- **Why BroadcastState**: Thresholds are read-only and identical across all task instances. O(1) lookup per event without key shuffling.
- **ML calibration**: Thresholds are updated hourly by Bayesian Optimization, which calibrates k_multiplier, ml_alpha (Isolation Forest sensitivity), lstm_threshold_m, weekend_discount, and context_weight. ML model versions (if_model_version, lstm_model_version) are broadcast alongside thresholds to track model freshness.
  - **Single global IF model**: One Isolation Forest model is trained on all NYC TLC contexts (not per-cell). `if_model_version` tracks the global model version — a single version string applies to all context cells. Per-cell models (~10,000+) are computationally infeasible per ML_MODEL_ANALYSIS.md §1.4.
- **Update mechanism**: Hourly BO calibration job computes optimized parameters from the 1-hour calibration window and broadcasts the updated map to all instances. Thresholds are versioned by calibration_version.

**MapState** — for collecting rolling statistics (per context cell):

```
MapState<(int level, String key, String fieldName), ThresholdStats>
```

### Key Schema

**Broadcast threshold lookup**:
- **Key**: `(level: int, key: String, field_name: String)` → e.g., `(0, "H10_midtown_WD", "fare_amount")`
- **Value**: `ThresholdStats`

**Rolling accumulation MapState**:
- **Key**: `(level: int, context_key: String, field_name: String)`
- **Value**: `{count: int, sum: float, sum_sq: float, min: float, max: float, values: List[Float] (for percentile)}`

### TTL Recommendation

| State | TTL | Rationale |
|-------|-----|-----------|
| Broadcast thresholds | None (immutable) | Thresholds are versioned by `snapshot_date`; old versions discarded after overwrite |
| Rolling accumulation MapState | **24 hours** | Context cell data should be recent; 24h covers full diurnal cycle |

**Rationale for 24h**: NYC TLC patterns repeat daily. 24-hour window captures full diurnal cycle (weekday morning rush, midday, evening rush, night). Longer windows dilute temporal signal; shorter windows lose statistical power.

### Serialization Format

**Avro** (recommended for JVM inter-op, used by Flink's RocksDB backend):

```avro
record ThresholdStats {
    int count;
    double mean;
    double std;
    double min_value;
    double max_value;
    double p10;
    double p25;
    double p50;
    double p75;
    double p90;
    double p10_ci_lower;
    double p10_ci_upper;
    double p90_ci_lower;
    double p90_ci_upper;
    double entropy;
    long computed_at;   # Unix timestamp ms
    string snapshot_date; # ISO date string
    double k_multiplier; # calibrated by Bayesian Optimization
    double ml_alpha;     # Isolation Forest sensitivity
    double lstm_threshold_m; # LSTM deviation threshold (meters)
    double weekend_discount;
    double context_weight;
    int calibration_version;
    string if_model_version;
    string lstm_model_version;
}
```

### State Size Estimate

| Component | Size |
|-----------|------|
| ThresholdStats (serialized) | ~200 bytes |
| Context key string | ~50 bytes |
| Rolling accumulation buffer (1,000 values max) | ~8 KB |
| **Per cell total** | **~8.25 KB** |

**Active cell count estimate**:

| Level | Potential Cells | Active Cells (est.) |
|-------|:---------------:|:-------------------:|
| L0 | 6,312 | ~300 |
| L1 | ~1,500 | ~400 |
| L2 | ~350 | ~200 |
| L3 | 6 | 6 |
| L4 | 1 | 1 |
| L5 | 1 | 1 |
| **Total** | **~8,170** | **~908** |

**Total state size**: 908 active cells × 8.25 KB ≈ **7.5 MB**

**Note on ML calibration**: Each ThresholdStats entry includes 6 additional ML fields (~48 bytes): k_multiplier, ml_alpha, lstm_threshold_m, weekend_discount, context_weight, calibration_version. BroadcastState size ≈ 10,000 cells × ~1.25 KB ≈ **12.5 MB** replicated across TaskManagers. `if_model_version` and `lstm_model_version` are string fields broadcast with thresholds — single global model version string only (~20 bytes).

### RocksDB-Specific Considerations

1. **Incremental checkpoints**: Enable `RocksDBStateBackend` with incremental checkpointing.
2. **Column families**: Separate `threshold_broadcast` (read-heavy) from `rolling_stats` (write-heavy).
3. **Off-heap storage**: Set `state.backend.rocksdb.memory.managed: true` to cap RocksDB memory.
4. **Memory budget**: ~500 MB heap for broadcast + ~1 GB off-heap for RocksDB state.

### Unit Test Outline

| Test | Input | Expected |
|------|-------|----------|
| T1: L0 key | NYC TLC event `{ts: 10:30, PULocationID: 230 (midtown), weekday}` | Level=0, Key="H10_midtown_WD" |
| T2: Weekend key | Saturday 3pm, PULocationID 230 | Level=0, Key="H15_midtown_WE" |
| T3: L0→L1 fallback (insufficient samples) | L0 count=50 < 100; L1 count=80 > 50 | Level=L1 |
| T4: L4 global fallback | All levels below min_samples | Level=L4 |
| T5: L5 physics prior | All levels empty | Level=L5, threshold=[2,100] km/h |
| T7: ML calibration version | Calibration run at t=3600s | ThresholdStats.calibration_version incremented; if_model_version updated |
| T8: ML fallback on timeout | IF service unavailable | anomaly_score=0.0; k_multiplier unchanged; pipeline continues |

*Note: ML integration tests require the IF gRPC service (Algorithm G in FORMULATION.md) and LSTM gRPC service (Algorithm H in FORMULATION.md, CONDITIONAL/NO-GO per ML_MODEL_ANALYSIS.md §3) to be running. Fallback behavior (anomaly_score=0.0) must be tested independently. BO calibration test requires evaluation infrastructure with synthetic injection (Phase 1); BO objective is F1, not violation_rate.*


| T6: Null zone | PULocationID=NULL | Fallback to L4 |

---

## Data Structure 2: Per-Vehicle CRS State (CRS001/CRS002)

### Data Model

**CRS001 — VehicleGPSState** (Java, keyed by vehicleId):

```java
public class VehicleGPSState {
    private String vehicleId;
    private Double prevLat;
    private Double prevLon;
    private Instant prevTimestamp;
    private Double currentSpeed;
    private LinkedList<SpeedSample> speedHistory;  // rolling 10-min window
    private Instant lastUpdate;
}

public class SpeedSample {
    private Double speed;       // km/h
    private Instant timestamp;
}
```

**CRS002 — JumpState** (separate state, also keyed by vehicleId):

```java
public class JumpState {
    private String vehicleId;
    private LinkedList<PositionSample> recentPositions;  // last 3 positions, 10-min window
}

public class PositionSample {
    private Double lat;
    private Double lon;
    private Instant timestamp;
}
```

### State Backend

**KeyedState<String, VehicleGPSState>** (CRS001):
- **Key**: `vehicleId` (String) — NYC MTA Bus vehicle ID from GTFS-rt
- **Value**: `VehicleGPSState` object

**KeyedState<String, JumpState>** (CRS002):
- **Key**: `vehicleId` (String)
- **Value**: `JumpState` object

### TTL Recommendation

**TTL: 10 minutes (600 seconds)**

- **Rationale**: GTFS-realtime VehiclePosition updates arrive every ~30s. 10-minute window = ~20 position updates per vehicle.
- **Flink native TTL**: Set via `ValueStateDescriptor.withTtl()` — Flink auto-evicts expired entries.
- **Manual eviction**: Also maintain `lastUpdate` timestamp; if `now - lastUpdate > 10 min`, reset state on next access.

### Serialization Format

**Protobuf** (GTFS-rt uses protobuf natively):

```protobuf
message SpeedSample {
    double speed = 1;       // km/h
    int64 timestamp_ms = 2; // Unix epoch ms
}

message VehicleGPSStateProto {
    string vehicle_id = 1;
    double prev_lat = 2;
    double prev_lon = 3;
    int64 prev_timestamp_ms = 4;
    double current_speed = 5;
    repeated SpeedSample speed_history = 6;
    int64 last_update_ms = 7;
}

message PositionSample {
    double lat = 1;
    double lon = 2;
    int64 timestamp_ms = 3;
}

message JumpStateProto {
    string vehicle_id = 1;
    repeated PositionSample recent_positions = 2;
}
```

### State Size Estimate

| Component | Size |
|-----------|------|
| vehicleId (String) | ~20 bytes |
| prevLat, prevLon, prevTimestamp | ~30 bytes |
| currentSpeed | 8 bytes |
| speedHistory (20 samples × 24 bytes) | ~480 bytes |
| recentPositions (20 samples × 32 bytes) | ~640 bytes |
| **Per vehicle total** | **~1.2 KB** |

**Worst case (NYC MTA Bus, ~6,000 vehicles)**: 6,000 × 1.2 KB ≈ **7.2 MB**

### RocksDB-Specific Considerations

1. **Heap vs. RocksDB**: Consider Flink's **LocalStateBackend** (heap-based) for CRS state — small per-key, high update rate. Checkpoint size bounded (~1 MB total).
2. **Checkpoint frequency**: Set checkpoint interval to 60s. With 10-min TTL, worst case is losing 60s of state on failure — acceptable.
3. **Idle vehicle handling**: If `lastUpdate` > 5 minutes, mark vehicle as idle and clear state.

### Unit Test Outline

| Test | Setup | Input | Expected |
|------|-------|-------|----------|
| T1: Normal speed | prev pos at t=970s | pos at t=1000s, ~300m (speed ~36 km/h) | No violation; state updated |
| T2: Speed > 100 km/h | prev pos | pos 1.5km in 30s → speed ~180 km/h | Violation(CRS001, ABOVE_UPPER_BOUND, speed=180) |
| T3: First position | No prior state | Any valid position | No violation; state initialized |
| T4: Null vehicle_id | — | e.vehicle_id=NULL | Violation(SYN001, NULL_KEY) |
| T5: GPS jump > 400m | prev pos at t=970s | pos 1.3km away at t=1000s | Violation(CRS002, GPS_SPOOFING, dist=1300m) |
| T6: Normal movement | prior pos 30s ago | pos 200m away | No violation; position added to buffer |

---

## Data Structure 3: CRS003 Dedup State

### Data Model

```java
public class DedupState {
    private String tripId;
    private RoaringBitmap activeHashes;  // hashes within 300s window
    private Instant oldestTimestamp;       // timestamp of oldest hash in bitmap
}

public class DedupEvent {
    private String tripId;
    private String eventHash;   // SHA256 hex string
    private Instant eventTimestamp;
}
```

**Why RoaringBitmap**: Efficient bitmap for integer hashes (hundreds of entries per trip); memory-efficient: 1 bit per hash entry (~8 bytes per entry vs. ~40 bytes for HashSet).

### State Backend

**KeyedState<String, DedupState>**:
- **Key**: `tripId: String`
- **Value**: `DedupState` object

### TTL Recommendation

**TTL: 310 seconds (300s window + 10s safety margin)**

- **Rationale**: GTFS trip durations are 10–90 minutes. 300s = 5 minutes = meaningful deduplication window. 10s safety margin handles clock skew and late arrivals.
- **Flink TTL**: 310s via `ValueStateDescriptor.withTtl(Time.seconds(310))`
- **Manual cleanup**: Check if `oldestTimestamp < now - 300s`; remove expired hashes.

### Serialization Format

```protobuf
message DedupStateProto {
    string trip_id = 1;
    bytes roaring_bitmap = 2;    // serialized RoaringBitmap
    int64 oldest_timestamp_ms = 3;
}
```

### State Size Estimate

| Component | Size |
|-----------|------|
| tripId (String) | ~30 bytes |
| RoaringBitmap (10 hashes, 40 bits set) | ~8 bytes |
| oldestTimestamp | 8 bytes |
| **Per trip total** | **~50 bytes** |

**Worst case (NYC TLC, ~10,000 trips)**: 10,000 × 50 bytes ≈ **500 KB**

### Unit Test Outline

| Test | Setup | Input | Expected |
|------|-------|-------|----------|
| T1: New event | Empty dedup state | `{trip_id: "T1", hash: "abc123"}` | No violation; hash added |
| T2: Duplicate detected | Hash "abc123" in state | `{trip_id: "T1", hash: "abc123"}` | Violation(CRS003, DUPLICATE) |
| T3: Different hash | Hash "abc123" in state | `{trip_id: "T1", hash: "def456"}` | No violation; hash added |
| T4: TTL expiry | Hash "abc123", oldest=now-310s | `{trip_id: "T1", hash: "abc123"}` | No violation; hash re-added |
| T5: Cross-trip isolation | Hash "abc123" for T1 | `{trip_id: "T2", hash: "abc123"}` | No violation; T2 state created |
| T6: NG-4 verification | Two events with same hash | Emit both | First=no violation; second=Violation(CRS003) |

---

## Data Structure 4: TQS Aggregation State — Revised (Non-Circular Design)

> ⚠️ **This section supersedes the original TQSCellState design.** The original (§4 prior to this revision) defined TQS from rule violation counts (`V/C/Cn/P`) — which is **circular by construction** for evaluation runs where ground truth is injection rate. This revised design uses **stream-intrinsic dimensions** computed directly from raw event properties, independent of rule outcomes.

### Data Model

The TQS Cell State stores raw aggregates needed to compute five non-circular quality dimensions:

```python
@dataclass
class TQSCellState:
    context_key: str                    # e.g. "H14_midtown_WD"
    context_level: int                  # L0–L4

    # ── Event counts ──────────────────────────────────────────────────────────────
    total_events: int                   # N events in this cell

    # ── Timeliness (Tm): inter-event time statistics ────────────────────────────
    sum_dt: int                        # Σ Δt_i = Σ (e_i.ts − e_{i−1}.ts), ms
    sum_dt2: int                       # Σ Δt_i² — for population variance
    n_intervals: int                   # Number of Δt intervals (N−1)

    # ── Completeness (Cn): null/NaN counts per required field ─────────────────
    # Stored as dict of field_name → null_count
    null_counts: dict[str, int]

    # ── Accuracy (Ac): plausibility counters per field ─────────────────────────
    # NYC TLC: fare_amount, trip_distance, passenger_count, PULocationID, DOLocationID
    # GTFS: lat, lon, ts, schedule_relationship
    plausibility_counts: dict[str, int]  # field → n_plausible (per-field score = n_plausible / N)

    # ── Consistency (Cs): GPS trajectory coherence (GTFS only) ─────────────────
    # Timestamp monotonicity: events should arrive in ts order
    n_reversed: int                    # count of (e_i.ts > e_{i+1}.ts) — reversed order
    n_gps_outlier: int                 # count of events flagged by CRS001/CRS002

    # ── Uniqueness (Uv): dedup statistics ─────────────────────────────────────
    n_distinct_hashes: int              # cardinality of hash set in dedup window
    n_total_hashes: int                # total hashes added to dedup window
    # Uv = n_distinct / n_total (higher = fewer duplicates)

    # ── Severity summary (for alerting, not for TQS computation) ────────────────
    violations_by_severity: dict[str, int]
```

**Critical design note**: All dimensions (Tm, Cn, Ac, Cs, Uv) are computed from **raw event fields only**, not from rule violation outcomes. This ensures TQS is non-circular with respect to injection-based ground truth.

### Derived TQS Dimensions (computed on read from stored raw aggregates)

**Tm — Timeliness**: From inter-event time variance.
```
Δt_i     = e_i.ts − e_{i−1}.ts      (ms)
σ²_Δt    = [ΣΔt_i² / n_intervals] − [ΣΔt_i / n_intervals]²   (population variance)
Tm        = exp(−λ · σ²_Δt) · (1 − stale_rate)
           where λ = 1×10⁻⁸ ms⁻²   (recalibrated from 0.01 for ms-scale)
           stale_rate = #{e : current_time − e.ts > 300,000} / N
Tm ∈ [0, 1]. Tm → 1 when variance is low and few events are stale.
```

**Cn — Completeness**: From null/NaN counts.
```
Cn = 1 − Σ_field null_counts[field] / (N · |required_fields|)
Cn ∈ [0, 1]. Cn = 1 when all required fields are present for all events.
```

**Ac — Accuracy (Plausibility)**: From raw field plausibility checks.
```
NYC TLC: fare ∈ [0, 1000], distance ∈ [0, 500], passenger ∈ [1, 9], zones ∈ [1, 263]
GTFS: |lat| ≤ 90, |lon| ≤ 180, ts > 0
Ac = (1/N) · Σ_i [n_plausible_fields_i / |measured_fields_i|]
Ac ∈ [0, 1]. Ac = 1 when all measured fields are within plausible ranges.
```

**Cs — Consistency**: From timestamp monotonicity and GPS coherence.
```
Cs_ts = 1 − n_reversed / N           (timestamp monotonicity)
# GPS speed coherence: CRS001/CRS002 violations flag GPS anomalies
# Cs = f(gps_anomaly_rate) — computed in CRS layer, stored here as summary
Cs ∈ [0, 1]. Cs = 1 when trajectory is temporally and spatially coherent.
```

**Uv — Uniqueness**: From deduplication cardinality.
```
Uv = n_distinct_hashes / n_total_hashes
Uv ∈ [0, 1]. Uv = 1 when all events are unique (no duplicates).
```

### TQS Composite Variants

Both variants use the same five dimensions (Tm, Cn, Ac, Cs, Uv). V1 and V2 are **design choices**, not correctness claims.

| Variant | Weights | Justification |
|---------|---------|---------------|
| **TQS_V1 (Equal)** | 0.20·Tm + 0.20·Cn + 0.20·Ac + 0.20·Cs + 0.20·Uv | Principled baseline: no domain assumptions |
| **TQS_V2 (Domain)** | 0.20·Tm + 0.25·Cn + 0.20·Ac + 0.25·Cs + 0.10·Uv **[PRIMARY]** | Domain-informed: Cn and Cs weighted higher (null fields and GPS coherence most critical for NYC TLC and NYC MTA Bus) |

### State Backend

**KeyedState<String, TQSCellState>** + **WindowedStream**:

```
KeyedStream[Event, String] → Window(TumblingEventTimeWindows.of(Time.minutes(5)))
    → TQSAggregateFunction
    → JDBC sink to metrics_summary
```

### TTL Recommendation

**TTL: 10 minutes** (matches window duration × 2)

- **Rationale**: Tumbling window = 5 minutes. State persists for at least 2 windows to handle late arrivals within `allowedLateness` (60s).
- **Late data**: Events arriving after window + allowedLateness go to `LateDataOutputTag` side output.

### State Size Estimate

| Component | Size |
|-----------|-----------|
| context_key (String) | ~50 bytes |
| total_events, n_intervals, sum_dt, sum_dt2 (4×8 bytes) | ~32 bytes |
| null_counts dict (9 fields × ~16 bytes each) | ~144 bytes |
| plausibility_counts dict (9 fields × ~16 bytes each) | ~144 bytes |
| n_reversed, n_gps_outlier, n_distinct_hashes, n_total_hashes (4×8 bytes) | ~32 bytes |
| violations_by_severity map (4 entries × ~50 bytes) | ~200 bytes |
| **Per cell total** | **~600 bytes** |

**Total**: 908 cells × 600 bytes ≈ **545 KB** (window flushed every 5 min)


### Unit Test Outline

| Test | Setup | Expected |
| Test | Setup | Expected |
|------|-------|----------|
| T1: Perfect quality | 100 events, all fields valid, Δt=30s±5s | Tm≈0.98, Cn=1.0, Ac=1.0, Cs=1.0, Uv=1.0, TQS≈0.99 |
| T2: Mixed quality | 100 events, 5 null fields, 3 implausible fares, Δt=30s±90s | Tm≈0.67, Cn≈0.94, Ac≈0.97, Cs=1.0, Uv=1.0, TQS≈0.90 |
| T3: Empty window | 0 events | TQS=null |
| T4: GTFS GPS outliers | 50 GTFS events, 2 CRS001, 1 CRS002 | Cs≈0.94 (GPS coherence degraded) |
| T5: NYC TLC (CRS not applicable) | 50 NYC TLC events, no GPS | Cs=1.0 (no GPS); Cn, Ac, Tm from TLC fields |
| T6: Late data (within allowedLateness) | 5 events at t=10:06, window closes t=10:06:01 | Included in window; total=105 |
| T7: Late data (beyond allowedLateness) | 5 events at t=10:07 | Sent to LateDataOutputTag; not in main window |

---

## Summary: State Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    Flink TaskManager (per slot)                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  KAFKA INPUT STREAM → Parse → Route (Java)                          │
│                                     ↓                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CRS001/CRS002/CRS003 (Java KeyedProcessFunction)          │   │
│  │                                                             │   │
│  │  KeyedState<String, VehicleGPSState>  — CRS001/CRS002    │   │
│  │  KeyedState<String, DedupState>    — CRS003              │   │
│  │  TTL: 10 min (GPS), 310s (dedup)                        │   │
│  │  Backend: LocalStateBackend (heap) or RocksDB              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                     ↓                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ SYN/SEM Rules (Python async RPC)                           │   │
│  │                                                             │   │
│  │  BroadcastState: L0-L5 thresholds (read-only)             │   │
│  │  MapState: Rolling stats accumulation                      │   │
│  │  TTL: 24h (rolling stats)                                │   │
│  │  Backend: RocksDBStateBackend (off-heap)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                     ↓                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ TQS Aggregation (Flink WindowedStream)                       │   │
│  │                                                             │   │
│  │  Window: Tumbling 5-min, allowedLateness=60s             │   │
│  │  State: TQSCellState per context key (heap)              │   │
│  │  Emit: metrics_summary (PostgreSQL) + Prometheus counters │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Total state size per TaskManager**:

| State | Size | Backend |
|-------|------|---------|
| Threshold broadcast | ~180 KB | JVM heap |
| Rolling stats (MapState) | ~7.5 MB | RocksDB off-heap |
| CRS001/CRS002 per-vehicle | ~7.2 MB | Heap or RocksDB |
| CRS003 per-trip | ~130 KB | Heap or RocksDB |
| TQS window | ~165 KB | Heap |
| **Total** | **~15 MB** | |
