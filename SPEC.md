# SPEC.md — Product Requirements & Evaluation Strategy

## "A Context-Aware Framework for Streaming Data Quality Monitoring"

---

## 1. Product Overview

**Name**: StreamDQ

**One-liner**: Validate streaming data quality in real-time with context-aware thresholds and full explainability.

**Target users**:
- Data engineers who need to monitor streaming pipelines
- Data analysts who trust downstream data
- SRE/on-call teams who need alerts with actionable context

**Not in scope**:
- Batch data quality (use Great Expectations / dbt instead)
- ML-based anomaly detection (future work)
- Multi-tenant isolation (future work)

---

## 2. Functional Requirements

### 2.1 Core Features

| ID | Feature | Description | Acceptance Criteria |
|---|---|---|---|
| F1 | **Streaming rule evaluation** | Evaluate data quality rules as events flow through Kafka | Events processed within 500ms of arrival (P99) |
| F2 | **Syntactic validation** | Detect null, type, range, format violations | All SYN001-003 rules fire correctly on test data |
| F3 | **Semantic validation** | Detect domain-specific violations (fare, duration, speed) | All SEM001-003 rules fire correctly with known ground truth |
| F4 | **Cross-record detection** | Detect anomalies across multiple records (duplicates, GPS jumps) | CRS001-003 detect injected anomalies with >70% recall |
| F5 | **Adaptive thresholds** | Statistical thresholds computed from rolling window | Thresholds update every 1,000 events; no hardcoded magic numbers |
| F6 | **Violation storage** | Persist violations with full context | SQLite demo; queryable by rule_id, entity_id, time range |
| F7 | **Metrics dashboard** | Real-time Grafana dashboard | Violations/min, latency P50/P99, throughput |
| F8 | **Data source: NYC TLC** | Replay historical taxi data to Kafka | 100K+ events replayable; anomalies injectable |
| F9 | **Data source: GTFS Malaysia** | Live public transport GPS data | 30-second polling; CRS001-002 applicable |
| F10 | **Rule extensibility** | Add new rule by subclassing DataQualityRule | New rule has unit tests; runs in same pipeline |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target | Measurement |
|---|---|---|---|
| NF1 | **Setup time (local demo)** | < 30 min to first violation | Stopwatch from `docker compose up` to violation in Grafana |
| NF2 | **Processing throughput** | > 5,000 events/sec per Spark executor | Benchmark test |
| NF3 | **Pipeline availability** | > 99% in production | Prometheus uptime metrics |
| NF4 | **Rule test coverage** | 100% of rules have unit tests | pytest --cov |
| NF5 | **Reproducibility** | Same anomaly injection -- same detection result | Determinism test with fixed seed |

---

## 3. Evaluation Strategy — How to Prove the Product is Good

### 3.1 Four Proof Dimensions

**Proof 1 — Metrics (Automated)**

```
Run: 100,000 NYC TLC events + 5% injected anomalies
Measure:
  - Detection rate per anomaly type (recall)
  - False positive rate (1 - precision)
  - Latency: time from event to violation
  - Rule coverage: which rules fired, which were silent
```

**Proof 2 — Comparison vs. Existing Tools**

```
Same dataset, same anomaly injection, measure:
  StreamDQ vs. Great Expectations vs. Soda Core vs. No validation

Dimensions:
  - Precision / Recall
  - Latency (streaming vs. batch)
  - Setup complexity
  - Cross-record capability
  - Explainability score (violation context quality)
```

**Proof 3 — Case Study (Business Impact)**

```
Scenario: NYC Taxi analytics pipeline
Without monitoring: 5% anomalies undetected
Business impact: 120,000 bad records/month -- wrong analytics decisions
With StreamDQ: 100% recall (measured) -- 0 bad records/month
Cost savings: data team debug time x monthly anomaly volume
```

**Proof 4 — Demo (Reproducible Environment)**

```
Single command to run full pipeline:
  docker compose up
  -- Kafka starts
  -- NYC TLC data replays to Kafka
  -- StreamDQ processes events
  -- Violations appear in SQLite + Grafana
  -- GTFS Malaysia live feed visible
```

### 3.2 Success Thresholds

> **Note**: Results distinguish between **measured** (DuckDB evaluation on 100K records, `evaluation_results.json`) and **target** (desired performance). LocalPipeline latency is hardcoded to 0 (limitation B6) — Spark pipeline benchmarks are pending.

| Metric | Measured | Target | Minimum Acceptable |
|---|---|---|---|
| Detection Rate (recall) | 100% (all 8 types) | > 80% | > 70% |
| Precision | 22.9% (DuckDB) | > 85% | > 75% |
| Layer 1 Latency (P50) | 0 ms (B6) | < 500ms | < 1,000ms |
| Layer 1 Latency (P99) | 0 ms (B6) | < 500ms | < 2,000ms |
| Layer 2 Latency (cross-record) | -- | < 5 min | < 10 min |
| Setup time (local) | -- | < 30 min | < 60 min |
| Rule test coverage | 100% (all rules tested) | 100% | 80% |
| Configurable data rate | -- | 100-10,000 events/sec | 100-1,000 events/sec |

**Precision gap (22.9% vs >75% target)**: Driven by CRS003 over-triggering on natural duplicates. Known limitation B2 must be fixed to improve precision toward the target.

---

## 4. Data Specification

### 4.1 NYC TLC Taxi Data

**Source**: `s3://nyc-tlc/trip data/yellow/yellow_tripdata_{YYYY-MM}.parquet`
**Direct download**: `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet`
**Schema**: 19 columns (see PILLARS.md Section: Data Sources)
**Volume**: ~3M records/month
**Key validation fields**: `fare_amount`, `trip_distance`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`, `PULocationID`, `DOLocationID`

### 4.2 GTFS Malaysia Realtime

**Source**: `https://api.data.gov.my/gtfs-realtime/vehicle-position/{agency}`
**Agencies**: KTMB (trains), Prasarana (buses, LRT, MRT, monorail)
**Format**: GTFS Realtime protobuf
**Update frequency**: Every 30 seconds
**Key validation fields**: `latitude`, `longitude`, `timestamp`, `vehicle_id`, `speed`

---

## 5. Rule Specification

### 5.1 Required Rules

| ID | Rule | Type | Trigger |
|---|---|---|---|
| SYN001 | Fare amount non-null, non-negative, numeric | SYNTACTIC | `fare_amount` is null / < 0 / wrong type |
| SYN002 | Pickup location ID valid (1-263) | SYNTACTIC | `PULocationID` not in 1-263 |
| SYN003 | Pickup timestamp not in future | SYNTACTIC | `tpep_pickup_datetime` > now + 5min |
| SEM001 | Fare within contextual range (adaptive) | SEMANTIC | `fare_amount` > P99 x 2 or < P1 |
| SEM002 | Trip duration 1 min - 24 hours | SEMANTIC | `(dropoff - pickup)` outside range |
| SEM003 | Average speed <= 80 mph | SEMANTIC | `trip_distance / duration_hours` > 80 |
| CRS001 | Vehicle GPS speed <= 120 km/h | CROSS_RECORD | `haversine(lat1,lon1,lat2,lon2) / dt` > 120 km/h |
| CRS002 | Stationary vehicle position jump | CROSS_RECORD | speed < 1 km/h but distance > 100m |
| CRS003 | Duplicate trip records | CROSS_RECORD | Same `(trip_id, PULocationID, DOLocationID, distance)` within 5 min |

### 5.2 Anomaly Injection Types (for Testing)

| Type | Implementation | Affected Rule |
|---|---|---|
| `fare_negative` | `fare_amount = random.uniform(-50, -2.5)` | SYN001 |
| `fare_outlier` | `fare_amount = random.uniform(500, 2000)` | SEM001 |
| `location_invalid` | `PULocationID = random.randint(9999, 99999)` | SYN002 |
| `timestamp_future` | `pickup = now + 7 days` | SYN003 |
| `duration_negative` | `dropoff = pickup - 30 min` | SEM002 |
| `duration_outlier` | `dropoff = pickup + 20 hours` | SEM002 |
| `speed_outlier` | `trip_distance = 100, duration = 30 min` | SEM003 |
| `gps_jump` | GTFS: previous + next positions 50km apart, 60s | CRS001 |
| `gps_spoofing` | GTFS: same vehicle, no movement, position 500m diff | CRS002 |
| `duplicate` | Same trip data emitted twice | CRS003 |

---

## 6. Architecture Constraints

| Constraint | Reason |
|---|---|
| Max 4 services for local demo | Minimize setup friction |
| No API keys required | Self-contained demo |
| Python-first for rules | Developer-friendly, testable |
| SQLite for violations (demo) | Zero-config |
| Spark Structured Streaming | Accessible API, good Kafka integration |
| Docker Compose | One-command setup |

---

## 7. Out of Scope (v1)

These are legitimate features deferred to v2:

| Feature | Reason Deferred |
|---|---|
| ML-based anomaly detection | Requires training data, model management |
| Multi-tenant isolation | Complexity > benefit for v1 |
| Schema evolution handling | Manageable with manual migration in v1 |
| Rule approval workflow | Simple file-based versioning in v1 |
| Kubernetes production deployment | Docker Compose sufficient for v1 demo |

---

## 8. Acceptance Checklist

Before v1 is considered "done", all items must be verified:

```
[ ] NYC TLC data replays to Kafka at configurable rate
[ ] GTFS Malaysia live feed visible in violation stream
[ ] All 9 rules fire correctly on injected anomalies (unit tests pass)
[ ] Violations stored in SQLite with full context
[ ] Grafana dashboard shows real-time violations/min + latency
[ ] Detection rate > 70% for all anomaly types
[ ] Precision > 75% (false positive rate < 25%) -- NOTE: currently 22.9%, below target
[ ] Layer 1 latency P99 < 2 seconds -- NOTE: pending Spark benchmark
[ ] docker compose up -- violations visible in < 30 minutes
[ ] Rule test coverage >= 80%
[ ] No hardcoded magic numbers in rules (thresholds from config or stats)
```
