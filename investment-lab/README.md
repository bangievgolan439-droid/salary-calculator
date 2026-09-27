# investment-lab

A small, self-contained backtesting scaffold: an SMA-crossover strategy,
a fixed-fractional-risk position sizer, and an event-loop backtest
engine, wired together behind `backtest/run_backtest.py`.

**This is a demo/starting scaffold, not a production trading system.**
It never places live or paper orders — it only reads historical price
data and simulates trades in memory.

## Setup

```bash
cd investment-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data source

By default there are no Alpaca credentials configured, so
`backtest/run_backtest.py` falls back to a deterministic **synthetic**
price series (clearly labeled in its output) so the pipeline is
runnable end-to-end without a brokerage account.

To backtest against real historical bars from Alpaca instead:

```bash
cp .env.example .env
# fill in ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY (a free paper-trading
# account's keys are enough — this project never submits orders)
```

## Running the backtest

```bash
python3 backtest/run_backtest.py
python3 backtest/run_backtest.py --symbol MSFT --start 2023-01-01 --end 2024-01-01 \
    --fast-window 10 --slow-window 30 --risk-per-trade 0.02
```

Output: a summary report on stdout, plus an equity curve and trade log
CSV under `backtest/output/`.

## Layout

- `strategy/moving_average_crossover.py` — signal generation (fast/slow SMA crossover).
- `risk/risk_manager.py` — position sizing (fixed-fractional risk) and stop-loss/take-profit levels.
- `data/loader.py` — historical bar loading (Alpaca, with synthetic fallback).
- `backtest/engine.py` — the simulation loop (signals are shifted one bar to avoid lookahead; entries/exits execute at the next bar's open).
- `backtest/metrics.py` — return, CAGR, Sharpe, max drawdown, win rate.
- `backtest/run_backtest.py` — CLI entrypoint.

## Known simplifications

- No commissions or slippage are modeled.
- Stop-loss/take-profit are checked against the same bar's low/high,
  including the bar a position is opened on — a standard daily-bar
  simplification, not exact intraday fill simulation.
- Long-only, single-symbol, one open position at a time.

None of the results this produces are investment advice or a
performance guarantee — treat it as a code scaffold to build a real
strategy and risk process on top of.
