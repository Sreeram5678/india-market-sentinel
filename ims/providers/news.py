from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser

from ims.core.settings import Settings
from ims.providers.http import HttpClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsItem:
    published_at: str | None
    source: str
    title: str
    url: str


class GoogleNewsRssProvider:
    def __init__(self, http: HttpClient, settings: Settings):
        self.http = http
        self.settings = settings

    def _rss_url(self, query: str) -> str:
        q = urllib.parse.quote(query)
        return (
            f"https://news.google.com/rss/search?q={q}"
            f"&hl={urllib.parse.quote(self.settings.google_news_hl)}"
            f"&gl={urllib.parse.quote(self.settings.google_news_gl)}"
            f"&ceid={urllib.parse.quote(self.settings.google_news_ceid)}"
        )

    def search(self, query: str, *, limit: int = 30) -> list[NewsItem]:
        url = self._rss_url(query)
        xml = self.http.get_text(url)
        feed = feedparser.parse(xml)
        out: list[NewsItem] = []
        for e in (feed.entries or [])[:limit]:
            title = (getattr(e, "title", "") or "").strip()
            link = (getattr(e, "link", "") or "").strip()
            if not title or not link:
                continue
            source = "Google News"
            if getattr(e, "source", None) and getattr(e.source, "title", None):
                source = str(e.source.title)
            published_at = None
            if getattr(e, "published_parsed", None):
                dt = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                published_at = dt.isoformat()
            out.append(NewsItem(published_at=published_at, source=source, title=title, url=link))
        return out

