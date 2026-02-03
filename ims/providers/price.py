from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceBar:
    ts: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None


class YahooPriceProvider:
    def __init__(self):
        import yfinance as yf  # lazy import

        self.yf = yf

    def _candidates(self, symbol: str) -> list[str]:
        base = symbol.upper().strip()
        return [base + ".NS", base + ".BO", base]

    def history(self, symbol: str, *, period_days: int) -> list[PriceBar]:
        last_err: Exception | None = None
        for ticker in self._candidates(symbol):
            try:
                t = self.yf.Ticker(ticker)
                df = t.history(period=f"{period_days}d", auto_adjust=False)
                if df is None or df.empty:
                    continue
                df = df.reset_index()
                out: list[PriceBar] = []
                for _, r in df.iterrows():
                    ts = r.get("Date") or r.get("Datetime")
                    if isinstance(ts, pd.Timestamp):
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        ts_str = ts.isoformat()
                    elif isinstance(ts, datetime):
                        ts_str = ts.isoformat()
                    else:
                        ts_str = str(ts)
                    out.append(
                        PriceBar(
                            ts=ts_str,
                            open=_to_float(r.get("Open")),
                            high=_to_float(r.get("High")),
                            low=_to_float(r.get("Low")),
                            close=_to_float(r.get("Close")),
                            volume=_to_float(r.get("Volume")),
                        )
                    )
                return out
            except Exception as e:  # noqa: BLE001
                last_err = e
                logger.warning("Yahoo history failed ticker=%s err=%s", ticker, e)
        raise RuntimeError(f"Yahoo price history unavailable for {symbol}") from last_err


def _to_float(v) -> float | None:
    try:
        if v is None:
            return None
        if pd.isna(v):
            return None
        return float(v)
    except Exception:  # noqa: BLE001
        return None

