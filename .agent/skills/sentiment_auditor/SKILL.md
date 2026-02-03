---
name: sentiment_auditor
description: "Scans news headlines for Indian stocks and assigns a quantitative sentiment score (Mood Score)."
---

# Sentiment Auditor Skill

This skill quantifies market sentiment by analyzing news flow related to specific Indian stocks.

## Capabilities

- **News Aggregation**: Scrapes headlines from sources like Google News (India) or Yahoo Finance (India).
- **Sentiment Scoring**: Uses NLP (`textblob` or similar) to assign a polarity score between -1.0 (Highly Negative) and +1.0 (Highly Positive).
- **Historical Mood Tracking**: Trends sentiment over a specified time window.

## Tools & Libraries

- `beautifulsoup4`, `requests` for scraping headlines.
- `textblob` for basic NLP sentiment analysis.
- `pandas` for structuring temporal sentiment data.

## Workflow

1. Search news for "{Company Name} stock news".
2. Extract headline text and publication timestamps.
3. Pass each headline through the sentiment model.
4. Calculate a "Mood Score" (weighted average of recent sentiment).
