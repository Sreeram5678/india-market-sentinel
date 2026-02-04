from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from ims.providers.http import HttpClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BseAnnouncement:
    announced_at: str | None
    title: str
    pdf_url: str


class BseAnnouncementsProvider:
    """
    Best-effort BSE corporate announcements fetcher.

    Default implementation uses BSE's JSON API endpoint configured via Settings.bse_ann_endpoint.
    If BSE changes the API, set `IMS_BSE_ANN_ENDPOINT` and/or adjust params in code.
    """

    def __init__(self, http: HttpClient, endpoint: str):
        self.http = http
        self.endpoint = endpoint

    @staticmethod
    def _fmt(d: date) -> str:
        return d.strftime("%Y%m%d")

    @staticmethod
    def _normalize_pdf_url(raw: str) -> str:
        pdf_url = (raw or "").strip()
        if not pdf_url:
            return ""
        if pdf_url.startswith("//"):
            return "https:" + pdf_url
        if pdf_url.startswith("http://") or pdf_url.startswith("https://"):
            return pdf_url
        if pdf_url.startswith("/"):
            return "https://www.bseindia.com" + pdf_url
        if pdf_url.lower().endswith(".pdf"):
            return f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_url}"
        return ""

    def list_announcements(self, *, scrip_code: str, from_date: date, to_date: date) -> list[BseAnnouncement]:
        params = {
            "strCat": "-1",
            "strPrevDate": self._fmt(from_date),
            "strScrip": str(scrip_code),
            "strSearch": "P",
            "strToDate": self._fmt(to_date),
            "strType": "C",
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/",
        }
        payload = self.http.get_json(self.endpoint, params=params, headers=headers)

        items = payload.get("Table") or payload.get("table") or payload.get("d") or payload
        if not isinstance(items, list):
            logger.warning("Unexpected BSE response shape: %s", type(items))
            return []

        out: list[BseAnnouncement] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            title = (row.get("NEWSSUB") or row.get("headline") or row.get("SUBJECT") or "").strip()
            pdf_url = self._normalize_pdf_url(
                row.get("ATTACHMENTNAME") or row.get("attachment") or row.get("pdf") or ""
            )

            dt = row.get("NEWS_DT") or row.get("date") or row.get("announced_at")
            announced_at: str | None = None
            if isinstance(dt, str) and dt.strip():
                announced_at = dt.strip()
            elif isinstance(dt, datetime):
                announced_at = dt.isoformat()

            if not title or not pdf_url:
                continue

            out.append(BseAnnouncement(announced_at=announced_at, title=title, pdf_url=pdf_url))
        return out
