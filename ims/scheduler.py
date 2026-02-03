from __future__ import annotations

import logging
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler

from ims.core.settings import Settings
from ims.storage.db import connect
from ims.storage.repos import Repos

logger = logging.getLogger(__name__)


@dataclass
class SchedulerState:
    scheduler: BackgroundScheduler


def start_scheduler(settings: Settings) -> SchedulerState:
    sched = BackgroundScheduler(daemon=True)

    def refresh_watchlist() -> None:
        from ims.pipelines.analyze import run_analyze

        with connect(settings.db_path) as conn:
            repos = Repos(conn)
            for item in repos.list_watchlist():
                symbol = item["symbol"]
                run = repos.create_run(symbol)
                try:
                    run_analyze(
                        repos=repos,
                        settings=settings,
                        symbol=symbol,
                        lookback_days=settings.price_default_lookback_days,
                        run_id=run.id,
                    )
                    repos.finish_run(run.id, "SUCCESS")
                except Exception as e:  # noqa: BLE001
                    repos.add_run_log(run.id, "ERROR", f"Watchdog analyze failed: {e}")
                    repos.finish_run(run.id, "FAILED")

    sched.add_job(refresh_watchlist, "interval", minutes=settings.scheduler_interval_minutes, id="watchlist-refresh")
    sched.start()
    logger.info("Scheduler started interval_minutes=%s", settings.scheduler_interval_minutes)
    return SchedulerState(scheduler=sched)

