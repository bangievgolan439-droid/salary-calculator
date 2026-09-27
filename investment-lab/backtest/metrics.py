"""Standard backtest performance metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_metrics(
    equity_df: pd.DataFrame, trades_df: pd.DataFrame, initial_capital: float, periods_per_year: int = 252
) -> dict:
    equity = equity_df["equity"]
    final_equity = float(equity.iloc[-1])
    total_return = final_equity / initial_capital - 1

    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25
    cagr = (final_equity / initial_capital) ** (1 / years) - 1 if years > 0 else float("nan")

    daily_returns = equity.pct_change().dropna()
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(periods_per_year)
    else:
        sharpe = float("nan")

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = float(drawdown.min())

    num_trades = len(trades_df)
    if num_trades > 0:
        win_rate = float((trades_df["pnl"] > 0).mean())
        avg_pnl = float(trades_df["pnl"].mean())
    else:
        win_rate = float("nan")
        avg_pnl = float("nan")

    return {
        "final_equity": final_equity,
        "total_return": total_return,
        "cagr": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "num_trades": num_trades,
        "win_rate": win_rate,
        "avg_trade_pnl": avg_pnl,
    }
