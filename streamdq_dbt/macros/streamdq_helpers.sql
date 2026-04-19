{# Macro: Grant usage to reporting role #}
{% macro grant_usage(schema) %}
  {% if target.type == 'postgres' %}
    grant usage on schema {{ schema }} to reporting_role;
    grant select on all tables in schema {{ schema }} to reporting_role;
  {% endif %}
{% endmacro %}

{# Macro: Get date range for incremental models #}
{% macro get_violation_date_range(start_date='2024-01-01', end_date='today') %}
    date_trunc('day', detected_at)
    between '{{ start_date }}' and '{{ end_date }}'
{% endmacro %}

{# Macro: Violation rate alert threshold #}
{% macro violation_rate_threshold() %}
    {# Returns violation rate above which an alert should fire #}
    {{ return(0.05) }}  {# 5% violation rate threshold #}
{% endmacro %}

{# Macro: Severity severity ordering #}
{% macro severity_order(severity) %}
    case {{ severity }}
        when 'CRITICAL' then 1
        when 'HIGH'     then 2
        when 'MEDIUM'   then 3
        when 'LOW'      then 4
        else 5
    end
{% endmacro %}
