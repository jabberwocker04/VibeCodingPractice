from __future__ import annotations

from collections import deque

from namoo_overseas_bot.models import Signal
from namoo_overseas_bot.strategies.base import BaseStrategy


class RsiStrategy(BaseStrategy):
    """RSI (Relative Strength Index) strategy.

    매수: RSI < oversold_threshold (기본 30) - 과매도 구간
    매도: RSI > overbought_threshold (기본 70) - 과매수 구간
    """

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ) -> None:
        if period < 2:
            raise ValueError("period must be >= 2")
        if not (0 < oversold < overbought < 100):
            raise ValueError("oversold/overbought must satisfy 0 < oversold < overbought < 100")

        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self._prices: deque[float] = deque(maxlen=period + 1)
        self._last_signal = Signal.HOLD

    @property
    def name(self) -> str:
        return f"RSI({self.period})"

    def reset(self) -> None:
        self._prices.clear()
        self._last_signal = Signal.HOLD

    def on_price(self, price: float) -> Signal:
        self._prices.append(price)
        if len(self._prices) < self.period + 1:
            return Signal.HOLD

        rsi = self._calculate_rsi()
        if rsi is None:
            return Signal.HOLD

        if rsi < self.oversold and self._last_signal != Signal.BUY:
            self._last_signal = Signal.BUY
            return Signal.BUY
        if rsi > self.overbought and self._last_signal != Signal.SELL:
            self._last_signal = Signal.SELL
            return Signal.SELL
        return Signal.HOLD

    def _calculate_rsi(self) -> float | None:
        prices = list(self._prices)
        gains = []
        losses = []
        for i in range(1, len(prices)):
            delta = prices[i] - prices[i - 1]
            if delta > 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(delta))

        if not gains:
            return None

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def current_rsi(self) -> float | None:
        if len(self._prices) < self.period + 1:
            return None
        return self._calculate_rsi()
