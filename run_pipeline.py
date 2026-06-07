"""
Signal full pipeline runner.
Ingestion → Agent → Storage → dbt
"""
import subprocess
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


def run_full_pipeline():
    logger.info("=" * 60)
    logger.info("SIGNAL PIPELINE STARTING")
    logger.info("=" * 60)

    # Step 1: Ingest
    logger.info("STEP 1: Running ingestion...")
    from ingestion.pipeline import run_ingestion
    ingestion_summary = run_ingestion(hours_lookback=72)
    logger.info(f"Ingestion complete: {ingestion_summary}")

    # Step 2: Run agent
    logger.info("STEP 2: Running agent...")
    from agent.runner import run_agent
    reports = run_agent(hours_lookback=72)
    logger.info(f"Agent complete: {len(reports)} reports generated")

    # Step 3: Store reports
    logger.info("STEP 3: Storing reports...")
    from storage.runner import init_storage, store_reports
    import uuid
    run_id = str(uuid.uuid4())[:8]
    init_storage()
    store_reports(reports, run_id=run_id)

    # Step 4: Run dbt
    logger.info("STEP 4: Running dbt models...")
    result = subprocess.run(
        ["uv", "run", "dbt", "run", "--project-dir", "dbt", "--profiles-dir", "dbt"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        logger.info("dbt models built successfully")
    else:
        logger.error(f"dbt failed: {result.stderr[-500:]}")

    # Step 5: Verify everything
    logger.info("STEP 5: Verifying storage...")
    from storage.db import get_recent_reports
    saved = get_recent_reports(limit=10)
    logger.info(f"PostgreSQL: {len(saved)} reports in DB")

    from storage.vector_store import search_reports
    results = search_reports("AI agents and LLM tools", limit=3)
    logger.info(f"Qdrant search test: {len(results)} results")
    for r in results:
        logger.info(f"  [{r['domain']}] {r['title']} (score={r['score']:.3f})")

    logger.info("=" * 60)
    logger.info(f"PIPELINE COMPLETE — run_id: {run_id}")
    logger.info(f"  Reports generated: {len(reports)}")
    logger.info(f"  Reports in PostgreSQL: {len(saved)}")
    logger.info(f"  Reports in Qdrant: {len(results)} searchable")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_full_pipeline()