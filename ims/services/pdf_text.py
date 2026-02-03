from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PdfTextResult:
    text: str
    pages: int


def extract_pdf_text(pdf_path: Path) -> PdfTextResult:
    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    for p in reader.pages:
        try:
            chunks.append(p.extract_text() or "")
        except Exception as e:  # noqa: BLE001
            logger.warning("PDF text extract failed page err=%s", e)
    return PdfTextResult(text="\n".join(chunks).strip(), pages=len(reader.pages))

