"""A simple, transparent example strategy: SMA crossover.

Long when the fast SMA is above the slow SMA, flat otherwise. This is a
textbook illustrative strategy for exercising the backtest engine and
risk manager - not a claim that it is profitable or suitable for real
trading.
"""
from __future__ import annotations

import pandas as pd


class MovingAverageCrossoverStrategy:
    def __init__(self, fast_window: int = 20, slow_window: int = 50):
        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """Return a Series of {1: long, 0: flat} aligned to `bars.index`."""
        fast = bars["close"].rolling(self.fast_window).mean()
        slow = bars["close"].rolling(self.slow_window).mean()
        signal = (fast > slow).astype(int)
        signal[fast.isna() | slow.isna()] = 0
        return signal
