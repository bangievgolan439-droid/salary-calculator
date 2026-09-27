"""EMA and ADX(Wilder), implemented directly on pandas Series so the exact formula
is auditable here rather than hidden in a third-party indicator library.
"""

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothing: first value is a simple sum over `period`, then each
    next value is prev - prev/period + current. Equivalent to an EMA with
    alpha = 1/period, seeded by a sum instead of the first observation."""
    values = series.to_numpy(dtype=float)
    smoothed = np.full(len(values), np.nan)
    if len(values) < period:
        return pd.Series(smoothed, index=series.index)
    smoothed[period - 1] = values[:period].sum()
    for i in range(period, len(values)):
        smoothed[i] = smoothed[i - 1] - (smoothed[i - 1] / period) + values[i]
    return pd.Series(smoothed, index=series.index)


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)

    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    smoothed_tr = _wilder_smooth(tr, period)
    smoothed_plus_dm = _wilder_smooth(plus_dm, period)
    smoothed_minus_dm = _wilder_smooth(minus_dm, period)

    plus_di = 100 * smoothed_plus_dm / smoothed_tr
    minus_di = 100 * smoothed_minus_dm / smoothed_tr

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return _wilder_smooth(dx.fillna(0), period) / period
