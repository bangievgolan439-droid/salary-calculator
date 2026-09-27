import os
import sys

from backtesting import Strategy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from strategy.indicators import adx, ema


class EmaAdxCrossStrategy(Strategy):
    """PLAN.md Section 5a: enter long only when the fast EMA is above the slow
    EMA *and* ADX is above the trend threshold; exit on either condition failing.
    Long-only, one position at a time -- this is Phase 1 pipeline scaffolding,
    not a claim that it is a profitable edge (see PLAN.md Section 5a)."""

    ema_fast = config.EMA_FAST
    ema_slow = config.EMA_SLOW
    adx_period = config.ADX_PERIOD
    adx_threshold = config.ADX_TREND_THRESHOLD

    def init(self):
        close = self.data.Close.s
        high = self.data.High.s
        low = self.data.Low.s
        self.ema_fast_line = self.I(ema, close, self.ema_fast)
        self.ema_slow_line = self.I(ema, close, self.ema_slow)
        self.adx_line = self.I(adx, high, low, close, self.adx_period)

    def next(self):
        trending = self.adx_line[-1] > self.adx_threshold
        bullish = self.ema_fast_line[-1] > self.ema_slow_line[-1]

        if not self.position and trending and bullish:
            self.buy()
        elif self.position and not (trending and bullish):
            self.position.close()
