---
name: correlation_dashboard
description: "Handles the visualization of stock prices, mood scores, and filing events in a Streamlit dashboard."
---

# Correlation Dashboard Skill

This skill focuses on building the user interface where data from the Corporate Spy and Sentiment Auditor converge.

## Capabilities

- **Streamlit Layout**: Creates a clean, dark-themed financial dashboard.
- **Interactive Charts**: Plots stock price history using `matplotlib` or `plotly`.
- **Annotation Layer**: Overlays sentiment scores (as a line chart or color gradient) and corporate filings (as markers on the timeline).
- **Responsive Controls**: Simple inputs for stock symbols and date ranges.

## Tools & Libraries

- `streamlit` for the web interface.
- `matplotlib` and `pandas` for data visualization.
- `yfinance` (optional, but recommended) for fetching historical price data.

## UI Design Goals

- **Minimalist**: A single search bar and a large trend chart.
- **Informative**: Hovering over a filing marker should show the one-sentence summary.
- **Dynamic**: Real-time update of sentiment scores.
