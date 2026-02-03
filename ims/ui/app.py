from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass

import plotly.graph_objects as go
import requests
import streamlit as st


@dataclass(frozen=True)
class UiConfig:
    api_base: str = "http://127.0.0.1:8000"


def _api_get(path: str):
    return requests.get(_cfg().api_base + path, timeout=15)


def _api_post(path: str, json: dict):
    return requests.post(_cfg().api_base + path, json=json, timeout=30)


def _api_delete(path: str):
    return requests.delete(_cfg().api_base + path, timeout=15)


@st.cache_resource
def _cfg() -> UiConfig:
    return UiConfig(api_base=st.secrets.get("api_base", "http://127.0.0.1:8000"))


def main() -> None:
    st.set_page_config(page_title="India Market Sentinel", layout="wide")
    st.title("India Market Sentinel")
    st.caption("Local-first dashboard: filings (OCR) + news mood + price correlation.")

    page = st.sidebar.radio("Page", ["Watchlist", "Analyze", "Dashboard"], index=0)
    if page == "Watchlist":
        render_watchlist()
    elif page == "Analyze":
        render_analyze()
    else:
        render_dashboard()


def render_watchlist() -> None:
    st.subheader("Watchlist")
    try:
        r = _api_get("/watchlist")
        r.raise_for_status()
        items = r.json()
    except Exception as e:  # noqa: BLE001
        st.error(f"Backend unavailable at {_cfg().api_base}. Start FastAPI first. ({e})")
        return

    col1, col2 = st.columns([2, 1])
    with col2:
        st.markdown("### Add symbol")
        symbol = st.text_input("Symbol (seeded in DB)", value="BEL").strip().upper()
        if st.button("Add to watchlist"):
            rr = _api_post("/watchlist", {"symbol": symbol})
            if rr.ok:
                st.success("Added")
                st.rerun()
            else:
                st.error(rr.text)

    with col1:
        st.markdown("### Current")
        if not items:
            st.info("Watchlist is empty. Seed companies and add a symbol.")
            return
        st.dataframe(items, use_container_width=True)
        symbol_to_remove = st.selectbox("Remove symbol", [i["symbol"] for i in items])
        if st.button("Remove"):
            _api_delete(f"/watchlist/{symbol_to_remove}")
            st.rerun()


def render_analyze() -> None:
    st.subheader("Analyze")
    try:
        wl = _api_get("/watchlist")
        wl.raise_for_status()
        items = wl.json()
    except Exception as e:  # noqa: BLE001
        st.error(f"Backend unavailable at {_cfg().api_base}. Start FastAPI first. ({e})")
        return

    if not items:
        st.warning("Add a symbol to the watchlist first.")
        return

    symbol = st.selectbox("Symbol", [i["symbol"] for i in items])
    lookback_days = st.slider("Lookback (days)", min_value=7, max_value=365, value=30)
    if st.button("Analyze"):
        rr = _api_post(f"/analyze/{symbol}", {"lookback_days": int(lookback_days)})
        if not rr.ok:
            st.error(rr.text)
            return
        run_id = rr.json()["run_id"]
        st.success(f"Run started: {run_id}")
        with st.spinner("Waiting for completion..."):
            status = poll_run(run_id)
        st.json(status)


def poll_run(run_id: str, *, max_wait_s: int = 90):
    start = dt.datetime.now(dt.timezone.utc)
    while (dt.datetime.now(dt.timezone.utc) - start).total_seconds() < max_wait_s:
        r = _api_get(f"/runs/{run_id}")
        if r.ok:
            data = r.json()
            if data.get("status") in {"SUCCESS", "FAILED"}:
                return data
        time.sleep(1.0)
    return {"id": run_id, "status": "UNKNOWN_TIMEOUT"}


def render_dashboard() -> None:
    st.subheader("Dashboard")
    try:
        wl = _api_get("/watchlist")
        wl.raise_for_status()
        items = wl.json()
    except Exception as e:  # noqa: BLE001
        st.error(f"Backend unavailable at {_cfg().api_base}. Start FastAPI first. ({e})")
        return

    if not items:
        st.info("Add a symbol in Watchlist first.")
        return

    symbol = st.selectbox("Symbol", [i["symbol"] for i in items])
    colA, colB = st.columns([1, 1])
    with colA:
        from_date = st.date_input("From", value=dt.date.today() - dt.timedelta(days=90))
    with colB:
        to_date = st.date_input("To", value=dt.date.today())

    r = _api_get(f"/timeline/{symbol}?from_={from_date.isoformat()}&to={to_date.isoformat()}")
    if not r.ok:
        st.error(r.text)
        return
    payload = r.json()

    fig = build_chart(payload)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Filings"):
        st.dataframe(payload.get("filings", []), use_container_width=True)
    with st.expander("Headlines"):
        st.dataframe(payload.get("headlines", []), use_container_width=True)
    with st.expander("Mood (daily)"):
        st.dataframe(payload.get("mood_daily", []), use_container_width=True)


def build_chart(payload: dict) -> go.Figure:
    prices = payload.get("prices") or []
    filings = payload.get("filings") or []
    mood = payload.get("mood_daily") or []

    fig = go.Figure()
    if prices:
        x = [p["ts"] for p in prices]
        y = [p["close"] for p in prices]
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Close"))

    if mood:
        mx = [m["date"] for m in mood]
        my = [m["mood_avg"] for m in mood]
        fig.add_trace(go.Scatter(x=mx, y=my, mode="markers+lines", name="Mood (avg)", yaxis="y2"))

    for f in filings:
        ts = f.get("announced_at") or f.get("created_at")
        if not ts:
            continue
        fig.add_vline(
            x=ts,
            line_width=1,
            line_dash="dot",
            line_color="orange",
            annotation_text=f.get("category", "FILING"),
            annotation_position="top left",
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Price",
        yaxis2=dict(title="Mood", overlaying="y", side="right", range=[-1, 1]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return fig


if __name__ == "__main__":
    main()
