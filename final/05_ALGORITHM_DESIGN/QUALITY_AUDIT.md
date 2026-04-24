# Algorithm Design Quality Audit: ContextAware-DQ

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Engine**: Apache Flink (Java for CRS, Python for SYN/SEM)
**Auditor**: Code Reviewer (Pre-Implementation)
**Date**: April 23, 2026
**Sources**: `final/03_IDEA_SELECTION/report.md`, `final/04_NOVELTY_CONTRIBUTION/NOVELTY_SCORES.md`, `final/04_NOVELTY_CONTRIBUTION/SIGNIFICANCE_TABLE.md`
**Status**: Design-phase audit — NO code files were read. All findings derive from design documents only.

---

## Summary Quality Audit Table

*(All 36 issues, sorted by severity)*

| # | Severity | Algorithm | Issue | Recommendation |
|---|:--------:|----------|-------|----------------|
| 1 | **CRITICAL** | TQS Aggregation | `total_events = 0` → divide-by-zero | Guard: `if total_events == 0: emit TQS = None or skip aggregation` |
| 2 | **CRITICAL** | CRS001 | `time_delta = 0` → divide-by-zero | Guard: check `time_delta == 0` before division, flag as GPS_SPOOFING (CRS002) |
| 3 | **CRITICAL** | L0–L5 Context | `event.hour` is NaN → silent pass-through (B1) | SYN001 NaN guard must run BEFORE context key extraction |
| 4 | **CRITICAL** | CRS003 | `vehicleId` consistency unverified across duplicate hash events | Add vehicleId consistency check: same hash + different vehicleId = possible entity swap |
| 5 | **CRITICAL** | CRS003 | Replay suppression gate blocked (NG-4): synthetic duplicates tagged is_replay=True; recall and precision UNMEASURABLE | Must emit TWO records in `synthetic_injector.py`; document as Tier 3 limitation |
| 6 | **CRITICAL** | CRS002 | CRS002 severity for 2–20 km/h GPS_SPOOFING is absent from spec | Add explicit severity mapping: `2–20 km/h → HIGH GPS_SPOOFING` |
| 7 | **MAJOR** | L0–L5 Context | Context key exists but count < min_samples → behavior unspecified | Explicit: "key exists with count < min_samples → fall back to next level" |
| 8 | **MAJOR** | CRS001 | `prevTimestamp` is None (first position) → silently passes | Explicit: "pass silently, initialize state" with logging |
| 9 | **MAJOR** | CRS002 | Jump detected with only 1 prior position → "lower confidence" is vague | Define explicit confidence tiers: 1 prior = LOW, 2+ prior = MEDIUM, 3+ = HIGH |
| 10 | **MAJOR** | CRS002 | Broadcast state empty on first event → no fallback threshold defined | Explicit: "initialize state with current position; no violation possible" |
| 11 | **MAJOR** | TQS Aggregation | C dimension = 1.0 for NYC TLC → spec conflates two datasets | Explicit: "C = 1.0 on NYC TLC; C = f(CRS001+CRS002) on NYC MTA Bus" |
| 12 | **MAJOR** | CRS001 | Upper bound [2, 100] km/h hardcoded — NYC MTA Bus urban speeds are 20–50 km/h | Add: "100 km/h is physically implausible for NYC MTA Bus; updated from 120 to 100 km/h to close B3 detection gap" |
| 13 | **MAJOR** | CRS001 | Lower bound gap: moderate spoofing in 2–20 km/h range (B3) | Document: "2–20 km/h speed range = CRS002 territory; CRS001 lower bound gap acknowledged" |
| 14 | **MAJOR** | L0–L5 Context | Broadcast state initialization — no spec for first-event behavior | Explicit: "first event → L5 physics priors → populate state → subsequent events use L0-L4" |
| 15 | **MAJOR** | CRS002 | `only 1 prior position in window` → comparison is to that single position | Explicit: "compare to most recent prior position" |
| 16 | **MAJOR** | CRS002 | `All positions older than 30s` → "no comparison needed" → passes, but no action defined | Explicit: "update state with current position; pass silently" |
| 17 | **MAJOR** | CRS003 | `time_delta = 0` in CRS001 → flagged as GPS_SPOOFING; CRS002 spec reuses same case | Explicit: "CRS001 handles time_delta=0; CRS002 receives already-processed positions" |
| 18 | **MAJOR** | CRS003 | TTL = 310s but window = 300s → 10s overlap; reason unspecified | Explicit: "310s TTL allows 10s grace for late-arriving duplicates" |
| 19 | **MAJOR** | SYN001 | `math.inf` not a violation by itself → no rule checks range after inf detection | SYN002/SEM001/SEM002 must handle inf as OUT_OF_RANGE, not pass-through |
| 20 | **MAJOR** | TQS Aggregation | Individual dimension zero-division not explicitly guarded | Guard: `if dimension_total == 0: score = 1.0` |
| 21 | **MINOR** | L0–L5 Context | `event.zone_category is None` → fallback to L2 — not explicitly stated | Explicit: "zone_category extraction failure → fall back to L2" |
| 22 | **MINOR** | CRS001 | Speed = 0, time_delta > 0 → below lower bound → flagged VIOLATION | Clarify: "vehicles at traffic lights legitimately have speed=0; 2 km/h threshold may be too aggressive for urban stop-and-go" |
| 23 | **MINOR** | CRS002 | "Same position reported multiple times" → Haversine = 0 → not a jump | But if same position repeats at 5+ timestamps, may indicate stale sensor — consider GTFSSem002 (stale > 5 min) |
| 24 | **MINOR** | CRS001 | GPS coordinates outside valid range → SYN003 violation | Note: CRS001 processes lat/lon from GTFS; SYN003 is separate rule; sequencing must be explicit |
| 25 | **MINOR** | CRS002 | Hash collision (SHA256) → "astronomically unlikely → ignore" | Document: "SHA256 collision probability is 2^-256; no mitigation needed for research platform" |
| 26 | **MINOR** | CRS003 | CRS003 runs on BOTH NYC TLC and NYC MTA Bus — NYC TLC has no lat/lon | Confirm: `hash = SHA256(trip_id + timestamp)` for NYC TLC |
| 27 | **MINOR** | CRS001 | `vehicleId is None` → "cannot key state → should flag violation" | Assign: SYN001 (NULL on required field) |
| 28 | **MINOR** | SYN001 | `float('nan')` vs `numpy.nan` vs `pandas.NA` — three NaN types, one guard needed | Specify: "use `math.isnan()` for float.nan; `np.isnan()` for np.nan; `pd.isna()` for pd.NA" |
| 29 | **MINOR** | CRS002 | `lat or lon is None` → "SYN001 before jump check" — sequencing with CRS001 unspecified | Explicit: "SYN001 runs BEFORE CRS002; CRS002 receives pre-validated lat/lon" |
| 30 | **MINOR** | TQS Aggregation | V1/V2/V3 weight selection criteria not specified | Add: "V2 (domain-prioritized) is primary; criteria: Validity (V) most critical for taxi data quality" |
| 31 | **MINOR** | CRS002 | 100m/30s = 10% of maximum distance (1000m) → justification exists but confidence not derived | Consider: "lower confidence if jump < 30% of max (300m); higher if > 60% (600m)" |
| 32 | **MINOR** | L0–L5 Context | L4 minimum = 5 samples — source is "per rule from NYC TLC metadata" but rule is not named | Cite the specific NYC TLC metadata rule that sets min=5 |
| 33 | **MINOR** | CRS003 | TTL = 310s; event arrives 311s later → hash no longer in state → treated as new | Correct: 311s > 310s TTL; this is the intended boundary behavior |
| 34 | **MINOR** | CRS001 | Haversine distance tiny (<1m) → "stationary vehicle → pass at next update" | Clarify: "speed=0 with non-zero time_delta → very slow (not stationary); flag if time_delta > 60s" |
| 35 | **MINOR** | SYN001 | Empty string `''` → "not a violation (empty is not null)" | Define per-field: which fields allow empty string vs null? |
| 36 | **MINOR** | CRS002 | "GPS jump >400m in 30s" — GTFS-realtime default update interval = 1s, not 30s | Resolve: "GTFS-rt default = 1s; vehicles skipping reports accumulate up to 30s; 100m/30s conservative for worst-case gap" |

---

## Algorithm 1: L0–L5 Context Key Computation

### Edge Case Audit

| Edge Case | Current Handling | Severity | Recommendation |
|-----------|-----------------|:--------:|----------------|
| `event.hour is None` | Should fall back to L4 | **CRITICAL** | Add explicit spec: "hour extraction returns None → L4 fallback" |
| `event.hour is NaN` | NaN guard missing (B1) | **CRITICAL** | SYN001 NaN guard must run BEFORE context key extraction; NaN in hour field → SYN001 violation, not fallback |
| `event.zone_category is None` | Should fall back to L2 | MINOR | Add explicit spec: "zone_category extraction failure → L2 fallback" |
| `event is None` entirely | Should return L4 + global threshold | MAJOR | Add explicit: "null event → L4 global fallback + HIGH severity violation" |
| Context key not found in broadcast state | Should fall back | MAJOR | Explicit spec: "key not in broadcast → L3 → L2 → L1 → L0 → L4 → L5" |
| Broadcast state is empty (first event) | Should use L5 physics priors | MAJOR | Explicit: "empty state → L5 priors → populate state with first event → subsequent events use L0-L4" |
| Context key exists but count < min_samples | **Behavior unspecified** | **MAJOR** | Add: "key exists with count < min_samples → fall back to next level (same as key not found)" |
| `event` contains non-NaN but invalid type for hour (e.g., string) | Type mismatch not handled | MAJOR | SYN001 TYPE_MISMATCH before context extraction |
| D4 (External context — holiday indicator) | "PARTIAL" in verification (I16) | MAJOR | D4 is a stub; context key computation cannot use holiday indicator until D4 is implemented |

### SOLID Audit

| Function | Responsibility | Violation? | Fix |
|----------|---------------|:----------:|-----|
| `ContextDimension.temporal()` | Extract temporal fields from event | No | — |
| `ContextDimension.spatial()` | Extract spatial fields from event | No | — |
| `ContextDimension.entity()` | Extract operational fields from event | No | — |
| `ContextDimension.source()` | Extract data characteristics from event | No | — |
| `get_context_key(level)` | Construct context key string from extracted fields | No | — |
| `get_threshold_with_fallback(ctx_key)` | Lookup threshold; fall back on insufficient samples | **Yes** | Split into: (a) `lookup_threshold(ctx_key)` and (b) `resolve_fallback(ctx_key, available_samples)` |
| Broadcast state population | Populate broadcast state with L0-L5 thresholds | **Yes** | Separate initialization logic from hot-path evaluation |

### Complexity Audit

| Function | Branches | Complexity | Flag? |
|----------|:--------:|:----------:|:-----:|
| `get_threshold_with_fallback()` | ~12 (6 levels × fall-forward + empty state) | High | ✓ |
| `ContextDimension` extractors (×4) | 3–5 each | Low | ✗ |
| L0 key construction | 3 nested field extractions | Low | ✗ |
| Broadcast state population | 2 (empty vs. populated) | Low | ✗ |

### Error Handling Audit

| Scenario | Current Behavior | Severity | Fix |
|----------|------------------|:--------:|-----|
| Broadcast state returns None | Falls through to next level | MAJOR | Explicit: "None → next level" |
| L0–L4 all return insufficient samples | Falls to L5 physics priors | MAJOR | Explicit: "exhausted L0-L4 → L5" |
| Sample count equals exactly min_samples boundary | Unspecified | MAJOR | Explicit: "count >= min_samples → use this level; count < min_samples → fall back" |
| Flink broadcast state not yet initialized | Unspecified | MAJOR | Explicit: "state initialization → L5 → async populate → L0-L4 available" |
| L5 physics priors used | No tracking of fallback level | MAJOR | Emit `fallback_level` metric for Prometheus |

### Testability Audit

| Component | Testable? | Test Approach |
|-----------|:---------:|---------------|
| Context dimension extractors | Yes | Unit test with mock events; verify key strings |
| `get_context_key()` per level | Yes | Parametrized tests: valid event → L0 key; None fields → correct fallback level |
| `get_threshold_with_fallback()` | Partial | Unit test with mocked broadcast state; cannot test Flink state backend directly |
| Broadcast state population | No | Integration test with real Flink; not unit-testable |
| NaN propagation through context keys | Yes | Test: NaN in hour → SYN001 violation BEFORE context lookup |

---

## Algorithm 2: CRS001 — GPS Speed Bounds

### Edge Case Audit

| Edge Case | Current Handling | Severity | Recommendation |
|-----------|-----------------|:--------:|----------------|
| `lat` or `lon` is None | Should flag SYN001 violation | MAJOR | SYN001 runs BEFORE CRS001; CRS001 receives pre-validated coordinates |
| `lat` or `lon` is NaN | Should flag SYN001 violation (B1) | **CRITICAL** | `math.isnan()` guard required; NaN lat/lon must not produce NaN speed |
| `timestamp` is None | Should flag SYN001 violation | MAJOR | Add explicit: "None timestamp → SYN001 NULL violation" |
| `prevTimestamp` is None (first position) | Cannot compute speed; silently passes | MAJOR | Explicit: "initialize state with current position; pass silently; log initialization" |
| `time_delta = 0` (two positions at same timestamp) | **Divide-by-zero → should flag GPS_SPOOFING** | **CRITICAL** | Guard: `if time_delta == 0: emit GPS_SPOOFING violation (CRS002)` |
| `distance = 0`, `time_delta > 0` | speed = 0 → below lower bound (2 km/h) → **VIOLATION** | MINOR | Clarify: "vehicles at traffic lights legitimately have speed=0; consider time_delta threshold" |
| Speed computed, Haversine tiny (<1m) | "stationary vehicle → pass at next update" | MINOR | Clarify: "speed=0 with non-zero time_delta → very slow; flag if time_delta > 60s" |
| GPS coordinates outside valid range (lat > 90, lon > 180) | SYN003 violation | MINOR | Note: CRS001 runs after SYN003; SYN003 validates range first |
| `vehicleId` is None | Cannot key state; should flag violation | MINOR | Assign SYN001 NULL violation; vehicleId is required for stateful tracking |
| Hardcoded [2, 100] km/h | Upper bound far above NYC MTA Bus urban speed (20–50 km/h) | MAJOR | Add: "100 km/h is physically implausible; updated from 120 to 100 km/h to close B3 detection gap" |
| Moderate spoofing in 2–20 km/h range | Gap: CRS002 detects jumps but not slow-speed anomalies | MAJOR | Document: "2–20 km/h range → CRS002 territory; CRS001 lower bound gap acknowledged (B3)" |

### SOLID Audit

| Function | Responsibility | Violation? | Fix |
|----------|---------------|:----------:|-----|
| `CRS001KeyedProcessFunction.processElement()` | GPS coordinate validation + speed computation + violation emission | **Yes** | Split: (a) `validate_coordinates(lat, lon, timestamp)` → boolean; (b) `compute_speed(current, prev)` → float; (c) `evaluate_speed_bound(speed)` → Optional[Violation] |
| Haversine distance computation | Pure calculation of distance between two GPS points | No | — |
| Violation construction | Build Violation object | No | — |
| State management | Store previous position per vehicle | No | — |

### Complexity Audit

| Function | Branches | Complexity | Flag? |
|----------|:--------:|:----------:|:-----:|
| `processElement()` | ~14 (SYN001 checks × 3, state checks × 2, range checks × 2, division guard, TTL, initialization, normal path, violation path) | **High** | ✓ |
| Haversine computation | 3 (edge cases) | Low | ✗ |
| Speed range check | 3 (below lower, in range, above upper) | Low | ✗ |

### Error Handling Audit

| Scenario | Current Behavior | Severity | Fix |
|----------|------------------|:--------:|-----|
| Division by zero (time_delta=0) | Unhandled → JVM crash or NaN speed | **CRITICAL** | Guard before division: `if time_delta_ms == 0: handle as CRS002 trigger` |
| NaN speed produced | NaN comparison always false → violation not flagged | **CRITICAL** | Guard with `Double.isNaN(speed)` |
| State TTL expired | Flink state TTL handles automatically | MAJOR | Explicit: "Flink TTL = 10 min; state auto-evicts" |
| First position (prevTimestamp=None) | Pass silently, initialize state | MAJOR | Explicit + logging |

### Testability Audit

| Component | Testable? | Test Approach |
|-----------|:---------:|---------------|
| Haversine computation | Yes | Parametrized: known lat/lon pairs → verified distances |
| Speed computation | Yes | Mock current/prev positions; verify speed calculation |
| Speed range check | Yes | Test: below-lower, in-range, above-upper boundaries |
| `processElement()` integration | Partial | Unit test with mock state; integration test with real Flink |
| Divide-by-zero guard | Yes | Test: time_delta=0 → GPS_SPOOFING violation emitted |

---

## Algorithm 3: CRS002 — GPS Jump Detection

### Edge Case Audit

| Edge Case | Current Handling | Severity | Recommendation |
|-----------|-----------------|:--------:|----------------|
| First position for vehicle | Pass silently, initialize state | MAJOR | Explicit: "first position → store in state → pass silently" |
| Only 1 prior position in window | Compare to it | MAJOR | Explicit: "compare to most recent prior position" |
| All positions in window older than 30s | "no comparison needed → pass" | MAJOR | Explicit: "update state with current position; pass silently" |
| Jump detected, only 1 prior position | "flag with lower confidence" | MAJOR | Define explicit tiers: 1 prior = LOW; 2+ prior = MEDIUM; 3+ = HIGH confidence |
| Same position reported multiple times | Haversine = 0 → not a jump → pass | MAJOR | Repeated same position → possible stale sensor → consider GTFSSem002 trigger |
| `position.lat` or `position.lon` is None | SYN001 before jump check | MAJOR | Explicit: "SYN001 validates coordinates BEFORE CRS002 evaluation" |
| Jump distance near threshold boundary (95–105m) | No boundary handling | MINOR | Add tolerance: ">400m" means >=101m; 100m exactly → pass (conservative) |
| CRS002 severity for 2–20 km/h GPS_SPOOFING | Absent from spec | **CRITICAL** | Add: `2–20 km/h → HIGH GPS_SPOOFING` per severity table |
| CRS001 time_delta=0 handling | Handled in CRS001, not CRS002 | MAJOR | Explicit: "CRS001 handles time_delta=0; CRS002 receives cleaned positions" |
| GPS coordinates outside valid range | SYN003 before CRS002 | MINOR | Sequencing must be explicit |

### SOLID Audit

| Function | Responsibility | Violation? | Fix |
|----------|---------------|:----------:|-----|
| `CRS002KeyedProcessFunction.processElement()` | Jump detection + state management + confidence scoring + violation | **Yes** | Split: (a) `detect_jump(current, window)` returns (jump_magnitude, confidence); (b) `emit_violation_if_needed()` |
| State window management | Maintain last N positions per vehicle | **Yes** | Extract as `VehiclePositionWindow` class with `add()`, `get_positions()`, `get_most_recent()` |
| Jump magnitude computation | Haversine distance | No | — |
| Confidence tier assignment | Assign confidence based on prior position count | **Yes** | Extract as `ConfidenceTier.compute(prior_count, jump_magnitude)` |

### Complexity Audit

| Function | Branches | Complexity | Flag? |
|----------|:--------:|:----------:|:-----:|
| `processElement()` | ~15 (SYN001 validation, first-position, stale-window, jump-detected, jump-not-detected, confidence tiers × 3, same-position, initialization, normal-path) | **High** | ✓ |
| State window management | 4 (add, get, evict old, handle empty) | Low | ✗ |
| Confidence scoring | 4 (LOW/MEDIUM/HIGH/VERY_HIGH) | Low | ✗ |

### Error Handling Audit

| Scenario | Current Behavior | Severity | Fix |
|----------|------------------|:--------:|-----|
| State window is empty (first position) | Pass silently | MAJOR | Explicit + logging |
| All prior positions older than 30s | Pass silently, update state | MAJOR | Explicit: "no comparison; state updated" |
| Invalid coordinates before jump check | SYN001 validation runs first | MAJOR | Explicit sequencing |
| Jump detected but only 1 prior (LOW confidence) | Flagged with LOW confidence | MAJOR | Explicit: "LOW confidence → flag with confidence=LOW; do not suppress" |

### Testability Audit

| Component | Testable? | Test Approach |
|-----------|:---------:|---------------|
| Jump magnitude computation | Yes | Known lat/lon pairs → verified Haversine distances |
| Confidence tier assignment | Yes | Parametrized: prior_count=1→LOW, 2→MEDIUM, 3+→HIGH |
| Jump detection (no jump) | Yes | Same position × 5 timestamps → pass |
| Jump detection (jump detected) | Yes | Positions 100m apart in 30s → violation emitted |
| State window management | Partial | Unit test with mock state; integration test for TTL/eviction |
| `processElement()` integration | Partial | Unit test with mock KeyedProcessFunction context |

---

## Algorithm 4: CRS003 — Event Deduplication

### Edge Case Audit

| Edge Case | Current Handling | Severity | Recommendation |
|-----------|-----------------|:--------:|----------------|
| `trip_id` is None | Cannot hash → flag SYN001 violation | MAJOR | Explicit: "None trip_id → SYN001 NULL violation; event not added to dedup window" |
| Same hash with different `vehicleId` | "considered duplicate (hash is identity)" | **CRITICAL** | Add: "same hash + different vehicleId = possible vehicle swap or entity confusion → flag as DUPLICATE with vehicleId_mismatch=true" |
| Hash collision (SHA256) | "astronomically unlikely (2^-256) → ignore" | MINOR | Document as accepted risk |
| Event arrives 311s later | TTL=310s; hash not in state → treated as new | MINOR | Correct behavior |
| CRS003 blocked by replay gate (NG-4) | Replay gate blocked; **recall and precision UNMEASURABLE** | **CRITICAL** | `synthetic_injector.py` must emit TWO records; fix is P0. Until fixed, CRS003 recall and precision are **Tier 3 — Unmeasurable**. |
| CRS003 runs on NYC TLC (no lat/lon) | Spec says hash = SHA256(trip_id + timestamp + lat + lon) | **CRITICAL** | NYC TLC has no lat/lon; clarify: "hash for NYC TLC = SHA256(trip_id + timestamp + PULocationID + DOLocationID)" |

### SOLID Audit

| Function | Responsibility | Violation? | Fix |
|----------|---------------|:----------:|-----|
| Hash computation | SHA256(trip_id + timestamp + location) | **Yes** | Split: (a) `compute_hash(event)`; (b) `check_dedup(hash, event)` — current mixes hashing with dedup check |
| Hash-based dedup check | Look up hash in state; emit if found | No | — |
| State TTL management | Evict hashes older than 310s | No | Flink TTL handles |
| VehicleId consistency check | Verify vehicleId matches across same hash | **Yes** | Extract: `check_vehicle_consistency(hash, vehicleId, state)` |

### Complexity Audit

| Function | Branches | Complexity | Flag? |
|----------|:--------:|:----------:|:-----:|
| `compute_hash()` | 5 (None checks for each field, type checks) | Medium | ✗ |
| `check_dedup()` | 3 (hash found, hash not found, hash-found-different-vehicleId) | Low | ✗ |
| `CRS003KeyedProcessFunction.processElement()` | 4 (hash computation, state lookup, emission logic, state update) | Low | ✗ |

### Error Handling Audit

| Scenario | Current Behavior | Severity | Fix |
|----------|------------------|:--------:|-----|
| Hash computation fails (None fields) | SYN001 violation emitted; event not hashed | MAJOR | Explicit: "SYN001 emitted first; event excluded from dedup window" |
| Hash found in state (duplicate detected) | Violation emitted; state not updated | MAJOR | Explicit: "violation emitted; original hash remains in state with original timestamp" |
| Hash not found in state (new event) | Added to state with TTL=310s | MAJOR | Explicit + Flink TTL config |
| Same hash + different vehicleId | Currently: same behavior as duplicate | **CRITICAL** | Distinguish: "same hash + same vehicleId = true duplicate; same hash + different vehicleId = entity swap" |

### Testability Audit

| Component | Testable? | Test Approach |
|-----------|:---------:|---------------|
| Hash computation | Yes | Test: known inputs → known SHA256 outputs |
| Dedup check (duplicate) | Yes | Emit same hash twice → second emission → violation |
| Dedup check (no duplicate) | Yes | Emit different hashes → no violation |
| VehicleId consistency | Yes | Two events, same hash, different vehicleId → vehicleId_mismatch flag set |
| TTL behavior | Partial | Test with mock TTL; integration test for Flink state TTL |
| NG-4 fix (is_replay=False tagging) | Yes | Test: inject duplicate → verify TWO records emitted with linked entity_index |
| **CRS003 recall/precision** | **No** | **NG-4 blocks measurement**: replay suppression gate blocks synthetic duplicates → CRS003 has no original to compare against → recall = 0% by construction; precision cannot be computed without valid ground-truth matching |

---

## Algorithm 5: SYN001 — Null/NaN Check

### Edge Case Audit

| Edge Case | Current Handling | Severity | Recommendation |
|-----------|-----------------|:--------:|----------------|
| `float('nan')` in Python | Must use `math.isnan()` — NOT `x != x` | **CRITICAL** | Add explicit: "use `math.isnan()` for float.nan; NOT `x != x` (fails for None)" |
| `numpy.nan` | Must use `np.isnan()` or `pd.isna()` | **CRITICAL** | Add explicit: "use `np.isnan()` for np.nan; use `pd.isna()` for pd.NA" |
| Empty string `''` | Not a violation | MINOR | Explicit: define per-field — which fields allow empty vs null? |
| `None` | VIOLATION (NULL) | MAJOR | Add: "None → NULL violation; severity per field criticality" |
| Wrong type (string where int expected) | VIOLATION (TYPE_MISMATCH) | MAJOR | Add: "TYPE_MISMATCH → violation; include expected vs actual type in details" |
| `math.inf` | Not a violation by itself | MAJOR | Add: "inf → not NULL/NAN; must be caught by range check in SYN002/SEM001/SEM002; if no range check, inf passes through" |
| NaN propagated to context key computation | B1: NaN silently passes through | **CRITICAL** | Explicit: "SYN001 runs BEFORE any context key extraction; NaN in required field → SYN001 violation" |
| NaN in optional field | Not a violation | MAJOR | Explicit: "NaN in optional field → field treated as missing → no violation" |
| NaN in lat/lon for CRS rules | B1 affects CRS001/CRS002 | **CRITICAL** | Explicit: "CRS001/CRS002 MUST validate lat/lon with NaN guard before Haversine computation" |

### SOLID Audit

| Function | Responsibility | Violation? | Fix |
|----------|---------------|:----------:|-----|
| `check_null(value, field_name)` | Detect NULL violations | No | — |
| `check_nan(value, field_name)` | Detect NAN violations | **Yes** | Split: `is_nan(value)` → boolean; separate from violation construction |
| `check_type(value, expected_type, field_name)` | Detect TYPE_MISMATCH violations | No | — |
| `synthesize_violation(reason, field, value, details)` | Build Violation object | No | — |
| `SYN001Rule.evaluate(ctx)` | Orchestrate null/NaN/type checks | No | — |

### Complexity Audit

| Function | Branches | Complexity | Flag? |
|----------|:--------:|:----------:|:-----:|
| `SYN001Rule.evaluate()` | 6 (null check, nan check, type check × N types, pass-through) | Medium | ✗ |
| `is_nan()` | 4 (float.nan, np.nan, pd.NA, other) | Medium | ✗ |
| `check_type()` | 3–5 per type (string, int, float, bool, datetime) | Medium | ✗ |

### Error Handling Audit

| Scenario | Current Behavior | Severity | Fix |
|----------|------------------|:--------:|-----|
| NaN not caught by `x != x` trick | Silent pass-through | **CRITICAL** | Mandate `math.isnan()` / `np.isnan()` / `pd.isna()` |
| `None` vs `NaN` confusion | Both treated as violation | MAJOR | Explicit: "None → NULL; NaN → NAN; these are distinct reason codes" |
| `inf` not caught | Passes through | MAJOR | Add: "SYN002/SEM001 must handle inf as OUT_OF_RANGE" |

### Testability Audit

| Component | Testable? | Test Approach |
|-----------|:---------:|---------------|
| NULL check | Yes | Test: None → violation; non-None → pass |
| NAN check (float) | Yes | Test: `float('nan')` → violation; `1.0` → pass |
| NAN check (numpy) | Yes | Test: `np.nan` → violation; `np.array([1.0])[0]` → pass |
| Type mismatch | Yes | Test: string where int expected → violation |
| Empty string | Yes | Test: `''` → pass (or per-field policy) |
| NaN propagation | Yes | Test: NaN in event.hour → SYN001 violation; event does not reach context key extraction |

---

## Algorithm 6: TQS Aggregation

### Edge Case Audit

| Edge Case | Current Handling | Severity | Recommendation |
|-----------|-----------------|:--------:|----------------|
| `total_events = 0` | Division by zero → crash or NaN | **CRITICAL** | Guard: `if total_events == 0: emit TQS = None or skip aggregation; log warning` |
| No violations in window | Tm=Cn=Ac=Cs=1.0, Uv=0.0, TQS=0.85 | MAJOR | Explicit: "zero violations → perfect quality scores" |
| All fields out of range | Ac=0.0, TQS < 0.85 | MAJOR | Explicit: "all-events anomalous → degraded quality scores" |
| CRS violations on NYC TLC | C dimension not applicable on NYC TLC | MAJOR | Explicit: "Cs on NYC TLC uses price-per-mile consistency; always active; not artificially set to 1.0" |
| Individual dimension zero-division | Not explicitly guarded | **MAJOR** | Guard: `if dimension_total == 0: score = 1.0` (no events in dimension → no violations → perfect score) |
| TQS weight selection criteria | V2 primary, but criteria not stated | MINOR | Add: "V2 (domain-prioritized): Completeness and Consistency weighted highest for taxi and transit DQ" |
| Window duration = 0 | Aggregation over zero-length window | MINOR | Guard: skip aggregation if window is empty |
| Context-decomposed TQS — empty context cell | No events → TQS=None | MINOR | Explicit: "context cell with 0 events → TQS=None; not counted in average" |
| Bootstrap CI computation | 1,000 iterations required | MAJOR | Explicit: "bootstrap on TQS dimension scores, not composite; composite CI derived from dimension CIs" |

### SOLID Audit

| Function | Responsibility | Violation? | Fix |
|----------|---------------|:----------:|-----|
| `compute_dimension_score(violations, total, rule_set)` | Compute V, C, Cn, P individually | **Yes** | Extract: `DimensionScore.compute(dimension, violations, total)` — aggregator should not compute individual scores |
| `compute_composite_tqs(V, C, Cn, P, weights)` | Weighted sum of dimensions | **Yes** | Extract: `TQSComposite.compute(dimensions, variant)` — separate from aggregation logic |
| `aggregate_by_context_cell()` | Group violations by L0 context key | No | — |
| Zero-division guards | Prevent division by zero | No | Already correct responsibility |

### Complexity Audit

| Function | Branches | Complexity | Flag? |
|----------|:--------:|:----------:|:-----:|
| `TQSaggregator.aggregate()` | 9 (total_events==0, Tm, Cn, Ac, Cs, Uv, each dimension, composite, context-decomposed) | **High** | ✓ |
| `compute_dimension_score()` | 3 (violations==0, total==0, normal) | Low | ✗ |
| `compute_composite_tqs()` | 3 (V1, V2, V3 weight selection, null weights) | Low | ✗ |
| Context-decomposed grouping | 2 (with context key, without) | Low | ✗ |

### Error Handling Audit

| Scenario | Current Behavior | Severity | Fix |
|----------|------------------|:--------:|-----|
| total_events = 0 | Divide by zero | **CRITICAL** | `if total_events == 0: return TQSResult(N=0, tqs=null)` |
| dimension_total = 0 | Divide by zero per dimension | **MAJOR** | `if dimension_total == 0: return 1.0` (no events in dimension = no evidence of bad quality) |
| V2 variant weights = None | Composite = NaN | MINOR | Guard: `if weights is None: use V2 defaults` |
| Missing violation counts for some rules | Score computed on partial data | MAJOR | Warn: "rules not found in window; dimension score may be inaccurate" |
| NYC MTA Bus vs NYC TLC scoring | C dimension conflates two datasets | MAJOR | Explicit: "compute TQS separately per entity_type; aggregate only when mixing is intentional" |

### Testability Audit

| Component | Testable? | Test Approach |
|-----------|:---------:|---------------|
| `compute_dimension_score()` | Yes | Parametrized: violations=0→1.0; all→0.0; partial→correct fraction |
| `compute_composite_tqs()` | Yes | Test V1, V2, V3: known inputs → known outputs |
| Zero-division guards | Yes | Test: total_events=0 → returns null; dimension_total=0 → returns 1.0 |
| Context-decomposed aggregation | Yes | Test: same context key → aggregated together; different keys → separate |
| TQS score trend over time | Partial | Integration test with time-series window; cannot unit test trend behavior |
| V2 weight selection | Yes | Test: variant=V2 → weights=[0.20, 0.25, 0.20, 0.25, 0.10] |

---

## Cross-Cutting Issues

### A. Missing Explicit Sequencing Between Rules

No document specifies the order in which SYN001, SYN002, SYN003, CRS001, CRS002, CRS003 execute relative to each other.

**Recommendation**: Add explicit rule execution ordering:

```
Raw Event → SYN001 → SYN002 → SYN003 → [CRS001 || CRS002] → CRS003 → TQS Aggregation
```

Where `[CRS001 || CRS002]` are parallel (independent) and CRS003 runs last (uses all prior validation state).

### B. NaN Propagation Chain

The NaN pass-through (B1) creates a propagation chain:

```
event.hour = NaN → context key extraction → broadcast state lookup with NaN key → key not found → fallback to L4
```

vs.

```
event.hour = NaN → SYN001 fires → event rejected → no context lookup
```

**These produce different outcomes.** The spec must establish that SYN001 runs BEFORE context key computation.

### C. CRS002 Severity Gap

The severity table maps:
- `CRS002 GPS_SPOOFING (< 1 km/h)` → CRITICAL
- `CRS002 GPS_SPOOFING (1–20 km/h)` → HIGH

But the CRS002 algorithm computes Haversine jump distance — it does not compute speed. The mapping between jump magnitude (meters) and speed (km/h) requires `time_delta`, which CRS002 does not always have (it compares positions from a window, not necessarily consecutive positions).

**Recommendation**: Distinguish two CRS002 modes:
- **Consecutive mode** (prevTimestamp known): `speed = distance / time_delta` → use speed-based severity
- **Window mode** (non-consecutive): `distance only` → use jump-magnitude-based severity (>400m = HIGH, >500m = CRITICAL)

### D. D4 External Context Is a Stub

D4 (External: holiday indicator) is marked PARTIAL in the verification report (Issue I16). All context key computation at L0–L4 that uses D4 fields will silently degrade to the next level.

### E. TQS Circularity — Resolved

The original TQS design used `TQS = 1 − violation_rate`, making correlation with injection rate guaranteed by construction. This has been replaced by a stream-intrinsic design: `TQS = f(Tm, Cn, Ac, Cs, Uv)` where each dimension is computed from raw event properties only. Correlation with injection rate is now expected (anomalies affect raw values) but NOT guaranteed, and must be validated empirically.

### F. CRS003 NYC TLC Hash Is Under-Specified

CRS003 hash for NYC TLC is specified as `SHA256(trip_id + timestamp + lat + lon)`, but NYC TLC has no GPS coordinates. Must specify: `hash = SHA256(trip_id + timestamp + PULocationID + DOLocationID)` for NYC TLC.

### G. `processing_latency_ms` Hardcoded to 0 (B6)

No algorithm specifies how `processing_latency_ms` should be computed. For Flink: `processing_latency_ms = System.currentTimeMillis() - event.getEventTimestamp()`.

### H. CRS003 Recall and Precision Are UNMEASURABLE (NG-4)

**Status: CRITICAL — Tier 3 (Unmeasurable)**

CRS003 recall and precision cannot be measured because the duplicate injection mechanism does NOT emit both the original event and the duplicate event. CRS003 requires two records (original + duplicate) to detect the duplicate: the first occurrence is stored in state, and the second occurrence triggers the violation.

**How CRS003 works**:
```
1. Original event arrives → hash stored in per-trip state (TTL=310s)
2. Duplicate event arrives (same hash) → hash found in state → DUPLICATE violation emitted
```
CRS003 recall = (duplicates detected) / (duplicates injected). If only the duplicate is emitted (not the original), CRS003 never stores the original in state, so the "duplicate" has no original to compare against. The second occurrence is treated as the first occurrence — recall = 0% by construction.

**Impact on evaluation**:
- H3-CRS003 is Tier 3 — Unmeasurable
- CRS layer evaluation is incomplete: CRS001 and CRS002 can be measured, CRS003 cannot
- TQS Uv dimension is still measurable (raw hash deduplication is independent of CRS003 rule)
- CRS003 precision cannot be computed without valid ground-truth matching

**Fix required**: `synthetic_injector.py` must emit TWO records per duplicate injection:
- Record 1: original event with `entity_index = N`, `is_original = true`
- Record 2: duplicate event with `entity_index_duplicate = N`, `is_duplicate = true`, `original_entity_index = N`

**Mitigation until NG-4 is fixed**:
- Explicitly scope CRS evaluation to CRS001 and CRS002 only
- Report CRS003 metrics as Tier 3 — Unmeasurable
- Do not claim CRS003 recall or precision in evaluation results

---

## SOLID Principles: Summary Assessment

| Principle | Status | Violations Found |
|-----------|:------:|-----------------|
| **Single Responsibility** | ✗ FAIL | CRS001, CRS002, TQS aggregator each mix 2–3 responsibilities |
| **Open/Closed** | ✓ PASS | New rules add new classes, no modification to base |
| **Liskov Substitution** | ✓ PASS | Rule interface is consistent |
| **Interface Segregation** | ✓ PASS | Small, focused rule interface |
| **Dependency Inversion** | ✓ PASS | Threshold engine injected; Violation is a data class |

**Most critical SOLID fix**: Refactor `CRS002KeyedProcessFunction` — it currently handles state window management, jump magnitude computation, confidence tier assignment, and violation construction. Extract state window management into a dedicated `VehiclePositionWindow` class.

---

## Cyclomatic Complexity Summary

| Algorithm | Highest Complexity Function | Branch Count | Threshold | Flag |
|-----------|---------------------------|:------------:|:---------:|:----:|
| L0–L5 Context | `get_threshold_with_fallback()` | ~12 | >10 | ✓ |
| CRS001 | `processElement()` | ~14 | >10 | ✓ |
| CRS002 | `processElement()` | ~15 | >10 | ✓ |
| CRS003 | `compute_hash()` + `check_dedup()` | 5 | >10 | ✗ |
| SYN001 | `evaluate()` | 6 | >10 | ✗ |
| TQS Aggregation | `aggregate()` | 9 | >10 | ✓ |

**Two functions flagged**: CRS001 and CRS002 `processElement()` both exceed the >10 branch threshold. Refactoring extract methods (per SOLID recommendations) will reduce branch counts.

---

## Priority Action Items (Before Implementation)

### P0 — Must Fix Before Any Implementation

| # | Action | Reason |
|---|--------|--------|
| 1 | **Fix NG-4**: tag synthetic duplicates `is_replay=False` to bypass replay suppression gate | CRS003 recall and precision are **Tier 3 — Unmeasurable**; CRS layer evaluation incomplete; P0 |
| 2 | **Fix B1**: Add `math.isnan()` guard to SYN001; SYN001 runs BEFORE context key computation | NaN silently passes through |
| 3 | **Fix B6**: Specify `processing_latency_ms = System.currentTimeMillis() - event.getEventTimestamp()` | Latency hardcoded to 0 |
| 4 | **Clarify CRS002 severity**: Add explicit severity mapping for jump-distance-based (vs speed-based) violations | 2–20 km/h range gap undocumented |
| 5 | **Specify CRS003 NYC TLC hash**: Add: `hash = SHA256(trip_id + timestamp + PULocationID + DOLocationID)` for NYC TLC | Current spec contradicts NYC TLC data model |

### P1 — Must Fix Before Phase 2 (CRS Rules)

| # | Action | Reason |
|---|--------|--------|
| 6 | **Refactor CRS001**: Split `processElement()` into coordinate validation, speed computation, range check, violation construction | Exceeds >10 branch complexity threshold |
| 7 | **Refactor CRS002**: Extract `VehiclePositionWindow` class; define explicit confidence tiers | Exceeds >10 branch complexity threshold; mixed responsibilities |
| 8 | **Add divide-by-zero guard to CRS001**: `if time_delta == 0: emit GPS_SPOOFING violation (CRS002)` | JVM crash or NaN speed; CRITICAL severity |
| 9 | **Add vehicleId consistency check to CRS003**: same hash + different vehicleId → `vehicleId_mismatch=true` | False duplicate on entity swap |
| 10 | **Specify rule execution ordering**: SYN001 → SYN002 → SYN003 → [CRS001 || CRS002] → CRS003 → TQS | Missing sequencing spec |

### P2 — Must Fix Before Evaluation

| # | Action | Reason |
|---|--------|--------|
| 11 | **Add TQS zero-division guard**: `if total_events == 0: return TQSResult(N=0, tqs=null)` | Crash or NaN; CRITICAL severity |
| 12 | **Add TQS per-dimension zero-division guard**: `if dimension_total == 0: return 1.0` | Per-dimension crash; MAJOR severity |
| 13 | **Define CRS002 confidence tiers**: 1 prior = LOW, 2+ = MEDIUM, 3+ = HIGH | "Lower confidence" is vague |
| 14 | **Implement D4 (External context)**: or explicitly document it as deferred, not partial | D4 is a stub; context computation incomplete |
| 15 | **Add L0–L4 sample count boundary**: `count >= min_samples → use this level` | Behavior unspecified for count < min_samples |

### P3 — Recommended Before Paper Submission

| # | Action | Reason |
|---|--------|--------|
| 16 | **Refactor TQS aggregator**: Split into `DimensionScore` and `TQSComposite` classes | Mixed responsibilities |
| 17 | **Add TQS variant selection criteria**: Document why V2 is primary | Weight selection is ad hoc |
| 18 | **Add boundary tolerance to CRS002**: `>400m` means `>=401m`; add unit test for 400m boundary | Boundary handling unspecified |
| 19 | **Define NYC TLC field null-vs-empty policy**: Explicit per-field specification for SYN001 | Empty string policy unclear |
| 20 | **Add CRS001 speed=0 clarification**: Vehicles at traffic lights legitimately have speed=0; consider time_delta threshold | Conflicting justifications |
