from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _user_home() -> Path:
    return Path(os.path.expanduser("~"))


@dataclass(frozen=True)
class Settings:
    # Storage
    app_dir: Path = _user_home() / ".india-market-sentinel"
    db_path: Path = _user_home() / ".india-market-sentinel" / "ims.db"
    data_dir: Path = _user_home() / ".india-market-sentinel" / "data"
    logs_dir: Path = _user_home() / ".india-market-sentinel" / "logs"

    # Network
    http_timeout_s: float = 20.0
    http_retries: int = 3
    user_agent: str = "IndiaMarketSentinel/0.1 (+local-first)"

    # BSE
    bse_ann_endpoint: str = os.getenv(
        "IMS_BSE_ANN_ENDPOINT",
        "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w",
    )

    # OCR
    ocr_lang: str = os.getenv("IMS_OCR_LANG", "eng")
    ocr_max_pages: int = int(os.getenv("IMS_OCR_MAX_PAGES", "12"))
    pdf_text_min_chars: int = int(os.getenv("IMS_PDF_TEXT_MIN_CHARS", "250"))

    # News RSS
    google_news_ceid: str = os.getenv("IMS_GOOGLE_NEWS_CEID", "IN:en")
    google_news_hl: str = os.getenv("IMS_GOOGLE_NEWS_HL", "en-IN")
    google_news_gl: str = os.getenv("IMS_GOOGLE_NEWS_GL", "IN")

    # Sentiment
    mood_positive_threshold: float = float(os.getenv("IMS_MOOD_POS_TH", "0.10"))
    mood_negative_threshold: float = float(os.getenv("IMS_MOOD_NEG_TH", "-0.10"))

    # Price
    price_default_lookback_days: int = int(os.getenv("IMS_PRICE_LOOKBACK_DAYS", "90"))

    # Scheduler
    scheduler_enabled: bool = os.getenv("IMS_SCHEDULER_ENABLED", "true").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )
    scheduler_interval_minutes: int = int(os.getenv("IMS_SCHEDULER_INTERVAL_MIN", "60"))

    # Optional local LLM (Ollama)
    ollama_enabled: bool = os.getenv("IMS_OLLAMA_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )
    ollama_base_url: str = os.getenv("IMS_OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("IMS_OLLAMA_MODEL", "llama3.2")


def get_settings() -> Settings:
    return Settings()

