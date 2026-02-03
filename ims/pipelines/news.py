from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone

from ims.providers.news import GoogleNewsRssProvider
from ims.services.sentiment import score_headline
from ims.storage.repos import Repos, stable_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsIngestStats:
    fetched: int
    persisted: int


def ingest_news(
    *,
    repos: Repos,
    run_id: str,
    symbol: str,
    company_name: str,
    provider: GoogleNewsRssProvider,
    lookback_days: int,
) -> NewsIngestStats:
    query = f"{symbol} {company_name} stock"
    items = provider.search(query, limit=50)
    persisted = 0
    by_day: dict[date, list[float]] = {}

    for it in items:
        try:
            ss = score_headline(it.title)
            hid = stable_id(symbol.upper(), it.url)
            repos.upsert_headline(
                headline_id=hid,
                symbol=symbol,
                published_at=it.published_at,
                source=it.source,
                title=it.title,
                url=it.url,
                mood_score=ss.score,
                confidence=ss.confidence,
            )
            persisted += 1

            if it.published_at:
                dt = _parse_iso(it.published_at)
                if dt:
                    day = dt.date()
                    by_day.setdefault(day, []).append(ss.score)
        except Exception as e:  # noqa: BLE001
            repos.add_run_log(run_id, "WARN", f"News ingest failed: {e}")

    for d, scores in by_day.items():
        repos.upsert_mood_daily(symbol, d, scores)

    return NewsIngestStats(fetched=len(items), persisted=persisted)


def _parse_iso(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:  # noqa: BLE001
        return None

