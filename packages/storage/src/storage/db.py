import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, String, Float, Text,
    DateTime, Integer, MetaData, Table, inspect
)
from sqlalchemy.dialects.postgresql import insert
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://signal:signal123@localhost:5432/signal")

engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
metadata = MetaData()

reports_table = Table(
    "intelligence_reports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String(50), nullable=False),
    Column("domain", String(50), nullable=False),
    Column("title", String(500), nullable=False),
    Column("summary", Text, nullable=False),
    Column("key_themes", Text, nullable=False),       # comma-separated
    Column("notable_signals", Text, nullable=False),  # comma-separated
    Column("sentiment", String(20), nullable=False),
    Column("quality_score", Float, nullable=False),
    Column("quality_feedback", Text, nullable=True),
    Column("generated_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), default=datetime.now(timezone.utc)),
)


def init_db():
    """Create tables if they don't exist."""
    inspector = inspect(engine)
    if not inspector.has_table("intelligence_reports"):
        metadata.create_all(engine)
        logger.info("Created intelligence_reports table")
    else:
        logger.info("intelligence_reports table already exists")


def save_report(report: dict, run_id: str) -> int:
    """
    Insert or update a report in PostgreSQL.
    Returns the inserted row id.
    """
    with engine.begin() as conn:
        stmt = insert(reports_table).values(
            run_id=run_id,
            domain=report["domain"],
            title=report["title"],
            summary=report["summary"],
            key_themes=", ".join(report.get("key_themes", [])),
            notable_signals=", ".join(report.get("notable_signals", [])),
            sentiment=report["sentiment"],
            quality_score=report["quality_score"],
            quality_feedback=report.get("quality_feedback", ""),
            generated_at=datetime.fromisoformat(report["generated_at"]),
            created_at=datetime.now(timezone.utc),
        )
        result = conn.execute(stmt)
        row_id = result.inserted_primary_key[0]
        logger.info(f"Saved report [{report['domain']}] to PostgreSQL (id={row_id})")
        return row_id


def get_recent_reports(limit: int = 20) -> list[dict]:
    """Fetch recent reports from PostgreSQL."""
    with engine.connect() as conn:
        result = conn.execute(
            reports_table.select()
            .order_by(reports_table.c.created_at.desc())
            .limit(limit)
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]