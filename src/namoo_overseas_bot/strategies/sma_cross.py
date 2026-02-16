from __future__ import annotations

from collections import deque

from namoo_overseas_bot.models import Signal


class SmaCrossStrategy:
    def __init__(self, short_window: int, long_window: int) -> None:
        if short_window <= 0 or long_window <= 0:
            raise ValueError("window sizes must be positive")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")

        self.short_window = short_window
        self.long_window = long_window
        self._prices = deque(maxlen=long_window)
        self._last_signal = Signal.HOLD

    def on_price(self, price: float) -> Signal:
        self._prices.append(price)
        if len(self._prices) < self.long_window:
            return Signal.HOLD

        prices = list(self._prices)
        short_sma = sum(prices[-self.short_window :]) / self.short_window
        long_sma = sum(prices) / self.long_window

        if short_sma > long_sma and self._last_signal != Signal.BUY:
            self._last_signal = Signal.BUY
            return Signal.BUY
        if short_sma < long_sma and self._last_signal != Signal.SELL:
            self._last_signal = Signal.SELL
            return Signal.SELL
        return Signal.HOLD
