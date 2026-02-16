from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import threading
import time

from namoo_overseas_bot.brokers.base import BrokerClient
from namoo_overseas_bot.models import Candle, Order, Side, Signal
from namoo_overseas_bot.notifiers.base import NotifierClient
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


@dataclass
class RuntimeStatus:
    running: bool
    paused: bool
    symbol: str
    trades: int
    cash: float
    position_qty: int
    last_price: float
    equity: float
    last_signal: str
    last_candle_timestamp: str
    loop_count: int
    started_at_utc: str
    last_error: str


class PaperTradingBot:
    def __init__(
        self,
        *,
        broker: BrokerClient,
        strategy: SmaCrossStrategy,
        notifier: NotifierClient,
        symbol: str,
        quantity: int,
        candles: list[Candle],
        tick_seconds: float,
        max_position_qty: int,
    ) -> None:
        if not candles:
            raise ValueError("candles must not be empty")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if tick_seconds <= 0:
            raise ValueError("tick_seconds must be positive")
        if max_position_qty < quantity:
            raise ValueError("max_position_qty must be >= quantity")

        self.broker = broker
        self.strategy = strategy
        self.notifier = notifier
        self.symbol = symbol
        self.quantity = quantity
        self.candles = candles
        self.tick_seconds = tick_seconds
        self.max_position_qty = max_position_qty

        self._status = RuntimeStatus(
            running=False,
            paused=False,
            symbol=symbol,
            trades=0,
            cash=broker.cash_balance(),
            position_qty=broker.position_qty(symbol),
            last_price=0.0,
            equity=broker.cash_balance(),
            last_signal=Signal.HOLD.value,
            last_candle_timestamp="",
            loop_count=0,
            started_at_utc="",
            last_error="",
        )

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._cursor = 0

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._status.running = True
            self._status.paused = False
            self._status.started_at_utc = datetime.now(timezone.utc).isoformat()
            self._status.last_error = ""
            self._thread = threading.Thread(target=self._run_loop, name="paper-trading-bot", daemon=True)
            self._thread.start()

        self._safe_notify(
            f"[START] {self.symbol} paper bot started | qty={self.quantity}, tick={self.tick_seconds}s"
        )

    def pause(self) -> None:
        with self._lock:
            self._status.paused = True
        self._safe_notify(f"[PAUSE] {self.symbol} bot paused")

    def resume(self) -> None:
        with self._lock:
            self._status.paused = False
        self._safe_notify(f"[RESUME] {self.symbol} bot resumed")

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            self._status.running = False
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=5)
        self._safe_notify(f"[STOP] {self.symbol} bot stopped")

    def process_next_candle(self) -> None:
        candle = self.candles[self._cursor % len(self.candles)]
        self._cursor += 1

        signal = self.strategy.on_price(candle.close)
        fill_message = ""

        if signal == Signal.BUY:
            current_pos = self.broker.position_qty(self.symbol)
            if current_pos + self.quantity <= self.max_position_qty:
                fill = self.broker.submit_order(
                    Order(symbol=self.symbol, side=Side.BUY, qty=self.quantity),
                    price=candle.close,
                    timestamp=candle.timestamp,
                )
                fill_message = f"[FILL] BUY {fill.qty} {fill.symbol} @ {fill.price:.2f}"
                with self._lock:
                    self._status.trades += 1
            else:
                fill_message = (
                    f"[SKIP] BUY blocked by max_position_qty={self.max_position_qty} "
                    f"(current={current_pos})"
                )

        if signal == Signal.SELL and self.broker.position_qty(self.symbol) >= self.quantity:
            fill = self.broker.submit_order(
                Order(symbol=self.symbol, side=Side.SELL, qty=self.quantity),
                price=candle.close,
                timestamp=candle.timestamp,
            )
            fill_message = f"[FILL] SELL {fill.qty} {fill.symbol} @ {fill.price:.2f}"
            with self._lock:
                self._status.trades += 1

        cash = self.broker.cash_balance()
        position_qty = self.broker.position_qty(self.symbol)
        equity = cash + position_qty * candle.close

        with self._lock:
            self._status.last_signal = signal.value
            self._status.last_candle_timestamp = candle.timestamp
            self._status.last_price = candle.close
            self._status.cash = cash
            self._status.position_qty = position_qty
            self._status.equity = equity
            self._status.loop_count += 1

        if signal != Signal.HOLD:
            self._safe_notify(
                f"[SIGNAL] {self.symbol} {signal.value.upper()} | price={candle.close:.2f} | ts={candle.timestamp}"
            )
        if fill_message:
            self._safe_notify(fill_message)

    def status(self) -> dict[str, object]:
        with self._lock:
            return asdict(self._status)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self._is_paused():
                    time.sleep(0.2)
                    continue
                self.process_next_candle()
            except Exception as exc:  # pragma: no cover - defensive runtime path
                with self._lock:
                    self._status.last_error = str(exc)
                self._safe_notify(f"[ERROR] runtime exception: {exc}")
            time.sleep(self.tick_seconds)

    def _is_paused(self) -> bool:
        with self._lock:
            return self._status.paused

    def _safe_notify(self, message: str) -> None:
        try:
            self.notifier.send(message)
        except Exception:
            # Notifications should never crash trading runtime.
            return
