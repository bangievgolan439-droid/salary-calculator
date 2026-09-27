"""Event-loop backtest engine.

Signals are computed from close prices then shifted one bar forward, so
a trade decided from bar N's close is executed at bar N+1's open - this
avoids the classic same-bar lookahead bug. Stop-loss / take-profit exits
are checked against the same bar's low/high, which is a standard
simplification for daily-bar backtests (it assumes the stop could have
been touched intraday on the bar it is opened or held on).
"""
from __future__ import annotations

import pandas as pd

from risk.risk_manager import RiskManager


def run_backtest(
    bars: pd.DataFrame,
    signals: pd.Series,
    risk_manager: RiskManager,
    initial_capital: float = 100_000.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    trade_signal = signals.shift(1).fillna(0).astype(int)

    cash = initial_capital
    shares = 0
    entry_price = stop_price = take_profit_price = None
    entry_date = None

    equity_rows = []
    trades = []

    for date, row in bars.iterrows():
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        sig = trade_signal.loc[date]

        if shares > 0:
            exit_price = exit_reason = None
            if risk_manager.stop_hit(l, stop_price):
                exit_price, exit_reason = stop_price, "stop_loss"
            elif risk_manager.take_profit_hit(h, take_profit_price):
                exit_price, exit_reason = take_profit_price, "take_profit"
            elif sig == 0:
                exit_price, exit_reason = o, "signal_exit"

            if exit_price is not None:
                cash += shares * exit_price
                trades.append(
                    {
                        "entry_date": entry_date,
                        "exit_date": date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": shares,
                        "pnl": (exit_price - entry_price) * shares,
                        "exit_reason": exit_reason,
                    }
                )
                shares = 0
                entry_price = stop_price = take_profit_price = entry_date = None

        if shares == 0 and sig == 1:
            sized = risk_manager.size_position(cash, o)
            cost = sized.shares * o
            if sized.shares > 0 and cost <= cash:
                shares = sized.shares
                entry_price = o
                stop_price = sized.stop_price
                take_profit_price = sized.take_profit_price
                entry_date = date
                cash -= cost

        equity_rows.append({"date": date, "equity": cash + shares * c, "cash": cash, "shares": shares})

    if shares > 0:
        last_date = bars.index[-1]
        last_close = bars.iloc[-1]["close"]
        cash += shares * last_close
        trades.append(
            {
                "entry_date": entry_date,
                "exit_date": last_date,
                "entry_price": entry_price,
                "exit_price": last_close,
                "shares": shares,
                "pnl": (last_close - entry_price) * shares,
                "exit_reason": "end_of_backtest",
            }
        )
        equity_rows[-1]["equity"] = cash
        equity_rows[-1]["cash"] = cash
        equity_rows[-1]["shares"] = 0

    equity_df = pd.DataFrame(equity_rows).set_index("date")
    trades_df = pd.DataFrame(trades)
    return equity_df, trades_df
