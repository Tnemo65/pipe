{{ config(tags=['unit-test']) }}

-- Test: processing_latency_ms is never negative
select
    entity_id,
    processing_latency_ms
from {{ ref('stg_violations') }}
where processing_latency_ms < 0
limit 1
