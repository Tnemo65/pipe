# IMPLEMENTATION_PLAN.md — Build Roadmap

## "A Context-Aware Framework for Streaming Data Quality Monitoring"

---

## Build Philosophy

**Ship in phases. Each phase delivers a working system, not a half-working whole.**

- Phase 1: Core pipeline works with real data. No demo theater.
- Phase 2: All rules implemented and tested.
- Phase 3: Metrics, dashboards, adaptive thresholds.
- Phase 4: Evaluation, comparison, case study.

---

## Phase 0: Project Setup (1-2 hours)

### Goal: Project scaffold with running pipeline

**Deliverables**:
- Git repository initialized
- Python package structure
- Docker Compose with Kafka + Spark + SQLite
- Minimal "hello world" pipeline: Kafka → Spark → SQLite (no rules yet)
- Data download script for NYC TLC

### Tasks

```
[ ] Initialize project
    mkdir streamdq && cd streamdq
    git init
    mkdir -p streamdq/{rules,producers,evaluation,storage} tests
    touch streamdq/__init__.py

[ ] Create Docker Compose (minimal)
    - Kafka (port 9092)
    - Zookeeper
    - Kafka UI (optional, for debugging)
    - No Spark yet (use local Python for Phase 0)

[ ] Data download
    python scripts/download_nyc_taxi.py --month 2023-01
    python scripts/download_nyc_taxi.py --month 2023-02  # backup
    Verify: parquet loads, print shape

[ ] Minimal Kafka producer
    python -m streamdq.producers.nyc_taxi_replay \
        --local-parquet /data/nyc-taxi/yellow_tripdata_2023-01.parquet \
        --kafka localhost:9092 \
        --topic nyc-taxi-events \
        --rate 100

[ ] Minimal consumer (Python)
    python -c "from kafka import KafkaConsumer; c = KafkaConsumer('nyc-taxi-events'); print(next(c))"
    Verify: events visible

[ ] SQLite schema
    python -c "from streamdq.storage import ViolationStore; v = ViolationStore('sqlite'); print('OK')"
```

**Exit criteria**: `docker compose up` → Kafka running → `python replay_producer.py` → events visible in consumer. < 2 hours.

---

## Phase 1: Core Rule Engine (2-3 days)

### Goal: All 9 rules implemented, unit tested, integrated

**Deliverables**:
- `streamdq/rules/` — base class + all 9 rules
- `streamdq/rules/__init__.py` — clean exports
- Unit tests: `tests/test_rules.py` (pytest)
- Coverage ≥ 80%

### Task Breakdown

#### Day 1: Base classes + Syntactic rules

```
[ ] streamdq/rules/__init__.py — exports
[ ] streamdq/rules/base.py
    - DataQualityRule (ABC)
    - RuleContext (dataclass)
    - Violation (dataclass)
    - AdaptiveThresholdEngine

[ ] streamdq/rules/syntactic.py
    - FareAmountRangeRule (SYN001)
    - PickupLocationValidRule (SYN002)
    - TimestampNotFutureRule (SYN003)

[ ] tests/test_syntactic_rules.py
    - Happy path (valid event → no violation)
    - Edge cases (null, negative, out-of-range)
    - Coverage report
```

#### Day 2: Semantic rules

```
[ ] streamdq/rules/semantic.py
    - FareRangeRule (SEM001) with adaptive threshold integration
    - TripDurationSanityRule (SEM002)
    - AverageSpeedSanityRule (SEM003)

[ ] streamdq/rules/cross_record.py
    - TrajectoryAnomalyRule (CRS001) — Haversine distance
    - GPS spoofing (CRS002) — stationary jump
    - DuplicateEventRule (CRS003) — hash-based dedup

[ ] streamdq/rules/registry.py
    - RuleRegistry class
    - build_default_registry()

[ ] tests/test_semantic_rules.py
[ ] tests/test_cross_record_rules.py
    - Haversine correctness tests
    - GPS jump: known coordinates
    - Duplicate: same hash detection
```

#### Day 3: Integration

```
[ ] Integrate rules into pipeline
    - Rules loaded from registry
    - Each event evaluated against all applicable rules
    - Violations stored

[ ] Verify against injected anomalies
    - Run producer with 5% anomaly injection
    - Check SQLite for expected violations
    - Print detection rate per rule

[ ] Coverage check
    pytest --cov=streamdq/rules --cov-report=term-missing
    Target: ≥ 80% line coverage
```

**Exit criteria**: `pytest tests/test_rules.py` → all pass. Violations visible in SQLite after running pipeline with injected anomalies.

---

## Phase 2: Streaming Pipeline (2-3 days)

### Goal: Spark Structured Streaming pipeline processing real data

**Deliverables**:
- `streamdq/pipeline.py` — Spark Structured Streaming pipeline
- `Dockerfile.spark` — containerized Spark
- Kafka topics configured
- Real-time violation stream (Kafka `quality-violations` topic)

### Task Breakdown

```
[ ] Set up Spark environment
    Option A: Local Spark (simpler, for demo)
        pip install pyspark==3.5.0
    Option B: Spark in Docker (production-like)
        docker compose with spark-master + spark-worker

[ ] Implement Spark pipeline (streamdq/pipeline.py)
    - Read from Kafka (nyc-taxi-events)
    - Parse JSON → DataFrame
    - ForEachBatch: evaluate rules → store violations
    - Write violation events to quality-violations topic
    - Prometheus metrics endpoint

[ ] Kafka topic configuration
    kafka-topics --create --topic nyc-taxi-events --partitions 8
    kafka-topics --create --topic quality-violations --partitions 8

[ ] End-to-end test
    1. Start docker compose
    2. Run replay producer (1000 events/sec)
    3. Start Spark pipeline
    4. Watch violations appear in Kafka quality-violations topic
    5. Check SQLite for violations
    Verify: 5% injected → ~5% violations detected
```

**Exit criteria**: Spark streaming job running, processing 1000+ events/sec, violations in SQLite.

---

## Phase 3: GTFS Live Data (1-2 days)

### Goal: Integrate Malaysia GTFS Realtime as live data source

**Deliverables**:
- `streamdq/producers/gtfs_live.py` — GTFS consumer
- GTFS vehicle positions flowing to Kafka
- CRS001 (GPS speed) + CRS002 (GPS spoofing) rules active

### Task Breakdown

```
[ ] Install GTFS Realtime protobuf
    pip install gtfs-realtime-bindings

[ ] Implement streamdq/producers/gtfs_live.py
    - Poll every 30 seconds
    - Parse protobuf
    - Push to Kafka topic (gtfs-vehicle-pos)

[ ] Update Spark pipeline
    - Add second Kafka source (gtfs-vehicle-pos)
    - Apply CRS001/CRS002 rules
    - Store GTFS violations separately

[ ] Verify
    python -m streamdq.producers.gtfs_live --kafka localhost:9092
    Watch GTFS vehicle positions appear in Kafka
    Check violations for any GPS anomalies detected
```

**Exit criteria**: GTFS vehicle positions visible in Kafka within 60 seconds of startup. Trajectory rules running.

---

## Phase 4: Adaptive Thresholds (1-2 days)

### Goal: Statistical thresholds computed from data, not hardcoded

**Deliverables**:
- `AdaptiveThresholdEngine` integrated into pipeline
- Rules use `ctx.historical_stats` for adaptive bounds
- Visual proof: threshold changes visible in logs/metrics

### Task Breakdown

```
[ ] Integrate AdaptiveThresholdEngine into pipeline
    - Every N events: compute rolling P10, P90, mean, std
    - Pass stats to RuleContext for rules to use

[ ] Update FareRangeRule (SEM001)
    - Use historical_stats["fare_amount"]["p10"] and ["p90"] instead of hardcoded
    - Fallback to static bounds if insufficient data (< 1000 events)

[ ] Add threshold change logging
    [AdaptiveThreshold] fare_amount: p10=5.0, p90=45.0, n=10000
    [AdaptiveThreshold] fare_amount: p10=5.2, p90=47.5, n=20000
    → Visible that threshold adapts

[ ] Benchmark: same data, static vs adaptive
    - Run with adaptive disabled (hardcoded bounds)
    - Run with adaptive enabled
    - Compare false positive rate
```

**Exit criteria**: Thresholds update every 1,000 events. Rules use adaptive bounds after 1,000 events. Fallback to static bounds before that.

---

## Phase 5: Observability (1-2 days)

### Goal: Real-time dashboards proving the pipeline works

**Deliverables**:
- Grafana dashboards (violations, latency, throughput)
- Prometheus metrics
- Violation explorer UI (simple HTML or Streamlit)

### Task Breakdown

```
[ ] Prometheus metrics
    - Total events processed
    - Violations by rule, type, severity
    - Processing latency (histogram)
    - Throughput (events/sec)

[ ] Grafana dashboards
    Dashboard 1: Real-Time Health
      - Events per minute (line chart)
      - Violations per minute (stacked bar, by severity)
      - Processing latency P50/P95/P99 (histogram)
    Dashboard 2: Rule Performance
      - Violations per rule (bar chart)
      - Detection rate over time (line)
      - False positive rate trend (line)
    Dashboard 3: Data Quality Heatmap
      - Violations by hour of day × rule type

[ ] Violation explorer (optional: Streamlit)
    - Filter by rule_id, entity_id, severity, time range
    - Click violation → see full details (record snapshot, expected, context)
    - Mark as false positive (feedback)
```

**Exit criteria**: Grafana accessible at localhost:3000. Dashboards updating in real-time as events flow.

---

## Phase 6: Evaluation & Proof (1-2 days)

### Goal: Demonstrate product quality with evidence

**Deliverables**:
- `streamdq/evaluation/run_evaluation.py` — full evaluation script
- `streamdq/evaluation/comparison.py` — comparison with baselines
- `streamdq/evaluation/case_study.py` — business impact report
- README with benchmark results

### Task Breakdown

```
[ ] Evaluation script
    python -m streamdq.evaluation.run_evaluation \
        --dataset /data/nyc-taxi/yellow_tripdata_2023-01.parquet \
        --anomaly-rate 0.05 \
        --rate 1000

    Output:
    - Precision: 85.3%
    - Recall: 81.7%
    - Latency P50: 120ms
    - Latency P99: 890ms
    - By-rule breakdown
    - By-anomaly-type detection rate

[ ] Comparison table (vs. Great Expectations, Soda Core)
    Generate comparison table with metrics

[ ] Case study generation
    python -m streamdq.evaluation.case_study > CASE_STUDY.md

[ ] README.md benchmark section
    Update README with:
    - Setup instructions (3 commands)
    - Benchmark results (live from evaluation run)
    - Architecture diagram
    - Rule summary table
```

**Exit criteria**: Evaluation script runs end-to-end. Results reproducible. README is the "landing page" that proves the product works.

---

## Phase 7: Polish & Documentation (1 day)

### Goal: Clean, shippable, demo-ready

**Deliverables**:
- Clean README with quickstart
- All scripts run without errors
- No TODO comments in code
- Error messages are actionable

### Task Breakdown

```
[ ] README.md
    - Architecture diagram (ASCII)
    - Quickstart: 3 commands to full pipeline
    - Evaluation results (live)
    - Screenshot of Grafana dashboard
    - "How to contribute a new rule" guide

[ ] Error handling pass
    - Kafka connection errors: retry with backoff
    - Malformed events: skip + log, don't crash pipeline
    - Missing fields: graceful degradation

[ ] Performance optimization
    - Batch violations (write every 100, not every 1)
    - Rule evaluation: skip if entity_type doesn't match rule

[ ] Final test: fresh machine
    - git clone
    - docker compose up
    - python -m streamdq.evaluation.run_evaluation
    → Everything works
```

---

## Timeline Summary

| Phase | Task | Time |
|---|---|---|
| 0 | Project setup | 1-2 hours |
| 1 | Rule engine (9 rules + tests) | 2-3 days |
| 2 | Spark streaming pipeline | 2-3 days |
| 3 | GTFS live data | 1-2 days |
| 4 | Adaptive thresholds | 1-2 days |
| 5 | Observability (Grafana) | 1-2 days |
| 6 | Evaluation & proof | 1-2 days |
| 7 | Polish & documentation | 1 day |
| **Total** | | **~10-15 days** |

**With AI agents**: Parallelizable — one agent on Phase 1 (rules), one on Phase 2 (pipeline), one on Phase 3+4 (GTFS + adaptive), one on Phase 5+6 (observability + evaluation).

---

## File Structure

```
d:\dtl\pipeline_real\
├── PILLARS.md                    # Full product specification
├── SPEC.md                       # Requirements & acceptance criteria
├── IMPLEMENTATION_PLAN.md        # This file — build roadmap
├── README.md                     # Quickstart + benchmark results
│
├── docker-compose.yml            # Kafka + Spark + PostgreSQL + Grafana
├── Dockerfile.spark              # Spark image
│
├── streamdq/                     # Main package
│   ├── __init__.py
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base.py              # DataQualityRule, RuleContext, Violation
│   │   ├── syntactic.py         # SYN001, SYN002, SYN003
│   │   ├── semantic.py          # SEM001, SEM002, SEM003
│   │   ├── cross_record.py      # CRS001, CRS002, CRS003
│   │   ├── adaptive.py          # AdaptiveThresholdEngine
│   │   └── registry.py          # RuleRegistry, build_default_registry()
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── spark_pipeline.py    # Spark Structured Streaming
│   │   └── local_pipeline.py    # Python-only pipeline (for quick test)
│   ├── producers/
│   │   ├── __init__.py
│   │   ├── nyc_taxi_replay.py   # Replay parquet to Kafka
│   │   └── gtfs_live.py         # GTFS Malaysia → Kafka
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── run_evaluation.py    # Main evaluation script
│   │   ├── comparison.py        # vs. GE, Soda Core
│   │   ├── case_study.py        # Business impact
│   │   └── metrics.py           # Precision, recall, latency
│   └── storage/
│       ├── __init__.py
│       └── violation_store.py    # SQLite + PostgreSQL
│
├── tests/
│   ├── test_syntactic_rules.py
│   ├── test_semantic_rules.py
│   ├── test_cross_record_rules.py
│   └── test_pipeline_integration.py
│
├── scripts/
│   ├── download_nyc_taxi.py     # Download TLC parquet files
│   └── run_demo.sh              # One-command demo
│
├── data/
│   └── nyc-taxi/                # Downloaded parquet files
│       └── yellow_tripdata_2023-01.parquet
│
├── dashboards/                  # Grafana provisioning
│   ├── dashboards.yaml
│   └── streamdq_dashboard.json
│
├── prometheus.yml
└── .env                         # Environment variables
```

---

## Running the Full Demo (End-to-End)

Once Phase 0-2 are complete, the full demo runs in 3 commands:

```bash
# Step 1: Download data
python scripts/download_nyc_taxi.py --month 2023-01

# Step 2: Start infrastructure
docker compose up -d

# Step 3: Run pipeline + evaluation
python -m streamdq.producers.nyc_taxi_replay --rate 1000 &
python -m streamdq.pipeline.spark_pipeline &
python -m streamdq.evaluation.run_evaluation
```

Expected results:
- NYC TLC events flowing to Kafka within 60 seconds
- StreamDQ processing at ~1000 events/sec
- Violations visible in SQLite: `sqlite3 /tmp/streamdq_violations.db "SELECT COUNT(*) FROM violations;"`
- Grafana dashboard at `localhost:3000` with real-time charts
- Evaluation output: precision, recall, latency metrics
