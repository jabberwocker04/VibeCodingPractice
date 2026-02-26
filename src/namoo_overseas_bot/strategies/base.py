from __future__ import annotations

from abc import ABC, abstractmethod

from namoo_overseas_bot.models import Signal


class BaseStrategy(ABC):
    """All trading strategies must implement this interface."""

    @abstractmethod
    def on_price(self, price: float) -> Signal:
        """Process a new price and return a trading signal."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state (e.g. when switching symbols)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        ...
