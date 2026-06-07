import os
import duckdb
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from loguru import logger
from functools import lru_cache

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://signal:signal123@localhost:5432/signal")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/duckdb/signal.db")


@lru_cache()
def get_engine():
    return create_engine(POSTGRES_URL, pool_pre_ping=True)


@lru_cache()
def get_qdrant():
    return QdrantClient(url=QDRANT_URL)


def get_duckdb():
    return duckdb.connect(DUCKDB_PATH, read_only=True)


def check_health() -> dict:
    health = {
        "postgres": False,
        "qdrant": False,
        "duckdb": False,
        "total_signals": 0,
        "total_reports": 0,
    }

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM intelligence_reports"))
            health["total_reports"] = result.scalar()
            health["postgres"] = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")

    try:
        client = get_qdrant()
        client.get_collections()
        health["qdrant"] = True
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")

    try:
        conn = get_duckdb()
        health["total_signals"] = conn.execute(
            "SELECT COUNT(*) FROM raw.raw_signals"
        ).fetchone()[0]
        conn.close()
        health["duckdb"] = True
    except Exception as e:
        logger.error(f"DuckDB health check failed: {e}")

    return health