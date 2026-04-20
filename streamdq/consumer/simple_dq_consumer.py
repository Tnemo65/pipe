#!/usr/bin/env python3
"""
Simple Kafka Consumer for StreamDQ - Alternative to Spark Streaming
Demonstrates end-to-end data quality monitoring without Spark JAR dependencies
"""
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from kafka import KafkaConsumer, KafkaProducer
from prometheus_client import Counter, Gauge, start_http_server
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics (with collision protection)
try:
    EVENTS_PROCESSED = Counter('streamdq_events_processed_total', 'Total events processed')
    VIOLATIONS_DETECTED = Counter('streamdq_violations_detected_total', 'Violations detected', ['rule_id', 'severity'])
    PROCESSING_LAG = Gauge('streamdq_processing_lag_seconds', 'Consumer lag in seconds')
except ValueError:
    # Metrics already registered, fetch existing
    from prometheus_client import REGISTRY
    EVENTS_PROCESSED = REGISTRY._names_to_collectors.get('streamdq_events_processed_total')
    VIOLATIONS_DETECTED = REGISTRY._names_to_collectors.get('streamdq_violations_detected_total')
    PROCESSING_LAG = REGISTRY._names_to_collectors.get('streamdq_processing_lag_seconds')

# Data quality rules
class DataQualityRules:
    """NYC Taxi data quality validation rules"""

    @staticmethod
    def validate_syntactic(record: Dict) -> List[Dict]:
        """SYN001-003: Syntactic validation"""
        violations = []
        trip_id = record.get('trip_id', 'unknown')

        # SYN001: Negative fare amount
        fare = record.get('fare_amount')
        if fare is not None and fare < 0:
            violations.append({
                'rule_id': 'SYN001',
                'rule_name': 'Negative fare amount',
                'entity_id': trip_id,
                'entity_type': 'nyc_taxi',
                'severity': 'HIGH',
                'violation_type': 'SYNTACTIC',
                'record_snapshot': json.dumps(record),
                'detected_at': datetime.now().isoformat(),
            })

        # SYN002: Invalid pickup location
        pu_location = record.get('PULocationID')
        if pu_location is not None and (pu_location < 1 or pu_location > 263):
            violations.append({
                'rule_id': 'SYN002',
                'rule_name': 'Invalid pickup location ID',
                'entity_id': trip_id,
                'entity_type': 'nyc_taxi',
                'severity': 'MEDIUM',
                'violation_type': 'SYNTACTIC',
                'record_snapshot': json.dumps(record),
                'detected_at': datetime.now().isoformat(),
            })

        # SYN003: Invalid dropoff location
        do_location = record.get('DOLocationID')
        if do_location is not None and (do_location < 1 or do_location > 263):
            violations.append({
                'rule_id': 'SYN003',
                'rule_name': 'Invalid dropoff location ID',
                'entity_id': trip_id,
                'entity_type': 'nyc_taxi',
                'severity': 'MEDIUM',
                'violation_type': 'SYNTACTIC',
                'record_snapshot': json.dumps(record),
                'detected_at': datetime.now().isoformat(),
            })

        return violations

    @staticmethod
    def validate_semantic(record: Dict) -> List[Dict]:
        """SEM001-003: Semantic validation"""
        violations = []
        trip_id = record.get('trip_id', 'unknown')

        # SEM001: Trip distance vs fare mismatch
        distance = record.get('trip_distance', 0)
        fare = record.get('fare_amount', 0)
        if distance > 0 and fare > 0:
            fare_per_mile = fare / distance
            if fare_per_mile < 1.0 or fare_per_mile > 50.0:
                violations.append({
                    'rule_id': 'SEM001',
                    'rule_name': 'Fare per mile out of range',
                    'entity_id': trip_id,
                    'entity_type': 'nyc_taxi',
                    'severity': 'MEDIUM',
                    'violation_type': 'SEMANTIC',
                    'record_snapshot': json.dumps(record),
                    'detected_at': datetime.now().isoformat(),
                })

        return violations


class StreamDQConsumer:
    """Simple Kafka consumer for data quality monitoring"""

    def __init__(
        self,
        kafka_bootstrap: str,
        input_topic: str,
        output_topic: str,
        postgres_config: Dict,
        metrics_port: int = 9091
    ):
        self.kafka_bootstrap = kafka_bootstrap
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.postgres_config = postgres_config
        self.metrics_port = metrics_port

        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            input_topic,
            bootstrap_servers=kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='streamdq-consumer-group'
        )

        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # PostgreSQL connection
        self.pg_conn = None
        self._connect_postgres()

        logger.info(f"StreamDQ Consumer initialized")
        logger.info(f"  Input topic: {input_topic}")
        logger.info(f"  Output topic: {output_topic}")
        logger.info(f"  Kafka bootstrap: {kafka_bootstrap}")

    def _connect_postgres(self):
        """Connect to PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(**self.postgres_config)
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.pg_conn = None

    def _write_to_postgres(self, violations: List[Dict]):
        """Write violations to PostgreSQL"""
        if not self.pg_conn or not violations:
            return

        try:
            with self.pg_conn.cursor() as cur:
                values = [
                    (
                        v['rule_id'],
                        v['rule_name'],
                        v['entity_id'],
                        v['entity_type'],
                        v['severity'],
                        v['violation_type'],
                        v['record_snapshot'],
                        v['detected_at']
                    )
                    for v in violations
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO violations
                    (rule_id, rule_name, entity_id, entity_type, severity,
                     violation_type, record_snapshot, detected_at)
                    VALUES %s
                    """,
                    values
                )
                self.pg_conn.commit()
                logger.debug(f"Wrote {len(violations)} violations to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to write to PostgreSQL: {e}")
            self.pg_conn.rollback()
            # Try to reconnect
            self._connect_postgres()

    def process_message(self, message) -> int:
        """Process a single Kafka message"""
        try:
            record = message.value

            # Add trip_id if not present
            if 'trip_id' not in record:
                record['trip_id'] = f"{message.partition}-{message.offset}"

            # Apply data quality rules
            violations = []
            violations.extend(DataQualityRules.validate_syntactic(record))
            violations.extend(DataQualityRules.validate_semantic(record))

            # Update metrics
            EVENTS_PROCESSED.inc()
            for violation in violations:
                VIOLATIONS_DETECTED.labels(
                    rule_id=violation['rule_id'],
                    severity=violation['severity']
                ).inc()

            # Send violations to Kafka
            for violation in violations:
                self.producer.send(self.output_topic, value=violation)

            # Write to PostgreSQL
            if violations:
                self._write_to_postgres(violations)
                logger.info(f"Detected {len(violations)} violations in trip {record['trip_id']}")

            return len(violations)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return 0

    def run(self):
        """Run the consumer loop"""
        logger.info(f"Starting consumer loop...")
        logger.info(f"Prometheus metrics: http://localhost:{self.metrics_port}/metrics")

        # Start Prometheus metrics server
        start_http_server(self.metrics_port)

        violation_count = 0
        processed_count = 0

        try:
            for message in self.consumer:
                violations = self.process_message(message)
                violation_count += violations
                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} events, detected {violation_count} violations")

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.consumer.close()
            self.producer.close()
            if self.pg_conn:
                self.pg_conn.close()
            logger.info(f"Consumer stopped. Total: {processed_count} events, {violation_count} violations")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='StreamDQ Simple Kafka Consumer')
    parser.add_argument('--kafka-bootstrap', required=True, help='Kafka bootstrap servers')
    parser.add_argument('--input-topic', required=True, help='Input Kafka topic')
    parser.add_argument('--output-topic', required=True, help='Output Kafka topic for violations')
    parser.add_argument('--postgres-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int, default=5433, help='PostgreSQL port')
    parser.add_argument('--postgres-db', default='streamdq', help='PostgreSQL database')
    parser.add_argument('--postgres-user', default='streamdq', help='PostgreSQL user')
    parser.add_argument('--postgres-password', default='streamdq', help='PostgreSQL password')
    parser.add_argument('--metrics-port', type=int, default=9091, help='Prometheus metrics port')

    args = parser.parse_args()

    postgres_config = {
        'host': args.postgres_host,
        'port': args.postgres_port,
        'database': args.postgres_db,
        'user': args.postgres_user,
        'password': args.postgres_password,
    }

    consumer = StreamDQConsumer(
        kafka_bootstrap=args.kafka_bootstrap,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        postgres_config=postgres_config,
        metrics_port=args.metrics_port
    )

    consumer.run()


if __name__ == '__main__':
    main()
