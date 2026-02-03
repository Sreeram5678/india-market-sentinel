---
name: corporate_spy
description: "Handles fetching, reading, and summarizing official Indian corporate filings (BSE/NSE). Specialized in OCR for scanned PDFs."
---

# Corporate Spy Skill

This skill allows the agent to monitor and analyze official corporate announcements from Indian stock exchanges.

## Capabilities

- **Filing Discovery**: Search for latest filings for a given NSE/BSE symbol.
- **PDF Extraction**: Download and extract text from PDF filings.
- **OCR Engine**: Convert scanned image-based PDFs into searchable text using `pytesseract` and `pdf2image`.
- **Smart Summarization**: Distill complex legal/financial jargon into a single, punchy sentence (e.g., "BEL won a ₹500Cr order from the Ministry of Defense").

## Tools & Libraries

- `requests`, `beautifulsoup4` for scraping exchange websites.
- `pytesseract` for OCR.
- `pdf2image` for converting PDF pages to images for OCR.
- `PyPDF2` for text-based PDF extraction.

## Workflow

1. Identify the company symbol.
2. Fetch the latest announcements list.
3. Download the relevant PDF.
4. Attempt direct text extraction; if failed/empty, trigger OCR.
5. Analyze the content and generate a summary.
