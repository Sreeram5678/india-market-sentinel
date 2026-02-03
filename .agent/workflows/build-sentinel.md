---
description: Build the India Market Sentinel dashboard from scratch
---

# India Market Sentinel Build Workflow

Follow these steps to implement the core features of the sentinel.

## Phase 1: Environment Setup

1. Ensure all dependencies from `requirements.txt` are installed.
   ```bash
   pip install -r requirements.txt
   ```
2. Verify system dependencies for OCR (Tesseract):
   ```bash
   brew install tesseract poppler
   ```

## Phase 2: Core Logic Implementation

3. **Corporate Spy**: Create `src/corporate_spy.py` to handle BSE/NSE filing scraping and OCR.
4. **Sentiment Auditor**: Create `src/sentiment_auditor.py` to scrape news and calculate Mood Scores.

## Phase 3: Dashboard Assembly

5. **UI**: Create `app.py` using Streamlit.
6. **Data Integration**: Connect the logic scripts to the Streamlit UI.
7. **Visualization**: Implement the price + sentiment + filing event chart.

## Phase 4: Testing & Polish

8. Test with a sample symbol like `BEL` (Bharat Electronics) or `RELIANCE`.
9. Ensure OCR handles low-quality PDF snippets.
