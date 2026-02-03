from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ims.core.settings import Settings
from ims.providers.bse import BseAnnouncementsProvider
from ims.providers.http import HttpClient
from ims.services.ocr import ocr_pdf
from ims.services.pdf_text import extract_pdf_text
from ims.services.summarize import summarize_filing
from ims.storage.repos import Repos, stable_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FilingIngestStats:
    fetched: int
    downloaded: int
    ocr_used: int
    persisted: int
    skipped_existing: int


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest_filings(
    *,
    repos: Repos,
    settings: Settings,
    http: HttpClient,
    provider: BseAnnouncementsProvider,
    run_id: str,
    symbol: str,
    scrip_code: str,
    from_date: date,
    to_date: date,
) -> FilingIngestStats:
    anns = provider.list_announcements(scrip_code=scrip_code, from_date=from_date, to_date=to_date)
    stats = {"fetched": len(anns), "downloaded": 0, "ocr_used": 0, "persisted": 0, "skipped_existing": 0}

    for ann in anns:
        try:
            date_dir = (ann.announced_at or date.today().isoformat()).split("T")[0]
            base_dir = settings.data_dir / "filings" / symbol.upper() / date_dir
            tmp_pdf = base_dir / "download.pdf"
            http.download(ann.pdf_url, tmp_pdf)
            stats["downloaded"] += 1

            pdf_sha = _sha256(tmp_pdf)
            if repos.filing_exists(symbol, pdf_sha):
                stats["skipped_existing"] += 1
                continue

            pdf_path = base_dir / f"{pdf_sha}.pdf"
            tmp_pdf.replace(pdf_path)

            pdf_text = extract_pdf_text(pdf_path)
            text = pdf_text.text.strip()
            text_source = "pdf_text"
            ocr_used = False
            ocr_pages = 0
            ocr_version = None

            if len(text) < settings.pdf_text_min_chars:
                ocr = ocr_pdf(pdf_path, lang=settings.ocr_lang, max_pages=settings.ocr_max_pages)
                text = ocr.text.strip() or text
                ocr_used = True
                text_source = "ocr"
                ocr_pages = ocr.pages_ocr
                ocr_version = ocr.engine_version
                stats["ocr_used"] += 1

            # Summarize (heuristics first)
            sr = summarize_filing(ann.title, text)
            summary = sr.summary
            confidence = sr.confidence
            category = sr.category

            # Optional Ollama fallback for low confidence
            if settings.ollama_enabled and confidence < 0.55:
                try:
                    from ims.services.ollama import OllamaClient

                    summary = OllamaClient(
                        base_url=settings.ollama_base_url, model=settings.ollama_model
                    ).summarize_one_sentence(title=ann.title, text=text)
                    confidence = max(confidence, 0.60)
                except Exception as e:  # noqa: BLE001
                    repos.add_run_log(run_id, "WARN", f"Ollama fallback failed: {e}")

            text_path = base_dir / f"{pdf_sha}.txt"
            text_path.write_text(text, encoding="utf-8", errors="ignore")

            filing_id = stable_id(symbol.upper(), pdf_sha)
            repos.upsert_filing(
                filing_id=filing_id,
                symbol=symbol,
                announced_at=ann.announced_at,
                title=ann.title,
                category=category,
                summary=summary,
                confidence=confidence,
                pdf_url=ann.pdf_url,
                pdf_sha256=pdf_sha,
                text_source=text_source,
            )
            repos.insert_filing_artifact(
                artifact_id=stable_id(filing_id, "artifact"),
                filing_id=filing_id,
                pdf_path=str(pdf_path),
                text_path=str(text_path),
                ocr_used=ocr_used,
                ocr_pages=ocr_pages,
                ocr_engine_version=ocr_version,
            )
            stats["persisted"] += 1
        except Exception as e:  # noqa: BLE001
            repos.add_run_log(run_id, "ERROR", f"Filing ingest failed: {ann.title} ({e})")
            logger.exception("Filing ingest failed")

    return FilingIngestStats(**stats)

