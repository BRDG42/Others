"""
Price data loader for the SMA-crossover backtest.

Primary source is yfinance, exactly as specified. In sandboxes where Yahoo
Finance blocks the egress IP (HTTP 429 on every endpoint), we fall back to
stockanalysis.com's daily history API, which returns the same fields:
raw OHLCV plus an adjusted close.

Both paths produce an identical frame: a DatetimeIndex and columns
open/high/low/close/volume, where OHLC are *split- and dividend-adjusted*.
Adjusting the whole bar by the same factor (adj_close / close) is what
yfinance's auto_adjust=True does internally, so the two paths agree.
"""

import json
import os

import pandas as pd
import requests

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spy_raw.csv")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _from_yfinance(ticker, start, end):
    import yfinance as yf

    df = yf.download(
        ticker, start=start, end=end, auto_adjust=True, progress=False, actions=False
    )
    if df.empty:
        raise RuntimeError("yfinance returned an empty frame")
    if isinstance(df.columns, pd.MultiIndex):          # yf>=0.2 single-ticker shape
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def _from_stockanalysis(ticker, start, end):
    url = f"https://stockanalysis.com/api/symbol/e/{ticker.lower()}/history"
    r = requests.get(
        url, params={"period": "Daily", "range": "Max"},
        headers={"User-Agent": UA}, timeout=60,
    )
    r.raise_for_status()
    rows = json.loads(r.text)["data"]

    df = pd.DataFrame(rows)
    df["t"] = pd.to_datetime(df["t"])
    df = df.sort_values("t").set_index("t")

    # adj_close / close is the cumulative split+dividend factor for that bar.
    # Scaling open/high/low by the same factor keeps the bar internally
    # consistent, which is what makes "buy at the next open" comparable to
    # "signal off the close".
    factor = df["a"] / df["c"]
    out = pd.DataFrame(
        {
            "open": df["o"] * factor,
            "high": df["h"] * factor,
            "low": df["l"] * factor,
            "close": df["a"],
            "volume": df["v"].astype(float),
        }
    )
    return out.loc[str(start):str(end)]


def load_prices(ticker="SPY", start="2009-01-01", end="2025-01-01", use_cache=True):
    """Return adjusted daily OHLCV, plus a string naming the source actually used."""
    if use_cache and os.path.exists(CACHE):
        df = pd.read_csv(CACHE, index_col=0, parse_dates=True)
        return df.loc[str(start):str(end)], f"cache ({os.path.basename(CACHE)})"

    try:
        df = _from_yfinance(ticker, start, end)
        source = "yfinance (Yahoo Finance)"
    except Exception as exc:                       # noqa: BLE001 - fallback is the point
        print(f"[data] yfinance unavailable ({type(exc).__name__}: {exc}); "
              f"falling back to stockanalysis.com")
        df = _from_stockanalysis(ticker, start, end)
        source = "stockanalysis.com (yfinance blocked in this environment)"

    df.to_csv(CACHE)
    return df, source
