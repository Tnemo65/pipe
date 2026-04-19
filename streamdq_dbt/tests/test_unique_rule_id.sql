{{ config(tags=['unit-test']) }}

-- Test: rule_id is always unique
select
    rule_id,
    count(*) as occurrence_count
from {{ ref('stg_violations') }}
group by rule_id
having count(*) > 1
limit 1
