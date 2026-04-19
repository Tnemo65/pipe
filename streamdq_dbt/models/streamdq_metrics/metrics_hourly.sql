{{
  config(
    materialized='incremental',
    schema='streamdq',
    unique_key='rule_id || hour_bucket',
    on_schema_change='sync_all_columns',
  )
}}

with violation_base as (
    select * from {{ ref('stg_violations') }}
),

hourly_metrics as (
    select
        rule_id,
        rule_name,
        violation_type,
        severity,
        hour_bucket,
        count(*)                                          as violation_count,
        count(distinct entity_id)                          as distinct_entities,
        count(distinct trip_id)                           as distinct_trips,
        avg(processing_latency_ms)                        as avg_latency_ms,
        percentile_cont(0.50) within group (order by processing_latency_ms) as p50_latency_ms,
        percentile_cont(0.99) within group (order by processing_latency_ms) as p99_latency_ms,
        min(processing_latency_ms)                        as min_latency_ms,
        max(processing_latency_ms)                        as max_latency_ms,
        -- Top violation reason
        mode() within group (order by violation_reason)    as top_violation_reason,
        -- Fields affected
        list_distinct(affected_field)                    as affected_fields
    from violation_base
    {% if is_incremental() %}
    where hour_bucket > (select max(hour_bucket) from {{ this }})
    {% endif %}
    group by rule_id, rule_name, violation_type, severity, hour_bucket
),

daily_rollup as (
    select
        date_trunc('day', hour_bucket) as day_bucket,
        count(*)                       as total_violations,
        count(distinct rule_id)        as rules_firing,
        count(distinct entity_id)      as entities_with_violations,
        avg(avg_latency_ms)            as avg_processing_latency_ms
    from hourly_metrics
    group by day_bucket
)

select
    h.*,
    d.total_violations      as daily_total_violations,
    d.rules_firing          as daily_rules_firing,
    d.entities_with_violations as daily_entities_with_violations,
    d.avg_processing_latency_ms as daily_avg_latency_ms,
    current_timestamp()      as computed_at
from hourly_metrics h
left join daily_rollup d on h.day_bucket = d.day_bucket
