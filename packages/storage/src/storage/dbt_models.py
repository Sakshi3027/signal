import os
from pathlib import Path
from loguru import logger

DBT_PROJECT_ROOT = Path("dbt")


def create_dbt_project():
    """Create dbt project structure for DuckDB analytics."""

    # Create directories
    dirs = [
        DBT_PROJECT_ROOT / "models" / "marts",
        DBT_PROJECT_ROOT / "models" / "staging",
        DBT_PROJECT_ROOT / "seeds",
        DBT_PROJECT_ROOT / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # dbt_project.yml
    project_yml = DBT_PROJECT_ROOT / "dbt_project.yml"
    if not project_yml.exists():
        project_yml.write_text("""name: signal
version: '1.0.0'
config-version: 2

profile: signal

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]

models:
  signal:
    staging:
      +materialized: view
    marts:
      +materialized: table
""")

    # profiles.yml
    profiles_yml = DBT_PROJECT_ROOT / "profiles.yml"
    if not profiles_yml.exists():
        duckdb_path = os.path.abspath("data/duckdb/signal.db")
        profiles_yml.write_text(f"""signal:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '{duckdb_path}'
      threads: 4
""")

    # Staging model — clean raw signals
    staging_model = DBT_PROJECT_ROOT / "models" / "staging" / "stg_signals.sql"
    if not staging_model.exists():
        staging_model.write_text("""{{ config(materialized='view') }}

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
""")

    # Mart 1 — signal trends by domain and day
    trends_model = DBT_PROJECT_ROOT / "models" / "marts" / "signal_trends.sql"
    if not trends_model.exists():
        trends_model.write_text("""{{ config(materialized='table') }}

select
    domain,
    signal_type,
    date_trunc('day', published_at)  as signal_date,
    count(*)                         as signal_count,
    count(distinct source_name)      as source_count,
    avg(title_length)                as avg_title_length
from {{ ref('stg_signals') }}
group by 1, 2, 3
order by signal_date desc, signal_count desc
""")

    # Mart 2 — source reliability scores
    source_model = DBT_PROJECT_ROOT / "models" / "marts" / "source_reliability.sql"
    if not source_model.exists():
        source_model.write_text("""{{ config(materialized='table') }}

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
from {{ ref('stg_signals') }}
group by 1, 2, 3
order by reliability_score desc
""")

    # Mart 3 — domain summary
    domain_model = DBT_PROJECT_ROOT / "models" / "marts" / "domain_summary.sql"
    if not domain_model.exists():
        domain_model.write_text("""{{ config(materialized='table') }}

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
""")

    # Schema with tests
    schema_yml = DBT_PROJECT_ROOT / "models" / "staging" / "schema.yml"
    if not schema_yml.exists():
        schema_yml.write_text("""version: 2

models:
  - name: stg_signals
    description: "Cleaned and enriched signals from all ingestion sources"
    columns:
      - name: url
        description: "Unique URL of the signal"
        tests:
          - not_null
          - unique
      - name: domain
        description: "Signal domain: ai_ml or fintech"
        tests:
          - not_null
          - accepted_values:
              values: ['ai_ml', 'fintech']
      - name: signal_type
        description: "Type of signal: news, repository, or research"
        tests:
          - not_null
          - accepted_values:
              values: ['news', 'repository', 'research']
      - name: title
        tests:
          - not_null
""")

    logger.info("dbt project structure created at ./dbt/")