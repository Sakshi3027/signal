
  
    
    

    create  table
      "signal"."main"."source_reliability__dbt_tmp"
  
    as (
      

select
    source_name,
    domain,
    signal_type,
    count(*)                              as total_signals,
    avg(title_length)                     as avg_title_length,
    avg(summary_length)                   as avg_summary_length,
    min(published_at)                     as first_seen,
    max(published_at)                     as last_seen,
    count(distinct date_trunc('day', published_at)) as active_days,
    -- Reliability score: sources with longer summaries
    -- and more active days score higher
    round(
        least(1.0,
            (avg(summary_length) / 500.0) * 0.5 +
            (least(active_days, 7) / 7.0) * 0.5
        )::numeric, 3
    )                                     as reliability_score
from "signal"."main"."stg_signals"
group by 1, 2, 3
order by reliability_score desc
    );
  
  