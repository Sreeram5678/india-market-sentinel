from __future__ import annotations

import logging
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException

from ims.core.logging import setup_logging
from ims.core.settings import get_settings
from ims.domain.types import AnalyzeRequest, RunStatus, TimelineResponse, WatchlistItem
from ims.storage.db import connect, init_db
from ims.storage.repos import Repos

logger = logging.getLogger(__name__)

settings = get_settings()
setup_logging(settings.logs_dir)
init_db(settings.db_path)

app = FastAPI(title="India Market Sentinel", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    if settings.scheduler_enabled:
        try:
            from ims.scheduler import start_scheduler

            app.state.scheduler_state = start_scheduler(settings)
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to start scheduler: %s", e)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/watchlist", response_model=list[WatchlistItem])
def list_watchlist():
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        return repos.list_watchlist()


@app.post("/watchlist")
def add_watchlist(payload: dict):
    symbol = (payload.get("symbol") or "").upper().strip()
    if not symbol:
        raise HTTPException(400, "Missing symbol")
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        if not repos.get_company(symbol):
            raise HTTPException(400, f"Unknown symbol: {symbol}. Seed companies first.")
        repos.add_to_watchlist(symbol)
    return {"ok": True}


@app.delete("/watchlist/{symbol}")
def remove_watchlist(symbol: str):
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        repos.remove_from_watchlist(symbol)
    return {"ok": True}


@app.post("/analyze/{symbol}")
def analyze(symbol: str, req: AnalyzeRequest):
    symbol = symbol.upper().strip()
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        company = repos.get_company(symbol)
        if not company:
            raise HTTPException(400, f"Unknown symbol: {symbol}. Seed company and add to watchlist first.")
        try:
            run = repos.create_run(symbol)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(500, f"Unable to create analyze run for {symbol}: {e}") from e
        try:
            from ims.pipelines.analyze import run_analyze

            run_analyze(
                repos=repos,
                settings=settings,
                symbol=symbol,
                lookback_days=req.lookback_days,
                run_id=run.id,
            )
            repos.finish_run(run.id, "SUCCESS")
            return {"run_id": run.id, "status": "SUCCESS"}
        except Exception as e:  # noqa: BLE001
            repos.add_run_log(run.id, "ERROR", f"Analyze failed: {e}")
            repos.finish_run(run.id, "FAILED")
            return {"run_id": run.id, "status": "FAILED", "error": str(e)}


@app.get("/runs/{run_id}", response_model=RunStatus)
def get_run(run_id: str):
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        r = repos.get_run(run_id)
        if not r:
            raise HTTPException(404, "Run not found")
        return r


@app.get("/timeline/{symbol}", response_model=TimelineResponse)
def timeline(symbol: str, from_: str | None = None, to: str | None = None):  # noqa: A002
    symbol = symbol.upper().strip()
    to_date = date.fromisoformat(to) if to else date.today()
    from_date = date.fromisoformat(from_) if from_ else (to_date - timedelta(days=90))
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        return {
            "symbol": symbol,
            "prices": repos.list_prices(symbol, from_date.isoformat(), to_date.isoformat()),
            "filings": repos.list_filings(symbol, from_date.isoformat(), to_date.isoformat()),
            "mood_daily": repos.list_mood_daily(symbol, from_date.isoformat(), to_date.isoformat()),
            "headlines": repos.list_headlines(symbol, from_date.isoformat(), to_date.isoformat()),
        }


@app.get("/filings/{filing_id}")
def filing_detail(filing_id: str):
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        f = repos.get_filing(filing_id)
        if not f:
            raise HTTPException(404, "Filing not found")
        return f
