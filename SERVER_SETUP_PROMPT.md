# StreamDQ Server Setup Prompt

Use this file as a prompt for a Claude agent to set up StreamDQ on a remote server from scratch.

---

## CONTEXT

You are setting up **StreamDQ** (A Context-Aware Framework for Streaming Data Quality Monitoring) on a remote Linux server (`sg-resintern01`, user: `dacthinh`).

The codebase is cloned from GitHub. You must complete the full setup: environment, data, Docker infrastructure, and verification.

---

## PROJECT OVERVIEW

**StreamDQ** validates streaming data quality in real-time:
- NYC Taxi events (Kafka → rules → violations)
- GTFS Malaysia live GPS feeds
- 9 rules: SYN001-003 (syntactic), SEM001-003 (semantic), CRS001-003 (cross-record)
- Stack: Python 3.10+, Apache Spark Structured Streaming, Kafka, SQLite/PostgreSQL, Prometheus, Grafana

**Architecture:**
```
NYC Taxi Parquet → Kafka Producer → Kafka → StreamDQ Spark Pipeline → Violations (SQLite/Kafka)
                                                    ↓
GTFS Malaysia API → GTFS Consumer → Kafka →  Promethes + Grafana
```

---

## STEP 1: System Prerequisites

### 1A: Check Python version

```bash
python3 --version
```

**Expected:** Python 3.10 or higher.

**If Python < 3.10**, install Python 3.11:

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Make python3.11 the default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2  # keep 3.8 if needed

# Verify
python3 --version
```

### 1B: Check Docker

```bash
docker --version
docker compose version
```

**If Docker not installed**, install Docker Engine:

```bash
# On Ubuntu
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

**If Docker not running**, start it:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 1C: Check Java (required for Spark)

```bash
java -version
```

**If Java not installed**, install OpenJDK 17:
```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Add to .bashrc for persistence
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
```

### 1D: Verify all prerequisites

```bash
python3 --version   # Must be >= 3.10
docker --version    # Must be >= 20.x
java -version       # Must be >= 17
```

---

## STEP 2: Clone & Environment Setup

### 2A: Create project directory

```bash
mkdir -p /home/dacthinh/streamdq
cd /home/dacthinh/streamdq
```

### 2B: Clone from GitHub

*(Replace `YOUR_USERNAME` and `YOUR_REPO` with actual values)*

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

If you already have the code locally, skip clone and go to step 2C.

### 2C: Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2D: Create .env file

```bash
cp .env.example .env
```

Then edit `.env` (using `nano .env` or `vim .env`) with these values:

```env
# PostgreSQL (Docker — credentials match docker-compose.yml)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=streamdq
POSTGRES_USER=streamdq
POSTGRES_PASSWORD=streamdq

# Kafka (Docker)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### 2E: Verify Python packages installed

```bash
python -c "import pyspark; import pandas; import kafka; import prometheus_client; print('All packages OK')"
```

---

## STEP 3: Download NYC Taxi Data

The NYC Taxi data is hosted on AWS Open Data / NYC TLC CloudFront CDN. It is **free, no API key required**.

### 3A: Create data directory

```bash
mkdir -p data/nyc-taxi
```

### 3B: Download parquet file

```bash
# Download January 2023 (recommended — ~60MB, 3M records)
python scripts/download_nyc_taxi.py --month 2023-01

# Alternative: download via curl/wget directly
cd data/nyc-taxi
curl -o yellow_tripdata_2023-01.parquet \
  "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
```

### 3C: Verify download

```bash
ls -lh data/nyc-taxi/
# Expected: yellow_tripdata_2023-01.parquet (~60MB)

python -c "import pandas as pd; df=pd.read_parquet('data/nyc-taxi/yellow_tripdata_2023-01.parquet'); print(f'Rows: {len(df)}, Columns: {list(df.columns)}')"
```

### 3D: Download additional months (optional, for benchmarks)

```bash
# Download 6 months for more thorough evaluation
for month in 2023-02 2023-03 2023-04 2023-05 2023-06 2023-07; do
  python scripts/download_nyc_taxi.py --month $month
done
```

---

## STEP 4: Docker Infrastructure

### 4A: Build Docker images

```bash
docker compose build
```

This builds the `streamdq-spark-streaming` image from `Dockerfile.spark`.

### 4B: Start infrastructure services (NOT Spark yet)

```bash
docker compose up -d zookeeper kafka kafka-ui prometheus grafana postgres
```

### 4C: Wait for services to be healthy

```bash
# Wait 30 seconds for Kafka to be ready
sleep 30

# Verify all containers are running
docker compose ps

# Expected output:
# NAME                    STATUS
# streamdq-zookeeper      running
# streamdq-kafka          running
# streamdq-kafka-ui       running
# streamdq-prometheus     running
# streamdq-grafana        running
# streamdq-postgres       running
```

### 4D: Verify Kafka is working

```bash
# List topics
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Create topics explicitly if not auto-created
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --topic nyc-taxi-events \
  --partitions 3 \
  --replication-factor 1

docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --topic gtfs-vehicle-pos \
  --partitions 3 \
  --replication-factor 1

docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --topic quality-violations \
  --partitions 3 \
  --replication-factor 1
```

### 4E: Verify Prometheus

```bash
curl -s http://localhost:9090/-/healthy
# Expected: {"status":"ok"}

curl -s http://localhost:9090/api/v1/rules | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Rule groups: {len(d[\"data\"][\"groups\"])}')"
# Expected: Rule groups: 5
```

### 4F: Verify Grafana

```bash
curl -s http://localhost:3000/api/health
# Expected: {"analytics":{"clickhouseAvailable":false,...},"commit":"...","db":"ok","version":"10.1.0"}

# Access: http://<server-ip>:3000
# Default credentials: admin / admin
```

---

## STEP 5: Initialize Database

### 5A: PostgreSQL — Create schema

```bash
docker compose exec postgres psql -U streamdq -d streamdq -c "
-- StreamDQ violations table (matches ViolationStore schema)
CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    rule_id TEXT NOT NULL,
    rule_name TEXT,
    entity_id TEXT,
    entity_type TEXT,
    severity TEXT,
    violation_type TEXT,
    details TEXT,
    expected TEXT,
    record_snapshot TEXT,
    detected_at TEXT,
    processing_latency_ms REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_violations_rule_id ON violations(rule_id);
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);
CREATE INDEX IF NOT EXISTS idx_violations_detected_at ON violations(detected_at);
CREATE INDEX IF NOT EXISTS idx_violations_entity_id ON violations(entity_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE violations TO streamdq;
"
```

### 5B: Verify PostgreSQL table

```bash
docker compose exec postgres psql -U streamdq -d streamdq -c "\d violations"
```

---

## STEP 6: Fix Dockerfile.spark (Critical — config directory issue)

The `Dockerfile.spark` has this line that will fail:
```dockerfile
COPY config /app/config
```

**But the `config/` directory does not exist in the repo.**

Fix by editing `Dockerfile.spark`:

```bash
# Option A: Remove the broken line
# In Dockerfile.spark, remove or comment out:
#   COPY config /app/config

# Option B: Create a minimal config directory
mkdir -p config
echo "# StreamDQ Configuration" > config/streamdq.conf
echo "# Add rule thresholds, data source configs here" >> config/streamdq.conf
```

After fixing, rebuild:
```bash
docker compose build spark-streaming
```

---

## STEP 7: Start StreamDQ Pipeline

### 7A: Option A — Docker container (recommended)

```bash
# Start the Spark streaming pipeline
docker compose up -d spark-streaming

# Watch logs
docker compose logs -f spark-streaming
```

**Expected log output:**
```
[StreamDQ] Prometheus metrics server started on port 9091
StreamDQ pipeline started. Reading from: nyc-taxi-events
Violations stored to: sqlite
[StreamDQ] Kafka violation producer ready: quality-violations
```

### 7B: Option B — Local Python (for development/debug)

```bash
source .venv/bin/activate
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

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

### 7C: Verify Spark pipeline is running

```bash
docker compose ps spark-streaming
# Expected: streamdq-spark   running

# Check metrics endpoint
curl -s http://localhost:9091/metrics | grep "^streamdq" | head -5
```

---

## STEP 8: Run Producers

### 8A: NYC Taxi Replay Producer

In a **new terminal**:

```bash
cd /home/dacthinh/streamdq
source .venv/bin/activate

python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 1000 \
    --inject-anomalies \
    --anomaly-rate 0.05

# Or run in background
python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 1000 \
    --inject-anomalies \
    --anomaly-rate 0.05 \
    --max-rows 100000 &
```

### 8B: GTFS Live Producer (optional)

```bash
python -m streamdq.producers.gtfs_live \
    --kafka localhost:9092 \
    --topic gtfs-vehicle-pos \
    --agencies ktmb prasaranabus \
    --poll-interval 30 \
    --once
```

---

## STEP 9: Verify End-to-End

### 9A: Check Prometheus metrics

```bash
curl -s http://localhost:9091/metrics | grep "^streamdq"
```

**Expected metrics:**
```
streamdq_events_total{topic="nyc-taxi-events"}
streamdq_violations_total{rule_id="SYN001", violation_type="SYNTACTIC"}
streamdq_batch_latency_seconds_bucket{le="..."}
```

### 9B: Check violations in Kafka

Open **Kafka-UI**: http://<server-ip>:8080
1. Select topic: `quality-violations`
2. Click "Produce Message" to browse or consume
3. Verify messages contain `rule_id`, `entity_id`, `violation_type`

### 9C: Check SQLite violations

```bash
docker compose exec spark-streaming sqlite3 /data/violations.db \
  "SELECT rule_id, severity, COUNT(*) FROM violations GROUP BY rule_id, severity;"
```

### 9D: Check PostgreSQL violations

```bash
docker compose exec postgres psql -U streamdq -d streamdq -c \
  "SELECT rule_id, severity, COUNT(*) FROM violations GROUP BY rule_id, severity;"
```

### 9E: Check Grafana dashboards

Open **Grafana**: http://<server-ip>:3000 (admin / admin)

Navigate to:
- **Dashboard > Violation Overview** — violations by rule, over time
- **Dashboard > Latency** — batch processing latency P50/P95/P99

---

## STEP 10: Run Evaluation

```bash
cd /home/dacthinh/streamdq
source .venv/bin/activate

python -m streamdq.evaluation.run_evaluation \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --anomaly-rate 0.05 \
    --max-events 100000 \
    --output evaluation_results.json

# View results
cat evaluation_results.json
```

---

## Service URLs Summary

| Service | URL | Credentials |
|---------|-----|-------------|
| Kafka-UI | http://\<server-ip\>:8080 | — |
| Prometheus | http://\<server-ip\>:9090 | — |
| Grafana | http://\<server-ip\>:3000 | admin / admin |
| Spark Metrics | http://\<server-ip\>:9091/metrics | — |
| PostgreSQL | localhost:5432 | streamdq / streamdq |
| SQLite | `/data/violations.db` (container) | — |

---

## Troubleshooting

### Kafka won't start

```bash
docker compose logs kafka | tail -30
# Common fix: wait longer
docker compose up -d zookeeper
sleep 10
docker compose up -d kafka
```

### Spark container OOM (Out of Memory)

```bash
# Increase Docker memory limit, or reduce Spark memory in docker-compose.yml:
# environment:
#   SPARK_EXECUTOR_MEMORY: 1g
#   SPARK_DRIVER_MEMORY: 1g
docker compose restart spark-streaming
```

### NYC Taxi download fails

```bash
# Try wget instead
cd data/nyc-taxi
wget "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
```

### Python packages import errors

```bash
source .venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

### Prometheus scrape fails

```bash
# Check if spark-streaming container is healthy
docker compose ps
curl -s http://localhost:9091/metrics | head -5

# If metrics endpoint is down, restart
docker compose restart spark-streaming
```

### Data directory permission error

```bash
mkdir -p data/nyc-taxi
chmod 755 data/
```

---

## Quick Start Script (copy-paste all)

```bash
#!/bin/bash
set -e
cd /home/dacthinh/streamdq

# 1. Environment
source .venv/bin/activate
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# 2. Start Docker infrastructure
docker compose up -d zookeeper kafka kafka-ui prometheus grafana postgres
echo "Waiting 30s for services..."
sleep 30

# 3. Create Kafka topics
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic nyc-taxi-events --partitions 3 --replication-factor 1 || true
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic quality-violations --partitions 3 --replication-factor 1 || true

# 4. Initialize PostgreSQL schema
docker compose exec postgres psql -U streamdq -d streamdq -c "
CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY, rule_id TEXT NOT NULL, rule_name TEXT,
    entity_id TEXT, entity_type TEXT, severity TEXT, violation_type TEXT,
    details TEXT, expected TEXT, record_snapshot TEXT, detected_at TEXT,
    processing_latency_ms REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_violations_rule_id ON violations(rule_id);
" 2>/dev/null || true

# 5. Start Spark pipeline
docker compose up -d spark-streaming
sleep 5

# 6. Run producer (100k events, ~2 minutes)
timeout 180 python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 500 \
    --inject-anomalies \
    --anomaly-rate 0.05 \
    --max-rows 100000 &

# 7. Verify
sleep 10
curl -s http://localhost:9091/metrics | grep "^streamdq" | wc -l
echo "Setup complete! Check Grafana at http://localhost:3000"
```

---

## Known Limitations

- **Python 3.8 on server**: Code requires Python 3.10+. Install Python 3.11 as shown in Step 1A.
- **Docker not available**: If server has no Docker, use Option B (local Python with `--master local[*]`) — Spark runs in local mode.
- **22 PDF papers in repo**: These are reference materials in `paper-to-learn/`. They are tracked by git (not ignored). If repo is large, consider removing them: `rm -rf paper-to-learn/*.pdf`.
- **`config/` directory missing**: Dockerfile.spark references `COPY config /app/config` but the directory doesn't exist. Fix as described in Step 6.
