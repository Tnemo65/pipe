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

**BroadcastState** — for threshold lookup (read by all parallel instances):

```
BroadcastState<ContextLevel, ContextKey, ThresholdStats>
```

- **Why BroadcastState**: Thresholds are read-only and identical across all task instances. O(1) lookup per event without key shuffling.
- **Update mechanism**: Periodic background job (every 1h) computes new thresholds from `context_statistics` PostgreSQL table and broadcasts the updated map to all instances.

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
| T5: L5 physics prior | All levels empty | Level=L5, threshold=[2,120] km/h |
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
| T2: Speed > 120 km/h | prev pos | pos 1.5km in 30s → speed ~180 km/h | Violation(CRS001, ABOVE_UPPER_BOUND, speed=180) |
| T3: First position | No prior state | Any valid position | No violation; state initialized |
| T4: Null vehicle_id | — | e.vehicle_id=NULL | Violation(SYN001, NULL_KEY) |
| T5: GPS jump > 100m | prev pos at t=970s | pos 1.3km away at t=1000s | Violation(CRS002, GPS_SPOOFING, dist=1300m) |
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
| T6: B2 verification | Two events with same hash | Emit both | First=no violation; second=Violation(CRS003) |

---

## Data Structure 4: TQS Aggregation State

### Data Model

```python
@dataclass
class TQSCellState:
    context_key: str
    context_level: int              # L0–L4
    total_events: int
    syn001_violations: int
    syn002_violations: int
    syn003_violations: int
    crs001_violations: int
    crs002_violations: int
    crs003_violations: int
    sem001_violations: int
    sem002_violations: int
    sem003_violations: int
    violations_by_severity: dict[str, int]
```

**Derived TQS components** (computed on read):

| Component | Formula |
|-----------|---------|
| V (Validity) | `1 - (syn001 + syn002) / total` |
| C (Consistency) | `1 - (crs001 + crs002) / total` (GTFS only) |
| Cn (Completeness) | `1 - sem003 / total` |
| P (Plausibility) | `1 - (sem001 + sem002) / total` |
| TQS_V1 (Equal) | `0.25×V + 0.25×C + 0.25×Cn + 0.25×P` |
| TQS_V2 (Domain) | `0.40×V + 0.20×C + 0.30×Cn + 0.10×P` **[PRIMARY]** |
| TQS_V3 (Consist) | `0.20×V + 0.35×C + 0.25×Cn + 0.20×P` |

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
|-----------|------|
| context_key (String) | ~50 bytes |
| 9 rule violation counters | ~36 bytes |
| violations_by_severity map (4 entries) | ~100 bytes |
| **Per cell total** | **~200 bytes** |

**Total**: 908 cells × 200 bytes ≈ **180 KB** (window flushed every 5 min)

### Unit Test Outline

| Test | Setup | Expected |
|------|-------|----------|
| T1: Perfect quality | 100 events, 0 violations | TQS=1.0 |
| T2: Mixed violations | 100 events, 5 SYN001, 3 SYN002, 2 CRS001 | V=0.92; TQS_V2≈0.964 |
| T3: Empty window | 0 events | TQS=null |
| T4: GTFS (CRS applicable) | 50 GTFS events, 2 CRS001, 1 CRS002 | C=0.94 |
| T5: NYC TLC (CRS not applicable) | 50 NYC TLC events | C=1.0 (always) |
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
