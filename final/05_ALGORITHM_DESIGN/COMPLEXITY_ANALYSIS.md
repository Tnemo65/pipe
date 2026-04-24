# Algorithm Complexity & Statistical Analysis

**Project**: ContextAware-DQ — A Context-Aware Framework for Streaming Data Quality Monitoring
**Engine**: Apache Flink (Java + Python async RPC)
**Reviewer Role**: Statistical Analysis Specialist
**Date**: April 23, 2026
**Sources**: `final/03_IDEA_SELECTION/report.md`; `final/04_NOVELTY_CONTRIBUTION/SIGNIFICANCE_TABLE.md`

---

## Key Questions — Direct Answers

**Q1: L0-L5 lookup — O(1) or O(k)?**
O(1) amortized. Flink `BroadcastState` is a hash-map with O(1) lookup per key. The worst-case is 6 sequential lookups (L0 through L5) but the algorithm short-circuits on the first hit, so average cost is 1 lookup. The fallback chain is a **conditional sequence**, not a loop — cost is deterministic given context sparsity. ~0–5% of events hit L0, ~20–40% fall to L4 global, meaning most events require 1–4 lookups before success or L5 fallback.

**Q2: CRS state update — O(1) amortized?**
Yes. Keyed state (RocksDB-backed) provides O(1) average lookup by `vehicleId`/`tripId`. State updates touch only fixed-size structures (buffer ≤ 3 positions, history ≤ 20 speeds). No per-event allocation, no GC pressure in the Java hot path.

**Q3: TQS aggregation — per-event vs. window-based?**
Hybrid. **Per-event**: increment counters (total, per-rule violations) — O(1). **Window emission**: triggered every 5 minutes — O(1) arithmetic over pre-aggregated counters. The heavy lifting is the **rolling P10/P90** for SEM001/SEM002, which requires stateful window aggregation of all values in the window.

**Q4: Rolling P10/P90 convergence — minimum samples?**
Stable estimate: **~50 samples** (P10/P90 converge at O(1/√n); trustworthy estimate: **~100–200 samples** (halves the standard error of the percentile). Below 30 samples, percentile estimates are unreliable (sparse order statistics). Default 1-hour window at 1,000 events/sec = 3.6M samples, well into the stable regime. At low-throughput context cells, convergence may take hours.

**Q5: Broadcast state update from ML calibration?**
Periodic (every 1 hour), off the event-processing critical path. The ML layer runs as a **background task**, not inline. It writes updated threshold values to BroadcastState via the `BroadcastChannel` API. Update cost: O(k) where k = number of changed context cells per hour. With 6,312 potential L0 cells and hourly recalibration, worst-case is O(6,312) keys written — a batch operation, not per-event.

---

## Algorithm A: L0–L5 Context Key Computation

### Time Complexity

| Operation | Complexity | Notes |
|-----------|:----------:|-------|
| Extract 5D context fields | O(1) | 5 field reads; no parsing (fields already in event) |
| Compute L0 key string | O(1) | String interpolation of 3 values (hour, zone_category, weekend flag) |
| BroadcastState lookup (L0) | O(1) | HashMap lookup in Flink BroadcastState |
| Fallback L1–L4 | O(1) each | Conditional sequence, short-circuits on first hit |
| L5 physics prior | O(1) | No lookup; return hardcoded `[2, 100]` km/h or similar |
| **Per-event (all paths)** | **O(1)** | **Short-circuits; bounded by ≤6 sequential O(1) lookups** |

### Space Complexity

| Component | Complexity | Notes |
|-----------|:----------:|-------|
| Per-event context key | O(1) | ~50 bytes: 5D key string + fields |
| Broadcast state (L0–L4 thresholds) | O(U₁ + U₂ + U₃ + U₄) | Uₗ = number of unique context keys at level l |
| Broadcast state size | O(T × D) | T threshold values per cell × D fields (fare_amount, trip_distance) |
| Max L0 cells | ~6,312 | 263 zones × 24 hours (NYC TLC); actual active cells far fewer |
| Broadcast state total | ~100 KB–10 MB | Depends on active context cells; RocksDB-backed, spills to disk |

Broadcast state is **replicated to all TaskManagers** — not partitioned. At scale (10+ operators), this is a memory consideration but not a throughput bottleneck.

### Statistical Properties

| Property | Value | Notes |
|----------|:------:|-------|
| Bias | **Context-dependent** | P10/P90 percentiles from rolling stats are biased: P10 underestimated, P90 overestimated (finite window). L5 physics priors are unbiased (hard bounds). |
| Variance | Decreases as 1/n | For violation rate: Var(p̂) = p(1−p)/n. For percentiles: Var(P₁₀) ≈ c₁₀/(n × PDF(F)²) where PDF(F) is the density at the percentile. |
| Convergence | O(1/√n) | P10/P90: ~50 samples for stable estimate, ~100–200 for trustworthy. Violation rates: ~25–100 samples per cell. |
| Min samples | **Level-dependent** | L0: 100 (from power analysis, Cohen's d ≈ 0.30); L1: 50; L2: 25; L3: 10; L4: 5; L5: 0 (physics priors). |
| Min viable output | **Level-dependent** | Violation classification meaningful at L4+ (≥5 samples). TQS decomposition meaningful at ≥100 events per cell. |

### Bottleneck

**Bottleneck**: None in the per-event path. BroadcastState lookups are O(1) hash operations. The actual bottleneck is **context cell sparsity** — most events fall through to L4/L5, meaning the adaptive thresholds are bypassed for 60–80% of events. This is an architectural limitation, not a performance one. The per-event cost is bounded by a small constant (~6 hash lookups maximum), making this suitable for high-throughput streaming.

**Statistical bottleneck**: Rolling P10/P90 statistics (for SEM001/SEM002) require O(n) window state per context cell. At low-traffic cells (L3/L4), convergence takes hours. The adaptive threshold is unreliable until the rolling window fills.

---

## Algorithm B: CRS001 — GPS Speed Bounds

### Time Complexity

| Operation | Complexity | Notes |
|-----------|:----------:|-------|
| Keyed state lookup (vehicleId) | O(1) | RocksDB hash lookup; JVM-native, no Python serialization |
| Haversine distance computation | O(1) | 6 trig operations (sin, cos, atan2, sqrt) + arithmetic; Java Math library |
| Time delta | O(1) | Timestamp subtraction |
| Speed check (bounds ∈ [2, 100]) | O(1) | Two comparisons |
| State update | O(1) | Write prev position, prev timestamp; append to fixed-size speed deque |
| TTL management | O(1) amortized | Flink TTL background cleanup; not on critical path |
| **Per-event** | **O(1)** | **All operations constant-time; no iteration** |

**Haversine formula cost**: ~6 floating-point trig operations. On a modern JVM (JIT-compiled), this is ~50–100 ns per call. At 10,000 events/sec, Haversine costs ~0.5–1 ms/sec — negligible.

### Space Complexity

| Component | Complexity | Notes |
|-----------|:----------:|-------|
| Per-vehicle state | O(1) | prev_lat, prev_lon, prev_timestamp (3 × 8 bytes) + speed_history (≤20 × 8 bytes) ≈ **200 bytes/vehicle** |
| Max active vehicles (10-min window) | ≤ 1,000–5,000 | NYC MTA Bus fleet size; actual active = vehicles with position update in last 10 min |
| Total keyed state | O(V) | V = number of active vehicles × 200 bytes ≈ **200 KB–1 MB** |
| State backend | RocksDB | Spills to SSD; keyed state only in memory when hot |

### Statistical Properties

| Property | Value | Notes |
|----------|:------:|-------|
| Bias | **Zero** | Hard-coded physics bounds `[2, 100]` km/h — no learned parameters. No statistical bias possible. |
| Variance | Binomial | For violation rate: Var(p̂) = p(1−p)/n_per_vehicle. n = number of speed measurements per vehicle. |
| Convergence | O(1/√n) | For speed distribution estimation; single-event violation is deterministic — no convergence needed for flag. |
| Min samples | **1** | A single speed measurement outside `[2, 100]` km/h triggers a violation. No sample-count threshold required. |
| False positive risk | **Low** | `[2, 100]` km/h is well above walking pace (2 km/h) and below highway speed (100 km/h for NYC buses). Urban buses rarely exceed 80 km/h. |

### Bottleneck

**Bottleneck**: `KeyedState` RocksDB I/O for the state lookup/update on every event. With 1,000–5,000 active vehicles and 10-min TTL, state is hot (L1/L2 cache-resident). The Java `KeyedProcessFunction` hot path is JIT-compiled and lock-free. The actual bottleneck is **checkpointing**: every 30s, Flink serializes all keyed state to HDFS/S3 — state size × checkpoint interval determines checkpoint duration. With ~1 MB total keyed state, checkpoint is negligible.

**Known limitation (B3)**: There is a **gap** in the `[2, 100]` km/h range — speeds between 2–20 km/h are not validated. GPS spoofing that keeps speed within this range will not be detected. CRS002 partially covers this gap.

---

## Algorithm C: CRS002 — GPS Jump Detection

### Time Complexity

| Operation | Complexity | Notes |
|-----------|:----------:|-------|
| Keyed state lookup (vehicleId) | O(1) | Same as CRS001; JVM-native |
| Buffer append (current position) | O(1) | Fixed-size ring buffer; append to end, evict oldest |
| Prior-position iteration | O(b) | b = number of positions in buffer; b ≤ 3 (fixed size) |
| Prior-position time filter | O(b) | Check timestamp < 30s; constant per prior position |
| Haversine distance (per prior) | O(1) | Same Haversine as CRS001 |
| Jump threshold check (>400m) | O(1) | Distance comparison |
| Buffer eviction (>10 min) | O(1) | Ring buffer eviction on append; mark-based, not scan-based |
| **Per-event** | **O(1)** | **b is bounded by fixed buffer size (≤3); no unbounded iteration** |

### Space Complexity

| Component | Complexity | Notes |
|-----------|:----------:|-------|
| Per-vehicle buffer | O(b) | b ≤ 3 positions × (lat + lon + timestamp) ≈ **100–150 bytes/vehicle** |
| Buffer structure | Fixed-size ring | No dynamic allocation; pre-allocated array, circular overwrite |
| Total keyed state | O(V) | V = active vehicles × 150 bytes ≈ **150 KB–750 KB** |
| Comparison cost | O(1) | Haversine only called for positions within 30s window (filtered before distance check) |

### Statistical Properties

| Property | Value | Notes |
|----------|:------:|-------|
| Bias | **Zero** | Hard-coded threshold (>400m/30s) — no learned parameters. |
| Variance | Decreases with buffer size | With b=3 positions, 3 comparisons possible per event. Variance in jump detection rate decreases as 1/b. |
| Convergence | **Minimum 2 positions required** | Cannot detect a jump with only 1 position. Buffer fills within 2–3 update intervals (GTFS-RT: every 30s → buffer fills in ≤90s). |
| Min samples | **2 positions in buffer** | First position always passes (no prior to compare). Detection active from event 3 onwards. |
| False negative risk | **Low** | 400m threshold is calibrated (40% of max 1,000m possible in 30s at 100 km/h). Low probability of missing real jumps. |

### Bottleneck

**Bottleneck**: Haversine computation iterated up to 3 times per event (one per buffer slot). This is negligible — 3 × ~100 ns = ~300 ns/event. The ring buffer evicts positions older than 10 min on each append, but this is O(1) mark-based eviction (not a scan).

**Key difference from CRS001**: CRS002 compares positions directly — it does **not** use a rolling speed history. This makes it **more sensitive to immediate GPS jumps** but less robust to single outlier measurements. CRS001 catches sustained speed anomalies; CRS002 catches instantaneous position jumps. Both can fire on the same event — they detect different anomaly signatures.

---

## Algorithm D: CRS003 — Event Deduplication

### Time Complexity

| Operation | Complexity | Notes |
|-----------|:----------:|-------|
| SHA-256 hash computation | O(1) | Hash of trip_id + timestamp + lat + lon. ~20–50 bytes input; SHA-256 is fast. |
| Keyed state lookup (tripId) | O(1) | HashSet/RoaringBitmap lookup per tripId |
| Hash membership check | O(1) | RoaringBitmap: O(1) word lookup. HashSet: O(1) average. |
| Hash insertion (new event) | O(1) | Add to HashSet or RoaringBitmap; set TTL |
| TTL management | O(1) amortized | Flink TTL; lazy eviction on next access |
| **Per-event** | **O(1)** | **All operations are O(1) hash operations** |

**Hash choice note**: SHA-256 is chosen for collision resistance (not performance). For 300s deduplication windows, a faster non-cryptographic hash (MurmurHash3, xxHash) would suffice and is ~10× faster. SHA-256 is defensible for cryptographic integrity but unnecessary for this use case.

### Space Complexity

| Component | Complexity | Notes |
|-----------|:----------:|-------|
| Per-hash entry | O(1) | SHA-256 = 32 bytes; RoaringBitmap word = 8 bytes |
| Per-trip state | O(w × r) | w = events per trip in 300s window; r = hash size. NYC MTA Bus: ~10–60 events/trip. |
| RoaringBitmap vs HashSet | RoaringBitmap wins | Sparse sets: 2–8 bytes/entry vs HashSet's 40–56 bytes/entry. |
| Total keyed state | O(T × w) | T = active trips; w = events per trip in window. NYC MTA Bus: 100 trips × 30 events × 8 bytes ≈ **24 KB** (RoaringBitmap). |
| TTL | 310s | Slightly larger than dedup window (300s) to handle boundary events. |

### Statistical Properties

| Property | Value | Notes |
|----------|:------:|-------|
| Bias | **Potential over-deduplication** | Sliding window: if event arrivals are bursty, duplicates near the window edge may be evicted and re-admitted, creating double-counting. |
| Variance | Depends on arrival process | For Poisson arrivals, expected window occupancy = λ × 300s. Variance = λ × 300s. For bursty traffic (common in GTFS-RT), variance is higher. |
| Convergence | **Immediate for duplicate detection** | A duplicate is detected on its second occurrence — no convergence needed. |
| Min samples | **2 identical hashes within 310s** | Detection requires two events with identical hash. Single events always pass. |
| False negative risk | **Hash collision** | SHA-256 collision probability is negligible (~2⁻²⁵⁶). Practically zero. |

### Bottleneck

**Bottleneck**: State growth if a single trip generates many events in 310s. NYC MTA Bus: typical trip generates 10–60 GTFS-RT positions (at 30s intervals, 5–30 min trip = 10–60 positions). State per trip is bounded. However, if a vehicle is stationary and reporting every 30s, a trip_id persists → state grows unbounded for that trip until TTL eviction.

**Known limitation (NG-4)**: CRS003 evaluation is blocked by the replay suppression gate. Synthetic duplicates are tagged `is_replay=True` by `_enrich_with_lineage()`, which triggers the gate in `evaluate_duplicate_event()` and suppresses violation emission. Additionally: NG-1 (low-confidence suppression) and NG-2 (temporal clustering) reduce recall for low-confidence and repeated duplicates. All three are evaluation bugs, not dedup logic bugs.

**RoaringBitmap vs HashSet**: For high-throughput dedup (1,000+ events/sec per trip), RoaringBitmap is more memory-efficient. For low-throughput, HashSet is simpler. The choice affects memory, not throughput.

---

## Algorithm E: TQS Aggregation

### Time Complexity

| Operation | Complexity | Notes |
|-----------|:----------:|-------|
| **Per-event** | | |
| Counter increment (total) | O(1) | Atomic increment |
| Counter increment (per-rule) | O(1) | HashMap update for SYN001, SYN002, etc. |
| **Per-window (5-min tumbling)** | | |
| TQS sub-metric computation | O(1) | 4 division operations (V, C, Cn, P) |
| TQS composite (weighted sum) | O(1) | 4 multiply-add operations (α, β, γ, δ) |
| Emit to PostgreSQL + Prometheus | O(1) | Batch JDBC write (200 rows/batch, 2s flush) |
| **Rolling P10/P90 (SEM001/SEM002)** | | |
| Value insertion | O(1) | Append to sliding window |
| Percentile computation | O(n) naive; O(1) approximate | Naive: sort/select O(n). Use t-digest or Count-Min Sketch for O(1) approximate. |

TQS is **window-based** (emitted every 5 min), not per-event. The per-event cost is O(1) counter updates. The rolling P10/P90 computation is the exception — it requires O(n) percentile selection if done naively.

### Space Complexity

| Component | Complexity | Notes |
|-----------|:----------:|-------|
| **Window state (per context cell)** | | |
| 5-min window at 1,000 events/sec | O(300,000) events | 5 min × 60 sec × 1,000 events/sec = 300,000 events/cell |
| Event storage (if storing full events) | ~90 MB/cell | Unlikely — counters are sufficient |
| **Counters (recommended)** | | |
| Counter state per cell | O(R) | R = number of rules (9 counters) + total events counter ≈ 10 integers/cell ≈ 80 bytes/cell |
| **Rolling P10/P90 state (SEM001/SEM002)** | | |
| 1-hour rolling window | O(3,600,000) values | 1 hour × 3,600 sec × 1,000 events/sec = 3.6M values |
| Value storage (float64) | ~29 MB/context cell | 3.6M × 8 bytes ≈ 28.8 MB/cell |
| **Total state** | **O(Context cells × window size)** | At high throughput: dominated by rolling P10/P90 windows. At low throughput: negligible. |

### Statistical Properties

| Property | Value | Notes |
|----------|:------:|-------|
| Bias | **Propagates from sub-metrics** | If V, C, Cn, P are unbiased, TQS is unbiased. P10/P90 from rolling window are biased (see Algorithm A). |
| Variance | Decreases with √n_per_window | For violation rate: Var(p̂) = p(1−p)/n. With 300,000 events/5-min window at 1,000 events/sec, variance is very low (SE < 0.2%). |
| Convergence | **O(1/√n_per_window)** | Stable TQS: ~100 events minimum; trustworthy TQS: ≥500 events per window. |
| Min samples for meaningful TQS | **~100 events/window** | Below 100 events, TQS is noisy (random variation dominates signal). |
| TQS weight sensitivity | **High** | V2: α=0.40, β=0.20, γ=0.30, δ=0.10. Changing weights changes TQS by ±0.10 or more. Weights are arbitrary (not learned) — known limitation. |
| Circularity in RQ3 | **Confirmed** | TQS = 1 − violation_rate; injection_rate ∝ violation_rate. Correlation between TQS and injection_rate is guaranteed by design. RQ3 measures experimental self-consistency, not real quality. |

### Bottleneck

**Bottleneck**: **Rolling P10/P90 state storage** — the dominant space consumer. At 1,000 events/sec with 1-hour rolling windows and 100 active context cells: 100 × 29 MB = **2.9 GB** of state. This exceeds JVM heap for most deployments. Mitigation: (1) use approximate percentile structures (t-digest, Count-Min Sketch) reducing state to ~1 MB/cell; (2) reduce rolling window size; (3) limit active context cells.

**Throughput bottleneck**: PostgreSQL JDBC batch writes (batch=200, flush=2s). With 1,000 events/sec and 0.5% violation rate → ~5 violations/sec → 200 rows/flush every 2s → 40 ms/flush. This is within budget. The JDBC connection pool is the limit, not the query speed.

---

## Summary Complexity Table

| Algorithm | Per-Event Time | Space (per-key) | Bottleneck | Min Samples |
|-----------|:--------------:|:---------------:|------------|:-----------:|
| **A: L0–L5 Context Key** | **O(1)** amortized (≤6 lookups, short-circuits) | Broadcast state: O(U₁+U₂+U₃+U₄) threshold cells; ~100 KB–10 MB total | Context cell sparsity (60–80% fall to L4/L5) | L0: 100; L4: 5; L5: 0 |
| **B: CRS001 GPS Speed** | **O(1)** (keyed lookup + Haversine + bounds check) | ~200 bytes/vehicle; ~1 MB total (≤5,000 vehicles) | RocksDB checkpoint serialization (negligible at 1 MB) | 1 (single out-of-bounds event) |
| **C: CRS002 GPS Jump** | **O(1)** (bounded buffer lookup + ≤3 Haversine calls) | ~150 bytes/vehicle; ~750 KB total | Haversine iteration (≤3×100 ns/event = negligible) | 2 positions in buffer |
| **D: CRS003 Dedup** | **O(1)** (SHA-256 + keyed lookup + hash check) | ~8–32 bytes/hash; ~24 KB total (100 trips × 30 events) | RoaringBitmap growth for long trips (TTL=310s) | 2 identical hashes within 310s |
| **E: TQS Aggregation** | **O(1)** per-event (counter increment); O(1) per-window (arithmetic) | ~80 bytes/cell (counters) + ~29 MB/cell (rolling P10/P90) | **Rolling P10/P90 state storage** (2.9 GB at 100 cells × 1,000 events/sec) | 100 events/window (trustworthy: ≥500) |

### Key Findings

1. **All five algorithms are O(1) per-event** — the framework is throughput-scalable. The O(1) guarantee holds because all state accesses are keyed (O(1) hash lookup) and all buffers are fixed-size (no unbounded iteration per event).

2. **Space is the actual bottleneck**, not time:
   - Algorithm E (TQS rolling P10/P90): 29 MB/context cell — the dominant memory consumer
   - Algorithm A (BroadcastState): Replicated to all TaskManagers — scales with operator parallelism
   - Algorithms B, C, D (per-vehicle keyed state): Well-bounded by TTL (10 min) and fixed-size buffers

3. **Statistical convergence is context-dependent**:
   - L0 context cells need ~100 events to stabilize thresholds (minutes at low traffic, seconds at high traffic)
   - CRS rules (B, C, D) need 1–2 measurements — immediate detection
   - TQS needs ≥100 events per 5-min window — reliable within 1–2 windows at moderate throughput

4. **Bias is minimal for CRS rules** (hard-coded physics thresholds) and moderate for SYN/SEM rules (rolling percentiles have known lower/upper bound bias). The L5 physics fallback has zero bias by construction.

5. **Known limitations affecting complexity**:
   - **NG-4 (replay suppression gate)**: Blocks CRS003 recall measurement on replay data — synthetic duplicates must be tagged `is_replay=False`
   - **B3 (CRS002 speed range gap)**: Speeds 2–20 km/h are not validated — CRS002 compensates partially
   - **RQ3 circularity**: TQS is defined as 1 − violation_rate, making TQS–injection_rate correlation guaranteed — not a meaningful RQ
