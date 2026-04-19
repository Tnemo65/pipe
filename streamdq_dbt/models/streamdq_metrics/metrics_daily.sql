{{
  config(
    materialized='incremental',
    schema='streamdq',
    unique_key='day_bucket',
    on_schema_change='sync_all_columns',
  )
}}

with daily_violations as (
    select
        date_trunc('day', detected_at) as day_bucket,
        -- Volume metrics
        count(*)                           as total_violations,
        count(distinct entity_id)          as entities_with_violations,
        count(distinct rule_id)           as rules_firing,
        -- Layer breakdown
        sum(case when violation_type = 'SYNTACTIC' then 1 else 0 end)   as syntactic_count,
        sum(case when violation_type = 'SEMANTIC' then 1 else 0 end)     as semantic_count,
        sum(case when violation_type = 'CROSS_RECORD' then 1 else 0 end) as cross_record_count,
        -- Severity breakdown
        sum(case when severity = 'CRITICAL' then 1 else 0 end)  as critical_count,
        sum(case when severity = 'HIGH' then 1 else 0 end)      as high_count,
        sum(case when severity = 'MEDIUM' then 1 else 0 end)     as medium_count,
        sum(case when severity = 'LOW' then 1 else 0 end)        as low_count,
        -- Top offenders
        mode() within group (order by rule_id)     as most_common_rule,
        mode() within group (order by entity_type)  as most_common_entity_type,
        -- Latency
        avg(processing_latency_ms)                            as avg_latency_ms,
        percentile_cont(0.50) within group (order by processing_latency_ms) as p50_latency_ms,
        percentile_cont(0.99) within group (order by processing_latency_ms) as p99_latency_ms,
        -- Anomaly rate estimation
        -- Assumes: if more than 5% of events produce violations, something is wrong
        case
            when count(*) > 0 then count(*) * 1.0 / nullif({{ var('estimated_daily_events', 100000) }}, 0)
            else 0
        end                                                    as estimated_violation_rate,
        current_timestamp()                                    as computed_at
    from {{ ref('stg_violations') }}
    {% if is_incremental() %}
    where day_bucket > (select max(day_bucket) from {{ this }})
    {% endif %}
    group by date_trunc('day', detected_at)
)

select * from daily_violations
order by day_bucket desc
