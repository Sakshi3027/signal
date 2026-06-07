from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from loguru import logger
from api.dependencies import get_engine
from api.models import ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", response_model=list[ReportResponse])
def get_reports(
    limit: int = Query(default=20, le=100),
    domain: str = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """Get recent intelligence reports, optionally filtered by domain and quality score."""
    engine = get_engine()
    with engine.connect() as conn:
        query = """
            SELECT * FROM intelligence_reports
            WHERE quality_score >= :min_score
            {domain_filter}
            ORDER BY created_at DESC
            LIMIT :limit
        """.format(
            domain_filter="AND domain = :domain" if domain else ""
        )

        params = {"limit": limit, "min_score": min_score}
        if domain:
            params["domain"] = domain

        result = conn.execute(text(query), params)
        rows = [dict(row._mapping) for row in result.fetchall()]

    return [ReportResponse.from_db_row(row) for row in rows]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int):
    """Get a single report by ID."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM intelligence_reports WHERE id = :id"),
            {"id": report_id},
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return ReportResponse.from_db_row(dict(row._mapping))


@router.get("/domain/{domain}", response_model=list[ReportResponse])
def get_reports_by_domain(domain: str, limit: int = Query(default=10, le=50)):
    """Get reports for a specific domain."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT * FROM intelligence_reports
                WHERE domain = :domain
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"domain": domain, "limit": limit},
        )
        rows = [dict(row._mapping) for row in result.fetchall()]

    return [ReportResponse.from_db_row(row) for row in rows]