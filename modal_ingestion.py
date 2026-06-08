"""
Signal ingestion pipeline — runs on Modal every 6 hours.
Fetches RSS, GitHub, arXiv signals and stores in DuckDB on Modal Volume.
"""
import modal

app = modal.App("signal-ingestion")

# Persistent volume for DuckDB file
volume = modal.Volume.from_name("signal-duckdb", create_if_missing=True)
VOLUME_PATH = "/data"
DUCKDB_PATH = f"{VOLUME_PATH}/signal.db"

# Container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "dlt[duckdb]>=1.9",
        "duckdb>=1.2",
        "feedparser>=6.0",
        "httpx>=0.27",
        "tenacity>=8.0",
        "loguru>=0.7",
        "pydantic>=2.0",
        "python-dotenv>=1.0",
    )
    .add_local_dir("packages/ingestion/src", remote_path="/app/src")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("signal-secrets")],
    volumes={VOLUME_PATH: volume},
    timeout=600,
    schedule=modal.Cron("0 */6 * * *"),  # every 6 hours
)
def run_ingestion():
    """Fetch signals from all sources and store in DuckDB on Modal Volume."""
    import sys
    import os

    sys.path.insert(0, "/app/src")
    os.environ["DUCKDB_PATH"] = DUCKDB_PATH

    from loguru import logger
    import dlt
    from ingestion.feeds import RSS_FEEDS
    from ingestion.github_source import fetch_github_signals
    from ingestion.arxiv_source import fetch_arxiv_signals
    from ingestion.pipeline import signal_source

    logger.info(f"Modal ingestion run starting → {DUCKDB_PATH}")

    pipeline = dlt.pipeline(
        pipeline_name="signal_ingestion",
        destination=dlt.destinations.duckdb(DUCKDB_PATH),
        dataset_name="raw",
        dev_mode=False,
    )

    load_info = pipeline.run(signal_source(hours_lookback=72))
    logger.info(f"Load complete: {load_info}")

    # Commit volume changes
    volume.commit()

    # Quick summary
    import duckdb
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    rows = conn.execute("""
        SELECT domain, COUNT(*) as count
        FROM raw.raw_signals
        GROUP BY domain
    """).fetchall()
    conn.close()

    summary = {row[0]: row[1] for row in rows}
    logger.info(f"DB summary: {summary}")
    return summary


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("signal-secrets")],
    volumes={VOLUME_PATH: volume},
    timeout=60,
)
def get_signal_count():
    """Quick health check — returns signal counts from Modal Volume DuckDB."""
    import duckdb
    try:
        conn = duckdb.connect(DUCKDB_PATH, read_only=True)
        rows = conn.execute("""
            SELECT domain, COUNT(*) as count
            FROM raw.raw_signals
            GROUP BY domain
        """).fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
    except Exception as e:
        return {"error": str(e)}


@app.local_entrypoint()
def main():
    """Run ingestion once manually — for testing."""
    result = run_ingestion.remote()
    print(f"Ingestion complete: {result}")