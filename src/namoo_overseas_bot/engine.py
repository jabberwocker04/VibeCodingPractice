from __future__ import annotations

from dataclasses import dataclass

from namoo_overseas_bot.brokers.base import BrokerClient
from namoo_overseas_bot.models import Candle, Order, Side, Signal
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


@dataclass
class EngineResult:
    trades: int
    cash: float
    position_qty: int
    last_price: float
    equity: float


class TradingEngine:
    def __init__(
        self,
        *,
        broker: BrokerClient,
        strategy: SmaCrossStrategy,
        symbol: str,
        quantity: int,
    ) -> None:
        self.broker = broker
        self.strategy = strategy
        self.symbol = symbol
        self.quantity = quantity

    def run(self, candles: list[Candle]) -> EngineResult:
        trades = 0
        last_price = 0.0

        for candle in candles:
            last_price = candle.close
            signal = self.strategy.on_price(candle.close)

            if signal == Signal.BUY:
                self.broker.submit_order(
                    Order(symbol=self.symbol, side=Side.BUY, qty=self.quantity),
                    price=candle.close,
                    timestamp=candle.timestamp,
                )
                trades += 1

            if signal == Signal.SELL and self.broker.position_qty(self.symbol) >= self.quantity:
                self.broker.submit_order(
                    Order(symbol=self.symbol, side=Side.SELL, qty=self.quantity),
                    price=candle.close,
                    timestamp=candle.timestamp,
                )
                trades += 1

        position_qty = self.broker.position_qty(self.symbol)
        cash = self.broker.cash_balance()
        equity = cash + position_qty * last_price
        return EngineResult(
            trades=trades,
            cash=cash,
            position_qty=position_qty,
            last_price=last_price,
            equity=equity,
        )
