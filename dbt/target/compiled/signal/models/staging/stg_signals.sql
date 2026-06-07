

select
    source_name,
    domain,
    title,
    url,
    left(summary, 500)           as summary,
    published_at::timestamp       as published_at,
    raw_tags,
    ingested_at::timestamp        as ingested_at,
    -- Derived fields
    case
        when source_name like 'arxiv%'  then 'research'
        when source_name like 'github%' then 'repository'
        else 'news'
    end                           as signal_type,
    length(title)                 as title_length,
    length(left(summary, 500))    as summary_length
from raw.raw_signals
where title is not null
  and url  is not null
  and title != ''