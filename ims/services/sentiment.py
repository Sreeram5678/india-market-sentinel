from __future__ import annotations

import math
import re
from dataclasses import dataclass

try:
    from textblob import TextBlob
except Exception:  # noqa: BLE001
    TextBlob = None  # type: ignore[assignment]


_POS_WORDS = {
    "surge",
    "rally",
    "beats",
    "beat",
    "wins",
    "win",
    "award",
    "order",
    "dividend",
    "record",
    "upgrade",
    "strong",
    "growth",
    "profit",
}
_NEG_WORDS = {
    "fall",
    "drops",
    "drop",
    "slump",
    "weak",
    "downgrade",
    "loss",
    "probe",
    "fraud",
    "penalty",
    "fine",
    "shutdown",
    "miss",
    "misses",
}


@dataclass(frozen=True)
class SentimentScore:
    score: float
    confidence: float


def score_headline(title: str) -> SentimentScore:
    title = (title or "").strip()
    if not title:
        return SentimentScore(score=0.0, confidence=0.0)

    if TextBlob is not None:
        try:
            blob = TextBlob(title)
            polarity = float(blob.sentiment.polarity)
            subjectivity = float(getattr(blob.sentiment, "subjectivity", 0.5))
            confidence = max(0.2, min(1.0, (1.0 - subjectivity) * 0.9 + 0.1))
            return SentimentScore(score=_clip(polarity), confidence=confidence)
        except Exception:  # noqa: BLE001
            pass

    # Fallback: tiny lexicon-based scoring.
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", title)}
    pos = len(words & _POS_WORDS)
    neg = len(words & _NEG_WORDS)
    raw = pos - neg
    score = math.tanh(raw / 3.0)
    confidence = min(0.7, 0.2 + 0.15 * (pos + neg))
    return SentimentScore(score=_clip(score), confidence=confidence)


def _clip(x: float) -> float:
    return max(-1.0, min(1.0, x))

