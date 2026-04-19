{{
  config(
    materialized='table',
    schema='streamdq',
    unique_id='rule_id',
  )
}}

with violation_base as (
    select
        rule_id,
        rule_name,
        entity_type,
        violation_type,
        severity,
        detected_at,
        processing_latency_ms,
        json_extract(details, '$.reason')      as violation_reason,
        json_extract(details, '$.field')         as affected_field,
        json_extract(details, '$.value')        as affected_value,
        json_extract(record_snapshot, '$.trip_id') as trip_id
    from {{ source('streamdq', 'violations') }}
),

enriched as (
    select
        rule_id,
        rule_name,
        entity_type,
        violation_type,
        severity,
        detected_at,
        date_trunc('hour', detected_at)        as hour_bucket,
        date_trunc('day', detected_at)         as day_bucket,
        processing_latency_ms,
        violation_reason,
        affected_field,
        affected_value,
        trip_id
    from violation_base
)

select * from enriched
