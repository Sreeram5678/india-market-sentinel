from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS companies (
  symbol TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  exchange TEXT NOT NULL DEFAULT 'BSE',
  bse_scrip_code TEXT,
  isin TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS watchlist (
  symbol TEXT PRIMARY KEY,
  added_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT,
  status TEXT NOT NULL,
  FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS run_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS filings (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  announced_at TEXT,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  summary TEXT NOT NULL,
  confidence REAL NOT NULL,
  pdf_url TEXT NOT NULL,
  pdf_sha256 TEXT NOT NULL,
  text_source TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_filings_symbol_sha ON filings(symbol, pdf_sha256);
CREATE INDEX IF NOT EXISTS idx_filings_symbol_time ON filings(symbol, announced_at);

CREATE TABLE IF NOT EXISTS filing_artifacts (
  id TEXT PRIMARY KEY,
  filing_id TEXT NOT NULL,
  pdf_path TEXT NOT NULL,
  text_path TEXT NOT NULL,
  ocr_used INTEGER NOT NULL,
  ocr_pages INTEGER NOT NULL,
  ocr_engine_version TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(filing_id) REFERENCES filings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS news_headlines (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  published_at TEXT,
  source TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  mood_score REAL NOT NULL,
  confidence REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_news_symbol_url ON news_headlines(symbol, url);
CREATE INDEX IF NOT EXISTS idx_news_symbol_time ON news_headlines(symbol, published_at);

CREATE TABLE IF NOT EXISTS mood_daily (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL,
  mood_avg REAL NOT NULL,
  mood_count INTEGER NOT NULL,
  mood_pos INTEGER NOT NULL,
  mood_neg INTEGER NOT NULL,
  PRIMARY KEY(symbol, date),
  FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prices (
  symbol TEXT NOT NULL,
  ts TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  PRIMARY KEY(symbol, ts),
  FOREIGN KEY(symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def connect(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

