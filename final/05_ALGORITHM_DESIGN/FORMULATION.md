# Algorithm Design: Mathematical Formulation & Pseudocode

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Phase**: Step 8 — Algorithm Design (Pseudocode + Mathematical Formulation)
**Date**: April 23, 2026
**Lead**: System Architecture Specialist
**Subagent Inputs**: Hypotheses (Subagent 1), Data Structures (Subagent 2), Complexity (Subagent 3), Quality Audit (Subagent 4), Failure Modes (Subagent 5)

---

## Table of Contents

1. [Notation & Definitions](#1-notation--definitions)
2. [Algorithm A: Context Key Computation & L0–L5 Threshold Fallback](#2-algorithm-a-context-key-computation--l0l5-threshold-fallback)
3. [Algorithm B: CRS001 — GPS Speed Bounds](#3-algorithm-b-crs001--gps-speed-bounds)
4. [Algorithm C: CRS002 — GPS Jump Detection](#4-algorithm-c-crs002--gps-jump-detection)
5. [Algorithm D: CRS003 — Event Deduplication](#5-algorithm-d-crs003--event-deduplication)
6. [Algorithm E: TQS Aggregation](#6-algorithm-e-tqs-aggregation)
7. [Algorithm F: SYN/SEM Rule Evaluation (Python RPC)](#7-algorithm-f-synsem-rule-evaluation-python-rpc)
8. [Complete Flink DataStream Operator Graph](#8-complete-flink-datastream-operator-graph)
9. [Algorithm Complexity Summary](#9-algorithm-complexity-summary)
10. [Unit Test Specifications](#10-unit-test-specifications)
11. [Reproducibility & Verification](#11-reproducibility--verification)

---

## 1. Notation & Definitions

### 1.1 Symbol Table

| Symbol | Definition | Type |
|--------|------------|------|
| `e` | A single streaming event (taxi trip or vehicle position) | Record |
| `e.field` | Field `field` of event `e` | Any |
| `e.ts` | Event timestamp (Unix epoch milliseconds) | Integer |
| `e.vehicle_id` | Vehicle or entity identifier | String |
| `e.trip_id` | Trip identifier | String |
| `e.lat`, `e.lon` | Latitude, longitude (WGS84 decimal degrees) | Float |
| `F` | Set of all field names in the schema | Set |
| `violation(e, rule)` | True if event `e` violates `rule` | Boolean |
| `V(e)` | Violation object for event `e` (if any) | Optional[Violation] |
| `T(e, level)` | Threshold value for event `e` at fallback `level` | Float |
| `S(ctx_key, level, field)` | ThresholdStats for `(ctx_key, level, field)` | ThresholdStats |
| `count(S)` | Sample count in ThresholdStats `S` | Integer |
| `p10(S)` | 10th percentile of field values in `S` | Float |
| `p90(S)` | 90th percentile of field values in `S` | Float |
| `μ(S)` | Mean of field values in `S` | Float |
| `σ(S)` | Standard deviation of field values in `S` | Float |
| `haversine(p₁, p₂)` | Great-circle distance in km between positions `p₁` and `p₂` | Float |
| `speed(p₁, p₂)` | Speed = `haversine(p₁, p₂) / (Δt)` in km/h | Float |
| `hash(e)` | Per-dataset: NYC TLC: SHA256(trip_id + ts + PULocationID + DOLocationID); NYC MTA Bus: SHA256(trip_id + ts + lat + lon) | String |
| `TQS` | Trajectory Quality Score (composite, stream-intrinsic) | Float ∈ [0, 1] |
| `Tm` | Timeliness dimension of TQS: `exp(−λ · σ²_Δt) · (1 − stale_rate)` | Float ∈ [0, 1] |
| `Cn` | Completeness dimension of TQS: field null/NaN ratio | Float ∈ [0, 1] |
| `Ac` | Accuracy dimension of TQS: raw field plausibility ranges | Float ∈ [0, 1] |
| `Cs` | Consistency dimension of TQS: GPS coherence, timestamp monotonicity | Float ∈ [0, 1] |
| `Uv` | Uniqueness dimension of TQS: duplicate rate via hash | Float ∈ [0, 1] |
| `ω_i` | TQS composite weights (Tm, Cn, Ac, Cs, Uv) | Float ∈ [0, 1], sum=1 |
| `σ²_Δt` | Population variance of inter-event time deltas (ms) | Float |
| `stale_rate` | Fraction of events older than 300 s relative to current time | Float ∈ [0, 1] |
| `missing_rate` | Fraction of required fields that are null or NaN | Float ∈ [0, 1] |
| `Δt_i` | Inter-event time delta: `e_i.ts − e_{i−1}.ts` (ms) | Integer |

### 1.2 Event Schema

**NYC TLC Taxi Trip**:
```
|e.trip_id        : String   (required)
|e.vehicle_id     : String   (required, medallion number)
|e.ts             : Long     (required, pickup datetime as epoch ms)
|e.passenger_count: Int      (required, [1, 6])
|e.trip_distance  : Float    (required, in miles)
|e.fare_amount    : Float    (required, USD)
|e.PULocationID   : Int      (required, [1, 263])
|e.DOLocationID   : Int      (required, [1, 263])
|e.payment_type   : Int      (required, [1, 5])
```

**NYC MTA Bus VehiclePosition** (GTFS-realtime protobuf):
```
|e.trip_id        : String   (required, GTFS trip_id)
|e.vehicle_id     : String   (required, vehicle label)
|e.ts             : Long     (required, epoch ms from GTFS timestamp)
|e.lat            : Float    (required, WGS84 decimal degrees)
|e.lon            : Float    (required, WGS84 decimal degrees)
|e.schedule_relationship: Enum (SCHEDULED, ADDED, UNSCHEDULED, CANCELED)
```

### 1.3 Rule Reference

| Rule | Type | Dataset | Description | Threshold |
|------|------|---------|-------------|-----------|
| SYN001 | Syntactic | Both | Null/NaN/wrong-type check on required fields | Hard constraint |
| SYN002 | Syntactic | NYC TLC | Fare amount range | Context-adaptive (L0–L4) |
| SYN003 | Syntactic | Both | Location validity (lat/lon bounds, zone IDs) | Hard constraint |
| SEM001 | Semantic | NYC TLC | Fare plausibility vs. rolling P10/P90 | Context-adaptive |
| SEM002 | Semantic | NYC TLC | Trip distance plausibility | Context-adaptive |
| SEM003 | Semantic | Both | Passenger count [1, 6] | Hard constraint |
| GTFSSem002 | Semantic | NYC MTA Bus | Vehicle position stale > 5 min | Hard constraint |
| CRS001 | Cross-Record | NYC MTA Bus | GPS speed [2, 100] km/h | L5 physics prior |
| CRS002 | Cross-Record | NYC MTA Bus | GPS jump >400m / 30s | L5 physics prior |
| CRS003 | Cross-Record | Both | Event deduplication (300s window) | L5 physics prior |

---

## 2. Algorithm A: Context Key Computation & L0–L5 Threshold Fallback

### 2.1 Mathematical Formulation

**Context key function** `ck(e, level)` maps an event to a string key at a given fallback level:

```
ck(e, L0) = f"H{e.hour:02d}_{zone_category(e)}_{weekend_indicator(e)}"
          = f"H{10}_{midtown}_{WD}"         # example: H10_midtown_WD

ck(e, L1) = f"{hour_bucket(e)}_{zone_category(e)}_{weekend_indicator(e)}"
          = f"morning_midtown_WD"             # hour_bucket ∈ {early, morning, midday, afternoon, evening, night}

ck(e, L2) = f"{hour_bucket(e)}_{borough(e)}_{weekend_indicator(e)}"
          = f"morning_Manhattan_WD"

ck(e, L3) = f"{time_category(e)}"
          = f"morning"

ck(e, L4) = "global"

ck(e, L5) = "physics"
```

**Zone category mapping** `zone_category(e)`:
```
zone_category(e) ∈ {airport, downtown, midtown, outer, other}
# Derived from PULocationID → zone lookup table
# airport: JFK, LaGuardia, Newark (PULocationID ∈ {1, 132, 138})
# downtown: Manhattan below 14th St (PULocationID ∈ lookup table)
# midtown: Manhattan 14th–59th St (PULocationID ∈ lookup table)
# outer: outer boroughs
# other: EWR, unknown
```

**Threshold retrieval function** `get_threshold(e, field)`:

```
FUNCTION get_threshold(e: Event, field: String) → (threshold: Float, level: Integer, stats: ThresholdStats)

FOR level IN [L0, L1, L2, L3, L4]:
    key = ck(e, level)
    stats = broadcast_state.get(level, key, field)   # O(1) lookup
    IF stats ≠ null AND count(stats) ≥ min_samples(level):
        RETURN (compute_threshold(stats, field), level, stats)
    ELSE:
        CONTINUE   # fall through to next level

# L5: Physics prior — no data required
RETURN (physics_prior(field), L5, null)

WHERE:
    min_samples(L0) = 100   # power analysis: Cohen's d=0.30, α=0.01, power=0.80
    min_samples(L1) = 50    # conservative bound for medium-traffic zones
    min_samples(L2) = 25    # borough-level aggregation minimum
    min_samples(L3) = 10   # time category minimum
    min_samples(L4) = 5     # global fallback minimum
    min_samples(L5) = 0    # physics prior — no data required
```

**Adaptive threshold computation** (for fields using rolling statistics):

```
# For SYN002 (fare_amount), SEM001 (fare_amount rolling), SEM002 (trip_distance rolling):
compute_threshold(stats, "fare_amount"):
    RETURN p90(stats)        # SYN002: violation if fare > p90

compute_threshold(stats, "trip_distance"):
    RETURN (p10(stats), p90(stats))   # SEM002: violation if trip_distance < p10 or > p90

# For rolling P10/P90 (SEM001):
threshold_k = μ(stats) + k * σ(stats)
# where k is calibrated by Bayesian Optimization per context cell
# [ASSUMES] default k = 3.0, range [1.5, 5.0]
```

### 2.2 Pseudocode: Context Key Computation

```
ALGORITHM A: compute_context_and_threshold(e: Event) → (ck: String, level: Int, threshold: Any, stats: ThresholdStats)

INPUT:  e — raw event record
OUTPUT: (ck, level, threshold, stats)

BEGIN
    # ── Guard: Event-level sanity check ──────────────────────────────────────
    IF e IS NULL:
        RETURN ("global", L4, null, null)   # Fall through to global

    # ── Step 1: Extract temporal context ─────────────────────────────────────
    hour           ← extract_hour(e.ts)                          # 0–23
    weekday        ← extract_weekday(e.ts)                      # Mon–Sun
    weekend        ← (weekday ∈ {Saturday, Sunday})
    rush_hour      ← (hour ∈ {7,8,9, 16,17,18,19})             # [ASSUMES]
    holiday        ← holiday_lookup(e.ts)                       # [PARTIAL — I16]
    time_category  ← bucket_to_time_category(hour)             # 6 categories

    # ── Step 2: Extract spatial context ───────────────────────────────────────
    zone           ← e.PULocationID IF e IS NYC_TAXI ELSE null
    zone_cat       ← zone_lookup(zone).category IF zone ≠ null ELSE "other"
    borough        ← zone_lookup(zone).borough IF zone ≠ null ELSE "unknown"

    # ── Step 3: Extract operational context ─────────────────────────────────────
    entity_type    ← e.entity_type   # "nyc_taxi" or "gtfs_vehicle"
    payment_type   ← e.payment_type IF entity_type = "nyc_taxi" ELSE null

    # ── Step 4: Extract data characteristics ────────────────────────────────────
    source_id      ← e.source_id     # "nyc_taxi_replay" or "gtfs_mta_bus"
    source_type    ← e.source_type   # "replay" or "live"
    is_replay      ← (source_type = "replay")

    # ── Step 5: L0–L4 fallback loop ──────────────────────────────────────────
    FOR level IN [L0, L1, L2, L3, L4]:
        SELECT level:
            L0: ck ← f"H{hour:02d}_{zone_cat}_{IF weekend THEN 'WE' ELSE 'WD'}"
            L1: ck ← f"{time_category}_{zone_cat}_{IF weekend THEN 'WE' ELSE 'WD'}"
            L2: ck ← f"{time_category}_{borough}_{IF weekend THEN 'WE' ELSE 'WD'}"
            L3: ck ← time_category
            L4: ck ← "global"

        stats ← broadcast_state.get(level, ck, target_field)
        IF stats ≠ null AND stats.count ≥ MIN_SAMPLES[level]:
            threshold ← compute_threshold(stats, target_field)
            RETURN (ck, level, threshold, stats)

    # ── Step 6: L5 physics prior ─────────────────────────────────────────────
    RETURN ("physics", L5, PHYSICS_PRIOR[target_field], null)

END
```

### 2.3 Physics Priors (L5 — Hardcoded, No Data Required)

| Rule | Field | L5 Lower | L5 Upper | Justification |
|------|-------|:--------:|:--------:|---------------|
| SYN002 | fare_amount | 0 | ∞ | Non-negative fare [REQUIRES BENCHMARK for upper bound] |
| CRS001 | GPS speed | 2 km/h | 100 km/h | Below 2 km/h = stationary; above 100 km/h = physically implausible for NYC MTA Bus (speed limit + safety margin); updated from 120 km/h to close B3 detection gap for moderate spoofing (20–100 km/h) |
| SEM002 | trip_distance | 0 | ∞ | Non-negative [REQUIRES BENCHMARK for upper bound] |
| CRS002 | GPS jump | 0 | 400 m/30s | >400m in 30s = GPS jump (99th-percentile displacement at ~45 km/h mean NYC MTA Bus urban speed; covers traffic 20–65 km/h) |
| CRS003 | dedup window | — | 300 s | Trip durations 10–90 min; 300s = meaningful dedup window |

---

## 3. Algorithm B: CRS001 — GPS Speed Bounds

### 3.1 Mathematical Formulation

**Haversine distance**:

```
haversine(p₁, p₂) =
    2 · R · arcsin ( √{ sin²((φ₂−φ₁)/2) + cos(φ₁) · cos(φ₂) · sin²((λ₂−λ₁)/2) } )

WHERE:
    φ₁, φ₂ = latitudes of p₁, p₂ in radians
    λ₁, λ₂ = longitudes of p₁, p₂ in radians
    R = 6,371 km (Earth mean radius)
```

**Speed computation**:

```
speed(p₁, t₁, p₂, t₂) =
    IF t₂ = t₁: return VIOLATION(CRS002, "ZERO_TIME_DELTA")   # divide-by-zero → GPS jump
    ELSE: return haversine(p₁, p₂) / |t₂ − t₁| × 3,600,000   # km/h
```

**Violation condition**:

```
violates_CRS001(e) ⇔
    speed IS DEFINED AND (speed < 2.0 OR speed > 100.0)
```

### 3.2 Pseudocode: CRS001

```
ALGORITHM B: evaluate_CRS001(e: Event, state: VehicleGPSState) → Optional[Violation]

INPUT:  e — GTFS VehiclePosition event
        state — per-vehicle GPS state (keyed by vehicle_id)
OUTPUT: Violation object if speed bound violated, null otherwise

BEGIN
    # ── Guard: SYN-level checks before GPS check ─────────────────────────────
    IF e.vehicle_id IS NULL:
        RETURN Violation(rule=CRS001, reason=NULL_KEY)

    IF e.lat IS NULL OR e.lon IS NULL:
        RETURN Violation(rule=SYN001, reason=NULL_FIELD, field="lat_or_lon")

    IF e.lat IS NaN OR e.lon IS NaN:
        RETURN Violation(rule=SYN001, reason=NAN_FIELD, field="lat_or_lon")

    IF e.lat ∉ [−90, 90] OR e.lon ∉ [−180, 180]:
        RETURN Violation(rule=SYN003, reason=OUT_OF_BOUNDS, field="lat_or_lon")

    IF e.ts IS NULL:
        RETURN Violation(rule=SYN001, reason=NULL_TIMESTAMP)

    # ── Step 1: Retrieve per-vehicle state ────────────────────────────────────
    prev ← state.get(e.vehicle_id)   # KeyedState lookup, O(1)

    IF prev IS NULL:
        # First position for this vehicle — initialize state, no violation possible
        state.put(e.vehicle_id, VehicleGPSState(
            vehicle_id       = e.vehicle_id,
            prev_lat         = e.lat,
            prev_lon         = e.lon,
            prev_timestamp   = e.ts,
            speed_history    = EmptyLinkedList(),
            last_update     = e.ts
        ))
        RETURN null   # First position — no baseline to compare

    # ── Step 2: Compute Haversine distance ─────────────────────────────────────
    p₁ ← Position(prev.prev_lat, prev.prev_lon)
    p₂ ← Position(e.lat, e.lon)
    dist_km ← haversine(p₁, p₂)

    time_delta_ms ← |e.ts − prev.prev_timestamp|
    time_delta_h  ← time_delta_ms / 3,600,000

    # ── Step 3: Handle zero time delta (CRS002 trigger) ────────────────────────
    IF time_delta_ms = 0:
        # Same-timestamp positions → GPS jump check (CRS002)
            IF dist_km × 1000 > 400:   # 400 meters in >0 seconds
            RETURN Violation(
                rule   = CRS002,
                type   = GPS_SPOOFING,
                reason = ZERO_TIME_DELTA,
                dist_m = dist_km × 1000,
                details = {prev_pos: p₁, curr_pos: p₂}
            )
        ELSE:
            # Same position at same time → ignore, update timestamp only
            prev.prev_timestamp ← e.ts
            prev.last_update    ← e.ts
            state.put(e.vehicle_id, prev)
            RETURN null

    # ── Step 4: Compute speed ──────────────────────────────────────────────────
    speed_kmh ← dist_km / time_delta_h

    # ── Step 5: Check speed bounds ─────────────────────────────────────────────
    # Consumer GPS error (±3-5m) produces apparent speeds of 0.3-1.2 km/h
    # between two stationary fixes 30s apart. We set lower bound at 0.5 km/h
    # with a 60s sustained-violation requirement to avoid false positives
    # from GPS jitter at red-light stops and bus stop dwells.
    IF speed_kmh < 0.5 AND time_delta_ms > 60000:
        # Sustained low speed — possible stuck GPS or vehicle off-route
        RETURN Violation(
            rule   = CRS001,
            type   = IMPOSSIBLE_SPEED,
            reason = SUSTAINED_LOW_SPEED,
            speed  = speed_kmh,
            bounds = [0.5, 100.0],
            details = {dist_m: dist_km × 1000, time_delta_ms: time_delta_ms}
        )
    END IF

    IF speed_kmh > 100.0:
        RETURN Violation(
            rule   = CRS001,
            type   = IMPOSSIBLE_SPEED,
            reason = ABOVE_UPPER_BOUND,
            speed  = speed_kmh,
            bounds = [0.5, 100.0],
            details = {dist_m: dist_km × 1000, time_delta_ms: time_delta_ms}
        )
    END IF

    # ── Step 6: Update state ────────────────────────────────────────────────────
    # Add speed to rolling history (10-min window)
    prev.speed_history.add(SpeedSample(speed_kmh, e.ts))
    prev ← evict_old_samples(prev.speed_history, window_ms = 600_000)   # 10 min
    prev.prev_lat      ← e.lat
    prev.prev_lon      ← e.lon
    prev.prev_timestamp ← e.ts
    prev.last_update   ← e.ts

    state.put(e.vehicle_id, prev)
    RETURN null   # Valid speed — no violation

END
```

---

## 4. Algorithm C: CRS002 — GPS Jump Detection

### 4.1 Mathematical Formulation

**Jump condition**:

```
violates_CRS002(e) ⇔ ∃p ∈ recent_positions(e.vehicle_id) SUCH THAT
    |e.ts − p.ts| ≤ 30,000 ms   # within 30-second window
    AND haversine(e.pos, p.pos) > 0.4 km   # > 400 meters
```

### 4.2 Pseudocode: CRS002

```
ALGORITHM C: evaluate_CRS002(e: Event, state: JumpState) → Optional[Violation]

INPUT:  e — GTFS VehiclePosition event
        state — per-vehicle jump state (keyed by vehicle_id)
OUTPUT: Violation object if GPS jump detected, null otherwise

BEGIN
    # ── Guards (SYN-level) ────────────────────────────────────────────────────
    IF e.lat IS NULL OR e.lon IS NULL:
        RETURN Violation(rule=SYN001, reason=NULL_FIELD, field="position")
    IF e.lat IS NaN OR e.lon IS NaN:
        RETURN Violation(rule=SYN001, reason=NAN_FIELD, field="position")
    IF e.ts IS NULL:
        RETURN Violation(rule=SYN001, reason=NULL_TIMESTAMP)

    # ── Step 1: Retrieve per-vehicle jump state ───────────────────────────────
    jstate ← state.get(e.vehicle_id)
    IF jstate IS NULL:
        jstate ← JumpState(vehicle_id = e.vehicle_id, recent_positions = EmptyList())
        state.put(e.vehicle_id, jstate)

    # ── Step 2: Evict positions older than 10 minutes ────────────────────────
    cutoff ← e.ts − 600_000   # 10 minutes in ms
    jstate.recent_positions ← FILTER pos IN jstate.recent_positions WHERE pos.timestamp ≥ cutoff

    # ── Step 3: Check for GPS jump against all recent positions ────────────────
    FOR pos IN jstate.recent_positions:
        IF |e.ts − pos.timestamp| ≤ 30_000:   # within 30-second window
            dist_km ← haversine(Position(e.lat, e.lon), Position(pos.lat, pos.lon))
            IF dist_km > 0.4:   # > 400 meters
                RETURN Violation(
                    rule     = CRS002,
                    type     = GPS_SPOOFING,
                    reason   = GPS_JUMP,
                    dist_m   = dist_km × 1000,
                    time_delta_s = |e.ts − pos.timestamp| / 1000.0,
                    details  = {
                        prev_pos: {lat: pos.lat, lon: pos.lon, ts: pos.timestamp},
                        curr_pos: {lat: e.lat, lon: e.lon, ts: e.ts}
                    }
                )

    # ── Step 4: Add current position to buffer ────────────────────────────────
    # Keep last 3 positions (covers 90s window at 30s intervals; minimum 3 positions
    # needed for triangle inequality jump detection. At 1Hz data, K=3 covers 3s.)
    # ⚠ If GTFS update interval >60s, this buffer may be insufficient — add frequency check.
    jstate.recent_positions.add(PositionSample(e.lat, e.lon, e.ts))
    IF SIZE(jstate.recent_positions) > 3:
        REMOVE oldest position from jstate.recent_positions

    state.put(e.vehicle_id, jstate)
    RETURN null   # No jump detected

END
```

---

## 5. Algorithm D: CRS003 — Event Deduplication

### 5.1 Mathematical Formulation

**Event hash** (per-dataset, see Algorithm D pseudocode for conditional logic):

```
# NYC TLC (no GPS — zone-level deduplication):
hash(e) = SHA256( CONCAT( e.trip_id, STR(e.ts),
    STR(e.PULocationID), STR(e.DOLocationID) ) )

# NYC MTA Bus GTFS-realtime (has GPS):
hash(e) = SHA256( CONCAT( e.trip_id, STR(e.ts),
    STR(e.lat), STR(e.lon) ) )
```

violates_CRS003(e) ⇔ hash(e) ∈ dedup_state.get(e.trip_id)

### 5.2 Pseudocode: CRS003

```
ALGORITHM D: evaluate_CRS003(e: Event, state: DedupState) → Optional[Violation]

INPUT:  e — event (NYC TLC or GTFS vehicle)
        state — per-trip dedup state (keyed by trip_id)
OUTPUT: Violation object if duplicate detected, null otherwise

BEGIN
    # ── Guard: trip_id must exist ─────────────────────────────────────────────
    IF e.trip_id IS NULL OR e.trip_id = "":
        RETURN Violation(rule=SYN001, reason=NULL_FIELD, field="trip_id")

    # ── Step 1: Compute event hash (per-dataset) ──────────────────────────────────
    IF e.lat IS NOT NULL AND e.lon IS NOT NULL:
        # NYC MTA Bus GTFS-realtime — hash includes GPS coordinates
        hash_val ← SHA256( CONCAT( STR(e.trip_id), "|", STR(e.ts), "|",
                                   STR(e.lat), "|", STR(e.lon) ) )
    ELSE:
        # NYC TLC — zone-level dedup (no lat/lon); include PULocationID + DOLocationID
        hash_val ← SHA256( CONCAT( STR(e.trip_id), "|", STR(e.ts), "|",
                                   STR(e.PULocationID), "|", STR(e.DOLocationID) ) )

    # ── Step 2: Retrieve per-trip dedup state ──────────────────────────────────
    dedup ← state.get(e.trip_id)   # RoaringBitmap or HashSet
    IF dedup IS NULL:
        dedup ← RoaringBitmap()    # Empty bitmap

    # ── Step 3: Check for duplicate ──────────────────────────────────────────
    IF dedup.contains(hash_val):
        RETURN Violation(
            rule     = CRS003,
            type     = DUPLICATE,
            reason   = HASH_MATCH,
            hash     = hash_val,
            trip_id  = e.trip_id,
            entity_id = e.vehicle_id
        )

    # ── Step 4: Add hash to state ─────────────────────────────────────────────
    dedup.add(hash_val)
    state.put(e.trip_id, dedup)   # TTL = 310s managed by Flink StateTtlConfig

    RETURN null   # Not a duplicate

END
```

**[BOUNDARY CASE]**: Duplicate arriving after 310s TTL expiry is NOT detected. This is a false negative — acknowledged limitation. GTFS trip durations are typically 10–90 minutes; a 300s window may miss inter-trip duplicates.

**[OPEN — NG-4]**: CRS003 evaluation on NYC TLC replay data is blocked by the replay suppression gate. Synthetic duplicate events are tagged `is_replay=True` by `_enrich_with_lineage()`, which triggers the gate in `evaluate_duplicate_event()` and suppresses violation emission. Fix: synthetic duplicates must be tagged `is_replay=False` to bypass the gate. Additionally: (a) NG-1: When confidence ≤ 0.4, the code stores the hash in dedup state but emits no violation — ground truth tracker never sees it; recall silently drops for low-confidence duplicates. (b) NG-2: Post-first-detection duplicates within the temporal clustering window are suppressed by the cluster mechanism — reduces recall for repeated duplicates. All three are evaluation measurement bugs, not deduplication logic bugs.

---

## 6. Algorithm E: TQS Aggregation — Revised Design

### 6.0 Why the Original Design Was Circular

The original TQS design defined:

```
V_score  = 1 − (n_syn001 + n_syn002) / N          # Validity
C_score  = 1 − (n_crs001 + n_crs002) / N          # Consistency
Cn_score = 1 − n_sem003 / N                        # Completeness
P_score  = 1 − (n_sem001 + n_sem002) / N           # Plausibility
TQS      = α·V + β·C + γ·Cn + δ·P
```

**This is circular by construction.** The ground truth in evaluation runs is the **injection rate** (0%, 5%, 10%, 20%). Injected anomalies are designed to trigger SYN/CRS/SEM violations. Therefore:

```
injection_rate ∝ violation_rate   (by experimental design)
TQS = 1 − violation_rate
∴ TQS ∝ injection_rate            (guaranteed by design, not by evidence)
```

A PC reviewer will immediately observe that TQS is trivially correlated with injection rate because TQS is defined as `1 − violation_rate` and violations are generated from injected anomalies. This is **self-referential**: the evaluation uses the same signal to define ground truth and to measure quality.

**The fix**: TQS must measure quality from **independent signals** — properties of the raw event stream that can be computed without reference to injection, but that are affected by the same anomalies that trigger violations. If high-quality events produce good TQS scores and anomalous events produce degraded TQS scores, then TQS is a meaningful quality metric independent of the rule engine.

---

### 6.1 New TQS Design: Stream-Intrinsic Quality Dimensions

We redesign TQS around **five stream-intrinsic dimensions** that are measurable directly from raw event properties, without referencing rule outcomes:

| Dimension | What It Measures | Signal Source |
|-----------|-----------------|---------------|
| **Timeliness (Tm)** | Inter-event time variance, staleness | Raw timestamps only |
| **Completeness (Cn)** | Field null/NaN ratio | Raw field values only |
| **Accuracy (Ac)** | Plausible field ranges (no rule engine) | Raw field values only |
| **Consistency (Cs)** | GPS coherence, timestamp monotonicity | Raw coordinates/timestamps |
| **Uniqueness (Uv)** | Duplicate rate via hash | Raw field hashes |

**Critical property**: Each dimension is computed from **raw event fields only**, not from whether violations fired. A negative fare_amount reduces Ac directly because `fare_amount < 0` is a property of the raw value — no SYN002 rule needed to compute it.

**Independent validation criterion**: TQS correlates with a quality signal that is **causally downstream** of data quality — specifically, downstream ETA prediction error on NYC MTA Bus (estimated from route planning queries). High-quality GPS positions → low ETA error. Low-quality GPS positions (jumps, duplicates) → high ETA error. TQS must be shown to correlate with ETA error reduction, not with injection rate.

---

### 6.2 Mathematical Formulation

#### 6.2.1 Dimension 1: Timeliness (Tm)

```
Tm(e₁, …, e_N) = exp(−λ · σ²_Δt) · (1 − stale_rate)

WHERE:
    Δt_i     = e_i.ts − e_{i−1}.ts          for i = 2…N    (ms)
    σ²_Δt    = VARIANCE(Δt_i)               (population variance, ms²)
    μ_Δt     = (e_N.ts − e₁.ts) / (N−1)    (mean inter-event time)
    λ        = 1 × 10⁻⁸                       (calibration constant, ms⁻²)
               # λ was originally 0.01 (second⁻²-scale). With Flink timestamps in ms,
               # σ²_Δt (ms²) = σ²_Δt (s²) × 10⁶. Applying λ=0.01 to ms² gives
               # λ·σ² ≈ 0.01 × 25×10⁶ = 250,000 → exp(−250,000) ≈ 0 for all streams.
               # Recalibrated: λ_ms = λ_s × 10⁻⁶ = 10⁻⁸ ms⁻².
               # At typical GTFS variance (σ²_Δt ≈ 25×10⁶ ms²): λ·σ² ≈ 0.25 → Tm ≈ 0.779 (good).
               # At high variance (σ²_Δt ≈ 400×10⁶ ms²): λ·σ² ≈ 4.0 → Tm ≈ 0.018 (degraded).
               # This produces meaningful discrimination: Tm is sensitive to variance changes
               # across the operating range without collapsing to zero.
    stale_rate = #{e : current_time − e.ts > 300,000} / N

Tm ∈ [0, 1]. Tm → 1 when variance is low and few events are stale.

Note: Stale events may indicate pipeline delays or upstream system failures. Duplicates
increase Δt variance (gaps filled by re-sends). NaN/null fields in timestamps reduce Δt
variance artificially (same-timestamp events). Raw inter-event deltas capture these
patterns without any rule evaluation.
```

#### 6.2.2 Dimension 2: Completeness (Cn)

```
Cn(e₁, …, e_N) = 1 − missing_count / (N · |required_fields|)

WHERE:
    required_fields("nyc_taxi")   = {trip_id, vehicle_id, ts, passenger_count,
                                     trip_distance, fare_amount, PULocationID,
                                     DOLocationID, payment_type}    (9 fields)
    required_fields("gtfs_vehicle") = {trip_id, vehicle_id, ts, lat, lon,
                                       schedule_relationship}         (6 fields)
    missing_count = #{e, f : e[f] IS NULL OR IS_NAN(e[f])}

Cn ∈ [0, 1]. Cn = 1 when all required fields are present for all events.

Note: Null/NaN fields are detectable WITHOUT rule evaluation. NaN propagation
(identified by B1) directly reduces Cn. The TQS completeness dimension is computed
directly from raw field inspection, not from SEM003 violations.
```

#### 6.2.3 Dimension 3: Accuracy (Ac)

```
Ac(e₁, …, e_N) = (1/N) · Σ_{i=1}^{N} accuracy_score(e_i)

NYC TLC accuracy_score(e):
    fare_valid     ← (0 ≤ e.fare_amount ≤ 1000)          (USD)
    distance_valid ← (0 ≤ e.trip_distance ≤ 500)          (miles)
    pax_valid      ← (0 ≤ e.passenger_count ≤ 9)
    location_valid ← (1 ≤ e.PULocationID ≤ 263 AND
                      1 ≤ e.DOLocationID ≤ 263)
    RETURN (fare_valid + distance_valid + pax_valid + location_valid) / 4

GTFS accuracy_score(e):
    coord_valid ← (|e.lat| ≤ 90 AND |e.lon| ≤ 180 AND e.lat IS NOT NULL)
    ts_valid    ← (e.ts IS NOT NULL AND e.ts > 0)
    RETURN (coord_valid + ts_valid) / 2

Ac ∈ [0, 1]. Ac = 1 when all measured fields are within plausible ranges.

Note: These are raw value range checks, NOT the same as SYN002/SEM001/SEM002.
SYN002 uses context-adaptive thresholds (L0–L5); Ac uses fixed plausibility bounds.
A negative fare_amount violates both Ac (raw) and SYN002 (context), but Ac is
computed without any threshold lookup or violation counting.
```

#### 6.2.4 Dimension 4: Consistency (Cs)

```
Cs(e₁, …, e_N) = (1/N_gps) · Σ_{i=1}^{N_gps} consistency_score(e_i)

consistency_score(e) [GTFS vehicles]:
    IF has_prior_position(e.vehicle_id):
        (prev_lat, prev_lon, prev_ts) ← get_prior_position(e.vehicle_id)
        Δt_s ← (e.ts − prev_ts) / 1000          # seconds
        IF Δt_s <= 0: RETURN 1.0                 # same-timestamp
        dist_m ← haversine(prev_lat, prev_lon, e.lat, e.lon) · 1000
        speed_kmh ← dist_m / Δt_s · 3.6
        IF speed_kmh < 0:     RETURN 0.0         # impossible
        IF speed_kmh > 130:   RETURN 0.0         # physically impossible (100 km/h CRS001 + 30 km/h tolerance)
        IF speed_kmh < 0.5:   RETURN 0.5         # suspicious (aligned with CRS001 lower bound)
        RETURN 1.0

consistency_score(e) [NYC TLC]:
    IF e.trip_distance > 0 AND e.fare_amount > 0:
        ppm ← e.fare_amount / (e.trip_distance + 0.001)
        IF ppm > 50: RETURN 0.0                   # impossible
        IF ppm > 20: RETURN 0.5                   # suspicious
    RETURN 1.0

Cs ∈ [0, 1]. Cs = 1 when all GPS measurements are physically plausible.

Note: The 150 km/h bound is NOT the CRS001 rule bound [2, 100] km/h. Cs measures
GPS coherence from raw positions. CRS001/CRS002 flag violations. They are
complementary and independent. Cs does not use the CRS001 speed threshold — it uses
a wider bound (150 km/h) to detect only physically impossible measurements, not
rule violations.
```

#### 6.2.5 Dimension 5: Uniqueness (Uv)

```
Uv(e₁, …, e_N) = 1 − |distinct_hashes| / N

WHERE:
    hash(e) = SHA256(e.trip_id | e.ts | e.lat | e.lon)

Uv ∈ [0, 1]. Uv = 0 when all events are unique. Uv → 1 when many duplicates.

Note: Unlike the original C_score (which used CRS003 violation rate), Uv is computed
directly from raw event hashes. It does NOT depend on CRS003 firing. Therefore Uv is
measurable even when CRS003 recall is unmeasurable (NG-4). High Uv (many duplicates)
indicates downstream ETA prediction degradation, providing the independent quality
signal needed to validate TQS non-circularly.
```

---

### 6.3 Composite TQS

```
TQS = ω_Tm·Tm + ω_Cn·Cn + ω_Ac·Ac + ω_Cs·Cs + ω_Uv·Uv

Default weights (V2-equivalent):
    ω_Tm = 0.20   # Timeliness: pipeline health
    ω_Cn = 0.25   # Completeness: field availability
    ω_Ac = 0.20   # Accuracy: value plausibility
    ω_Cs = 0.25   # Consistency: GPS coherence
    ω_Uv = 0.10   # Uniqueness: deduplication quality

V1-equivalent (equal):     ω_i = 0.20 for all i
V3-equivalent (Cs-heavy):  ω_Cs = 0.35, others reduced proportionally

Note: The 5-dimension composite avoids the C_dimension = 1.0 on NYC TLC problem
(SYN/SEM CRS rules do not apply to NYC TLC zone-level data). Cs on NYC TLC uses
fare-per-mile consistency rather than GPS consistency, making Cs always active.
```

---

### 6.4 Pseudocode: New TQS Aggregation

```
ALGORITHM E_REVISED: compute_TQS(window_events, context_key, level) → TQSResult

BEGIN
    N ← SIZE(window_events)
    IF N = 0: RETURN TQSResult(N=0, tqs=null)

    # ── Step 1: Timeliness (Tm) ───────────────────────────────────────────
    IF N >= 2:
        SORT BY ts ASC
        Δt_i ← events[i].ts − events[i−1].ts  for i=2…N
        μ_Δt ← (events[N].ts − events[1].ts) / (N−1)
        σ²_Δt ← VARIANCE(Δt_i)
        stale_count ← COUNT e WHERE (current_time_ms − e.ts) > 300_000
        Tm ← exp(−0.01 · σ²_Δt) · (1 − stale_count/N)
    ELSE: Tm ← 1.0

    # ── Step 2: Completeness (Cn) ────────────────────────────────────────
    required ← REQUIRED_FIELDS[events[1].entity_type]
    missing ← 0
    FOR e IN events:
        FOR f IN required:
            IF e[f] IS NULL OR IS_NAN(e[f]): missing ← missing + 1
    Cn ← 1 − missing / (N · SIZE(required))

    # ── Step 3: Accuracy (Ac) ────────────────────────────────────────────
    IF entity_type = "nyc_taxi":
        Ac ← AVERAGE OF (fare_valid + dist_valid + pax_valid + loc_valid) / 4
    ELSE:
        Ac ← AVERAGE OF (coord_valid + ts_valid) / 2

    # ── Step 4: Consistency (Cs) ────────────────────────────────────────
    IF entity_type = "gtfs_vehicle":
        gps ← FILTER e WITH prior position
        IF SIZE(gps) > 0: Cs ← AVERAGE consistency_score(gps)
        ELSE: Cs ← 1.0
    ELSE:
        Cs ← AVERAGE price_per_mile consistency

    # ── Step 5: Uniqueness (Uv) ─────────────────────────────────────────
    hashes ← SET OF SHA256(e.trip_id|e.ts|e.lat|e.lon) FOR e IN events
    Uv ← 1 − SIZE(hashes) / N

    # ── Step 6: Composite ────────────────────────────────────────────────
    TQS ← 0.20·Tm + 0.25·Cn + 0.20·Ac + 0.25·Cs + 0.10·Uv

    RETURN TQSResult(N=N, Tm=Tm, Cn=Cn, Ac=Ac, Cs=Cs, Uv=Uv,
                     TQS=TQS, TQS_V1=equal, TQS_V3=cs_heavy)

END
```

---

### 6.5 Relationship to Original TQS

| Aspect | Original TQS | New TQS |
|--------|-------------|---------|
| **Definition** | TQS = 1 − violation_rate | TQS = f(Tm, Cn, Ac, Cs, Uv) from raw events |
| **Circularity** | CIRCULAR: TQS = f(violations) | NOT CIRCULAR: TQS = f(raw fields) |
| **Ground truth** | Injection rate (circular) | Independent stream properties |
| **CRS003** | C_score = f(CRS003 violations), unmeasurable | Uv computed from hashes, measurable |
| **NYC TLC CRS** | C = 1.0 (no CRS) | Cs from trip consistency (always active) |
| **Independent validation** | None (circular with injection rate) | Uv correlates with downstream ETA error |

---

### 6.6 Open Questions (Require Benchmark)

1. **Monotonicity**: Does TQS decrease as injection rate increases? Theory: yes. Measurement needed.
2. **Dimension sensitivity**: Which dimension responds to which anomaly type?
3. **Independent validation**: TQS correlated with downstream ETA prediction error (not injection rate)?
4. **Weight justification**: V1 (equal) is only non-arbitrary choice. V2/V3 need domain justification.
5. **Cs vs. CRS001 boundary**: Cs uses 130 km/h; CRS001 uses [2, 100] km/h. Are these complementary or redundant?

---

### 6.7 Unit Test Specifications (Updated)

```
TEST E1: Perfect quality window — 100 NYC TLC events, all valid
  EXPECT: Tm=1.0, Cn=1.0, Ac=1.0, Cs=1.0, Uv=0.0
  TQS_V2 = 0.20·1 + 0.25·1 + 0.20·1 + 0.25·1 + 0.10·0 = 0.85

TEST E2: High NULL rate — 20 null fare_amount out of 100 events
  Cn = 1 − 20/(100·9) ≈ 0.978
  EXPECT: TQS lower than E1, driven by Cn

TEST E3: GPS speed anomaly — 10/50 GTFS events with speed > 130 km/h
  Cs = (40·1.0 + 10·0.0)/50 = 0.80
  EXPECT: TQS lower than E1, driven by Cs

TEST E4: High duplicate rate — 30 duplicates out of 100 events
  Uv = 1 − 70/100 = 0.30
  EXPECT: TQS lower than E1, driven by Uv

TEST E5: Empty window — EXPECT: N=0, tqs=null
TEST E6: Single event — EXPECT: Tm=1.0, Cn=1.0, Ac=1.0, Cs=1.0, Uv=0.0, TQS=0.85
TEST E7: Monotonicity — TQS(0%) ≥ TQS(5%) ≥ TQS(10%) ≥ TQS(20%)  [NEEDS BENCHMARK]
TEST E8: Independent signal — TQS correlates with ETA prediction error  [NEEDS BENCHMARK]
```

---

## 7. Algorithm F: SYN/SEM Rule Evaluation (Python RPC)

### 7.1 Rule Evaluation Pipeline

SYN/SEM rules run in Python via Flink async RPC (`AsyncDataStream.waitOrdered`):

```
ALGORITHM F: evaluate_syn_sem(e: Event, threshold: Any) → Optional[Violation]

BEGIN
    # ── SYN001: Null / NaN / Type Check ─────────────────────────────────────
    FOR field IN REQUIRED_FIELDS[e.entity_type]:
        value ← e[field]

        IF value IS NULL:
            RETURN Violation(rule=SYN001, reason=NULL, field=field)
        IF IS_NAN(value):                        # math.isnan() for float
            RETURN Violation(rule=SYN001, reason=NAN, field=field)
        IF NOT IS_VALID_TYPE(value, EXPECTED_TYPE[field]):
            RETURN Violation(rule=SYN001, reason=TYPE_MISMATCH, field=field)

    # ── SYN002: Fare Amount Range (Context-Adaptive) ──────────────────────────
    IF e.entity_type = "nyc_taxi":
        fare ← e.fare_amount
        IF fare IS NULL OR fare IS NAN: RETURN Violation(SYN001)
        IF fare < 0:
            RETURN Violation(rule=SYN002, reason=NEGATIVE_VALUE, field="fare_amount",
                             value=fare)
        (lower, upper) ← threshold   # from L0-L5 fallback
        IF fare < lower OR fare > upper:
            RETURN Violation(rule=SYN002, reason=OUT_OF_RANGE, field="fare_amount",
                             value=fare, expected=f"[{lower}, {upper}]")

    # ── SYN003: Location Validity ─────────────────────────────────────────────
    IF e.entity_type = "nyc_taxi":
        IF e.PULocationID ∉ [1, 263] OR e.DOLocationID ∉ [1, 263]:
            RETURN Violation(rule=SYN003, reason=INVALID_ZONE, ...)
    IF e.entity_type = "gtfs_vehicle":
        IF e.lat ∉ [−90, 90] OR e.lon ∉ [−180, 180]:
            RETURN Violation(rule=SYN003, reason=INVALID_COORDINATE, ...)

    # ── SEM001: Fare Plausibility (Rolling P10/P90) ──────────────────────────
    IF e.entity_type = "nyc_taxi":
        (p10, p90) ← rolling_stats.get("fare_amount", context_key)
        fare ← e.fare_amount
        IF p10 IS NOT NULL AND fare < p10:
            RETURN Violation(rule=SEM001, reason=BELOW_CONTEXTUAL_P10,
                             field="fare_amount", value=fare, p10=p10)
        IF p90 IS NOT NULL AND fare > p90:
            RETURN Violation(rule=SEM001, reason=ABOVE_CONTEXTUAL_P90,
                             field="fare_amount", value=fare, p90=p90)

    # ── SEM002: Trip Distance Plausibility ─────────────────────────────────────
    IF e.entity_type = "nyc_taxi":
        (d_lower, d_upper) ← threshold   # context-adaptive
        dist ← e.trip_distance
        IF dist < d_lower OR dist > d_upper:
            RETURN Violation(rule=SEM002, reason=OUT_OF_RANGE,
                             field="trip_distance", value=dist)

    # ── SEM003: Passenger Count ────────────────────────────────────────────────
    IF e.entity_type = "nyc_taxi":
        pax ← e.passenger_count
        IF pax IS NULL OR pax < 1 OR pax > 6:
            RETURN Violation(rule=SEM003, reason=OUT_OF_RANGE,
                             field="passenger_count", value=pax, expected="[1, 6]")

    # ── GTFSSem002: Stale Position ───────────────────────────────────────────
    IF e.entity_type = "gtfs_vehicle":
        age_s ← (current_time_ms − e.ts) / 1000
        IF age_s > 300:   # 5 minutes
            RETURN Violation(rule=GTFSSem002, reason=STALE_DATA,
                             field="position", age_s=age_s, threshold=300)

    RETURN null   # No violation

END
```

---

## 8. Algorithm G: Isolation Forest ML Pre-Filter (Python RPC)

### 8.1 Purpose

Isolation Forest (Liu et al., 2008; SDM 2025 adaptation) provides an anomaly confidence score per event for the SYN/SEM layer. The score adjusts the effective k-multiplier on context thresholds: `effective_k = base_k × (1 + α × anomaly_score)`.

### 8.2 Pseudocode: IF RPC Client

```
ALGORITHM G: score_isolation_forest(e: Event) → (anomaly_score: Float)

BEGIN
    # ── Step 1: Build feature vector ─────────────────────────────────────
    IF e.entity_type = "nyc_taxi":
        zone_cat ← zone_lookup(e.PULocationID).category
        hour_sin ← sin(2π × extract_hour(e.ts) / 24)
        hour_cos ← cos(2π × extract_hour(e.ts) / 24)
        weekend ← is_weekend(e.ts)

        f[0] ← normalize(e.fare_amount,     μ_fare, σ_fare)
        f[1] ← normalize(e.trip_distance,    μ_dist, σ_dist)
        f[2] ← float(e.passenger_count)
        f[3] ← hour_sin
        f[4] ← hour_cos
        f[5] ← zone_cat_to_onehot(zone_cat)      # [is_airport, is_downtown, is_midtown, is_outer]
        f[6] ← float(weekend)
        f[7] ← float(e.payment_type)
    ELSE IF e.entity_type = "gtfs_vehicle":
        speed_kmh ← compute_speed(e)               # from last two positions
        f[0] ← speed_kmh
        f[1] ← schedule_relationship_ordinal(e.schedule_relationship)
        f[2] ← hour_sin
        f[3] ← hour_cos
        f[4] ← float(is_bus)                      # one-hot: [is_bus, is_subway, is_rail]
        f[5] ← float(weekend)

    # ── Step 2: RPC call to IF service ──────────────────────────────────
    result ← grpc_client.call(
        service = "IsolationForestService",
        method  = "Score",
        request = ScoreRequest(features = f, context_key = ck(e, L0))
    )

    # ── Step 3: Handle timeout/error ────────────────────────────────────
    IF result.status = TIMEOUT OR result.status = ERROR:
        RETURN (0.0, "FALLBACK")   # No ML calibration; rule-only evaluation

    # ── Step 4: Return anomaly score ∈ [0, 1] ──────────────────────────
    RETURN (result.anomaly_score, "OK")

END
```

### 8.3 Architecture: Single Global Model

> **IMPORTANT**: This section specifies a **single global Isolation Forest model** trained on all NYC TLC contexts. Per-context-cell models (e.g., one IF per zone-hour cell) are computationally infeasible (~10,000+ models). The global model uses zone/hour as categorical features in the feature vector, allowing it to distinguish distributional patterns across contexts without maintaining separate model instances. Profile after implementation; multi-model only if single-model latency exceeds the 50ms budget.

**Feature vector for single global model** (11 features):
| Index | Feature | Source | Normalization |
|-------|---------|--------|---------------|
| f[0] | fare_z | `e.fare_amount` | Z-score from `ThresholdStats` |
| f[1] | dist_z | `e.trip_distance` | Z-score from `ThresholdStats` |
| f[2] | passenger_count | `e.passenger_count` | Raw integer |
| f[3] | hour_sin | `extract_hour(e.ts)` | `sin(2πh/24)` |
| f[4] | hour_cos | `extract_hour(e.ts)` | `cos(2πh/24)` |
| f[5–8] | zone_onehot | `zone_lookup(e.PULocationID)` | One-hot (4 categories) |
| f[9] | is_weekend | `is_weekend(e.ts)` | Binary |
| f[10] | payment_type | `e.payment_type` | Raw integer |

### 8.4 Integration with Threshold Lookup

```
# After compute_context_and_threshold() (Algorithm A), apply ML calibration:
(ck, level, threshold, stats) ← compute_context_and_threshold(e)

(anomaly_score, status) ← score_isolation_forest(e)

IF status = "OK" AND stats ≠ null:
    base_k ← stats.k_multiplier
    α ← stats.ml_alpha
    effective_k ← base_k × (1.0 + α × anomaly_score)
    # Apply effective_k to rolling P10/P90 threshold computation
ELSE:
    effective_k ← stats.k_multiplier   # No ML calibration
```

---

## 9. Algorithm H: LSTM Trajectory Prediction (Python RPC)

### 9.1 Purpose

> **STATUS: CONDITIONAL / NO-GO (Priority 4)**
> Per ML_MODEL_ANALYSIS.md §3: Three blockers identified: (1) 6-month NYC MTA Bus GPS archive is unconfirmed — training infeasible without it; (2) LSTM trajectory deviation is HIGHLY correlated with CRS002 GPS jump detection — HIGH redundancy; (3) alert elevation provides marginal value in research platform. **Re-evaluate if CRS002 recall < 60% on real GPS anomalies AND 6-month GPS archive is confirmed.** LSTM never vetoes CRS002 — only elevates severity.

A bidirectional LSTM model predicts the next vehicle position from the last 10 GPS positions. Events with high prediction deviation (> calibrated threshold) are pre-flagged with elevated severity for CRS002 evaluation.

### 9.2 Training Data Caveat

> **WARNING**: Training requires a 6-month historical NYC MTA Bus GPS trajectory archive. No such archive is confirmed to exist. The live GTFS-realtime feed replays recent data only. Without 6 months of historical data, LSTM training will be underfitted and the model will not generalize to seasonal patterns. **This must be verified before LSTM implementation proceeds.**

### 9.3 Pseudocode: LSTM RPC Client

```
ALGORITHM H: score_lstm_trajectory(e: Event, vehicle_history) → (deviation_km: Float, status: String)

BEGIN
    # ── Guard: Cold start ─────────────────────────────────────────────
    IF SIZE(vehicle_history) < 3:
        RETURN (null, "COLD_START")   # Skip LSTM pre-filter; CRS rules evaluate normally

    # ── Step 1: Build input sequence ───────────────────────────────────
    # Last 10 (lat, lon, timestamp) tuples from vehicle_history
    seq ← vehicle_history[-10:]
    seq_len ← SIZE(seq)

    # Normalize to NYC bounding box
    FOR i IN 0..seq_len-1:
        lat_norm[i] ← (seq[i].lat  − NYC.lat_min)  / (NYC.lat_max  − NYC.lat_min)
        lon_norm[i] ← (seq[i].lon  − NYC.lon_min)  / (NYC.lon_max  − NYC.lon_min)
        # Normalize timestamps to 30-minute window
        dt ← (seq[i].ts − seq[0].ts) / (30 × 60 × 1000)
        t_norm[i] ← clamp(dt, 0.0, 1.0)

        # Mark missing positions
        IF seq[i] IS NULL:
            position_mask[i] ← 0.0
        ELSE:
            position_mask[i] ← 1.0

    # ── Step 2: RPC call to LSTM service ────────────────────────────────
    result ← grpc_client.call(
        service = "LSTMTrajectoryService",
        method  = "PredictNext",
        request = PredictRequest(
            lat_sequence = lat_norm,
            lon_sequence = lon_norm,
            time_sequence = t_norm,
            position_mask = position_mask,
            vehicle_id = e.vehicle_id
        )
    )

    # ── Step 3: Handle timeout/error ────────────────────────────────────
    IF result.status = TIMEOUT OR result.status = ERROR:
        RETURN (null, "FALLBACK")   # Skip LSTM pre-filter

    # ── Step 4: Denormalize and compute Haversine deviation ─────────────
    pred_lat ← result.predicted_lat × (NYC.lat_max − NYC.lat_min) + NYC.lat_min
    pred_lon ← result.predicted_lon × (NYC.lon_max − NYC.lon_min) + NYC.lon_min
    deviation_km ← haversine(Position(e.lat, e.lon), Position(pred_lat, pred_lon))

    RETURN (deviation_km, "OK")

END
```

### 9.5 LSTM Pre-Filter Integration with CRS002

```
# In evaluate_CRS002(), after LSTM scoring:
(deviation_km, lstm_status) ← score_lstm_trajectory(e, vehicle_history)

IF lstm_status = "OK":
    lstm_threshold ← broadcast_state.get("lstm_threshold_m")
    IF deviation_km > lstm_threshold:
        # Elevate severity but do NOT block CRS002 evaluation
        violation.severity ← max(violation.severity, ELEVATED)
        violation.metadata["lstm_deviation_m"] ← deviation_km × 1000
        violation.metadata["lstm_prefilter"] ← true
    ELSE:
        violation.metadata["lstm_deviation_m"] ← deviation_km × 1000
        violation.metadata["lstm_prefilter"] ← false

# CRS002 evaluation always proceeds — ML never vetoes a rule
```

---

## 10. Algorithm I: Bayesian Optimization Calibration

### 10.1 Purpose

> **CRITICAL FIX**: Bayesian Optimization objective is **F1 on injected calibration data**, not violation_rate. Per ML_MODEL_ANALYSIS.md §2.8: violation_rate (false-positive rate) can diverge from F1. Optimizing FPR may worsen recall. The correct objective is `F1 = 2·P·R/(P+R)` on calibration data with known ground truth from synthetic injection. This requires the evaluation infrastructure (Phase 1) to be operational.

Gaussian Process surrogate model with Expected Improvement (EI) acquisition maximizes F1 on a 1-hour calibration window (with synthetic injection) by tuning: k_multiplier, if_alpha, lstm_threshold_m, weekend_discount, and context_weight.

### 10.2 Pseudocode: BO Calibration Loop

```
ALGORITHM I: run_bayesian_optimization(calibration_window, broadcast_state) → CalibratedParams

BEGIN
    # ── Step 1: Verify minimum data ───────────────────────────────────
    n_events ← count(calibration_window.events)
    IF n_events < 100:
        LOG WARNING "BO skipped: calibration window has only {n_events} events (minimum 100)"
        RETURN null   # Use default parameters

    # ── Step 2: Initialize optimizer ──────────────────────────────────
    optimizer ← GPyOptOptimizer(
        dimensions = [
            ("k_multiplier",       1.5, 5.0),     # k-multiplier for rolling thresholds
            ("if_alpha",           0.0, 0.5),     # Isolation Forest sensitivity
            ("lstm_threshold_m",  50.0, 250.0),  # LSTM deviation threshold (meters)
            ("weekend_discount",   0.0, 0.5),     # k reduction for weekends
            ("context_weight",     0.0, 1.0),     # context vs. global weight
        ],
        n_initial_points = 10,
        acq_func = "EI",
        random_state = 42
    )

    # ── Step 3: BO loop ────────────────────────────────────────────────
    FOR iteration IN 1..30:
        next_params ← optimizer.ask()

        # Apply parameters to broadcast state
        apply_params(broadcast_state, next_params)

        # Run evaluation on calibration window (WITH injection for F1 computation)
        # Requires: ground_truth_tracker operational; calibration window has injected anomalies
        violations ← run_rules(calibration_window.events, broadcast_state)
        ground_truth ← calibration_window.injected_anomalies
        (precision, recall) ← compute_pr(violations, ground_truth)
        f1_score ← 2 × precision × recall / (precision + recall + 1e-8)

        # Report to optimizer
        optimizer.tell(next_params, f1_score)

        # Convergence check: stop if no improvement for 5 consecutive iterations
        IF optimizer.no_improvement_count > 5:
            LOG "BO converged at iteration {iteration}"
            BREAK

    # ── Step 4: Staleness check ───────────────────────────────────────────
    # If calibration took > 15 minutes, skip broadcasting (parameters may be stale)
    calibration_duration ← now() - calibration_start_time
    IF calibration_duration > 15 MINUTES:
        LOG WARNING "BO calibration took {calibration_duration} — skipping broadcast (stale)"
        RETURN null   # Use existing parameters

    # ── Step 4: Extract best parameters ───────────────────────────────
    best_params ← optimizer.get_best()

    # ── Step 5: Broadcast updated thresholds ───────────────────────────
    FOR (level, ck, field) IN broadcast_state.keys():
        stats ← broadcast_state.get(level, ck, field)
        stats.k_multiplier ← best_params["k_multiplier"]
        stats.ml_alpha ← best_params["if_alpha"]
        stats.lstm_threshold_m ← best_params["lstm_threshold_m"]
        stats.weekend_discount ← best_params["weekend_discount"]
        stats.context_weight ← best_params["context_weight"]
        stats.computed_at ← current_timestamp_ms()
        stats.calibration_version ← stats.calibration_version + 1

    broadcast_state.broadcast()   # Push to all TaskManagers

    LOG "BO complete: best F1={best_params.best_value:.4f}, " \
        "k={best_params.k_multiplier}, " \
        "if_alpha={best_params.if_alpha}, " \
        "lstm_threshold={best_params.lstm_threshold_m}m, " \
        "weekend_discount={best_params.weekend_discount}, " \
        "context_weight={best_params.context_weight}"

    # ── Step 5: Broadcast to Flink ────────────────────────────────────────
    # Write calibrated parameters to BroadcastState (all TaskManagers receive update)
    broadcast_state.set("k_multiplier",      best_params.k_multiplier)
    broadcast_state.set("ml_alpha",          best_params.if_alpha)
    broadcast_state.set("lstm_threshold_m",  best_params.lstm_threshold_m)
    broadcast_state.set("weekend_discount",  best_params.weekend_discount)
    broadcast_state.set("context_weight",    best_params.context_weight)
    broadcast_state.set("calibration_version", broadcast_state.get("calibration_version") + 1)
    broadcast_state.set("calibration_timestamp", now())

    LOG "BroadcastState updated: calibration_version={broadcast_state.calibration_version}"
    RETURN best_params

END
```

### 10.3 BO Trigger and Timing

```
# BO runs hourly, after the calibration window closes
EVERY 1 HOUR:
    window_start ← now() − 1h
    window_end   ← now()
    calibration_events ← replay_events(window_start, window_end, injection_rate=0.0)

    params ← run_bayesian_optimization(calibration_events, broadcast_state)

    IF params IS NOT null:
        broadcast_state.update(params)
    ELSE:
        LOG "Using default parameters — BO skipped"
```

---

## 11. Complete Flink DataStream Operator Graph (Updated with ML)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           FLINK APPLICATION                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Kafka Topic: "raw-events"                                                  │
│  └── FlinkKafkaConsumer (exactly-once, watermarks)                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ OPERATOR 1: Watermark + Idleness + Parse                              │ │
│  │  • WatermarkStrategy.boundedOutOfOrderness(Duration.ofSeconds(60))     │ │
│  │  • WatermarkStrategy.withIdleness(Duration.ofMinutes(5))               │ │
│  │  • Parse JSON → Event (Java, fast-path)                                │ │
│  │  • Route to NYC_TAXI or GTFS_VEHICLE stream                           │ │
│  └────────────────────────────┬───────────────────────────────────────────┘ │
│                               │                                              │
│           ┌───────────────────┴───────────────────────┐                      │
│           ▼                                       ▼                          │
│  ┌─────────────────┐                       ┌──────────────────────────────┐ │
│  │ NYC_TAXI BRANCH │                       │ GTFS_VEHICLE BRANCH          │ │
│  │ (Python RPC)    │                       │ (Java KeyedProcessFunction) │ │
│  │                 │                       │                              │ │
│  │ SYN001–003      │                       │ CRS001: SpeedBoundsFunction │ │
│  │ SEM001–003      │                       │ CRS002: GPSJumpFunction      │ │
│  │ Context key →    │                       │ CRS003: DedupFunction        │ │
│  │ BroadcastState   │                       │ (per-vehicle keyed state)  │ │
│  │ threshold lookup │                       │                              │ │
│  │ (SYN002/SEM002) │                       │                              │ │
│  └────────┬────────┘                       └──────────────┬─────────────┘ │
│           │                                              │                  │
│           └──────────────────┬───────────────────────────┘                  │
│                              ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ OPERATOR 2: ML Async RPC (Python via gRPC)                             │ │
│  │  • AsyncDataStream.orderedWait / unorderedWait                           │ │
│  │  • Two parallel async calls:                                           │ │
│  │    (a) IsolationForestClient → anomaly_score ∈ [0, 1]                 │ │
│  │    (b) LSTMTrajectoryClient → (predicted_lat, predicted_lon, deviation_km)│ │
│  │  • Timeout: 50ms; fallback: anomaly_score=0.0 on timeout             │ │
│  │  • Output: EventEnriched(event, if_score, lstm_dev)                   │ │
│  └────────────────────────────────┬───────────────────────────────────────┘ │
│                                   │                                          │
│  ┌────────────────────────────────┴───────────────────────────────────────┐ │
│  │ OPERATOR 3: Post-Filter + Violation Router                              │ │
│  │  • Combine(rule_severity, IF_score, LSTM_dev) → alert_priority          │ │
│  │  • Violation → Kafka topic "quality-violations"                          │ │
│  │  • Violation → PostgreSQL violations table                               │ │
│  │  • Prometheus: streamdq_violations_total{rule_id, severity, reason}      │ │
│  └────────────────────────────────┬────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ OPERATOR 4: TQS Aggregation (5-min Tumbling Window)                   │ │
│  │  • WindowedBy(context_key)                                            │ │
│  │  • compute_TQS(window_events, context_key, level)                     │ │
│  │  • Emit → PostgreSQL metrics_summary + Prometheus TQS gauge           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ OPERATOR 5: Context Statistics + Bayesian Opt (hourly)                 │ |
│  │  • Every event: update rolling P10/P90 in PostgreSQL context_statistics │ │
│  │  • Every hour: ML calibration → update BroadcastState thresholds        │ │
│  │  • BroadcastState[level][ck][field] → updated threshold values        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 11.1 BroadcastState for ML-Calibrated Thresholds

```
BroadcastState layout (updated):
  key = (level: Int, ck: String, field: String)
  value = CalibratedThreshold {
      count: Int,
      p10: Float, p90: Float,
      k_multiplier: Float,        # calibrated by Bayesian Optimization
      ml_alpha: Float,            # calibrated by Bayesian Optimization
      lstm_threshold_m: Float,    # calibrated by Bayesian Optimization
      weekend_discount: Float,
      context_weight: Float,
      computed_at: Long,
      calibration_version: Int,
      if_model_version: String,
      lstm_model_version: String
  }

Example calibrated keys:
  (L0, "H10_midtown_WD", "fare_amount")
    → CalibratedThreshold(count=142, k=2.3, ml_alpha=0.15,
                          if_model_version="if_v2.3", lstm_model_version="lstm_v1.7", ...)
  (L1, "morning_midtown_WD", "fare_amount")
    → CalibratedThreshold(count=67, k=2.8, ml_alpha=0.20, ...)
  (L4, "global", "fare_amount")
    → CalibratedThreshold(count=5_234_567, k=3.0, ml_alpha=0.10, ...)
```

BroadcastState is immutable per calibration cycle (hourly). Events read O(1) from it.
Broadcast state size estimate:
  - 10,000 context cells × 5 fields × 1 KB ≈ 50 MB
  - BroadcastState replicated to all TaskManagers

---

## 12. Algorithm Complexity Summary

| Algorithm | Per-Event Time | Space (per-key) | Space (total) | Bottleneck |
|-----------|:--------------:|:---------------:|:-------------:|------------|
| **A: Context Key + L0–L5** | O(1) | O(1) (BroadcastState lookup) | O(C) cells × fields | BroadcastState deserialization [ASSUMES] |
| **B: CRS001 Speed** | O(1) amortized | O(W) per vehicle | O(V × W) | Haversine math (microseconds) |
| **C: CRS002 Jump** | O(K) where K ≤ 3 positions | O(K) per vehicle (K=3) | O(V × K) | Haversine × K comparisons |
| **D: CRS003 Dedup** | O(1) expected | O(H) per trip | O(T × H) | SHA256 hash (nanoseconds) |
| **E: TQS Aggregation** | O(1) counter update; O(N) at window close | O(1) per event | O(C) per context cell | Window emission (periodic, not per-event) |
| **F: SYN/SEM (Python RPC)** | O(1) × N_rules + RPC latency | O(1) | O(N_rules) | Async RPC round-trip (~1–5ms) [ASSUMES] |
| **G: Isolation Forest (RPC)** | O(1) RPC + IF scoring (~2ms) | O(1) | O(N_rules) | gRPC round-trip (~2ms per event) [ASSUMES] |
| **H: LSTM Trajectory (RPC)** | O(1) RPC + LSTM inference (~10ms) | O(S) per vehicle | O(S × V) | gRPC round-trip (~10ms per sequence) [ASSUMES] |
| **I: Bayesian Opt (hourly)** | O(n_iter × N_cal) | O(1) | O(N_params) | GP surrogate fit (n_iter=30, N_cal ~10K events) |

**Notation**: C = number of context cells; V = number of vehicles; T = number of trips; K = position history size (K=3); W = speed history size (W≈10 at 1Hz for 10-min window); H = dedup window size (max active hashes per trip); S = sequence length (S=10 for LSTM).

### 12.1 Space Complexity Details

```
CRS001 state (per vehicle):
  VehicleGPSState {
    vehicle_id: String (≤ 20 bytes)
    prev_lat, prev_lon: Double (16 bytes)
    prev_timestamp: Long (8 bytes)
    speed_history: List[SpeedSample] × W (≤ 10 samples × 24 bytes ≈ 240 bytes)
    last_update: Long (8 bytes)
  }
  ≈ 300 bytes per vehicle

CRS002 state (per vehicle):
  JumpState {
    vehicle_id: String (≤ 20 bytes)
    recent_positions: List[PositionSample] × K (≤ 3 × 24 bytes ≈ 72 bytes)
  }
  ≈ 100 bytes per vehicle

CRS003 state (per trip):
  DedupState {
    trip_id: String (≤ 50 bytes)
    hash_set: RoaringBitmap (≤ 1 byte per hash on average for sparse sets)
  }
  ≈ 50 + H bytes per trip

Total state (NYC MTA Bus, estimated 500 vehicles, 10,000 active trips):
  CRS001: 500 × 300 B ≈ 150 KB
  CRS002: 500 × 100 B ≈ 50 KB
  CRS003: 10,000 × 100 B ≈ 1 MB
  Total: ≈ 1.2 MB  ← well within RocksDB capacity

BroadcastState (thresholds):
  10,000 cells × 5 fields × 500 bytes ≈ 25 MB
  Replicated to all TaskManagers: 3 × 25 MB ≈ 75 MB total
```

---

## 13. Unit Test Specifications

### 13.1 Algorithm A — Context Key Computation

```
TEST A1: L0 key generation
  INPUT:  e = {ts: 2026-04-23 10:30:00, PULocationID: 100, entity_type: nyc_taxi}
  EXPECT: ck = "H10_midtown_WD" (assuming zone 100 = midtown, Thu = weekday)

TEST A2: Weekend key generation
  INPUT:  e = {ts: 2026-04-25 10:30:00, PULocationID: 100, entity_type: nyc_taxi}
  EXPECT: ck = "H10_midtown_WE" (Sat = weekend)

TEST A3: L0 → L1 fallback (insufficient samples)
  INPUT:  e = {ts: 2026-04-23 10:30:00, PULocationID: 100}
          BroadcastState: L0 count = 50 < 100; L1 count = 80 > 50
  EXPECT: level = L1, ck = "morning_midtown_WD"

TEST A4: L4 global fallback
  INPUT:  e = {ts: 2026-04-23 10:30:00, PULocationID: 999 (unknown)}
          BroadcastState: L0, L1, L2, L3 all count < min_samples
  EXPECT: level = L4, ck = "global"

TEST A5: L5 physics prior (all levels exhausted)
  INPUT:  e = {entity_type: gtfs_vehicle}
          BroadcastState: all levels empty
  EXPECT: level = L5, threshold = [2, 100] km/h for speed field

TEST A6: Null zone
  INPUT:  e = {ts: 2026-04-23 10:30:00, PULocationID: NULL}
  EXPECT: level = L4 (zone fallback → borough → global) [ASSUMES zone=null cascades correctly]
```

### 13.2 Algorithm B — CRS001 Speed Bounds

```
TEST B1: Valid speed
  INPUT:  e = {lat: 40.7128, lon: -74.0060, ts: 1000, vehicle_id: "MTA_B1"}
          state = {prev_lat: 40.7130, prev_lon: -74.0058, prev_ts: 970}  # ~30m in 30s
  COMPUTE: dist = haversine(...) ≈ 0.035 km; time_delta = 30s; speed ≈ 4.2 km/h
  EXPECT: RETURN null (speed ∈ [2, 100])

TEST B2: Below lower bound (stationary with GPS jitter)
  INPUT:  state has prev position; current pos ~2m away in 30s
  COMPUTE: speed ≈ 0.24 km/h < 2.0
  EXPECT: Violation(rule=CRS001, reason=BELOW_LOWER_BOUND, speed≈0.24)

TEST B3: Above upper bound (GPS spoofing)
  INPUT:  state has prev position; current pos ~1.5km away in 30s
  COMPUTE: speed ≈ 180 km/h > 100.0
  EXPECT: Violation(rule=CRS001, reason=ABOVE_UPPER_BOUND, speed≈180)

TEST B4: First position (no prior state)
  INPUT:  state.get("MTA_B1") = null
  EXPECT: RETURN null, state initialized with current position

TEST B5: Null vehicle_id
  INPUT:  e = {vehicle_id: NULL, lat: 40.7128, lon: -74.0060}
  EXPECT: Violation(rule=SYN001, reason=NULL_KEY, field="vehicle_id")

TEST B6: Null lat
  INPUT:  e = {vehicle_id: "MTA_B1", lat: NULL, lon: -74.0060, ts: 1000}
  EXPECT: Violation(rule=SYN001, reason=NULL_FIELD, field="lat")

TEST B7: NaN lat
  INPUT:  e = {vehicle_id: "MTA_B1", lat: NaN, lon: -74.0060, ts: 1000}
  EXPECT: Violation(rule=SYN001, reason=NAN_FIELD, field="lat")

TEST B8: Out-of-bounds lat
  INPUT:  e = {vehicle_id: "MTA_B1", lat: 95.0, lon: -74.0060, ts: 1000}
  EXPECT: Violation(rule=SYN003, reason=OUT_OF_BOUNDS, field="lat")
```

### 13.3 Algorithm C — CRS002 GPS Jump

```
TEST C1: No jump
  INPUT:  e = {lat: 40.7130, lon: -74.0058, ts: 1000}
          jstate = {positions: [{lat: 40.7128, lon: -74.0060, ts: 970}]}
  COMPUTE: dist = ~30m < 400m
  EXPECT: RETURN null

TEST C2: GPS jump detected
  INPUT:  e = {lat: 40.8000, lon: -73.9000, ts: 1000}  # ~10km away
          jstate = {positions: [{lat: 40.7128, lon: -74.0060, ts: 970}]}
  COMPUTE: dist ≈ 10km > 400m, |ts − pos.ts| = 30s ≤ 30s
  EXPECT: Violation(rule=CRS002, type=GPS_SPOOFING, dist_m≈10000)

TEST C3: Position outside 30s window (no check)
  INPUT:  e = {lat: 40.8000, lon: -73.9000, ts: 2000}
          jstate = {positions: [{lat: 40.7128, lon: -74.0060, ts: 970}]}
  COMPUTE: |2000 − 970| = 1030ms > 30s — position not checked
  EXPECT: RETURN null, position added to buffer
```

### 13.4 Algorithm D — CRS003 Dedup

```
TEST D1: New event (no duplicate)
  INPUT:  e = {trip_id: "T001", ts: 1000, lat: 40.7128, lon: -74.0060}
          dedup.get("T001") = null
  COMPUTE: hash = SHA256("T001|1000|40.7128|-74.0060")
  EXPECT: RETURN null, hash added to RoaringBitmap

TEST D2: Duplicate detected
  INPUT:  e = {trip_id: "T001", ts: 1000, lat: 40.7128, lon: -74.0060}
          dedup.get("T001") contains hash
  EXPECT: Violation(rule=CRS003, type=DUPLICATE, hash=h)

TEST D3: Null trip_id
  INPUT:  e = {trip_id: NULL}
  EXPECT: Violation(rule=SYN001, reason=NULL_FIELD, field="trip_id")
```

### 13.5 Algorithm E — TQS Aggregation

```
TEST E1: Perfect quality window
  INPUT:  window_events = 100 events, 0 violations
  COMPUTE: Tm=Cn=Ac=Cs=1.0, Uv=0.0; TQS_V2 = 0.85
  EXPECT: TQSResult(TQS_V2=0.85, N=100)

TEST E2: All violations (all fields out of range)
  INPUT:  window_events = 100 events, all Ac=0.0
  COMPUTE: TQS_V2 = 0.20·1 + 0.25·1 + 0.20·0 + 0.25·1 + 0.10·0 = 0.65
  EXPECT: TQSResult(TQS_V2=0.65, N=100)

TEST E3: Empty window
  INPUT:  window_events = []
  EXPECT: TQSResult(N=0, tqs=null)

TEST E4: CRS dimension on NYC TLC (no CRS rules)
  INPUT:  window_events = NYC TLC events, 0 violations
  COMPUTE: Cs from price-per-mile consistency; always active on NYC TLC
  EXPECT: Cs not artificially 1.0; TQS reflects true NYC TLC consistency
```

---

## 14. Reproducibility & Verification

### 14.1 How to Verify Each Algorithm

**Algorithm A (L0–L5)**:
1. Load 1000 NYC TLC events into test harness
2. Compute context key for each; verify L0/L1/L2/L3/L4/L5 distribution matches expected percentages
3. Verify that L5 fallback is used when all other levels fail (inject sparse zone/time combo)
4. Verify broadcast state update path: periodic job → PostgreSQL stats → BroadcastState push

**Algorithm B (CRS001)**:
1. Synthetic GPS trace: 10 positions along a known route at known timestamps
2. Verify: speed in [2, 100] → no violation; speed > 100 → violation; speed < 2 → violation
3. Verify: first position for vehicle → no violation, state initialized
4. Verify: NaN/null vehicle_id → SYN001 violation
5. Verify: out-of-bounds lat/lon → SYN003 violation

**Algorithm C (CRS002)**:
1. Two positions 200m apart at same timestamp → GPS_JUMP violation
2. Two positions 50m apart at same timestamp → no violation
3. Two positions 200m apart at t=0 and t=31s (outside 30s window) → no violation

**Algorithm D (CRS003)**:
1. Emit event H(trip=T001, ts=0) → no violation
2. Emit event H(trip=T001, ts=0, same lat/lon) → DUPLICATE violation
3. Emit event H(trip=T001, ts=310000) → no violation (TTL expired)

**Algorithm E (TQS)**:
1. Empty window → null TQS
2. All-pass window → TQS = 0.85 (not 1.0, since Uv=0 and weights sum < 1)
3. Known violation mix → verify TQS formula with hand-calculated expected values
4. V1 vs V2 vs V3 produce different composite scores → verify formula correctness
5. TQS computed from raw fields only — verify no rule outcome is used

### 14.2 Assumptions & Unvalidated Elements

| ID | Assumption | Location | Validation Required |
|----|-----------|----------|---------------------|
| [ASSUMES-1] | BroadcastState O(1) lookup | Algorithm A | Benchmark on 10K cells |
| [ASSUMES-2] | Python RPC latency ~1–5ms | Algorithm F | Measure actual RPC round-trip |
| [ASSUMES-3] | TQS weight V2 is primary | Algorithm E | Pre-registered; no change needed |
| [ASSUMES-4] | D4 holiday lookup partial | Algorithm A | Requires full calendar implementation |
| [ASSUMES-5] | 263 TLC zones mapped to zone_category | Algorithm A | Requires zone lookup table |
| [REQUIRES BENCHMARK] | Haversine microbenchmark | Algorithm B/C | Measure per-call latency on target JVM |
| [REQUIRES BENCHMARK] | CRS state size estimates | Section 9.1 | Verify actual RocksDB state sizes |
| [REQUIRES BENCHMARK] | BroadcastState size 50 MB | Section 8.1 | Measure actual memory footprint |
| [BOUNDARY CASE] | CRS003 TTL 310s misses duplicates after 310s | Algorithm D | Acknowledged limitation |
| [UNMEASURABLE] | CRS003 recall | Algorithm D | NG-4 — replay suppression gate blocks synthetic duplicates |
| [REQUIRES BENCHMARK] | CRS001 upper bound 100 km/h | Algorithm B | Verify on NYC MTA Bus real feed; may need further adjustment if buses exceed 100 km/h in normal traffic |
