from __future__ import annotations

from collections import defaultdict

from namoo_overseas_bot.brokers.base import BrokerClient
from namoo_overseas_bot.models import Fill, Order, Side


class PaperBroker(BrokerClient):
    def __init__(self, initial_cash_usd: float) -> None:
        self._cash = initial_cash_usd
        self._positions: dict[str, int] = defaultdict(int)

    def submit_order(self, order: Order, price: float, timestamp: str) -> Fill:
        notional = order.qty * price

        if order.side == Side.BUY:
            if notional > self._cash:
                raise ValueError(
                    f"insufficient cash: need {notional:.2f}, have {self._cash:.2f}"
                )
            self._cash -= notional
            self._positions[order.symbol] += order.qty
        elif order.side == Side.SELL:
            if self._positions[order.symbol] < order.qty:
                raise ValueError(
                    f"insufficient position: trying to sell {order.qty}, have {self._positions[order.symbol]}"
                )
            self._cash += notional
            self._positions[order.symbol] -= order.qty
        else:
            raise ValueError(f"unsupported side: {order.side}")

        return Fill(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=price,
            timestamp=timestamp,
        )

    def cash_balance(self) -> float:
        return self._cash

    def position_qty(self, symbol: str) -> int:
        return self._positions[symbol]
