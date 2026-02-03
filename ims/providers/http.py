from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HttpClient:
    timeout_s: float
    retries: int
    user_agent: str

    def get_text(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> str:
        last_exc: Exception | None = None
        merged_headers = {"User-Agent": self.user_agent}
        if headers:
            merged_headers.update(headers)
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_s, headers=merged_headers, follow_redirects=True) as c:
                    r = c.get(url, params=params)
                    r.raise_for_status()
                    return r.text
            except Exception as e:  # noqa: BLE001
                last_exc = e
                sleep_s = min(2**attempt, 8)
                logger.warning("GET failed attempt=%s url=%s err=%s", attempt, url, e)
                time.sleep(sleep_s)
        raise RuntimeError(f"GET failed after {self.retries} retries: {url}") from last_exc

    def get_json(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> dict:
        text = self.get_text(url, params=params, headers=headers)
        try:
            return httpx.Response(200, text=text).json()
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Invalid JSON from {url}") from e

    def download(self, url: str, dst_path, *, headers: dict | None = None) -> None:
        last_exc: Exception | None = None
        merged_headers = {"User-Agent": self.user_agent}
        if headers:
            merged_headers.update(headers)
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_s, headers=merged_headers, follow_redirects=True) as c:
                    with c.stream("GET", url) as r:
                        r.raise_for_status()
                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(dst_path, "wb") as f:
                            for chunk in r.iter_bytes():
                                f.write(chunk)
                return
            except Exception as e:  # noqa: BLE001
                last_exc = e
                sleep_s = min(2**attempt, 8)
                logger.warning("DOWNLOAD failed attempt=%s url=%s err=%s", attempt, url, e)
                time.sleep(sleep_s)
        raise RuntimeError(f"DOWNLOAD failed after {self.retries} retries: {url}") from last_exc

