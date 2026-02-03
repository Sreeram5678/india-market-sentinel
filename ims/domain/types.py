from __future__ import annotations

from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    symbol: str
    name: str
    exchange: str
    bse_scrip_code: str | None = None
    added_at: str


class RunStatus(BaseModel):
    id: str
    symbol: str
    started_at: str
    finished_at: str | None = None
    status: str
    logs: list[dict] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    lookback_days: int = 30


class TimelineResponse(BaseModel):
    symbol: str
    prices: list[dict]
    filings: list[dict]
    mood_daily: list[dict]
    headlines: list[dict]

