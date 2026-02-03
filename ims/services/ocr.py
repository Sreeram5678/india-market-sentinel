from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OcrResult:
    text: str
    pages_ocr: int
    engine_version: str | None


def ocr_pdf(
    pdf_path: Path,
    *,
    lang: str,
    max_pages: int,
) -> OcrResult:
    try:
        images = convert_from_path(str(pdf_path), first_page=1, last_page=max_pages)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(
            "pdf2image failed. On macOS install poppler: `brew install poppler`"
        ) from e

    texts: list[str] = []
    for idx, img in enumerate(images, start=1):
        try:
            texts.append(pytesseract.image_to_string(img, lang=lang))
        except Exception as e:  # noqa: BLE001
            logger.warning("OCR failed page=%s err=%s", idx, e)
    version = None
    try:
        version = pytesseract.get_tesseract_version().string  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        version = None
    return OcrResult(text="\n".join(texts).strip(), pages_ocr=len(images), engine_version=version)

