import os
from datetime import datetime, timezone, timedelta

import dlt
import feedparser
from dotenv import load_dotenv
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .feeds import RSS_FEEDS
from .github_source import fetch_github_signals
from .arxiv_source import fetch_arxiv_signals
from .sources import Domain, RawSignal

load_dotenv()

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/duckdb/signal.db")


def _parse_date(entry: dict) -> datetime:
    for field in ("published_parsed", "updated_parsed"):
        val = entry.get(field)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _is_recent(published_at: datetime, hours: int = 48) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return published_at >= cutoff


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def _fetch_feed(url: str) -> feedparser.FeedParserDict:
    return feedparser.parse(url)


def _extract_tags(entry: dict) -> list[str]:
    tags = []
    for tag in entry.get("tags", []):
        term = tag.get("term", "")
        if term:
            tags.append(term.lower().strip())
    return tags[:10]


@dlt.resource(
    name="raw_signals",
    write_disposition="append",
    primary_key="url",
)
def all_signals_resource(hours_lookback: int = 72):
    """
    Combined dlt resource yielding signals from:
    - RSS feeds (news, blogs)
    - GitHub API (trending repos)
    - arXiv API (research papers)
    """
    total = 0

    # --- RSS ---
    logger.info("=== RSS feeds ===")
    for feed_url, source_name, domain in RSS_FEEDS:
        logger.info(f"Fetching {source_name} ({domain.value})")
        try:
            feed = _fetch_feed(feed_url)
            source_count = 0
            for entry in feed.get("entries", []):
                published_at = _parse_date(entry)
                if not _is_recent(published_at, hours=hours_lookback):
                    continue
                signal = RawSignal(
                    source_name=source_name,
                    domain=domain,
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", "").strip(),
                    summary=entry.get("summary", "")[:2000].strip(),
                    published_at=published_at,
                    raw_tags=_extract_tags(entry),
                )
                if not signal.title or not signal.url:
                    continue
                yield signal.to_dict()
                source_count += 1
            logger.info(f"  → {source_count} from {source_name}")
            total += source_count
        except Exception as e:
            logger.error(f"RSS failed {source_name}: {e}")

    # --- GitHub ---
    logger.info("=== GitHub API ===")
    github_signals = fetch_github_signals(hours_lookback=hours_lookback)
    for s in github_signals:
        yield s
    total += len(github_signals)

    # --- arXiv ---
    logger.info("=== arXiv API ===")
    arxiv_signals = fetch_arxiv_signals(hours_lookback=hours_lookback)
    for s in arxiv_signals:
        yield s
    total += len(arxiv_signals)

    logger.info(f"=== Total signals yielded: {total} ===")


@dlt.source(name="signal_all")
def signal_source(hours_lookback: int = 72):
    return all_signals_resource(hours_lookback=hours_lookback)


def run_ingestion(hours_lookback: int = 72) -> dict:
    pipeline = dlt.pipeline(
        pipeline_name="signal_ingestion",
        destination=dlt.destinations.duckdb(DUCKDB_PATH),
        dataset_name="raw",
        dev_mode=False,
    )

    logger.info(f"Running full ingestion → {DUCKDB_PATH}")
    load_info = pipeline.run(signal_source(hours_lookback=hours_lookback))
    logger.info(f"Load complete: {load_info}")

    with pipeline.sql_client() as client:
        with client.execute_query("""
            SELECT domain, source_name, COUNT(*) as count
            FROM raw_signals
            GROUP BY domain, source_name
            ORDER BY domain, count DESC
        """) as cursor:
            rows = cursor.fetchall()

    logger.info("=== DB breakdown ===")
    for row in rows:
        logger.info(f"  {row[0]} | {row[1]}: {row[2]}")

    return {f"{row[0]}::{row[1]}": row[2] for row in rows}


if __name__ == "__main__":
    run_ingestion()