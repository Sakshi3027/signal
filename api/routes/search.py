from fastapi import APIRouter
from loguru import logger
from api.models import SearchRequest, SearchResult
from storage.vector_store import search_reports

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=list[SearchResult])
def semantic_search(request: SearchRequest):
    """
    Semantic search over intelligence reports using vector similarity.
    Optionally filter by domain.
    """
    logger.info(f"Search: '{request.query}' (limit={request.limit}, domain={request.domain})")

    results = search_reports(
        query=request.query,
        limit=request.limit,
        domain=request.domain,
    )

    return [
        SearchResult(
            domain=r["domain"],
            title=r["title"],
            summary=r["summary"],
            key_themes=r.get("key_themes", []),
            sentiment=r["sentiment"],
            quality_score=r["quality_score"],
            generated_at=r["generated_at"],
            score=r["score"],
        )
        for r in results
    ]