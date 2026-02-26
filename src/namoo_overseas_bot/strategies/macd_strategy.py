from __future__ import annotations

from collections import deque

from namoo_overseas_bot.models import Signal
from namoo_overseas_bot.strategies.base import BaseStrategy


class MacdStrategy(BaseStrategy):
    """MACD (Moving Average Convergence Divergence) strategy.

    MACD = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD, signal_period)

    매수: MACD가 Signal Line을 상향 돌파 (골든 크로스)
    매도: MACD가 Signal Line을 하향 돌파 (데드 크로스)
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> None:
        if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
            raise ValueError("all periods must be positive")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

        self._prices: deque[float] = deque()
        self._macd_history: deque[float] = deque(maxlen=signal_period)
        self._ema_fast: float | None = None
        self._ema_slow: float | None = None
        self._ema_signal: float | None = None
        self._prev_macd: float | None = None
        self._prev_signal: float | None = None
        self._last_signal = Signal.HOLD
        self._price_count = 0

    @property
    def name(self) -> str:
        return f"MACD({self.fast_period},{self.slow_period},{self.signal_period})"

    def reset(self) -> None:
        self._prices.clear()
        self._macd_history.clear()
        self._ema_fast = None
        self._ema_slow = None
        self._ema_signal = None
        self._prev_macd = None
        self._prev_signal = None
        self._last_signal = Signal.HOLD
        self._price_count = 0

    def on_price(self, price: float) -> Signal:
        self._price_count += 1

        k_fast = 2.0 / (self.fast_period + 1)
        k_slow = 2.0 / (self.slow_period + 1)
        k_signal = 2.0 / (self.signal_period + 1)

        if self._ema_fast is None:
            self._ema_fast = price
        else:
            self._ema_fast = price * k_fast + self._ema_fast * (1 - k_fast)

        if self._ema_slow is None:
            self._ema_slow = price
        else:
            self._ema_slow = price * k_slow + self._ema_slow * (1 - k_slow)

        if self._price_count < self.slow_period:
            return Signal.HOLD

        macd_value = self._ema_fast - self._ema_slow  # type: ignore[operator]

        if self._ema_signal is None:
            self._ema_signal = macd_value
        else:
            self._ema_signal = macd_value * k_signal + self._ema_signal * (1 - k_signal)

        if self._price_count < self.slow_period + self.signal_period:
            self._prev_macd = macd_value
            self._prev_signal = self._ema_signal
            return Signal.HOLD

        signal = Signal.HOLD
        if (
            self._prev_macd is not None
            and self._prev_signal is not None
            and self._prev_macd <= self._prev_signal
            and macd_value > self._ema_signal
            and self._last_signal != Signal.BUY
        ):
            signal = Signal.BUY
            self._last_signal = Signal.BUY
        elif (
            self._prev_macd is not None
            and self._prev_signal is not None
            and self._prev_macd >= self._prev_signal
            and macd_value < self._ema_signal
            and self._last_signal != Signal.SELL
        ):
            signal = Signal.SELL
            self._last_signal = Signal.SELL

        self._prev_macd = macd_value
        self._prev_signal = self._ema_signal
        return signal

    def current_macd(self) -> tuple[float | None, float | None]:
        """Return (macd_value, signal_line) or (None, None) if not ready."""
        if self._ema_fast is None or self._ema_slow is None:
            return None, None
        macd_value = self._ema_fast - self._ema_slow
        return macd_value, self._ema_signal
