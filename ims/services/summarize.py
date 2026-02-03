from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryResult:
    category: str
    summary: str
    confidence: float


_INR_RE = re.compile(r"(?:₹|INR)\s*([0-9][0-9,]*(?:\.[0-9]+)?)", re.IGNORECASE)
_DIV_RE = re.compile(r"\bdividend\b", re.IGNORECASE)
_BOARD_RE = re.compile(r"\bboard meeting\b|\bmeeting of the board\b", re.IGNORECASE)
_RESULTS_RE = re.compile(r"\b(results?|financial results?)\b", re.IGNORECASE)
_ORDER_RE = re.compile(r"\border\b|\bcontract\b|\bwork order\b|\baward(ed)?\b", re.IGNORECASE)
_RATING_RE = re.compile(r"\bcredit rating\b|\brating\b|\bcrisil\b|\bcare\b|\bicra\b", re.IGNORECASE)
_REG_RE = re.compile(r"\bsebi\b|\bregulat(ory|ion)\b|\bcompliance\b", re.IGNORECASE)


def summarize_filing(title: str, text: str) -> SummaryResult:
    title = (title or "").strip()
    text = (text or "").strip()
    blob = f"{title}\n{text}"

    if _DIV_RE.search(blob):
        amt = _first_inr(blob)
        if amt:
            return SummaryResult("DIVIDEND", f"Company declared a dividend of ₹{amt} per share.", 0.86)
        return SummaryResult("DIVIDEND", "Company announced a dividend.", 0.62)

    if _BOARD_RE.search(blob):
        return SummaryResult("BOARD_MEETING", "Company scheduled a board meeting to consider key corporate matters.", 0.60)

    if _RESULTS_RE.search(blob):
        return SummaryResult("RESULTS", "Company announced an update related to its financial results.", 0.58)

    if _ORDER_RE.search(blob):
        amt = _first_inr(blob)
        if amt:
            return SummaryResult("ORDER_WIN", f"Company received an order worth ₹{amt}.", 0.70)
        return SummaryResult("ORDER_WIN", "Company announced an order win / contract update.", 0.55)

    if _RATING_RE.search(blob):
        return SummaryResult("CREDIT_RATING", "Company shared an update related to its credit rating.", 0.55)

    if _REG_RE.search(blob):
        return SummaryResult("REGULATORY", "Company shared a regulatory / compliance update.", 0.52)

    return SummaryResult("OTHER", "Company made a corporate announcement.", 0.40)


def _first_inr(text: str) -> str | None:
    m = _INR_RE.search(text)
    if not m:
        return None
    return m.group(1).replace(",", "")

