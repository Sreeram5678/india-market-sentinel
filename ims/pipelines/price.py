from __future__ import annotations

import logging
from dataclasses import dataclass

from ims.providers.price import YahooPriceProvider
from ims.storage.repos import Repos

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceIngestStats:
    bars: int


def ingest_prices(*, repos: Repos, run_id: str, symbol: str, provider: YahooPriceProvider, lookback_days: int) -> PriceIngestStats:
    bars = provider.history(symbol, period_days=lookback_days)
    rows = [
        {"ts": b.ts, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume}
        for b in bars
    ]
    repos.upsert_prices(symbol, rows)
    return PriceIngestStats(bars=len(rows))

