"""
StreamDQ Weekly Precision/Recall Evaluation DAG.

Runs the evaluation framework on the week's data to compute:
- Precision and recall by rule
- Anomaly detection rates by type
- Comparison vs. previous week
- Alert if precision/recall drops below thresholds

Schedule: Every Monday at 07:00 UTC
"""
from __future__ import annotations

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "streamdq",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
}

with DAG(
    dag_id="streamdq_weekly_evaluation",
    default_args=default_args,
    description="Weekly StreamDQ precision/recall evaluation",
    schedule_interval="0 7 * * 1",  # Every Monday 07:00 UTC
    start_date=datetime(2026, 1, 6),
    catchup=False,
    tags=["streamdq", "data-quality", "evaluation"],
) as dag:

    # Wait for last day's daily report to complete
    wait_for_daily = ExternalTaskSensor(
        task_id="wait_for_last_daily_report",
        external_dag_id="streamdq_daily_quality_report",
        external_task_id=None,  # Wait for any task in daily DAG
        execution_delta=timedelta(hours=1),
        timeout=timedelta(hours=12),
    )

    with TaskGroup("compute_metrics") as compute_group:
        run_weekly_precision_recall = PythonOperator(
            task_id="compute_precision_recall",
            python_callable=_compute_precision_recall,
            provide_context=True,
        )

        compare_to_previous_week = PythonOperator(
            task_id="compare_to_previous_week",
            python_callable=_compare_to_previous_week,
            provide_context=True,
        )

        identify_degraded_rules = PythonOperator(
            task_id="identify_degraded_rules",
            python_callable=_identify_degraded_rules,
            provide_context=True,
        )

    with TaskGroup("evaluation_output") as output_group:
        store_weekly_report = PythonOperator(
            task_id="store_weekly_report",
            python_callable=_store_weekly_report,
            provide_context=True,
        )

        generate_trend_chart = PythonOperator(
            task_id="generate_trend_chart",
            python_callable=_generate_trend_chart,
            provide_context=True,
        )

    with TaskGroup("alerts") as alert_group:
        check_precision_threshold = PythonOperator(
            task_id="check_precision_threshold",
            python_callable=_check_precision_threshold,
            provide_context=True,
        )

        check_recall_threshold = PythonOperator(
            task_id="check_recall_threshold",
            python_callable=_check_recall_threshold,
            provide_context=True,
        )

    # DAG dependencies
    wait_for_daily >> compute_group >> output_group >> alert_group


def _compute_precision_recall(**context):
    """
    Run evaluation on the week's violation data.

    Uses ground truth from injected anomalies to compute:
    - TP: violations that match injected anomalies
    - FP: violations that don't match any injected anomaly
    - FN: injected anomalies that weren't detected

    Returns: {"precision": 0.85, "recall": 0.82, "f1": 0.83, "by_rule": {...}}
    """
    from datetime import datetime
    import json

    execution_date = context["execution_date"]
    week_start = execution_date - timedelta(days=7)
    week_end = execution_date

    print(f"Computing precision/recall for period {week_start} to {week_end}")

    # In production: query evaluation framework with week's data
    result = {
        "period_start": week_start.isoformat(),
        "period_end": week_end.isoformat(),
        "precision": 0.85,
        "recall": 0.82,
        "f1": 0.83,
        "by_rule": {
            "SYN001": {"precision": 0.95, "recall": 1.0, "f1": 0.97},
            "SYN002": {"precision": 0.99, "recall": 1.0, "f1": 0.99},
            "SYN003": {"precision": 0.98, "recall": 1.0, "f1": 0.99},
            "SEM001": {"precision": 0.72, "recall": 0.75, "f1": 0.73},
            "SEM002": {"precision": 0.95, "recall": 1.0, "f1": 0.97},
            "SEM003": {"precision": 0.99, "recall": 1.0, "f1": 0.99},
            "CRS001": {"precision": 0.80, "recall": 0.78, "f1": 0.79},
            "CRS002": {"precision": 0.70, "recall": 0.72, "f1": 0.71},
            "CRS003": {"precision": 0.85, "recall": 0.82, "f1": 0.83},
        },
        "by_anomaly_type": {
            "fare_negative": {"recall": 1.0},
            "fare_outlier": {"recall": 0.72},
            "location_invalid": {"recall": 1.0},
            "timestamp_future": {"recall": 1.0},
            "duration_negative": {"recall": 1.0},
            "duration_outlier": {"recall": 1.0},
            "speed_outlier": {"recall": 1.0},
            "duplicate": {"recall": 0.82},
        },
        "total_events": 700_000,
        "total_violations": 52_500,
        "anomaly_rate": 0.05,
    }

    print(f"Weekly evaluation: {json.dumps(result, indent=2)}")
    return result


def _compare_to_previous_week(**context):
    """Compare this week's precision/recall to the previous week."""
    ti = context["ti"]
    current = ti.xcom_pull(task_ids="compute_metrics.compute_precision_recall")

    # In production: query previous week's results from metrics store
    previous_week = {
        "precision": 0.83,
        "recall": 0.80,
        "f1": 0.81,
    }

    delta_precision = current["precision"] - previous_week["precision"]
    delta_recall = current["recall"] - previous_week["recall"]

    comparison = {
        "precision_delta": delta_precision,
        "recall_delta": delta_recall,
        "direction": "improving" if delta_precision > 0 and delta_recall > 0 else "degraded",
    }

    print(f"Week-over-week comparison: {comparison}")
    return comparison


def _identify_degraded_rules(**context):
    """Identify rules with degraded performance vs. baseline."""
    ti = context["ti"]
    current = ti.xcom_pull(task_ids="compute_metrics.compute_precision_recall")

    baseline = {"precision": 0.85, "recall": 0.82}
    degraded_rules = []

    for rule_id, metrics in current["by_rule"].items():
        precision_drop = baseline["precision"] - metrics["precision"]
        recall_drop = baseline["recall"] - metrics["recall"]
        if precision_drop > 0.05 or recall_drop > 0.05:
            degraded_rules.append({
                "rule_id": rule_id,
                "precision_drop": precision_drop,
                "recall_drop": recall_drop,
                "current_precision": metrics["precision"],
                "current_recall": metrics["recall"],
            })

    print(f"Degraded rules: {degraded_rules}")
    return {"degraded_rules": degraded_rules}


def _store_weekly_report(**context):
    """Store weekly evaluation results to the metrics database."""
    ti = context["ti"]
    results = ti.xcom_pull(task_ids="compute_metrics.compute_precision_recall")
    print(f"Storing weekly report: {results}")
    # In production: INSERT into metrics_history table


def _generate_trend_chart(**context):
    """Generate 4-week precision/recall trend chart for Grafana."""
    print("Generating trend chart for Grafana dashboard...")
    # In production: push data to Grafana dashboard via API


def _check_precision_threshold(**context):
    """Alert if weekly precision drops below 0.80."""
    ti = context["ti"]
    results = ti.xcom_pull(task_ids="compute_metrics.compute_precision_recall")

    if results["precision"] < 0.80:
        print(f"ALERT: Precision {results['precision']:.1%} below 80% threshold")
    return {"status": "OK" if results["precision"] >= 0.80 else "ALERT"}


def _check_recall_threshold(**context):
    """Alert if weekly recall drops below 0.75."""
    ti = context["ti"]
    results = ti.xcom_pull(task_ids="compute_metrics.compute_precision_recall")

    if results["recall"] < 0.75:
        print(f"ALERT: Recall {results['recall']:.1%} below 75% threshold")
    return {"status": "OK" if results["recall"] >= 0.75 else "ALERT"}
