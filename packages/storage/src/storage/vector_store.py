import os
from loguru import logger
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
from sentence_transformers import SentenceTransformer

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "signal_reports")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384

# Lazy-loaded singletons
_client = None
_embedder = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
        logger.info(f"Connected to Qdrant at {QDRANT_URL}")
    return _client


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def init_collection():
    """Create Qdrant collection if it doesn't exist."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
    else:
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists")


def embed_and_store(report: dict, postgres_id: int, run_id: str):
    """
    Embed a report and store it in Qdrant with metadata payload.
    Uses the report title + summary + themes as the embedding text.
    """
    client = get_client()
    embedder = get_embedder()

    # Build rich text for embedding
    themes_text = " | ".join(report.get("key_themes", []))
    signals_text = " | ".join(report.get("notable_signals", []))
    embed_text = f"{report['title']}. {report['summary']} Themes: {themes_text}. Signals: {signals_text}"

    vector = embedder.encode(embed_text).tolist()

    point = PointStruct(
        id=postgres_id,
        vector=vector,
        payload={
            "run_id": run_id,
            "domain": report["domain"],
            "title": report["title"],
            "summary": report["summary"],
            "key_themes": report.get("key_themes", []),
            "notable_signals": report.get("notable_signals", []),
            "sentiment": report["sentiment"],
            "quality_score": report["quality_score"],
            "generated_at": report["generated_at"],
        },
    )

    client.upsert(collection_name=COLLECTION_NAME, points=[point])
    logger.info(f"Stored embedding for report [{report['domain']}] (id={postgres_id})")


def search_reports(query: str, limit: int = 5, domain: str = None) -> list[dict]:
    """
    Semantic search over stored reports.
    Optionally filter by domain.
    """
    client = get_client()
    embedder = get_embedder()

    query_vector = embedder.encode(query).tolist()

    query_filter = None
    if domain:
        query_filter = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        query_filter=query_filter,
        with_payload=True,
    ).points

    return [
        {**hit.payload, "score": hit.score}
        for hit in results
    ]