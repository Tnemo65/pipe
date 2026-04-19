# StreamDQ Full-Stack Setup Guide

**Ngày:** April 19, 2026
**Mục tiêu:** Chạy real Spark + Kafka + Prometheus + Grafana end-to-end

---

## 1. Prerequisites

### 1.1 Hardware & OS Requirements

```
Windows 10/11 (WSL2) hoặc Linux/macOS
RAM: 16GB minimum (32GB recommended)
CPU: 8 cores minimum
Disk: 50GB free
```

### 1.2 Software Cần cài đặt

```bash
# 1. Docker Desktop (https://docs.docker.com/desktop/)
docker --version
# Expected: Docker version 20.x+

# 2. Docker Compose (thường đi kèm Docker Desktop)
docker compose version

# 3. Python 3.10+ (nếu chạy local)
python --version
# Expected: Python 3.10+

# 4. WSL2 (Windows only)
wsl --status
# Nếu chưa enable: wsl --install
```

---

## 2. Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER FACING                               │
│  Kafka-UI :8080      Prometheus :9090      Grafana :3000        │
└────────┬───────────────────┬──────────────────────┬────────────────┘
         │                   │                      │
         ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Kafka (port 9092)          Prometheus          Grafana       │
│  - Topics:                  - Scrapes metrics   - Dashboards   │
│    nyc-taxi-events          from Spark         - Alerts       │
│    gtfs-vehicle-pos         pipeline            - Anomaly viz  │
│    quality-violations                             (requires    │
│                                                  Prometheus)  │
└────────┬──────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Spark Streaming Pipeline (Docker container)                 │
│  - Reads: nyc-taxi-events, gtfs-vehicle-pos              │
│  - Evaluates: SYN000-003, SEM001-003, CRS001-003         │
│  - Writes: quality-violations + SQLite violations.db       │
│  - Exposes: Prometheus metrics on port 9091               │
└────────┬──────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL (port 5432)        SQLite (inside container)   │
│  - Violation store             - Fallback violation store   │
│  - Optional                    - /data/violations.db       │
└─────────────────────────────────────────────────────────────┘

PRODUCERS (chạy riêng):
┌──────────────────┐    ┌──────────────────────────────────┐
│ NYC Taxi Replay  │    │ GTFS Live Consumer                │
│ Python script     │    │ Python script                     │
│ Parquet -> Kafka │    │ GTFS API -> Kafka                 │
│ port 9092        │    │ port 9092                        │
└──────────────────┘    └──────────────────────────────────┘
```

---

## 3. Step-by-Step Setup

### STEP 1: Clone & Environment Setup

```bash
# Clone hoặc cd vào project
cd d:/dtl/pipeline_real

# Tạo virtual environment (nên dùng)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
# Edit .env với credentials nếu cần
```

### STEP 2: Download NYC Taxi Data

```bash
# Cần 1 file parquet để test (khoảng 60MB)
python scripts/download_nyc_taxi.py --month 2023-01

# Verify
ls data/nyc-taxi/
# Expected: yellow_tripdata_2023-01.parquet

# Download thêm tháng để benchmark (tùy chọn)
python scripts/download_nyc_taxi.py --month 2023-01 --months 6
```

### STEP 3: Build Docker Images

```bash
# Build tất cả Docker images
docker compose build

# Verify images được tạo
docker images | grep streamdq
# Expected:
#   streamdq-spark-streaming   latest
```

### STEP 4: Start Infrastructure Services (Không có Spark trước)

```bash
# Chỉ start infrastructure (Kafka, Prometheus, Grafana)
docker compose up -d zookeeper kafka kafka-ui prometheus grafana postgres

# Verify tất cả đang chạy
docker compose ps

# Expected output:
# NAME                    COMMAND                  SERVICE      STATUS
# streamdq-zookeeper     "/etc/confluent/dock…   zookeeper   running
# streamdq-kafka          "/etc/confluent/dock…   kafka       running
# streamdq-kafka-ui      /bin/sh -c 'java -ja…  kafka-ui    running
# streamdq-prometheus     "/bin/prometheus --c…  prometheus  running
# streamdq-grafana        "/run.sh"                grafana     running
# streamdq-postgres       "docker-entrypoint.s…   postgres    running
```

### STEP 5: Verify Kafka

```bash
# Test Kafka connection
docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Create topics nếu chưa có (Kafka tự tạo nhưng nên verify)
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Expected topics:
#   nyc-taxi-events
#   gtfs-vehicle-pos
#   quality-violations
```

Truy cập **Kafka-UI**: http://localhost:8080 để xem topics, messages

### STEP 6: Verify Prometheus

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify Prometheus config load được alert rules
curl http://localhost:9090/api/v1/rules | python -c "import sys,json; d=json.load(sys.stdin); print(f'Rules groups: {len(d[\"data\"][\"groups\"])}')"

# Expected: Rules groups: 5
```

Truy cập **Prometheus**: http://localhost:9090

### STEP 7: Verify Grafana

```bash
# Check Grafana health
curl http://localhost:3000/api/health

# Login: admin / admin (default)
# URL: http://localhost:3000
```

---

## 4. Running the Full Pipeline

### 4.1 Option A: Docker Container (Recommended for production-like test)

```bash
# Start Spark pipeline container
docker compose up -d spark-streaming

# Xem logs
docker compose logs -f spark-streaming

# Expected output:
# [StreamDQ] Prometheus metrics server started on port 9091
# StreamDQ pipeline started. Reading from: nyc-taxi-events
# Violations stored to: sqlite
# [StreamDQ] Kafka violation producer ready: quality-violations
```

### 4.2 Option B: Local Python (cho development/debug)

```bash
# Cần Java cho PySpark (nếu chạy local)
java -version
# Nếu chưa có: install OpenJDK 17

# Run với local Python (không qua Docker)
python -m streamdq.pipeline.spark_pipeline \
    --kafka-bootstrap localhost:9092 \
    --kafka-topic nyc-taxi-events \
    --violation-topic quality-violations \
    --gtfs-topic gtfs-vehicle-pos \
    --violation-store-backend sqlite \
    --violation-store-path /tmp/violations.db \
    --checkpoint-dir /tmp/spark-checkpoint \
    --metrics-port 9091
```

### 4.3 Producer: NYC Taxi Replay

```bash
# Chạy producer để gửi taxi events vào Kafka
# Rate 100 events/sec, inject anomalies 2%
python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 100 \
    --inject-anomalies \
    --anomaly-rate 0.02

# Hoặc chạy nhanh hơn (1000 events/sec)
python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 1000 \
    --inject-anomalies \
    --anomaly-rate 0.02

# Direct mode (không Kafka, chỉ print):
python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --direct
```

### 4.4 Producer: GTFS Live (Optional)

```bash
# GTFS producer requires: requests + gtfs-realtime-bindings
pip install requests gtfs-realtime-bindings

# Poll Malaysia GTFS realtime API -> Kafka
python -m streamdq.producers.gtfs_live \
    --kafka localhost:9092 \
    --topic gtfs-vehicle-pos \
    --agencies ktmb prasaranabus \
    --poll-interval 30 \
    --once   # Chỉ poll 1 lần để test

# Hoặc chạy liên tục
python -m streamdq.producers.gtfs_live \
    --kafka localhost:9092 \
    --topic gtfs-vehicle-pos \
    --agencies ktmb prasaranabus
```

---

## 5. Monitoring & Verification

### 5.1 Prometheus Metrics (Verify tất cả metrics)

```bash
# Prometheus endpoint từ Spark container
curl http://localhost:9091/metrics | grep "^streamdq"

# Expected metrics:
# streamdq_events_total{topic="nyc-taxi-events"}
# streamdq_violations_total{rule_id="SYN001", violation_type="SYNTACTIC"}
# streamdq_batch_latency_seconds_bucket{le="..."}
# streamdq_batch_size_bucket{le="..."}
# streamdq_threshold_p10{field="fare_amount"}
# streamdq_threshold_p90{field="fare_amount"}
# streamdq_processing_errors_total{error_type="..."}
```

### 5.2 Violations in Kafka (Quality-Violations Topic)

Truy cập **Kafka-UI** http://localhost:8080

```
1. Chọn topic: quality-violations
2. Xem messages (có thể filter theo rule_id)
3. Check: processing_latency_ms > 0
```

### 5.3 Grafana Dashboards

Truy cập **Grafana**: http://localhost:3000 (admin/admin)

Pre-configured dashboards cần tạo thủ công:

**Dashboard 1: Violation Overview**
```
Panels:
- Violations by Rule ID (Pie chart)
- Violations over time (Time series)
- Violation rate % (Gauge, threshold: 15% warning, 25% critical)
- Top violation types (Bar chart)
```

**Dashboard 2: Latency**
```
Panels:
- Batch processing latency P50/P95/P99 (Time series)
- Event processing throughput (Rate)
- Processing latency by rule (Heatmap)
```

**Dashboard 3: Adaptive Thresholds**
```
Panels:
- P10/P90 threshold values over time (Time series)
- Threshold stability (deviation)
- PSI drift indicator (if DriftDetector integrated)
```

### 5.4 PostgreSQL (Violations Query)

```bash
# Kết nối PostgreSQL
docker compose exec postgres psql -U streamdq -d streamdq

# Query violations
SELECT rule_id, severity, COUNT(*) as count
FROM streamdq.violations
GROUP BY rule_id, severity
ORDER BY count DESC;

# Check latency
SELECT
    MIN(processing_latency_ms) as min_lat,
    MAX(processing_latency_ms) as max_lat,
    AVG(processing_latency_ms) as avg_lat,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY processing_latency_ms) as p50_lat,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY processing_latency_ms) as p99_lat
FROM streamdq.violations;
```

### 5.5 SQLite (Fallback Violation Store)

```bash
# Nếu dùng SQLite
docker compose exec spark-streaming sqlite3 /data/violations.db

# Trong sqlite3 shell:
SELECT rule_id, severity, COUNT(*) FROM violations GROUP BY rule_id, severity;
.quit
```

---

## 6. Troubleshooting

### Kafka không start

```bash
# Check logs
docker compose logs kafka

# Common fix: wait for Zookeeper
docker compose up -d zookeeper
sleep 10
docker compose up -d kafka
```

### Prometheus scrape fail

```bash
# Check target status
curl http://localhost:9090/api/v1/targets | python -c "import sys,json; d=json.load(sys.stdin); [print(t['labels']['job'], t['health']) for t in d['data']['activeTargets']]"

# Nếu spark-streaming down: restart nó
docker compose restart spark-streaming
```

### Spark Out of Memory

```bash
# Tăng Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory: 8GB+

# Hoặc giảm batch size trong spark config
# Edit docker-compose.yml: SPARK_EXECUTOR_MEMORY: 2g
```

### NYC Taxi replay chậm

```bash
# Increase rate
python -m streamdq.producers.nyc_taxi_replay \
    --rate 5000   # Tăng từ 100 lên 5000

# Direct mode (không rate limit)
python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --direct
```

### GTFS producer lỗi protobuf

```bash
# Cài protobuf bindings
pip install gtfs-realtime-bindings

# Check
python -c "import gtfs_realtime_pb2; print('OK')"
```

---

## 7. Quick Test Sequence (5 phút)

```bash
# 1. Start infrastructure
docker compose up -d zookeeper kafka prometheus grafana postgres
sleep 15

# 2. Verify
curl -s http://localhost:9090/-/healthy  # Prometheus OK
curl -s http://localhost:3000/api/health  # Grafana OK
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 3. Start Spark pipeline (background)
docker compose up -d spark-streaming
sleep 5

# 4. Run producer (foreground, 30 giây)
timeout 30 python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 500 \
    --inject-anomalies \
    --anomaly-rate 0.05

# 5. Check metrics
curl -s http://localhost:9091/metrics | grep "^streamdq" | head -20

# 6. Check violations in Kafka UI
# http://localhost:8080 -> quality-violations topic

# 7. Stop
docker compose down
```

---

## 8. Performance Benchmark Checklist

Sau khi setup xong, chạy benchmark để lấy số liệu thực:

```
Metrics cần thu thập:
1. Throughput: events/sec (Kafka consumer lag)
2. Latency: P50, P95, P99 (Prometheus histogram)
3. Violation rate: % (Prometheus counter)
4. Precision/Recall: từ evaluation framework
5. Error rate: processing errors/sec

Expected ranges (để biết có bất thường không):
- Throughput: 1,000-10,000 events/sec (single driver)
- P50 latency: 50-500ms
- P99 latency: 200ms-5s
- Violation rate: 1-10% (với 2% anomaly injection)
```

---

## 9. Service URLs Summary

| Service | URL | Credentials | Purpose |
|---------|-----|------------|---------|
| Kafka-UI | http://localhost:8080 | - | Browse topics, messages |
| Prometheus | http://localhost:9090 | - | Metrics, alerts |
| Grafana | http://localhost:3000 | admin/admin | Dashboards |
| Spark Metrics | http://localhost:9091/metrics | - | Prometheus scrape target |
| PostgreSQL | localhost:5432 | streamdq/streamdq | Violation store |
| SQLite | /data/violations.db (container) | - | Fallback violation store |

---

## 10. Stop Everything

```bash
# Stop all containers
docker compose down

# Stop và remove volumes (clean slate)
docker compose down -v

# Remove downloaded parquet files
rm -rf data/nyc-taxi/

# Verify nothing running
docker compose ps
```
