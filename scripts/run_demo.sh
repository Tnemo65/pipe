#!/bin/bash
# run_demo.sh — Full StreamDQ demo in 3 commands
# Prerequisites: Docker, Python 3.10+, ~5GB disk

set -e

echo "=========================================="
echo "StreamDQ — Full Pipeline Demo"
echo "=========================================="

# Check prerequisites
command -v python >/dev/null 2>&1 || { echo "Python required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }

# Step 1: Download data
echo ""
echo "[Step 1/3] Downloading NYC TLC data..."
if [ ! -f "data/nyc-taxi/yellow_tripdata_2023-01.parquet" ]; then
    python scripts/download_nyc_taxi.py --month 2023-01
else
    echo "  Data already downloaded."
fi

# Step 2: Start infrastructure
echo ""
echo "[Step 2/3] Starting Docker infrastructure..."
docker compose up -d

echo "  Waiting for Kafka to be ready..."
sleep 10

# Step 3: Run evaluation
echo ""
echo "[Step 3/3] Running StreamDQ evaluation..."
echo ""

# Run the replay producer in background
python -m streamdq.producers.nyc_taxi_replay \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --kafka localhost:9092 \
    --topic nyc-taxi-events \
    --rate 1000 \
    --inject-anomalies \
    --anomaly-rate 0.05 \
    --max-rows 100000 &

PRODUCER_PID=$!

# Run evaluation
sleep 5

python -m streamdq.evaluation.run_evaluation \
    --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
    --anomaly-rate 0.05 \
    --max-events 100000 \
    --output evaluation_results.json

# Cleanup
kill $PRODUCER_PID 2>/dev/null || true

echo ""
echo "=========================================="
echo "Demo complete!"
echo "=========================================="
echo ""
echo "View results:"
echo "  - SQLite violations: sqlite3 /tmp/streamdq_violations.db"
echo "  - Evaluation JSON:   cat evaluation_results.json"
echo "  - Grafana:           http://localhost:3000 (admin/admin)"
echo ""
