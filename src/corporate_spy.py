from __future__ import annotations

"""
Compatibility module.

The v1 implementation lives under `ims/` (FastAPI backend + Streamlit UI).
This module provides a thin wrapper around the Corporate Spy pipeline so older
docs and scripts can still call it.
"""

from ims.core.settings import get_settings
from ims.storage.db import connect, init_db
from ims.storage.repos import Repos


def analyze_symbol(symbol: str, *, lookback_days: int = 30) -> str:
    settings = get_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        run = repos.create_run(symbol.upper())
        from ims.pipelines.analyze import run_analyze

        run_analyze(repos=repos, settings=settings, symbol=symbol.upper(), lookback_days=lookback_days, run_id=run.id)
        repos.finish_run(run.id, "SUCCESS")
        return run.id
