
  
    
    

    create  table
      "signal"."main"."signal_trends__dbt_tmp"
  
    as (
      

select
    domain,
    signal_type,
    date_trunc('day', published_at)  as signal_date,
    count(*)                         as signal_count,
    count(distinct source_name)      as source_count,
    avg(title_length)                as avg_title_length
from "signal"."main"."stg_signals"
group by 1, 2, 3
order by signal_date desc, signal_count desc
    );
  
  