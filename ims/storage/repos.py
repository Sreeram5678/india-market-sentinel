from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable


def new_id() -> str:
    return uuid.uuid4().hex


def stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()[:32]


@dataclass(frozen=True)
class RunRecord:
    id: str
    symbol: str
    status: str


class Repos:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # Companies / watchlist
    def upsert_company(
        self, symbol: str, name: str, exchange: str = "BSE", bse_scrip_code: str | None = None
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO companies(symbol, name, exchange, bse_scrip_code)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
              name=excluded.name,
              exchange=excluded.exchange,
              bse_scrip_code=COALESCE(excluded.bse_scrip_code, companies.bse_scrip_code)
            """,
            (symbol.upper(), name, exchange, bse_scrip_code),
        )

    def get_company(self, symbol: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT symbol, name, exchange, bse_scrip_code, isin FROM companies WHERE symbol=?",
            (symbol.upper(),),
        ).fetchone()
        return dict(row) if row else None

    def add_to_watchlist(self, symbol: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO watchlist(symbol) VALUES (?)", (symbol.upper(),))

    def remove_from_watchlist(self, symbol: str) -> None:
        self.conn.execute("DELETE FROM watchlist WHERE symbol=?", (symbol.upper(),))

    def list_watchlist(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT w.symbol, c.name, c.exchange, c.bse_scrip_code, w.added_at
            FROM watchlist w JOIN companies c ON c.symbol=w.symbol
            ORDER BY w.added_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    # Runs
    def create_run(self, symbol: str) -> RunRecord:
        run_id = new_id()
        self.conn.execute(
            "INSERT INTO runs(id, symbol, status) VALUES (?, ?, ?)",
            (run_id, symbol.upper(), "RUNNING"),
        )
        return RunRecord(id=run_id, symbol=symbol.upper(), status="RUNNING")

    def finish_run(self, run_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE runs SET status=?, finished_at=datetime('now') WHERE id=?",
            (status, run_id),
        )

    def add_run_log(self, run_id: str, level: str, message: str) -> None:
        self.conn.execute(
            "INSERT INTO run_logs(run_id, level, message) VALUES (?, ?, ?)",
            (run_id, level.upper(), message),
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        run = self.conn.execute(
            "SELECT id, symbol, started_at, finished_at, status FROM runs WHERE id=?",
            (run_id,),
        ).fetchone()
        if not run:
            return None
        logs = self.conn.execute(
            "SELECT level, message, at FROM run_logs WHERE run_id=? ORDER BY at ASC",
            (run_id,),
        ).fetchall()
        payload = dict(run)
        payload["logs"] = [dict(r) for r in logs]
        return payload

    # Filings
    def filing_exists(self, symbol: str, pdf_sha256: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM filings WHERE symbol=? AND pdf_sha256=? LIMIT 1",
            (symbol.upper(), pdf_sha256),
        ).fetchone()
        return row is not None

    def upsert_filing(
        self,
        *,
        filing_id: str,
        symbol: str,
        announced_at: str | None,
        title: str,
        category: str,
        summary: str,
        confidence: float,
        pdf_url: str,
        pdf_sha256: str,
        text_source: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO filings(
              id, symbol, announced_at, title, category, summary, confidence,
              pdf_url, pdf_sha256, text_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              announced_at=excluded.announced_at,
              title=excluded.title,
              category=excluded.category,
              summary=excluded.summary,
              confidence=excluded.confidence,
              pdf_url=excluded.pdf_url,
              pdf_sha256=excluded.pdf_sha256,
              text_source=excluded.text_source
            """,
            (
                filing_id,
                symbol.upper(),
                announced_at,
                title,
                category,
                summary,
                float(confidence),
                pdf_url,
                pdf_sha256,
                text_source,
            ),
        )

    def insert_filing_artifact(
        self,
        *,
        artifact_id: str,
        filing_id: str,
        pdf_path: str,
        text_path: str,
        ocr_used: bool,
        ocr_pages: int,
        ocr_engine_version: str | None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO filing_artifacts(
              id, filing_id, pdf_path, text_path, ocr_used, ocr_pages, ocr_engine_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                filing_id,
                pdf_path,
                text_path,
                1 if ocr_used else 0,
                int(ocr_pages),
                ocr_engine_version,
            ),
        )

    def list_filings(self, symbol: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT f.*, a.pdf_path, a.text_path, a.ocr_used, a.ocr_pages
            FROM filings f
            LEFT JOIN filing_artifacts a ON a.filing_id=f.id
            WHERE f.symbol=? AND date(COALESCE(f.announced_at, f.created_at)) BETWEEN date(?) AND date(?)
            ORDER BY COALESCE(f.announced_at, f.created_at) ASC
            """,
            (symbol.upper(), from_date, to_date),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_filing(self, filing_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT f.*, a.pdf_path, a.text_path, a.ocr_used, a.ocr_pages
            FROM filings f
            LEFT JOIN filing_artifacts a ON a.filing_id=f.id
            WHERE f.id=?
            """,
            (filing_id,),
        ).fetchone()
        return dict(row) if row else None

    # News
    def upsert_headline(
        self,
        *,
        headline_id: str,
        symbol: str,
        published_at: str | None,
        source: str,
        title: str,
        url: str,
        mood_score: float,
        confidence: float,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO news_headlines(id, symbol, published_at, source, title, url, mood_score, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              published_at=excluded.published_at,
              source=excluded.source,
              title=excluded.title,
              url=excluded.url,
              mood_score=excluded.mood_score,
              confidence=excluded.confidence
            """,
            (
                headline_id,
                symbol.upper(),
                published_at,
                source,
                title,
                url,
                float(mood_score),
                float(confidence),
            ),
        )

    def list_headlines(self, symbol: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM news_headlines
            WHERE symbol=? AND date(COALESCE(published_at, created_at)) BETWEEN date(?) AND date(?)
            ORDER BY COALESCE(published_at, created_at) ASC
            """,
            (symbol.upper(), from_date, to_date),
        ).fetchall()
        return [dict(r) for r in rows]

    def upsert_mood_daily(self, symbol: str, day: date, scores: list[float]) -> None:
        if not scores:
            return
        avg = sum(scores) / len(scores)
        pos = sum(1 for s in scores if s > 0)
        neg = sum(1 for s in scores if s < 0)
        self.conn.execute(
            """
            INSERT INTO mood_daily(symbol, date, mood_avg, mood_count, mood_pos, mood_neg)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
              mood_avg=excluded.mood_avg,
              mood_count=excluded.mood_count,
              mood_pos=excluded.mood_pos,
              mood_neg=excluded.mood_neg
            """,
            (symbol.upper(), day.isoformat(), float(avg), len(scores), pos, neg),
        )

    def list_mood_daily(self, symbol: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM mood_daily
            WHERE symbol=? AND date BETWEEN date(?) AND date(?)
            ORDER BY date ASC
            """,
            (symbol.upper(), from_date, to_date),
        ).fetchall()
        return [dict(r) for r in rows]

    # Prices
    def upsert_prices(self, symbol: str, rows: Iterable[dict[str, Any]]) -> None:
        payload = []
        for r in rows:
            payload.append(
                (
                    symbol.upper(),
                    r["ts"],
                    r.get("open"),
                    r.get("high"),
                    r.get("low"),
                    r.get("close"),
                    r.get("volume"),
                )
            )
        self.conn.executemany(
            """
            INSERT INTO prices(symbol, ts, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, ts) DO UPDATE SET
              open=excluded.open,
              high=excluded.high,
              low=excluded.low,
              close=excluded.close,
              volume=excluded.volume
            """,
            payload,
        )

    def list_prices(self, symbol: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT symbol, ts, open, high, low, close, volume
            FROM prices
            WHERE symbol=? AND date(ts) BETWEEN date(?) AND date(?)
            ORDER BY ts ASC
            """,
            (symbol.upper(), from_date, to_date),
        ).fetchall()
        return [dict(r) for r in rows]

    # Debug export
    def export_symbol_state(self, symbol: str) -> dict[str, Any]:
        return {
            "company": self.get_company(symbol),
            "watchlist": any(w["symbol"] == symbol.upper() for w in self.list_watchlist()),
        }

