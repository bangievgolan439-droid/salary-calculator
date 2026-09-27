"""Unit tests for the Phase 1 indicator math and strategy wiring.

These run entirely on synthetic, generated price series -- they prove the
code is mechanically correct, not that the strategy is profitable on real
markets. A run against real AAPL / BTC-USD data (PLAN.md Section 5a) requires
an Alpaca paper API key and is not part of this test suite.
"""

import os
import sys

import numpy as np
import pandas as pd
from backtesting import Backtest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from strategy.ema_adx_strategy import EmaAdxCrossStrategy
from strategy.indicators import adx, ema


def _synthetic_ohlcv(n=400, seed=7) -> pd.DataFrame:
    """First 60% of bars: a steady uptrend with small noise (should read as
    trending on ADX). Last 40%: sideways chop around a flat level (should
    read as non-trending)."""
    rng = np.random.default_rng(seed)
    trend_len = int(n * 0.6)
    chop_len = n - trend_len

    trend = 100 + np.arange(trend_len) * 0.6 + rng.normal(0, 0.5, trend_len)
    chop_level = trend[-1]
    chop = chop_level + rng.normal(0, 1.0, chop_len)
    close = np.concatenate([trend, chop])

    high = close + rng.uniform(0.1, 0.6, n)
    low = close - rng.uniform(0.1, 0.6, n)
    open_ = close + rng.normal(0, 0.2, n)
    volume = rng.integers(1000, 5000, n)

    index = pd.date_range("2024-01-01", periods=n, freq="4h")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=index
    )


def test_ema_tracks_price_direction():
    series = pd.Series(np.linspace(100, 200, 300))
    fast = ema(series, 50)
    slow = ema(series, 200)
    # On a steady uptrend, the faster EMA must pull ahead of the slower one.
    assert fast.iloc[-1] > slow.iloc[-1]


def test_adx_bounded_and_higher_in_trend_than_chop():
    df = _synthetic_ohlcv()
    adx_values = adx(df["High"], df["Low"], df["Close"], config.ADX_PERIOD)
    valid = adx_values.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()

    trend_len = int(len(df) * 0.6)
    trend_region = adx_values.iloc[config.ADX_PERIOD * 2 : trend_len].dropna()
    chop_region = adx_values.iloc[trend_len + config.ADX_PERIOD :].dropna()
    assert trend_region.mean() > chop_region.mean()


def test_backtest_runs_end_to_end_on_synthetic_data():
    """Smoke test: data -> strategy -> backtesting.py -> a completed run with
    at least one trade. Proves the pipeline wiring, not market performance."""
    df = _synthetic_ohlcv()
    bt = Backtest(df, EmaAdxCrossStrategy, cash=10_000, commission=0.001)
    stats = bt.run()
    assert stats["# Trades"] >= 1
