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

    @abstractmethod
    def get_params(self) -> dict[str, object]:
        """Return current strategy parameters as a dict."""
        ...

    @abstractmethod
    def update_params(self, **kwargs: object) -> None:
        """Dynamically update strategy parameters and reset internal state.

        Raises ValueError for invalid parameter values.
        Unknown keys are silently ignored.
        """
        ...
