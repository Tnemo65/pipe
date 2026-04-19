"""
NYC TLC Taxi Replay Producer.

Replays historical NYC TLC parquet data to Kafka as streaming events.
Supports configurable replay rate and synthetic anomaly injection.

Usage:
    python -m streamdq.producers.nyc_taxi_replay \\
        --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \\
        --kafka localhost:9092 \\
        --topic nyc-taxi-events \\
        --rate 1000 \\
        --inject-anomalies \\
        --anomaly-rate 0.02
"""
from __future__ import annotations
import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Optional Kafka import
try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False


ANOMALY_TYPES = [
    "fare_negative", "fare_outlier", "location_invalid",
    "duration_negative", "duration_outlier", "timestamp_future",
    "speed_outlier", "duplicate",  # NG-15: aligned with evaluation
]


class NYCTaxiReplayProducer:
    """
    Replay historical NYC TLC taxi data to Kafka as streaming events.

    Supports:
    - Configurable replay speed (events/sec)
    - Shuffling (randomize order)
    - Synthetic anomaly injection for testing
    - Direct mode (no Kafka) for quick local testing
    """

    def __init__(
        self,
        kafka_bootstrap: str = None,
        topic: str = "nyc-taxi-events",
        rate: int = 1000,
        shuffle: bool = True,
        inject_anomalies: bool = False,
        anomaly_rate: float = 0.02,
        random_seed: int = 42,
        direct_mode: bool = False,
    ):
        self.kafka_bootstrap = kafka_bootstrap
        self.topic = topic
        self.rate = rate
        self.shuffle = shuffle
        self.inject_anomalies = inject_anomalies
        self.anomaly_rate = anomaly_rate
        self.random_seed = random_seed
        self.direct_mode = direct_mode
        self._pending_duplicate: dict | None = None  # NG-15: for duplicate anomaly injection

        random.seed(random_seed)

        self.producer = None
        if not direct_mode and HAS_KAFKA and kafka_bootstrap:
            self.producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                acks="all",
                retries=3,
            )

        self.stats = {
            "sent": 0,
            "errors": 0,
            "anomalies_injected": 0,
            "start_time": None,
        }

    def _inject_anomaly(self, row: dict) -> dict:
        """Inject synthetic anomaly into event."""
        if not self.inject_anomalies or random.random() > self.anomaly_rate:
            return row

        row = dict(row)
        anomaly_type = random.choice(ANOMALY_TYPES)
        self.stats["anomalies_injected"] += 1

        if anomaly_type == "fare_negative":
            row["fare_amount"] = round(random.uniform(-50, -2.5), 2)
            row["total_amount"] = (row.get("total_amount", 0) or 0) + row["fare_amount"]

        elif anomaly_type == "fare_outlier":
            row["fare_amount"] = round(random.uniform(500, 2000), 2)
            row["total_amount"] = row["fare_amount"]

        elif anomaly_type == "location_invalid":
            row["PULocationID"] = random.randint(9999, 99999)

        elif anomaly_type == "duration_negative":
            pickup = row.get("tpep_pickup_datetime")
            if isinstance(pickup, str):
                try:
                    dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                    row["tpep_pickup_datetime"] = (dt + timedelta(hours=1)).isoformat()
                    row["tpep_dropoff_datetime"] = (dt - timedelta(minutes=30)).isoformat()
                except (ValueError, AttributeError):
                    pass

        elif anomaly_type == "duration_outlier":
            pickup = row.get("tpep_pickup_datetime")
            if isinstance(pickup, str):
                try:
                    dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                    row["tpep_dropoff_datetime"] = (dt + timedelta(hours=20)).isoformat()
                except (ValueError, AttributeError):
                    pass

        elif anomaly_type == "timestamp_future":
            row["tpep_pickup_datetime"] = (datetime.now() + timedelta(days=7)).isoformat()

        # NG-15: Align with evaluation — speed_outlier triggers SEM003
        elif anomaly_type == "speed_outlier":
            row["trip_distance"] = 100.0  # 100 miles
            pickup = row.get("tpep_pickup_datetime")
            if isinstance(pickup, str):
                try:
                    dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                    row["tpep_dropoff_datetime"] = (dt + timedelta(minutes=30)).isoformat()
                except (ValueError, AttributeError):
                    pass

        # NG-15: Align with evaluation — duplicate triggers CRS003
        # CRS003 needs the SAME event emitted TWICE within 5 minutes
        # Store the original event to re-emit as the duplicate
        elif anomaly_type == "duplicate":
            self._pending_duplicate = dict(row)

        return row

    def _get_duplicate(self) -> dict | None:
        """Return pending duplicate event and clear it. Called after each _inject_anomaly."""
        dup = self._pending_duplicate
        self._pending_duplicate = None
        return dup

    def _serialize_event(self, row: dict) -> dict:
        """Serialize event for Kafka (convert non-JSON types)."""
        event = {}
        for k, v in row.items():
            if isinstance(v, (pd.Timestamp, datetime)):
                event[k] = v.isoformat() if hasattr(v, "isoformat") else str(v)
            elif pd.isna(v):
                # NG-23 fix: Keep NaN as "NaN" string instead of None so that
                # NaN guards in rules (e.g. math.isnan checks) can detect it.
                # Previously pd.isna was converted to None, bypassing NaN detection.
                event[k] = "NaN"
            elif isinstance(v, (str, int, float, bool, type(None))):
                event[k] = v
            else:
                event[k] = str(v)
        return event

    def _emit(self, event: dict):
        """Emit event to Kafka or stdout."""
        # NG-2a: Attach Kafka produce timestamp for E2E latency measurement.
        # Must be added AFTER _serialize_event since that creates a fresh dict.
        kafka_ts_ms = time.time() * 1000
        serialized = self._serialize_event(event)
        serialized["kafka_arrival_ms"] = kafka_ts_ms
        if self.direct_mode:
            print(json.dumps(serialized))
            return True

        if self.producer is None:
            print("ERROR: Kafka producer not initialized. Use direct_mode=True or check Kafka connection.")
            return False

        try:
            self.producer.send(self.topic, value=serialized)
            self.stats["sent"] += 1
            return True
        except KafkaError as e:
            self.stats["errors"] += 1
            print(f"Kafka error: {e}")
            return False

    def replay(
        self,
        df: pd.DataFrame,
        batch_size: int = 1000,
    ):
        """Replay dataframe to Kafka at configured rate."""
        if self.shuffle:
            df = df.sample(frac=1.0, random_state=self.random_seed).reset_index(drop=True)

        total = len(df)
        print(f"Replaying {total:,} events at ~{self.rate} events/sec")
        print(f"Anomaly injection: {'ON (' + str(self.anomaly_rate) + ' rate)' if self.inject_anomalies else 'OFF'}")

        self.stats["start_time"] = time.time()
        interval = 1.0 / self.rate if self.rate > 0 else 0

        for i, row in df.iterrows():
            event = self._inject_anomaly(row.to_dict())
            self._emit(event)

            # NG-15: Emit duplicate immediately after original (CRS003 needs both)
            dup = self._get_duplicate()
            if dup is not None:
                self._emit(dup)
                self.stats["anomalies_injected"] += 1  # count the duplicate emission

            # Rate limiting (only for real Kafka mode)
            if not self.direct_mode and (i + 1) % self.rate == 0:
                elapsed = time.time() - self.stats["start_time"]
                expected = (i + 1) / self.rate
                if elapsed < expected:
                    time.sleep(expected - elapsed)

            if (i + 1) % (self.rate * 10 if self.rate > 0 else 10000) == 0:
                elapsed = time.time() - self.stats["start_time"]
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(f"  Progress: {i+1:,}/{total:,} ({100*(i+1)/total:.1f}%) — "
                      f"{rate:.0f} events/sec — "
                      f"Anomalies: {self.stats['anomalies_injected']:,}")

        if self.producer:
            self.producer.flush()

        elapsed = time.time() - self.stats["start_time"]
        print(f"\nReplay complete in {elapsed:.1f}s — "
              f"{(self.stats['sent']) / elapsed:.0f} events/sec — "
              f"Stats: {self.stats}")

    def close(self):
        if self.producer:
            self.producer.close()


def main():
    parser = argparse.ArgumentParser(description="Replay NYC TLC data to Kafka")
    parser.add_argument("--parquet-path", type=str, default="data/nyc-taxi/yellow_tripdata_2023-01.parquet")
    parser.add_argument("--kafka", type=str, default="localhost:9092", help="Kafka bootstrap servers")
    parser.add_argument("--topic", type=str, default="nyc-taxi-events")
    parser.add_argument("--rate", type=int, default=100, help="Events per second")
    parser.add_argument("--no-shuffle", action="store_true", help="Don't shuffle events")
    parser.add_argument("--inject-anomalies", action="store_true", help="Inject synthetic anomalies")
    parser.add_argument("--anomaly-rate", type=float, default=0.02, help="Anomaly injection rate")
    parser.add_argument("--direct", action="store_true", help="Direct mode (print to stdout, no Kafka)")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit number of rows")

    args = parser.parse_args()

    parquet_path = Path(args.parquet_path)
    if not parquet_path.exists():
        print(f"ERROR: Parquet file not found: {args.parquet_path}")
        print("Run: python scripts/download_nyc_taxi.py --month 2023-01")
        sys.exit(1)

    print(f"Loading parquet from {parquet_path}...")
    df = pd.read_parquet(parquet_path)

    if args.max_rows:
        df = df.head(args.max_rows)

    print(f"Loaded {len(df):,} records")

    producer = NYCTaxiReplayProducer(
        kafka_bootstrap=args.kafka,
        topic=args.topic,
        rate=args.rate,
        shuffle=not args.no_shuffle,
        inject_anomalies=args.inject_anomalies,
        anomaly_rate=args.anomaly_rate,
        direct_mode=args.direct,
    )

    producer.replay(df)
    producer.close()


if __name__ == "__main__":
    main()
