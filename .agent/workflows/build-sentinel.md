---
description: Build the India Market Sentinel dashboard from scratch
---

# India Market Sentinel Build Workflow

Follow these steps to implement the core features of the sentinel.

## Phase 1: Environment Setup (macOS)

1. Ensure all dependencies from `requirements.txt` are installed.
   ```bash
   pip install -r requirements.txt
   ```
2. Verify system dependencies for OCR (Tesseract):
   ```bash
   brew install tesseract poppler
   ```

## Phase 2: Bootstrap local data

3. Seed companies (symbol → BSE scrip code) by editing `data/seed_companies.csv`, then:
   ```bash
   python scripts/bootstrap_companies.py
   ```

## Phase 3: Run backend + UI

4. Start the backend (FastAPI):
   ```bash
   uvicorn ims.api:app --reload --port 8000
   ```
5. Start the UI (Streamlit):
   ```bash
   streamlit run app.py
   ```

## Phase 4: Testing & Polish

6. Test with a sample symbol like `BEL` (Bharat Electronics) or `RELIANCE`.
7. Ensure OCR handles low-quality PDF filings (non-selectable text).
