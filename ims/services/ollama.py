from __future__ import annotations

import json
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str
    timeout_s: float = 30.0

    def summarize_one_sentence(self, *, title: str, text: str) -> str:
        prompt = (
            "Summarize the following corporate announcement in exactly ONE sentence.\n"
            "Rules: factual only; include numbers/dates if present; no speculation.\n\n"
            f"TITLE: {title}\n\nTEXT:\n{text[:8000]}\n"
        )
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        url = self.base_url.rstrip("/") + "/api/generate"
        with httpx.Client(timeout=self.timeout_s) as c:
            r = c.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        resp = (data.get("response") or "").strip()
        if not resp:
            raise RuntimeError("Ollama returned empty response")
        # Safety: collapse to one sentence-ish.
        resp = resp.replace("\n", " ").strip()
        if len(resp) > 280:
            resp = resp[:277].rstrip() + "..."
        return resp

