{{ config(materialized='table') }}

select
    domain,
    count(*)                              as total_signals,
    count(distinct source_name)           as total_sources,
    count(distinct signal_type)           as signal_type_count,
    min(published_at)                     as earliest_signal,
    max(published_at)                     as latest_signal,
    avg(summary_length)                   as avg_summary_length
from {{ ref('stg_signals') }}
group by 1
order by total_signals desc
