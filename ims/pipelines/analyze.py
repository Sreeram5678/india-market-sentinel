from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from ims.core.settings import Settings
from ims.providers.bse import BseAnnouncementsProvider
from ims.providers.http import HttpClient
from ims.providers.news import GoogleNewsRssProvider
from ims.providers.price import YahooPriceProvider
from ims.pipelines.filings import FilingIngestStats, ingest_filings
from ims.pipelines.news import NewsIngestStats, ingest_news
from ims.pipelines.price import PriceIngestStats, ingest_prices
from ims.storage.repos import Repos

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalyzeResult:
    run_id: str
    filings: FilingIngestStats
    news: NewsIngestStats
    prices: PriceIngestStats


def run_analyze(
    *,
    repos: Repos,
    settings: Settings,
    symbol: str,
    lookback_days: int,
    run_id: str,
) -> AnalyzeResult:
    company = repos.get_company(symbol)
    if not company:
        raise RuntimeError(f"Unknown company symbol: {symbol} (seed companies first)")
    scrip_code = company.get("bse_scrip_code")
    if not scrip_code:
        raise RuntimeError(f"Missing BSE scrip code for {symbol}. Update companies table/seed.")

    http = HttpClient(
        timeout_s=settings.http_timeout_s, retries=settings.http_retries, user_agent=settings.user_agent
    )
    bse_provider = BseAnnouncementsProvider(http=http, endpoint=settings.bse_ann_endpoint)
    news_provider = GoogleNewsRssProvider(http=http, settings=settings)
    price_provider = YahooPriceProvider()

    to_d = date.today()
    from_d = to_d - timedelta(days=max(lookback_days, 30))

    repos.add_run_log(run_id, "INFO", f"Analyze started for {symbol} lookback_days={lookback_days}")

    filings_stats = ingest_filings(
        repos=repos,
        settings=settings,
        http=http,
        provider=bse_provider,
        run_id=run_id,
        symbol=symbol,
        scrip_code=str(scrip_code),
        from_date=from_d,
        to_date=to_d,
    )
    repos.add_run_log(
        run_id,
        "INFO",
        f"Filings: fetched={filings_stats.fetched} downloaded={filings_stats.downloaded} "
        f"persisted={filings_stats.persisted} ocr_used={filings_stats.ocr_used}",
    )

    news_stats = ingest_news(
        repos=repos,
        run_id=run_id,
        symbol=symbol,
        company_name=company["name"],
        provider=news_provider,
        lookback_days=lookback_days,
    )
    repos.add_run_log(run_id, "INFO", f"News: fetched={news_stats.fetched} persisted={news_stats.persisted}")

    price_stats = ingest_prices(
        repos=repos, run_id=run_id, symbol=symbol, provider=price_provider, lookback_days=lookback_days
    )
    repos.add_run_log(run_id, "INFO", f"Prices: bars={price_stats.bars}")

    return AnalyzeResult(run_id=run_id, filings=filings_stats, news=news_stats, prices=price_stats)

