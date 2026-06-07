from fastapi import APIRouter, Query
from loguru import logger
from api.dependencies import get_duckdb
from api.models import TrendPoint, SourceReliability, DomainStats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trends", response_model=list[TrendPoint])
def get_signal_trends(days: int = Query(default=7, le=30)):
    """Get signal volume trends from dbt mart."""
    conn = get_duckdb()
    try:
        rows = conn.execute("""
            SELECT
                domain,
                signal_type,
                signal_date,
                signal_count,
                source_count
            FROM main.signal_trends
            WHERE signal_date >= CURRENT_DATE - INTERVAL (? || ' days')
            ORDER BY signal_date DESC, signal_count DESC
        """, [str(days)]).fetchall()

        return [
            TrendPoint(
                domain=row[0],
                signal_type=row[1],
                signal_date=row[2],
                signal_count=row[3],
                source_count=row[4],
            )
            for row in rows
        ]
    finally:
        conn.close()


@router.get("/sources", response_model=list[SourceReliability])
def get_source_reliability():
    """Get source reliability scores from dbt mart."""
    conn = get_duckdb()
    try:
        rows = conn.execute("""
            SELECT
                source_name,
                domain,
                signal_type,
                total_signals,
                reliability_score,
                last_seen
            FROM main.source_reliability
            ORDER BY reliability_score DESC
        """).fetchall()

        return [
            SourceReliability(
                source_name=row[0],
                domain=row[1],
                signal_type=row[2],
                total_signals=row[3],
                reliability_score=float(row[4]),
                last_seen=row[5],
            )
            for row in rows
        ]
    finally:
        conn.close()


@router.get("/domains", response_model=list[DomainStats])
def get_domain_stats():
    """Get per-domain signal summary from dbt mart."""
    conn = get_duckdb()
    try:
        rows = conn.execute("""
            SELECT
                domain,
                total_signals,
                total_sources,
                latest_signal,
                earliest_signal
            FROM main.domain_summary
        """).fetchall()

        return [
            DomainStats(
                domain=row[0],
                total_signals=row[1],
                total_sources=row[2],
                latest_signal=row[3],
                earliest_signal=row[4],
            )
            for row in rows
        ]
    finally:
        conn.close()