import os
import duckdb
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/duckdb/signal.db")


def read_signals_for_domain(domain: str, hours_lookback: int = 72, limit: int = 30) -> list[dict]:
    """
    Read recent signals from DuckDB for a given domain.
    Returns list of signal dicts.
    """
    try:
        conn = duckdb.connect(DUCKDB_PATH, read_only=True)
        query = """
            SELECT 
                source_name,
                title,
                summary,
                url,
                published_at,
                raw_tags,
                domain
            FROM raw.raw_signals
            WHERE domain = ?
              AND published_at >= NOW() - INTERVAL (? || ' hours')
            ORDER BY published_at DESC
            LIMIT ?
        """
        result = conn.execute(query, [domain, str(hours_lookback), limit]).fetchall()
        columns = ["source_name", "title", "summary", "url", "published_at", "raw_tags", "domain"]
        signals = [dict(zip(columns, row)) for row in result]
        conn.close()
        logger.info(f"Read {len(signals)} signals for domain '{domain}'")
        return signals
    except Exception as e:
        logger.error(f"Failed to read signals for domain '{domain}': {e}")
        return []


def get_domain_stats(hours_lookback: int = 72) -> dict:
    """Get signal counts per domain for the Supervisor."""
    try:
        conn = duckdb.connect(DUCKDB_PATH, read_only=True)
        result = conn.execute("""
            SELECT domain, COUNT(*) as count
            FROM raw.raw_signals
            WHERE published_at >= NOW() - INTERVAL (? || ' hours')
            GROUP BY domain
            ORDER BY count DESC
        """, [str(hours_lookback)]).fetchall()
        conn.close()
        return {row[0]: row[1] for row in result}
    except Exception as e:
        logger.error(f"Failed to get domain stats: {e}")
        return {}