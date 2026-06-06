from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Domain(str, Enum):
    AI_ML = "ai_ml"
    FINTECH = "fintech"


@dataclass
class RawSignal:
    source_name: str
    domain: Domain
    title: str
    url: str
    summary: str
    published_at: datetime
    raw_tags: list[str]

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "domain": self.domain.value,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "published_at": self.published_at.isoformat(),
            "raw_tags": ",".join(self.raw_tags),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }