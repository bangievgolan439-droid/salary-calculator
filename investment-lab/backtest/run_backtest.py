import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backtesting import Backtest

import config
from strategy.ema_adx_strategy import EmaAdxCrossStrategy

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True)


def run(label: str, csv_path: str):
    data = load_csv(csv_path)
    bt = Backtest(data, EmaAdxCrossStrategy, cash=10_000, commission=0.001)
    stats = bt.run()
    print(f"\n=== {label} ===")
    print(stats)
    return stats


if __name__ == "__main__":
    run(config.TEST_STOCK_SYMBOL, os.path.join(DATA_DIR, "aapl_4h.csv"))
    run(config.TEST_CRYPTO_SYMBOL, os.path.join(DATA_DIR, "btcusd_4h.csv"))
