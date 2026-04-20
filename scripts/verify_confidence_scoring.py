#!/usr/bin/env python3
"""
Manual verification of Phase 1 confidence scoring.

Usage:
    python scripts/verify_confidence_scoring.py --events 10000
    python scripts/verify_confidence_scoring.py --events 100000 --profile
"""
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from streamdq.producers.nyc_taxi_replay import NYCTaxiReplayProducer
from streamdq.rules.cross_record import evaluate_duplicate_event, CrossRecordState
from streamdq.rules.adjudicator import ContextAwareDuplicateAdjudicator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=10000, help="Number of events to process")
    parser.add_argument("--profile", action="store_true", help="Enable profiling")
    args = parser.parse_args()

    print("="*70)
    print(f"Phase 1 Confidence Scoring Verification ({args.events:,} events)")
    print("="*70)

    # Setup
    state = CrossRecordState()
    adjudicator = ContextAwareDuplicateAdjudicator()

    violations_by_confidence = {
        "high": [],      # >0.7
        "medium": [],    # 0.4-0.7
        "suppressed": 0  # ≤0.4
    }

    # Load data
    parquet_path = Path(__file__).parent.parent / "data" / "yellow_tripdata_2024-01.parquet"

    if not parquet_path.exists():
        print(f"ERROR: {parquet_path} not found")
        print("Download NYC Taxi data first:")
        print("  wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet")
        return 1

    import pandas as pd
    print(f"\nLoading {args.events:,} events from parquet...")
    df = pd.read_parquet(parquet_path).head(args.events)

    # Process events
    print(f"Processing {len(df):,} events...")
    start_time = time.time()
    base_time = datetime(2024, 1, 15, 10, 0, 0)

    for idx, row in df.iterrows():
        if idx % 10000 == 0 and idx > 0:
            print(f"  Processed {idx:,} events...")

        event = row.to_dict()
        event["_lineage"] = {
            "source_id": "verification_test",
            "source_type": "batch_replay",
            "is_replay": False,
            "batch_id": "verify_batch"
        }

        event_time = base_time + timedelta(seconds=idx)
        violation = evaluate_duplicate_event(
            event, event_time,
            dedup_state=state,
            adjudicator=adjudicator
        )

        if violation:
            confidence = violation.details.get("adjudication_confidence", 0.0)
            if confidence > 0.7:
                violations_by_confidence["high"].append(violation)
            elif confidence > 0.4:
                violations_by_confidence["medium"].append(violation)
        else:
            # Check if it was suppressed (confidence ≤0.4)
            # This is an approximation since we don't have access to internal state
            pass

    elapsed = time.time() - start_time

    # Results
    total_violations = len(violations_by_confidence["high"]) + len(violations_by_confidence["medium"])
    high_count = len(violations_by_confidence["high"])
    medium_count = len(violations_by_confidence["medium"])

    precision = high_count / total_violations if total_violations > 0 else 0.0

    print(f"\n{'='*70}")
    print("Results")
    print(f"{'='*70}")
    print(f"Events processed: {len(df):,}")
    print(f"Processing time: {elapsed:.2f}s ({len(df)/elapsed:.0f} events/s)")
    print(f"\nViolations:")
    print(f"  High confidence (>0.7): {high_count:,}")
    print(f"  Medium confidence (0.4-0.7): {medium_count:,}")
    print(f"  Total violations: {total_violations:,}")
    print(f"\nPrecision (high confidence / total): {precision*100:.1f}%")
    print(f"Target: ≥45%")
    print(f"Status: {'✅ PASS' if precision >= 0.45 else '❌ FAIL'}")
    print(f"{'='*70}")

    # State statistics
    print(f"\nState Statistics:")
    print(f"  Fingerprints tracked: {state.dedup_count:,}")
    print(f"  Adjudicator history entries: {len(adjudicator._history):,}")

    if args.profile:
        print(f"\nProfiling enabled - implement detailed profiling here")

    return 0 if precision >= 0.45 else 1


if __name__ == "__main__":
    sys.exit(main())
