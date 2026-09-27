#!/usr/bin/env python3
"""CLI entrypoint: run the SMA-crossover strategy through the backtest engine.

Usage (from the investment-lab/ directory):
    python3 backtest/run_backtest.py
    python3 backtest/run_backtest.py --symbol MSFT --start 2023-01-01 --end 2024-01-01

This only reads historical price data (real, via Alpaca, if
ALPACA_API_KEY_ID/ALPACA_API_SECRET_KEY are set - otherwise a
clearly-labeled synthetic series) and simulates trades in memory. It
never places a real or paper order.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.engine import run_backtest  # noqa: E402
from backtest.metrics import compute_metrics  # noqa: E402
from data.loader import load_bars  # noqa: E402
from risk.risk_manager import RiskManager  # noqa: E402
from strategy.moving_average_crossover import MovingAverageCrossoverStrategy  # noqa: E402


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the SMA-crossover backtest.")
    p.add_argument("--symbol", default="AAPL")
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--end", default="2024-01-01")
    p.add_argument("--initial-capital", type=float, default=100_000.0)
    p.add_argument("--fast-window", type=int, default=20)
    p.add_argument("--slow-window", type=int, default=50)
    p.add_argument("--risk-per-trade", type=float, default=0.01)
    p.add_argument("--stop-loss-pct", type=float, default=0.05)
    p.add_argument("--take-profit-pct", type=float, default=0.15)
    p.add_argument("--max-position-pct", type=float, default=0.25)
    p.add_argument("--output-dir", default=str(ROOT / "backtest" / "output"))
    return p.parse_args()


def main() -> None:
    load_dotenv(ROOT / ".env")
    args = parse_args()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)

    bars, source = load_bars(args.symbol, start, end)
    print(f"Loaded {len(bars)} daily bars for {args.symbol} from {source} data source "
          f"({'REAL Alpaca historical data' if source == 'alpaca' else 'SYNTHETIC demo data - not real prices'}).")

    strategy = MovingAverageCrossoverStrategy(fast_window=args.fast_window, slow_window=args.slow_window)
    signals = strategy.generate_signals(bars)

    risk_manager = RiskManager(
        risk_per_trade=args.risk_per_trade,
        stop_loss_pct=args.stop_loss_pct,
        take_profit_pct=args.take_profit_pct,
        max_position_pct=args.max_position_pct,
    )

    equity_df, trades_df = run_backtest(bars, signals, risk_manager, initial_capital=args.initial_capital)
    metrics = compute_metrics(equity_df, trades_df, args.initial_capital)

    safe_symbol = args.symbol.replace("/", "-")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    equity_path = output_dir / f"{safe_symbol}_equity_curve.csv"
    trades_path = output_dir / f"{safe_symbol}_trades.csv"
    equity_df.to_csv(equity_path)
    trades_df.to_csv(trades_path, index=False)

    print()
    print(f"=== Backtest report: {args.symbol}  ({args.start} -> {args.end}) ===")
    print(f"Strategy: SMA({args.fast_window}/{args.slow_window}) crossover, long-only")
    print(f"Risk:     {args.risk_per_trade:.1%} risk/trade, {args.stop_loss_pct:.1%} stop-loss, "
          f"{args.take_profit_pct:.1%} take-profit, {args.max_position_pct:.1%} max position size")
    print(f"Initial capital: ${args.initial_capital:,.2f}")
    print(f"Final equity:    ${metrics['final_equity']:,.2f}")
    print(f"Total return:    {metrics['total_return']:.2%}")
    print(f"CAGR:            {metrics['cagr']:.2%}")
    print(f"Sharpe ratio:    {metrics['sharpe_ratio']:.2f}")
    print(f"Max drawdown:    {metrics['max_drawdown']:.2%}")
    print(f"Trades:          {metrics['num_trades']}  (win rate {metrics['win_rate']:.1%})"
          if metrics["num_trades"] else "Trades:          0")
    print()
    print(f"Equity curve written to {equity_path}")
    print(f"Trade log written to    {trades_path}")

    if source == "synthetic":
        print()
        print("NOTE: this run used synthetic demo data, not real market history -")
        print("the metrics above say nothing about how this strategy would have")
        print("performed on actual markets. Set ALPACA_API_KEY_ID/ALPACA_API_SECRET_KEY")
        print("(see .env.example) to backtest against real historical bars.")


if __name__ == "__main__":
    main()
