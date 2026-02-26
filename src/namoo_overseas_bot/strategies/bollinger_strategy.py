from __future__ import annotations

import math
from collections import deque

from namoo_overseas_bot.models import Signal
from namoo_overseas_bot.strategies.base import BaseStrategy


class BollingerStrategy(BaseStrategy):
    """Bollinger Bands strategy.

    Upper Band = SMA + (std_dev * 표준편차)
    Lower Band = SMA - (std_dev * 표준편차)

    매수: 가격이 하단 밴드 아래로 떨어질 때 (과매도)
    매도: 가격이 상단 밴드 위로 올라갈 때 (과매수)
    """

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> None:
        if period < 2:
            raise ValueError("period must be >= 2")
        if std_dev <= 0:
            raise ValueError("std_dev must be positive")

        self.period = period
        self.std_dev = std_dev
        self._prices: deque[float] = deque(maxlen=period)
        self._last_signal = Signal.HOLD

    @property
    def name(self) -> str:
        return f"Bollinger({self.period},{self.std_dev})"

    def reset(self) -> None:
        self._prices.clear()
        self._last_signal = Signal.HOLD

    def on_price(self, price: float) -> Signal:
        self._prices.append(price)
        if len(self._prices) < self.period:
            return Signal.HOLD

        upper, middle, lower = self._calculate_bands()

        if price < lower and self._last_signal != Signal.BUY:
            self._last_signal = Signal.BUY
            return Signal.BUY
        if price > upper and self._last_signal != Signal.SELL:
            self._last_signal = Signal.SELL
            return Signal.SELL
        return Signal.HOLD

    def _calculate_bands(self) -> tuple[float, float, float]:
        prices = list(self._prices)
        sma = sum(prices) / len(prices)
        variance = sum((p - sma) ** 2 for p in prices) / len(prices)
        std = math.sqrt(variance)
        upper = sma + self.std_dev * std
        lower = sma - self.std_dev * std
        return upper, sma, lower

    def current_bands(self) -> tuple[float, float, float] | None:
        """Return (upper, middle, lower) or None if not enough data."""
        if len(self._prices) < self.period:
            return None
        return self._calculate_bands()
