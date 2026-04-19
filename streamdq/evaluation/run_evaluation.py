"""
Main evaluation script — run full benchmark on NYC TLC data.

Usage:
    python -m streamdq.evaluation.run_evaluation \
        --parquet-path data/nyc-taxi/yellow_tripdata_2023-01.parquet \
        --anomaly-rate 0.05 \
        --max-events 100000 \
        --output evaluation_results.json
"""
from __future__ import annotations
import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from streamdq.pipeline.local_pipeline import LocalPipeline
from streamdq.rules.registry import build_default_registry, reset_cross_record_state
from streamdq.rules.adaptive import AdaptiveThresholdEngine
from streamdq.storage.violation_store import ViolationStore
from streamdq.evaluation.metrics import EvaluationMetrics
from streamdq.evaluation.case_study import generate_case_study, print_case_study
from streamdq.evaluation.comparison import run_comparison, print_comparison_table


# ────────────────────────────────────────────────────────────────
# Anomaly injection strategies
# ────────────────────────────────────────────────────────────────

ANOMALY_TYPES = [
    "fare_negative",
    "fare_outlier",
    "location_invalid",
    "timestamp_future",
    "duration_negative",
    "duration_outlier",
    "speed_outlier",
    "duplicate",
]


def inject_anomaly(event: dict, anomaly_type: str, index: int) -> tuple[dict, str]:
    """
    Inject a synthetic anomaly into an event.

    Returns:
        tuple: (modified_event, anomaly_type). For "duplicate", returns (original, anomaly_type)
        and the caller should inject a second copy of the event immediately after.
    """
    event = dict(event)  # shallow copy

    if anomaly_type == "fare_negative":
        event["fare_amount"] = round(random.uniform(-50, -2.5), 2)
        event["total_amount"] = event.get("total_amount", 0) + event["fare_amount"]

    elif anomaly_type == "fare_outlier":
        event["fare_amount"] = round(random.uniform(500, 2000), 2)
        event["total_amount"] = event["fare_amount"] + event.get("extra", 0) + event.get("mta_tax", 0)

    elif anomaly_type == "location_invalid":
        event["PULocationID"] = random.randint(9999, 99999)

    elif anomaly_type == "timestamp_future":
        event["tpep_pickup_datetime"] = (datetime.now() + timedelta(days=7)).isoformat()

    elif anomaly_type == "duration_negative":
        pickup = event.get("tpep_pickup_datetime")
        if isinstance(pickup, str):
            try:
                dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                event["tpep_pickup_datetime"] = (dt + timedelta(hours=1)).isoformat()
                event["tpep_dropoff_datetime"] = (dt - timedelta(minutes=30)).isoformat()
            except (ValueError, AttributeError):
                pass

    elif anomaly_type == "duration_outlier":
        pickup = event.get("tpep_pickup_datetime")
        if isinstance(pickup, str):
            try:
                dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                event["tpep_dropoff_datetime"] = (dt + timedelta(hours=20)).isoformat()
            except (ValueError, AttributeError):
                pass

    elif anomaly_type == "speed_outlier":
        # 100 miles in 30 minutes → 200 mph
        event["trip_distance"] = 100.0
        pickup = event.get("tpep_pickup_datetime")
        if isinstance(pickup, str):
            try:
                dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                event["tpep_dropoff_datetime"] = (dt + timedelta(minutes=30)).isoformat()
            except (ValueError, AttributeError):
                pass

    elif anomaly_type == "duplicate":
        # Duplicate handled at evaluation level (CRS003) not at injection
        pass

    return event, anomaly_type


# ────────────────────────────────────────────────────────────────
# Main evaluation
# ────────────────────────────────────────────────────────────────

def run_evaluation(
    parquet_path: str,
    anomaly_rate: float = 0.05,
    max_events: int = 100_000,
    random_seed: int = 42,
    output_path: str = None,
    warmup_events: int = 10_000,
    label_delay_events: int = 0,
) -> dict:
    """
    Args:
        ...
        label_delay_events: NG-33: Number of events to delay before ground-truth
            labels become available. Simulates real-world scenario where anomaly
            labels are not instantly available (e.g., manual review, business
            confirmation). During the delay window, violations on anomalous
            entities are NOT counted as TP — they accumulate as unclassified.
    """
    """
    Run full evaluation on NYC TLC parquet data.

    Steps:
    1. Load parquet file
    2. Shuffle and cap to max_events
    3. Inject anomalies at anomaly_rate
    4. Warmup: process events without recording metrics
    5. Process remaining events through LocalPipeline with metrics
    6. Compute metrics (precision, recall, latency)
    7. Generate case study and comparison
    """
    print("=" * 60)
    print("StreamDQ Evaluation — Full Benchmark")
    print("=" * 60)

    random.seed(random_seed)

    # ── Step 1: Load data ────────────────────────────────────────
    print(f"\n[1/6] Loading data from {parquet_path}...")
    import pandas as pd
    df = pd.read_parquet(parquet_path)
    print(f"  Loaded {len(df):,} records, {len(df.columns)} columns")

    # ── Step 2: Prepare events ───────────────────────────────────
    print(f"\n[2/6] Preparing {max_events:,} events (shuffling, capping)...")
    df = df.sample(frac=min(1.0, max_events / len(df)), random_state=random_seed)
    df = df.reset_index(drop=True)
    events = df.to_dict(orient="records")
    print(f"  Prepared {len(events):,} events")

    # ── Step 3: Inject anomalies ────────────────────────────────
    print(f"\n[3/6] Injecting anomalies at {anomaly_rate:.1%} rate...")
    anomaly_events = {}  # index -> anomaly_type
    num_anomalies = int(len(events) * anomaly_rate)
    anomaly_indices = random.sample(range(len(events)), num_anomalies)

    for idx in anomaly_indices:
        atype = random.choice(ANOMALY_TYPES)
        events[idx], _ = inject_anomaly(events[idx], atype, idx)
        anomaly_events[idx] = atype

    print(f"  Injected {num_anomalies:,} anomalies across types:")
    from collections import Counter
    type_counts = Counter(anomaly_events.values())
    for atype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    - {atype}: {count:,}")

    # ── Step 4: Run pipeline ─────────────────────────────────────
    print(f"\n[4/6] Running LocalPipeline on {len(events):,} events...")
    start_time = time.perf_counter()

    # Reset state
    reset_cross_record_state()

    # Build evaluation metrics tracker
    eval_metrics = EvaluationMetrics(label_delay_events=label_delay_events)

    # Track injected anomalies for ground truth
    injected_anomalies = {}  # index -> anomaly_type
    for idx in anomaly_indices:
        injected_anomalies[idx] = anomaly_events[idx]

    # Pipeline
    pipeline = LocalPipeline()
    all_violations = []

    # ── Step 4a: Warmup ──────────────────────────────────────────
    # Discard warmup events to let adaptive thresholds stabilize.
    # Recording violations during warmup would inflate false-positive rate.
    warmup_count = min(warmup_events, len(events) // 4)
    print(f"  Warmup: processing {warmup_count:,} events without metrics...")
    warmup_start = time.perf_counter()
    for i in range(warmup_count):
        pipeline.process_event(events[i])
    warmup_elapsed = time.perf_counter() - warmup_start
    print(f"  Warmup done in {warmup_elapsed:.1f}s")

    # ── Step 4b: Measurement ───────────────────────────────────────
    print(f"  Measurement: processing {len(events) - warmup_count:,} events...")
    event_start = time.perf_counter()

    for i in range(warmup_count, len(events)):
        event = events[i]
        injected_type = injected_anomalies.get(i)

        # For "duplicate" anomalies: the original event is clean (no violation expected).
        # The DUPLICATE is the anomaly. Only CRS003 on the 2nd occurrence fires.
        if injected_type == "duplicate":
            # Process original: violations here are NOT the duplicate anomaly.
            # Record with anomaly_type=None (non-anomalous violations).
            violations = pipeline.process_event(event)
            for v in violations:
                all_violations.append(v)
                # Original event is clean — don't associate its violations with "duplicate"
                eval_metrics.add_detected_violation(
                    rule_id=v.rule_id,
                    entity_index=i,
                    latency_ms=v.processing_latency_ms,
                    anomaly_type=None,
                )
            # Process duplicate (same event, new dedup hash entry):
            # CRS003 fires because the dedup state already has this hash.
            dup_violations = pipeline.process_event(dict(event))
            for v in dup_violations:
                all_violations.append(v)
                eval_metrics.add_detected_violation(
                    rule_id=v.rule_id,
                    entity_index=i,
                    latency_ms=v.processing_latency_ms,
                    anomaly_type="duplicate",
                )
        else:
            # Normal (non-duplicate) anomalies
            violations = pipeline.process_event(event)
            for v in violations:
                all_violations.append(v)
                eval_metrics.add_detected_violation(
                    rule_id=v.rule_id,
                    entity_index=i,
                    latency_ms=v.processing_latency_ms,
                    anomaly_type=injected_type,
                )

        # Progress
        if (i + 1) % 10_000 == 0:
            elapsed = time.perf_counter() - event_start
            rate = (i + 1 - warmup_count) / elapsed
            total = len(events) - warmup_count
            print(f"  Progress: {i+1-warmup_count:,}/{total:,} ({100*(i+1-warmup_count)/total:.1f}%) — {rate:.0f} events/sec")

    total_time = time.perf_counter() - start_time
    print(f"\n  Completed in {total_time:.1f}s — {len(events)/total_time:.0f} events/sec")

    # ── Step 5: Compute metrics ──────────────────────────────────
    print("\n[5/6] Computing metrics...")

    # Record injected anomalies
    for idx, atype in injected_anomalies.items():
        eval_metrics.add_injected_anomaly(atype, idx)

    report = eval_metrics.full_report()

    # Pipeline metrics
    pipeline_metrics = pipeline.get_metrics()

    # ── Step 6: Output results ──────────────────────────────────
    print("\n[6/6] Generating report...")

    # Extract point estimates from report dicts
    prec_pt = report["precision"]["point_estimate"]
    rec_pt = report["recall_overall"]["point_estimate"]

    # Case study
    case = generate_case_study(
        dataset_size=len(events),
        anomaly_rate=anomaly_rate,
        recall=rec_pt,
        precision=prec_pt,
    )

    # Comparison
    comparison = run_comparison()
    # Update StreamDQ results with actual evaluation
    comparison["streamdq"].precision = prec_pt
    comparison["streamdq"].recall = rec_pt
    comparison["streamdq"].f1_score = (
        2 * prec_pt * rec_pt / max(prec_pt + rec_pt, 0.001)
    )

    # Build final report
    final_report = {
        "evaluation_config": {
            "parquet_path": parquet_path,
            "anomaly_rate": anomaly_rate,
            "max_events": max_events,
            "random_seed": random_seed,
            "label_delay_events": label_delay_events,
        },
        "pipeline_metrics": {
            "total_events": pipeline_metrics["total_events"],
            "total_violations": pipeline_metrics["total_violations"],
            "violation_rate": round(pipeline_metrics["violation_rate"], 4),
            "throughput_events_per_sec": round(len(events) / total_time, 0),
        },
        "quality_metrics": {
            "precision": round(prec_pt, 4),
            "recall_overall": round(rec_pt, 4),
            "f1_score": round(comparison["streamdq"].f1_score, 4),
            "false_positive_rate": round(report["false_positive_rate"]["point_estimate"], 4),
            "precision_ci_95": report["precision"]["ci_95"],
            "recall_ci_95": report["recall_overall"]["ci_95"],
            "detection_rate_by_type": report["detection_rate_by_type"],
            "latency": report["latency"],
            "rule_coverage": report["rule_coverage"],
        },
        "business_impact": {
            "monthly_savings": case.monthly_savings,
            "annual_savings": case.monthly_savings * 12,
            "anomalies_caught_per_month": case.anomalies_caught,
        },
        "comparison": {name: r.to_dict() for name, r in comparison.items()},
    }

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"\nDataset: {len(events):,} events, {anomaly_rate:.1%} anomaly rate")
    print(f"Violations detected: {len(all_violations):,}")
    print(f"Precision: {prec_pt:.1%}  (95% CI: {report['precision']['ci_95'][0]:.1%}–{report['precision']['ci_95'][1]:.1%})")
    print(f"Recall:    {rec_pt:.1%}  (95% CI: {report['recall_overall']['ci_95'][0]:.1%}–{report['recall_overall']['ci_95'][1]:.1%})")
    print(f"F1 Score:  {comparison['streamdq'].f1_score:.1%}")
    print(f"FPR:       {report['false_positive_rate']['point_estimate']:.1%}")
    print(f"\nLatency P50: {report['latency']['p50_ms']:.0f}ms")
    print(f"Latency P99: {report['latency']['p99_ms']:.0f}ms")
    print(f"\nDetection by anomaly type:")
    for atype, d in sorted(report["detection_rate_by_type"].items(), key=lambda x: -x[1]["detection_rate"]):
        print(f"  {atype:25s}: {d['detection_rate']:6.1%} ({d['detected']}/{d['total']})")

    print("\n" + "-" * 60)
    print_case_study(case)
    print("-" * 60)
    print("\nTool Comparison:")
    print_comparison_table(comparison)

    # Save to file
    if output_path:
        with open(output_path, "w") as f:
            json.dump(final_report, f, indent=2, default=str)
        print(f"\nFull report saved to: {output_path}")

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)

    return final_report


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run StreamDQ evaluation benchmark")
    parser.add_argument(
        "--parquet-path",
        type=str,
        default="data/nyc-taxi/yellow_tripdata_2023-01.parquet",
        help="Path to NYC TLC parquet file",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.05,
        help="Fraction of events to inject anomalies into (default: 0.05)",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=100_000,
        help="Maximum events to process (default: 100,000)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_results.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10_000,
        help="Number of warmup events before measurement (default: 10,000)",
    )
    parser.add_argument(
        "--label-delay-events",
        type=int,
        default=0,
        help="NG-33: Number of events to delay before ground-truth labels are available."
             " Simulates real-world label delay (default: 0, meaning instant labels).",
    )

    args = parser.parse_args()

    # Check if parquet exists
    parquet_path = Path(args.parquet_path)
    if not parquet_path.exists():
        print(f"ERROR: Parquet file not found: {args.parquet_path}")
        print("Run: python scripts/download_nyc_taxi.py --month 2023-01")
        sys.exit(1)

    run_evaluation(
        parquet_path=str(parquet_path),
        anomaly_rate=args.anomaly_rate,
        max_events=args.max_events,
        random_seed=args.random_seed,
        output_path=args.output,
        warmup_events=args.warmup,
        label_delay_events=args.label_delay_events,
    )
