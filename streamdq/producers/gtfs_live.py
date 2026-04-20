"""
GTFS Malaysia Realtime Consumer.

Polls Malaysia's official GTFS Realtime API and pushes vehicle positions to Kafka.
Supports KTMB (trains) and Prasarana (buses, LRT, MRT, monorail).

Source: https://api.data.gov.my/gtfs-realtime/vehicle-position/{agency}
Update frequency: Every 30 seconds
Format: GTFS Realtime protobuf

Usage:
    python -m streamdq.producers.gtfs_live \\
        --kafka localhost:9092 \\
        --topic gtfs-vehicle-pos \\
        --agencies ktmb prasaranabus \\
        --poll-interval 30
"""
from __future__ import annotations
import argparse
import json
import sys
import threading
import time
from datetime import datetime
from typing import Optional
from streamdq.models.lineage import LineageMetadata

# Optional imports
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import gtfs_realtime_pb2
    HAS_GTFS_pb2 = True
except ImportError:
    HAS_GTFS_pb2 = False

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False


AGENCIES = {
    "ktmb": "https://api.data.gov.my/gtfs-realtime/vehicle-position/ktmb",
    "prasaranabus": "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasaranabus?category=rapid-bus-kl",
    "prasaranalrt": "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasaranabus?category=lrt",
}


class GTFSLiveConsumer:
    """
    Poll Malaysia GTFS Realtime API and push vehicle positions to Kafka.

    Features:
    - Polls every N seconds (default 30)
    - Parses GTFS Realtime protobuf
    - Handles errors gracefully (continues polling)
    - Runs in background thread
    """

    def __init__(
        self,
        kafka_bootstrap: str = None,
        kafka_topic: str = "gtfs-vehicle-pos",
        agencies: list[str] = None,
        poll_interval: int = 30,
        direct_mode: bool = False,
    ):
        self.kafka_bootstrap = kafka_bootstrap
        self.kafka_topic = kafka_topic
        self.agencies = list(agencies) if agencies else list(AGENCIES.keys())
        self.poll_interval = poll_interval
        self.direct_mode = direct_mode

        self.producer: Optional[KafkaProducer] = None
        if not direct_mode and HAS_KAFKA and kafka_bootstrap:
            self.producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                acks="all",
            )

        self.stats = {"polls": 0, "vehicles": 0, "errors": 0, "kafka_errors": 0}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _fetch_feed(self, url: str) -> Optional[gtfs_realtime_pb2.FeedMessage]:
        """Fetch and parse GTFS Realtime protobuf feed."""
        if not HAS_REQUESTS:
            print("ERROR: requests library not installed. Run: pip install requests")
            return None
        if not HAS_GTFS_pb2:
            print("ERROR: gtfs-realtime-bindings not installed. Run: pip install gtfs-realtime-bindings")
            return None

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(resp.content)
            return feed
        except Exception as e:
            print(f"Error fetching GTFS feed: {e}")
            self.stats["errors"] += 1
            return None

    def _parse_vehicle(self, entity) -> Optional[dict]:
        """Parse a GTFS Realtime VehiclePosition entity to dict."""
        if not entity.HasField("vehicle"):
            return None

        vehicle = entity.vehicle
        pos = vehicle.position
        trip = vehicle.trip
        vehicle_info = vehicle.vehicle

        lat = pos.latitude if pos.HasField("latitude") else None
        lon = pos.longitude if pos.HasField("longitude") else None

        if lat is None or lon is None:
            return None

        result = {
            "vehicle_id": str(vehicle_info.id) if vehicle_info.HasField("id") else "",
            "label": str(vehicle_info.label) if vehicle_info.HasField("label") else "",
            "latitude": float(lat),
            "longitude": float(lon),
            "bearing": float(pos.bearing) if pos.HasField("bearing") else None,
            "speed": float(pos.speed) if pos.HasField("speed") else None,
            "route_id": str(trip.route_id) if trip.HasField("route_id") else "",
            "trip_id": str(trip.trip_id) if trip.HasField("trip_id") else "",
            "direction_id": int(trip.direction_id) if trip.HasField("direction_id") else None,
            "stop_id": str(vehicle.stop_id) if vehicle.HasField("stop_id") else "",
            "timestamp": int(vehicle.timestamp) if vehicle.HasField("timestamp") else None,
            "timestamp_iso": (
                datetime.fromtimestamp(vehicle.timestamp).isoformat()
                if vehicle.HasField("timestamp") else None
            ),
            "event_time": datetime.now().isoformat(),
        }
        return result

    def _enrich_with_lineage(self, vehicle: dict, agency: str) -> dict:
        """
        Attach lineage metadata to vehicle position event.

        Adds _lineage field with source tracking info.
        Part of Phase 0 (T3: Source Lineage Awareness).

        Args:
            vehicle: Vehicle position dict
            agency: Agency name (ktmb, prasaranabus, etc.)

        Returns:
            Vehicle dict with _lineage field added
        """
        lineage = LineageMetadata(
            source_id=f"gtfs_api_{agency}",
            source_type="api_poll",
            is_replay=False,
            batch_id=None,
            producer_timestamp=datetime.now().isoformat(),
            hop_count=0
        )

        enriched = dict(vehicle)
        enriched["_lineage"] = lineage.to_dict()
        return enriched

    def _poll_agency(self, agency: str) -> list[dict]:
        """Poll a single agency and return parsed vehicle positions."""
        url = AGENCIES.get(agency)
        if not url:
            return []

        feed = self._fetch_feed(url)
        if feed is None:
            return []

        vehicles = []
        for entity in feed.entity:
            parsed = self._parse_vehicle(entity)
            if parsed:
                parsed["_agency"] = agency
                # NEW: Enrich with lineage metadata
                enriched = self._enrich_with_lineage(parsed, agency)
                vehicles.append(enriched)

        return vehicles

    def _poll_all(self) -> list[dict]:
        """Poll all configured agencies."""
        all_vehicles = []
        for agency in self.agencies:
            vehicles = self._poll_agency(agency)
            all_vehicles.extend(vehicles)
            self.stats["vehicles"] += len(vehicles)
        self.stats["polls"] += 1
        return all_vehicles

    def _emit_to_kafka(self, vehicles: list[dict]):
        """Emit vehicle positions to Kafka or stdout."""
        if self.direct_mode:
            for v in vehicles:
                print(json.dumps(v))
            return

        if self.producer is None:
            return

        for vehicle in vehicles:
            try:
                # NG-2a: Attach Kafka produce timestamp for E2E latency measurement
                vehicle["kafka_arrival_ms"] = time.time() * 1000
                future = self.producer.send(self.kafka_topic, value=vehicle)
                record_metadata = future.get(timeout=10)
                self.stats["kafka_errors"] = 0
            except KafkaError as e:
                self.stats["kafka_errors"] += 1
                print(f"[GTFS] Kafka send failed: {e}")

    def _run_loop(self):
        """Main polling loop (runs in background thread)."""
        while self._running:
            vehicles = self._poll_all()
            if vehicles:
                self._emit_to_kafka(vehicles)
                print(f"[GTFS] {len(vehicles)} vehicles ({self.stats['polls']} polls) "
                      f"— Total: {self.stats['vehicles']} vehicles — Errors: {self.stats['errors']}")
            else:
                print(f"[GTFS] Poll #{self.stats['polls']} — No vehicles or error — "
                      f"Errors: {self.stats['errors']}")
            time.sleep(self.poll_interval)

    def start(self):
        """Start polling in background thread."""
        if self._running:
            print("GTFS consumer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"GTFS Live Consumer started. Polling {self.agencies} every {self.poll_interval}s")
        print(f"Mode: {'DIRECT (stdout)' if self.direct_mode else 'KAFKA'}")

    def stop(self):
        """Stop polling and close connections."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.producer:
            self.producer.flush()
            self.producer.close()
        print(f"GTFS Live Consumer stopped. Final stats: {self.stats}")

    def poll_once(self) -> list[dict]:
        """Single poll (for testing). Returns all vehicle positions."""
        return self._poll_all()

    def get_stats(self) -> dict:
        """Return producer statistics for monitoring."""
        return dict(self.stats)


def main():
    parser = argparse.ArgumentParser(description="GTFS Malaysia Realtime Consumer")
    parser.add_argument("--kafka", type=str, default="localhost:9092", help="Kafka bootstrap servers")
    parser.add_argument("--topic", type=str, default="gtfs-vehicle-pos", help="Kafka topic")
    parser.add_argument("--agencies", nargs="+", default=["ktmb"], help="Agencies to poll")
    parser.add_argument("--poll-interval", type=int, default=30, help="Poll interval in seconds")
    parser.add_argument("--direct", action="store_true", help="Direct mode (print to stdout)")
    parser.add_argument("--once", action="store_true", help="Single poll and exit")

    args = parser.parse_args()

    consumer = GTFSLiveConsumer(
        kafka_bootstrap=args.kafka,
        kafka_topic=args.topic,
        agencies=args.agencies,
        poll_interval=args.poll_interval,
        direct_mode=args.direct,
    )

    if args.once:
        vehicles = consumer.poll_once()
        print(f"Found {len(vehicles)} vehicles:")
        for v in vehicles[:5]:
            print(f"  {v.get('vehicle_id')}: lat={v.get('latitude')}, lon={v.get('longitude')}")
        if len(vehicles) > 5:
            print(f"  ... and {len(vehicles) - 5} more")
    else:
        consumer.start()
        try:
            while consumer._running:
                time.sleep(1)
        except KeyboardInterrupt:
            consumer.stop()


if __name__ == "__main__":
    main()
