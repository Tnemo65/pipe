"""
StreamDQ Daily Quality Report DAG.

Generates a daily data quality report including:
- Violation counts by rule, type, and severity
- Latency statistics (P50, P99)
- Trend analysis vs. previous day
- Top violation reasons and affected entities

Schedule: Daily at 06:00 UTC
"""
from __future__ import annotations

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "streamdq",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="streamdq_daily_quality_report",
    default_args=default_args,
    description="Daily StreamDQ data quality report",
    schedule_interval="0 6 * * *",  # Daily at 06:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["streamdq", "data-quality", "reporting"],
) as dag:

    with TaskGroup("extract_and_transform") as et_group:
        # Refresh dbt models for violation analysis
        run_stg_violations = PostgresOperator(
            task_id="refresh_stg_violations",
            postgres_conn_id="streamdq_postgres",
            sql="""
                REFRESH MATERIALIZED VIEW CONCURRENTLY streamdq.stg_violations;
            """,
        )

        run_hourly_metrics = PostgresOperator(
            task_id="refresh_hourly_metrics",
            postgres_conn_id="streamdq_postgres",
            sql="""
                REFRESH MATERIALIZED VIEW CONCURRENTLY streamdq.metrics_hourly;
            """,
        )

        run_daily_metrics = PostgresOperator(
            task_id="refresh_daily_metrics",
            postgres_conn_id="streamdq_postgres",
            sql="""
                REFRESH MATERIALIZED VIEW CONCURRENTLY streamdq.metrics_daily;
            """,
        )

        [run_stg_violations, run_hourly_metrics, run_daily_metrics]

    with TaskGroup("reporting") as report_group:
        generate_daily_summary = PythonOperator(
            task_id="generate_daily_summary",
            python_callable=_generate_daily_summary,
            provide_context=True,
        )

        check_violation_rate = PythonOperator(
            task_id="check_violation_rate",
            python_callable=_check_violation_rate,
            provide_context=True,
        )

        generate_rule_firing_report = PythonOperator(
            task_id="generate_rule_firing_report",
            python_callable=_generate_rule_firing_report,
            provide_context=True,
        )

        [generate_daily_summary, check_violation_rate, generate_rule_firing_report]

    with TaskGroup("notifications") as notify_group:
        send_slack_alert = PythonOperator(
            task_id="send_slack_alert",
            python_callable=_send_slack_notification,
            trigger_rule="one_success",
            provide_context=True,
        )

        send_email_report = PythonOperator(
            task_id="send_email_report",
            python_callable=_send_email_report,
            trigger_rule="one_failed",
            provide_context=True,
        )

    # DAG dependencies
    et_group >> report_group >> notify_group


# ─────────────────────────────────────────────────────────────────────────────
# Python Callables (implement these with your reporting stack)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_daily_summary(**context):
    """Generate daily violation summary and push to metrics store."""
    from datetime import datetime
    import json

    execution_date = context["execution_date"]
    dag_run_id = context["dag_run"].run_id

    # Query violation summary for the last 24 hours
    # This would connect to the PostgreSQL violation store
    summary = {
        "dag_run_id": dag_run_id,
        "execution_date": execution_date.isoformat(),
        "total_violations": 0,  # Populated from DB query
        "by_rule": {},
        "by_severity": {},
        "by_type": {},
        "p50_latency_ms": 0,
        "p99_latency_ms": 0,
    }

    print(f"Daily summary: {json.dumps(summary, indent=2)}")
    # In production: query violation store and push to metrics/BI
    return summary


def _check_violation_rate(**context):
    """
    Check if today's violation rate exceeds threshold.
    Alert if >5% of events produced violations.
    """
    threshold = 0.05  # 5% threshold

    # In production: query metrics_daily for today's violation rate
    violation_rate = 0.03  # Placeholder

    if violation_rate > threshold:
        alert_msg = (
            f"[StreamDQ ALERT] Violation rate {violation_rate:.1%} "
            f"exceeds threshold {threshold:.1%}. "
            f"Review rule configurations."
        )
        print(f"ALERT: {alert_msg}")
        # In production: send to Slack/PagerDuty
        return {"status": "ALERT", "rate": violation_rate, "threshold": threshold}
    return {"status": "OK", "rate": violation_rate, "threshold": threshold}


def _generate_rule_firing_report(**context):
    """Generate report of which rules fired most frequently."""
    # In production: query metrics_hourly for rule firing patterns
    report = {
        "top_rules": [
            {"rule_id": "SYN001", "count": 150, "trend": "up"},
            {"rule_id": "SEM001", "count": 89, "trend": "stable"},
            {"rule_id": "CRS001", "count": 12, "trend": "down"},
        ],
        "rules_not_firing": ["CRS003"],  # Indicates possible issue
    }
    print(f"Rule firing report: {report}")
    return report


def _send_slack_notification(**context):
    """Send daily summary to Slack."""
    # In production: use SlackWebhookOperator or Slack API
    ti = context["ti"]
    summary = ti.xcom_pull(task_ids="reporting.generate_daily_summary")
    print(f"Slack notification: {summary}")


def _send_email_report(**context):
    """Send email report on failure."""
    # In production: use EmailOperator
    print("Sending failure notification email...")
