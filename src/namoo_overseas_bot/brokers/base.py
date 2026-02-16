from __future__ import annotations

from abc import ABC, abstractmethod

from namoo_overseas_bot.models import Fill, Order


class BrokerClient(ABC):
    @abstractmethod
    def submit_order(self, order: Order, price: float, timestamp: str) -> Fill:
        raise NotImplementedError

    @abstractmethod
    def cash_balance(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def position_qty(self, symbol: str) -> int:
        raise NotImplementedError
