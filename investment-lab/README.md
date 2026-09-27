# Investment Lab — Phase 1

Automated trading system, Phase 1: strategy + backtest. See [`PLAN.md`](./PLAN.md) for the full architecture, safety design, and approved decisions this build follows.

**Status:** paper/backtest only. No live account, no funding, no orders sent anywhere yet.

## What is here

| Path | What it does |
|---|---|
| `config.py` | Approved risk limits and strategy parameters (PLAN.md Section 4 & 5a) — the single place these numbers live |
| `strategy/indicators.py` | EMA and Wilder's ADX, implemented directly on pandas (no indicator-library dependency) |
| `strategy/ema_adx_strategy.py` | The `backtesting.py` Strategy: EMA 50/200 cross, gated by ADX(14) > 20 |
| `data/fetch_data.py` | Pulls historical bars for `AAPL` and `BTC/USD` from Alpaca via `alpaca-py` |
| `backtest/run_backtest.py` | Runs the strategy through `backtesting.py` on the fetched data and prints the stats |
| `tests/test_strategy.py` | Unit tests on synthetic data — proves the indicator math and the strategy/backtest wiring are correct, independent of any real market data |

## Setup

```bash
cd investment-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run the tests (no API key needed)

```bash
python3 -m pytest tests/ -v
```

All three currently pass against synthetic data.

## Run the real backtest (needs an Alpaca paper API key)

1. Create a free account at [alpaca.markets](https://alpaca.markets) and generate a **paper-mode** API key/secret pair.
2. Add `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` through this coding environment's own secrets settings (never in a file that gets committed, never in chat).
3. Fetch the data, then run the backtest:

```bash
python3 data/fetch_data.py
python3 backtest/run_backtest.py
```

This produces the actual Phase 1 result: whether the EMA/ADX strategy shows a positive or negative expectancy on `AAPL` and `BTC/USD` history. Either outcome is a valid Phase 1 result — the point of Phase 1 is proving the pipeline and getting a real number, not a specific number.
