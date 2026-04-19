"""Run StreamDQ evaluation and store results in DuckDB violations table."""
import os, sys, time, random, json, traceback
from datetime import datetime, timedelta
import signal

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

# Timeout handler
def timeout_handler(signum, frame):
    print("TIMEOUT: Script exceeded time limit")
    raise TimeoutError("Script exceeded time limit")
if hasattr(signal, 'SIGALRM'):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600)  # 10 minute timeout

from streamdq.pipeline.local_pipeline import LocalPipeline, NoOpViolationStore
from streamdq.rules.cross_record import reset_cross_record_state
from streamdq.evaluation.metrics import EvaluationMetrics
import duckdb
import pandas as pd

random.seed(42)

ANOMALY_TYPES = [
    "fare_negative", "fare_outlier", "location_invalid", "timestamp_future",
    "duration_negative", "duration_outlier", "speed_outlier", "duplicate",
]

def to_serializable(obj):
    """Convert any object to JSON-serializable form. Handles nested structures."""
    if obj is None:
        return None
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, (int, float, str, bool)):
        if isinstance(obj, float) and obj != obj:  # NaN
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_serializable(x) for x in obj]
    return obj

def inject_anomaly(event, anomaly_type):
    """Inject anomaly and return (modified_event, anomaly_type)."""
    event = dict(event)
    if anomaly_type == "fare_negative":
        event["fare_amount"] = round(random.uniform(-100, -2.5), 2)
    elif anomaly_type == "fare_outlier":
        event["fare_amount"] = round(random.uniform(500, 2000), 2)
    elif anomaly_type == "location_invalid":
        event["PULocationID"] = random.randint(9000, 9999)
    elif anomaly_type == "timestamp_future":
        event["tpep_pickup_datetime"] = (datetime.now() + timedelta(days=10)).isoformat()
    elif anomaly_type == "duration_negative":
        pickup = str(event.get("tpep_pickup_datetime", ""))
        if pickup:
            try:
                dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                event["tpep_pickup_datetime"] = (dt + timedelta(hours=2)).isoformat()
                event["tpep_dropoff_datetime"] = (dt + timedelta(hours=1)).isoformat()
            except (ValueError, AttributeError):
                pass
    elif anomaly_type == "duration_outlier":
        pickup = str(event.get("tpep_pickup_datetime", ""))
        if pickup:
            try:
                dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                event["tpep_dropoff_datetime"] = (dt + timedelta(hours=25)).isoformat()
            except (ValueError, AttributeError):
                pass
    elif anomaly_type == "speed_outlier":
        event["trip_distance"] = 100.0
        pickup = str(event.get("tpep_pickup_datetime", ""))
        if pickup:
            try:
                dt = datetime.fromisoformat(pickup.replace("Z", "+00:00"))
                event["tpep_dropoff_datetime"] = (dt + timedelta(minutes=30)).isoformat()
            except (ValueError, AttributeError):
                pass
    elif anomaly_type == "duplicate":
        pass
    return event, anomaly_type

try:
    # ─── Load data from DuckDB ─────────────────────────────────────────────────
    print("Loading NYC TLC data from DuckDB...")
    conn = duckdb.connect(os.path.join(BASE, "data", "streamdq_violations.duckdb"), read_only=True)
    df = conn.execute("SELECT * FROM nyc_tlc LIMIT 100000").fetchdf()
    conn.close()
    print("Loaded %d records, %d columns" % (len(df), len(df.columns)))
    print("Columns: %s" % list(df.columns))

    # Convert DataFrame to list of JSON-safe dicts
    events = []
    for row in df.itertuples(index=False):
        row_dict = {}
        for col, val in zip(df.columns, row):
            row_dict[col] = to_serializable(val)
        events.append(row_dict)

    print("Converted to %d events" % len(events))

    # ─── Inject anomalies ──────────────────────────────────────────────────────
    print("Injecting anomalies...")
    anomaly_rate = 0.05
    num_anomalies = int(len(events) * anomaly_rate)
    anomaly_indices = random.sample(range(len(events)), num_anomalies)
    injected_anomalies = {}
    for idx in anomaly_indices:
        atype = random.choice(ANOMALY_TYPES)
        events[idx], _ = inject_anomaly(events[idx], atype)
        injected_anomalies[idx] = atype

    from collections import Counter
    type_counts = Counter(injected_anomalies.values())
    print("Anomaly distribution:")
    for atype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print("  %s: %d" % (atype, count))

    # ─── Run pipeline ───────────────────────────────────────────────────────────
    print("Running LocalPipeline...")
    reset_cross_record_state()
    pipeline = LocalPipeline(violation_store=NoOpViolationStore())
    eval_metrics = EvaluationMetrics()
    all_violations = []

    start_time = time.perf_counter()
    event_start = time.perf_counter()

    for i, event in enumerate(events):
        injected_type = injected_anomalies.get(i)

        if injected_type:
            eval_metrics.add_injected_anomaly(injected_type, i)

        violations = pipeline.process_event(event)
        for v in violations:
            all_violations.append(v)
            eval_metrics.add_detected_violation(
                rule_id=v.rule_id,
                entity_index=i,
                latency_ms=v.processing_latency_ms,
                anomaly_type=None if injected_type == "duplicate" else injected_type,
            )

        if injected_type == "duplicate":
            dup_violations = pipeline.process_event(dict(event))
            for v in dup_violations:
                all_violations.append(v)
                eval_metrics.add_detected_violation(
                    rule_id=v.rule_id,
                    entity_index=i,
                    latency_ms=v.processing_latency_ms,
                    anomaly_type="duplicate",
                )

        if (i + 1) % 20000 == 0:
            elapsed = time.perf_counter() - event_start
            rate = (i + 1) / elapsed
            print("  %d/%d (%.0f%%) - %.0f events/sec" % (i+1, len(events), 100*(i+1)/len(events), rate))

    total_time = time.perf_counter() - start_time
    print("Done in %.1fs - %.0f events/sec" % (total_time, len(events)/total_time))

    # ─── Report ─────────────────────────────────────────────────────────────────
    report = eval_metrics.full_report()
    print()
    print("=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    precision = report["precision"]
    recall = report["recall_overall"]
    f1 = 2 * precision * recall / max(precision + recall, 0.0001)
    print("Precision: %.1f%%" % (precision * 100))
    print("Recall:    %.1f%%" % (recall * 100))
    print("F1:        %.1f%%" % (f1 * 100))
    print()
    print("Detection by type:")
    for atype, d in sorted(report["detection_rate_by_type"].items(), key=lambda x: -x[1]["detection_rate"]):
        dr = d["detection_rate"]
        print("  %-20s: %5.1f%% (%d/%d)" % (atype, dr*100, d["detected"], d["total"]))
    print()
    lat = report["latency"]
    avg_lat = sum(eval_metrics.latencies_ms) / max(len(eval_metrics.latencies_ms), 1)
    print("Latency: avg=%.0fms  P50=%.0fms  P95=%.0fms  P99=%.0fms" % (
        avg_lat, lat["p50_ms"], lat["p95_ms"], lat["p99_ms"]))
    print()
    print("Rule coverage:")
    for rule_id, cnt in sorted(report["rule_coverage"]["by_rule"].items(), key=lambda x: -x[1]):
        total_v = report["rule_coverage"]["total_violations"]
        print("  %s: %d (%.1f%%)" % (rule_id, cnt, 100*cnt/total_v if total_v > 0 else 0))

    # ─── Save to DuckDB violations table ───────────────────────────────────────
    print()
    print("Saving %d violations to DuckDB..." % len(all_violations))
    viol_conn = duckdb.connect(os.path.join(BASE, "data", "streamdq_violations.duckdb"))
    viol_conn.execute("DELETE FROM violations")

    rows = []
    for i, v in enumerate(all_violations):
        snapshot = to_serializable(v.record_snapshot) if v.record_snapshot else {}
        detected_ts = None
        if v.detected_at:
            try:
                dt = datetime.fromisoformat(str(v.detected_at).replace("Z", "+00:00"))
                detected_ts = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            except (ValueError, AttributeError):
                detected_ts = None
        rows.append((
            i + 1,  # explicit sequential id
            v.rule_id,
            v.rule_name,
            str(v.entity_id),
            v.entity_type,
            v.severity,
            v.violation_type,
            json.dumps(to_serializable(v.details) if v.details else {}),
            json.dumps(to_serializable(v.expected) if v.expected else {}),
            json.dumps(snapshot),
            detected_ts,
            v.processing_latency_ms,
        ))

    if rows:
        converted_rows = []
        for row in rows:
            row_list = list(row)
            # detected_at is at index 10 (ISO string -> DuckDB TIMESTAMP)
            if row_list[10]:
                try:
                    dt = datetime.fromisoformat(str(row_list[10]).replace("Z", "+00:00"))
                    row_list[10] = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                except (ValueError, AttributeError):
                    row_list[10] = None
            converted_rows.append(tuple(row_list))

        viol_conn.executemany("""
            INSERT INTO violations (id, rule_id, rule_name, entity_id, entity_type, severity,
                 violation_type, details, expected, record_snapshot, detected_at, processing_latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, converted_rows)
        print("Saved %d violations" % len(rows))
    viol_conn.close()

    # ─── Save JSON results ──────────────────────────────────────────────────────
    results = {
        "evaluation_config": {
            "data_source": "duckdb:nyc_tlc",
            "anomaly_rate": anomaly_rate,
            "max_events": len(events),
            "random_seed": 42,
            "pipeline": "LocalPipeline",
        },
        "pipeline_metrics": {
            "total_events": len(events),
            "total_violations": len(all_violations),
            "violation_rate": round(len(all_violations) / len(events), 4),
            "throughput_events_per_sec": round(len(events) / total_time, 1),
            "elapsed_seconds": round(total_time, 1),
        },
        "quality_metrics": {
            "precision": round(precision, 4),
            "recall_overall": round(recall, 4),
            "f1_score": round(f1, 4),
            "detection_rate_by_type": report["detection_rate_by_type"],
            "latency": report["latency"],
            "rule_coverage": report["rule_coverage"],
        },
    }

    out_path = os.path.join(BASE, "evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("Results saved to %s" % out_path)
    print("SUCCESS")

except Exception as e:
    print("ERROR: %s" % e)
    traceback.print_exc()
    sys.exit(1)
