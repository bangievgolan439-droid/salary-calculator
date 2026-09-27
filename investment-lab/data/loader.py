"""Historical price data loading.

Tries to pull real daily bars from Alpaca's market data API when
ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY are set in the environment.
Falls back to a deterministic, clearly-labeled synthetic price series
otherwise, so the backtest is runnable without a brokerage account.

This module only ever reads historical data - it has no code path that
places orders or touches a live/paper trading account.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd


def _synthetic_bars(symbol: str, start: datetime, end: datetime, seed: int = 7) -> pd.DataFrame:
    """Deterministic geometric-Brownian-motion price series for demo/backtest use.

    This is NOT real market data and NOT a price forecast for `symbol` -
    it exists so the backtest engine has something to run against when no
    Alpaca credentials are configured.
    """
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    if n == 0:
        raise ValueError(f"No business days between {start} and {end}")

    rng = np.random.default_rng(seed + sum(ord(c) for c in symbol))
    daily_drift = 0.0003
    daily_vol = 0.012
    shocks = rng.normal(daily_drift, daily_vol, n)
    close = 100 * np.exp(np.cumsum(shocks))

    intraday_range = np.abs(rng.normal(0, daily_vol * 0.6, n))
    high = close * (1 + intraday_range)
    low = close * (1 - intraday_range)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    volume = rng.integers(1_000_000, 8_000_000, n)

    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )
    df.index.name = "timestamp"
    return df


def _alpaca_bars(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    client = StockHistoricalDataClient(
        os.environ["ALPACA_API_KEY_ID"], os.environ["ALPACA_API_SECRET_KEY"]
    )
    request = StockBarsRequest(
        symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start, end=end
    )
    bars = client.get_stock_bars(request).df
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.xs(symbol, level="symbol")
    bars = bars.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    bars.index.name = "timestamp"
    return bars


def load_bars(symbol: str, start: datetime, end: datetime) -> tuple[pd.DataFrame, str]:
    """Return (ohlcv_dataframe, source) where source is 'alpaca' or 'synthetic'."""
    have_creds = os.environ.get("ALPACA_API_KEY_ID") and os.environ.get("ALPACA_API_SECRET_KEY")
    if have_creds:
        try:
            return _alpaca_bars(symbol, start, end), "alpaca"
        except Exception as exc:  # network/auth/plan issues -> fall back, don't crash the run
            print(
                f"[data] Alpaca fetch failed ({exc!r}); falling back to synthetic data.",
                file=sys.stderr,
            )
    return _synthetic_bars(symbol, start, end), "synthetic"
