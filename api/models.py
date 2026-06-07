from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReportResponse(BaseModel):
    id: int
    run_id: str
    domain: str
    title: str
    summary: str
    key_themes: list[str]
    notable_signals: list[str]
    sentiment: str
    quality_score: float
    quality_feedback: Optional[str]
    generated_at: datetime
    created_at: Optional[datetime]

    @classmethod
    def from_db_row(cls, row: dict) -> "ReportResponse":
        return cls(
            id=row["id"],
            run_id=row["run_id"],
            domain=row["domain"],
            title=row["title"],
            summary=row["summary"],
            key_themes=[t.strip() for t in row.get("key_themes", "").split(",") if t.strip()],
            notable_signals=[s.strip() for s in row.get("notable_signals", "").split(",") if s.strip()],
            sentiment=row["sentiment"],
            quality_score=row["quality_score"],
            quality_feedback=row.get("quality_feedback"),
            generated_at=row["generated_at"],
            created_at=row.get("created_at"),
        )


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    domain: Optional[str] = None


class SearchResult(BaseModel):
    domain: str
    title: str
    summary: str
    key_themes: list[str]
    sentiment: str
    quality_score: float
    generated_at: str
    score: float


class DomainStats(BaseModel):
    domain: str
    total_signals: int
    total_sources: int
    latest_signal: Optional[datetime]
    earliest_signal: Optional[datetime]


class TrendPoint(BaseModel):
    domain: str
    signal_type: str
    signal_date: datetime
    signal_count: int
    source_count: int


class SourceReliability(BaseModel):
    source_name: str
    domain: str
    signal_type: str
    total_signals: int
    reliability_score: float
    last_seen: Optional[datetime]


class PipelineRunResponse(BaseModel):
    run_id: str
    status: str
    reports_generated: int
    message: str


class HealthResponse(BaseModel):
    status: str
    postgres: bool
    qdrant: bool
    duckdb: bool
    total_signals: int
    total_reports: int