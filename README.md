# India Market Sentinel

An intelligent, local-first financial dashboard that gives Indian retail investors an institutional-grade edge by fusing:
- **Corporate Spy**: BSE corporate announcements + PDF text extraction + OCR fallback → **1-sentence summaries**
- **Sentiment Auditor**: recent headlines via RSS → **Mood Score** timeline
- **Correlation Dashboard**: price chart with overlays (filings + mood)

## Quickstart (macOS)

### 1) System dependencies (OCR)
```bash
brew install tesseract poppler
```

### 2) Python dependencies
> Note: this project is easiest to run on Python **3.12** today. If you’re on a newer Python and hit dependency issues, switch to 3.12 via pyenv/uv.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Seed a few companies (symbol → BSE scrip code)
Edit `data/seed_companies.csv` as needed, then:
```bash
python scripts/bootstrap_companies.py
```

### 4) Start backend (FastAPI)
```bash
uvicorn ims.api:app --reload --port 8000
```

### 5) Start UI (Streamlit)
```bash
streamlit run app.py
```

Open the Streamlit app, add a symbol to the watchlist (e.g. `BEL`), then click **Analyze**.

## Optional: local LLM fallback (Ollama)
If you have Ollama running locally and want better summaries for low-confidence filings:
```bash
export IMS_OLLAMA_ENABLED=true
export IMS_OLLAMA_MODEL=llama3.2
```

## Data storage (local-first)
The app stores everything on your machine:
- DB: `~/.india-market-sentinel/ims.db`
- Files: `~/.india-market-sentinel/data/`
- Logs: `~/.india-market-sentinel/logs/app.log`

## Project layout
- `ims/api.py`: FastAPI backend (endpoints + scheduler startup)
- `ims/pipelines/`: filing/news/price ingestion
- `ims/services/`: PDF text extraction, OCR, summarization, sentiment scoring
- `ims/ui/app.py`: Streamlit UI
- `data/seed_companies.csv`: seed symbols + BSE scrip codes

## Notes / Limitations (v1)
- BSE endpoints can change; if filings fetch breaks, set `IMS_BSE_ANN_ENDPOINT` accordingly.
- Yahoo symbol mapping may require `.NS` or `.BO`; the app tries both.
