"""Pulls historical bars from Alpaca for one stock and one crypto symbol.

Requires ALPACA_API_KEY / ALPACA_SECRET_KEY (paper-mode keys) as environment
variables. See PLAN.md Section 7 for how to obtain and set these -- do not
hardcode keys in this file or pass them on the command line.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _timeframe_from_string(value: str) -> TimeFrame:
    """Parses a string like '4Hour' or '1Day' into a TimeFrame."""
    for i, ch in enumerate(value):
        if not ch.isdigit():
            amount = int(value[:i]) if i > 0 else 1
            unit = TimeFrameUnit(value[i:])
            return TimeFrame(amount, unit)
    raise ValueError(f"Could not parse timeframe string: {value!r}")


def _get_credentials() -> tuple[str, str]:
    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError(
            "ALPACA_API_KEY / ALPACA_SECRET_KEY are not set. "
            "Add a paper-mode Alpaca key pair through this environment's "
            "secrets settings (PLAN.md Section 7) before fetching data."
        )
    return api_key, secret_key


def fetch_stock_bars(symbol: str, days_back: int) -> pd.DataFrame:
    api_key, secret_key = _get_credentials()
    client = StockHistoricalDataClient(api_key, secret_key)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=_timeframe_from_string(config.TIMEFRAME),
        start=datetime.now(timezone.utc) - timedelta(days=days_back),
        feed=DataFeed(config.DATA_FEED),
    )
    bars = client.get_stock_bars(request)
    return bars.df.xs(symbol, level="symbol") if "symbol" in bars.df.index.names else bars.df


def fetch_crypto_bars(symbol: str, days_back: int) -> pd.DataFrame:
    api_key, secret_key = _get_credentials()
    client = CryptoHistoricalDataClient(api_key, secret_key)
    request = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=_timeframe_from_string(config.TIMEFRAME),
        start=datetime.now(timezone.utc) - timedelta(days=days_back),
    )
    bars = client.get_crypto_bars(request)
    return bars.df.xs(symbol, level="symbol") if "symbol" in bars.df.index.names else bars.df


def to_backtesting_format(df: pd.DataFrame) -> pd.DataFrame:
    """backtesting.py expects columns Open/High/Low/Close/Volume, capitalized."""
    return df.rename(
        columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
    )[["Open", "High", "Low", "Close", "Volume"]]


if __name__ == "__main__":
    stock_df = to_backtesting_format(fetch_stock_bars(config.TEST_STOCK_SYMBOL, days_back=730))
    stock_df.to_csv(os.path.join(os.path.dirname(__file__), "aapl_4h.csv"))
    print(f"Saved {len(stock_df)} bars for {config.TEST_STOCK_SYMBOL}")

    crypto_df = to_backtesting_format(fetch_crypto_bars(config.TEST_CRYPTO_SYMBOL, days_back=730))
    crypto_df.to_csv(os.path.join(os.path.dirname(__file__), "btcusd_4h.csv"))
    print(f"Saved {len(crypto_df)} bars for {config.TEST_CRYPTO_SYMBOL}")
