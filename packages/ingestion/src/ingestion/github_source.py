import os
from datetime import datetime, timezone, timedelta

import httpx
from dotenv import load_dotenv
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .sources import Domain, RawSignal

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Search queries mapped to domains
GITHUB_SEARCHES: list[tuple[str, str, Domain]] = [
    # AI/ML repos
    ("language:python topic:llm stars:>50", "github_llm_repos", Domain.AI_ML),
    ("language:python topic:langchain stars:>20", "github_langchain_repos", Domain.AI_ML),
    ("language:python topic:machine-learning pushed:>2026-01-01 stars:>100", "github_ml_repos", Domain.AI_ML),
    ("topic:langgraph stars:>10", "github_langgraph_repos", Domain.AI_ML),
    # Fintech repos
    ("language:python topic:fintech stars:>30", "github_fintech_repos", Domain.FINTECH),
    ("topic:algorithmic-trading language:python stars:>20", "github_trading_repos", Domain.FINTECH),
]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def _search_repos(query: str, per_page: int = 10) -> list[dict]:
    """Search GitHub repos with retry logic."""
    with httpx.Client(timeout=15) as client:
        response = client.get(
            f"{GITHUB_API}/search/repositories",
            headers=HEADERS,
            params={
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": per_page,
            },
        )
        response.raise_for_status()
        return response.json().get("items", [])


def _is_recent(updated_at: str, hours: int = 72) -> bool:
    """Check if repo was updated within the last N hours."""
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return dt >= cutoff
    except Exception:
        return False


def fetch_github_signals(hours_lookback: int = 72) -> list[dict]:
    """
    Fetch recently updated GitHub repos matching our domain queries.
    Returns list of dicts ready for dlt ingestion.
    """
    signals = []
    seen_urls = set()

    for query, source_name, domain in GITHUB_SEARCHES:
        logger.info(f"Searching GitHub: {source_name} ({domain.value})")
        try:
            repos = _search_repos(query)
            source_count = 0

            for repo in repos:
                updated_at = repo.get("updated_at", "")

                if not _is_recent(updated_at, hours=hours_lookback):
                    continue

                url = repo.get("html_url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Build a rich summary from repo metadata
                description = repo.get("description") or ""
                topics = repo.get("topics", [])
                stars = repo.get("stargazers_count", 0)
                language = repo.get("language") or "unknown"

                summary = (
                    f"{description} | "
                    f"Stars: {stars} | "
                    f"Language: {language} | "
                    f"Topics: {', '.join(topics[:8])}"
                ).strip(" |")

                signal = RawSignal(
                    source_name=source_name,
                    domain=domain,
                    title=repo.get("full_name", ""),
                    url=url,
                    summary=summary[:2000],
                    published_at=datetime.fromisoformat(
                        updated_at.replace("Z", "+00:00")
                    ),
                    raw_tags=topics[:10],
                )

                signals.append(signal.to_dict())
                source_count += 1

            logger.info(f"  → {source_count} repos from {source_name}")

        except Exception as e:
            logger.error(f"Failed GitHub search '{source_name}': {e}")
            continue

    logger.info(f"Total GitHub signals: {len(signals)}")
    return signals