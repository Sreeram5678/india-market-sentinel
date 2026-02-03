from __future__ import annotations

"""
Compatibility module.

The v1 implementation lives under `ims/` (FastAPI backend + Streamlit UI).
This module provides a minimal entry for scoring headlines.
"""

from ims.services.sentiment import score_headline


def mood_score(title: str) -> float:
    return score_headline(title).score
