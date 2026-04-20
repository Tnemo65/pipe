#!/usr/bin/env python3
"""
Manual verification of lineage-aware duplicate detection.

Replays sample NYC Taxi events and verifies:
1. Events have _lineage metadata
2. Replay duplicates are suppressed
3. Live duplicates are detected
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from streamdq.producers.nyc_taxi_replay import NYCTaxiReplayProducer
from streamdq.rules.cross_record import evaluate_duplicate_event, CrossRecordState
from streamdq.models.lineage import LineageMetadata


def main():
    print("=" * 70)
    print("Phase 0 Lineage Verification")
    print("=" * 70)

    # Test 1: Replay producer enrichment
    print("\n✓ Test 1: Replay producer enrichment")
    producer = NYCTaxiReplayProducer(direct_mode=True, inject_anomalies=False)

    event = {
        "trip_id": "test_001",
        "PULocationID": 161,
        "DOLocationID": 237,
        "passenger_count": 1,
        "trip_distance": 2.5,
        "fare_amount": 15.50
    }

    enriched = producer._enrich_with_lineage(event)

    assert "_lineage" in enriched, "❌ Missing _lineage"
    lineage = LineageMetadata.from_dict(enriched["_lineage"])

    print(f"  source_id: {lineage.source_id}")
    print(f"  source_type: {lineage.source_type}")
    print(f"  is_replay: {lineage.is_replay}")
    print(f"  batch_id: {lineage.batch_id}")

    assert lineage.source_type == "batch_replay"
    assert lineage.is_replay is True
    print("  ✅ Replay enrichment works")

    # Test 2: Replay duplicate suppression
    print("\n✓ Test 2: Replay duplicate suppression")
    state = CrossRecordState()
    t1 = datetime.now()
    t2 = t1 + timedelta(seconds=30)

    violation1 = evaluate_duplicate_event(enriched, t1, dedup_state=state)
    print(f"  First event violation: {violation1}")
    assert violation1 is None

    enriched2 = producer._enrich_with_lineage(event)
    violation2 = evaluate_duplicate_event(enriched2, t2, dedup_state=state)
    print(f"  Duplicate event violation: {violation2}")
    assert violation2 is None, "❌ Replay duplicate NOT suppressed"
    print("  ✅ Replay duplicates suppressed")

    # Test 3: Live stream duplicate detection
    print("\n✓ Test 3: Live stream duplicate detection")
    state2 = CrossRecordState()

    live_event = {
        "trip_id": "test_002",
        "PULocationID": 150,
        "DOLocationID": 200,
        "passenger_count": 2,
        "trip_distance": 3.0
    }

    t3 = datetime.now()
    t4 = t3 + timedelta(seconds=30)

    violation3 = evaluate_duplicate_event(live_event, t3, dedup_state=state2)
    assert violation3 is None

    violation4 = evaluate_duplicate_event(live_event, t4, dedup_state=state2)
    print(f"  Live duplicate violation: {violation4}")
    assert violation4 is not None, "❌ Live duplicate NOT detected"
    assert violation4.rule_id == "CRS003"
    print("  ✅ Live duplicates detected")

    # Summary
    print("\n" + "=" * 70)
    print("✅ All Phase 0 lineage checks passed!")
    print("=" * 70)
    print(f"\nExpected impact: +5-8 precision points (22.9% → 28-31%)")
    print("Next: Phase 1 (T1: Context-Aware Duplicate Adjudication, Day 4-13)")


if __name__ == "__main__":
    main()
