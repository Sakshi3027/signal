import os
from loguru import logger
from dotenv import load_dotenv
from .db import init_db, save_report
from .vector_store import init_collection, embed_and_store
from .dbt_models import create_dbt_project

load_dotenv()


def init_storage():
    """Initialize all storage systems."""
    logger.info("Initializing storage layer...")
    init_db()
    init_collection()
    create_dbt_project()
    logger.info("Storage layer ready.")


def store_reports(reports: list[dict], run_id: str):
    """
    Save a list of intelligence reports to PostgreSQL + Qdrant.
    Called after every agent run.
    """
    if not reports:
        logger.warning("No reports to store.")
        return

    logger.info(f"Storing {len(reports)} reports for run [{run_id}]")

    for report in reports:
        # Save to PostgreSQL first — get the ID
        pg_id = save_report(report, run_id)

        # Embed and store in Qdrant using the PostgreSQL ID
        embed_and_store(report, postgres_id=pg_id, run_id=run_id)

    logger.info(f"All {len(reports)} reports stored successfully.")


if __name__ == "__main__":
    init_storage()
    logger.info("Storage systems initialized and ready.")