"""Position sizing and stop-loss rules for the backtest engine.

Uses fixed-fractional risk sizing: each new position risks at most
`risk_per_trade` of current equity, sized so that a hit on the stop-loss
loses roughly that amount, subject to a hard cap on how much of the
portfolio a single position may consume.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SizedPosition:
    shares: int
    stop_price: float
    take_profit_price: float


class RiskManager:
    def __init__(
        self,
        risk_per_trade: float = 0.01,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15,
        max_position_pct: float = 0.25,
    ):
        if not 0 < risk_per_trade < 1:
            raise ValueError("risk_per_trade must be between 0 and 1")
        if not 0 < stop_loss_pct < 1:
            raise ValueError("stop_loss_pct must be between 0 and 1")
        if not 0 < max_position_pct <= 1:
            raise ValueError("max_position_pct must be between 0 and 1")
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_pct = max_position_pct

    def size_position(self, equity: float, entry_price: float) -> SizedPosition:
        stop_price = entry_price * (1 - self.stop_loss_pct)
        take_profit_price = entry_price * (1 + self.take_profit_pct)

        risk_amount = equity * self.risk_per_trade
        stop_distance = entry_price - stop_price
        shares_by_risk = risk_amount / stop_distance if stop_distance > 0 else 0

        cap_amount = equity * self.max_position_pct
        shares_by_cap = cap_amount / entry_price if entry_price > 0 else 0

        shares = math.floor(min(shares_by_risk, shares_by_cap))
        return SizedPosition(shares=max(shares, 0), stop_price=stop_price, take_profit_price=take_profit_price)

    def stop_hit(self, low_price: float, stop_price: float) -> bool:
        return low_price <= stop_price

    def take_profit_hit(self, high_price: float, take_profit_price: float) -> bool:
        return high_price >= take_profit_price
