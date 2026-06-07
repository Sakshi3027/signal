import time
import httpx
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .sources import Domain, RawSignal

ARXIV_API = "https://export.arxiv.org/api/query"

# arXiv search queries mapped to domains
ARXIV_SEARCHES: list[tuple[str, str, Domain]] = [
    # AI/ML
    ("cat:cs.LG", "arxiv_machine_learning", Domain.AI_ML),
    ("cat:cs.AI", "arxiv_artificial_intelligence", Domain.AI_ML),
    ("cat:cs.CL", "arxiv_nlp", Domain.AI_ML),
    # Fintech
    ("cat:q-fin.CP OR cat:q-fin.TR", "arxiv_quantitative_finance", Domain.FINTECH),
    ("cat:q-fin.RM", "arxiv_risk_management", Domain.FINTECH),
]

ARXIV_NS = "{http://www.w3.org/2005/Atom}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
)
def _fetch_arxiv(query: str, max_results: int = 15) -> str:
    with httpx.Client(timeout=30) as client:
        response = client.get(
            ARXIV_API,
            params={
                "search_query": query,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": max_results,
            },
        )
        if response.status_code != 200:
            logger.error(f"arXiv returned {response.status_code}: {response.text[:200]}")
        response.raise_for_status()
        return response.text

def _parse_arxiv_date(date_str: str) -> datetime:
    """Parse arXiv date string to datetime."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _is_recent(published_at: datetime, hours: int = 72) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return published_at >= cutoff


def _parse_entries(xml_text: str) -> list[dict]:
    """Parse arXiv Atom XML into list of entry dicts."""
    root = ET.fromstring(xml_text)
    entries = []

    for entry in root.findall(f"{ARXIV_NS}entry"):
        try:
            title = entry.findtext(f"{ARXIV_NS}title", "").strip().replace("\n", " ")
            url = entry.findtext(f"{ARXIV_NS}id", "").strip()
            summary = entry.findtext(f"{ARXIV_NS}summary", "").strip().replace("\n", " ")
            published = entry.findtext(f"{ARXIV_NS}published", "")

            # Extract author names
            authors = [
                a.findtext(f"{ARXIV_NS}name", "")
                for a in entry.findall(f"{ARXIV_NS}author")
            ][:5]

            # Extract categories as tags
            tags = [
                c.get("term", "")
                for c in entry.findall(f"{ARXIV_NS}category")
                if c.get("term")
            ][:10]

            entries.append({
                "title": title,
                "url": url,
                "summary": summary[:2000],
                "published": published,
                "authors": authors,
                "tags": tags,
            })
        except Exception:
            continue

    return entries


def fetch_arxiv_signals(hours_lookback: int = 72) -> list[dict]:
    """
    Fetch recent arXiv papers for AI/ML and Fintech domains.
    Returns list of dicts ready for dlt ingestion.
    """
    signals = []
    seen_urls = set()

    for query, source_name, domain in ARXIV_SEARCHES:
        logger.info(f"Fetching arXiv: {source_name} ({domain.value})")
        try:
            xml_text = _fetch_arxiv(query)
            entries = _parse_entries(xml_text)
            source_count = 0

            for entry in entries:
                published_at = _parse_arxiv_date(entry["published"])

                if not _is_recent(published_at, hours=hours_lookback):
                    continue

                url = entry["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Enrich summary with author info
                author_str = ", ".join(entry["authors"])
                full_summary = f"{entry['summary']} | Authors: {author_str}"

                signal = RawSignal(
                    source_name=source_name,
                    domain=domain,
                    title=entry["title"],
                    url=url,
                    summary=full_summary[:2000],
                    published_at=published_at,
                    raw_tags=entry["tags"],
                )

                signals.append(signal.to_dict())
                source_count += 1

            logger.info(f"  → {source_count} papers from {source_name}")

            # Be polite to arXiv API — they ask for 3s between requests
            time.sleep(3)

        except Exception as e:
            logger.error(f"Failed arXiv fetch '{source_name}': {e}")
            continue

    logger.info(f"Total arXiv signals: {len(signals)}")
    return signals