from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import threading
import time

from namoo_overseas_bot.brokers.base import BrokerClient
from namoo_overseas_bot.market_data.yfinance_feed import fetch_candles, fetch_latest_price
from namoo_overseas_bot.models import Order, Side, Signal
from namoo_overseas_bot.notifiers.base import NotifierClient
from namoo_overseas_bot.strategies.base import BaseStrategy


@dataclass
class LiveBotStatus:
    running: bool
    paused: bool
    symbol: str
    company_name: str
    strategy: str
    interval: str
    trades: int
    cash: float
    position_qty: int
    last_price: float
    equity: float
    pnl: float
    pnl_pct: float
    last_signal: str
    last_tick_at: str
    loop_count: int
    started_at_utc: str
    last_error: str


class LiveTradingBot:
    """야후 파이낸스 실시간 데이터를 사용하는 자동매매 봇.

    지정된 티커 심볼에 대해 설정된 전략으로 자동매매를 수행합니다.
    실제 주문은 PaperBroker를 통해 시뮬레이션됩니다.
    """

    def __init__(
        self,
        *,
        broker: BrokerClient,
        strategy: BaseStrategy,
        notifier: NotifierClient,
        symbol: str,
        company_name: str = "",
        quantity: int,
        interval: str = "1d",
        history_period: str = "6mo",
        tick_seconds: float = 60.0,
        max_position_qty: int = 10,
    ) -> None:
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
        self.company_name = company_name or symbol
        self.quantity = quantity
        self.interval = interval
        self.history_period = history_period
        self.tick_seconds = tick_seconds
        self.max_position_qty = max_position_qty

        self._initial_cash = broker.cash_balance()
        self._status = LiveBotStatus(
            running=False,
            paused=False,
            symbol=symbol,
            company_name=self.company_name,
            strategy=strategy.name,
            interval=interval,
            trades=0,
            cash=broker.cash_balance(),
            position_qty=broker.position_qty(symbol),
            last_price=0.0,
            equity=broker.cash_balance(),
            pnl=0.0,
            pnl_pct=0.0,
            last_signal=Signal.HOLD.value,
            last_tick_at="",
            loop_count=0,
            started_at_utc="",
            last_error="",
        )

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._status.running = True
            self._status.paused = False
            self._status.started_at_utc = datetime.now(timezone.utc).isoformat()
            self._status.last_error = ""
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"live-bot-{self.symbol}",
                daemon=True,
            )
            self._thread.start()

        self._safe_notify(
            f"[시작] {self.company_name}({self.symbol}) 자동매매 시작\n"
            f"전략: {self.strategy.name} | 주기: {self.interval} | 수량: {self.quantity}주\n"
            f"초기자금: ${self._initial_cash:,.2f}"
        )

    def pause(self) -> None:
        with self._lock:
            self._status.paused = True
        self._safe_notify(f"[일시정지] {self.symbol} 봇 일시정지")

    def resume(self) -> None:
        with self._lock:
            self._status.paused = False
        self._safe_notify(f"[재개] {self.symbol} 봇 재개")

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            self._status.running = False
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=10)

        with self._lock:
            pnl = self._status.pnl
            pnl_pct = self._status.pnl_pct
            trades = self._status.trades
            equity = self._status.equity

        self._safe_notify(
            f"[중지] {self.symbol} 봇 중지\n"
            f"총 거래: {trades}회 | 최종 자산: ${equity:,.2f}\n"
            f"손익: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
        )

    def status(self) -> dict[str, object]:
        with self._lock:
            return asdict(self._status)

    def _run_loop(self) -> None:
        """메인 트레이딩 루프 - 히스토리 데이터로 전략 워밍업 후 실시간 틱 처리."""
        # 히스토리 데이터로 전략 상태 초기화 (워밍업)
        self._warmup_strategy()

        while not self._stop_event.is_set():
            try:
                if self._is_paused():
                    time.sleep(1.0)
                    continue
                self._process_tick()
            except Exception as exc:
                with self._lock:
                    self._status.last_error = str(exc)
                self._safe_notify(f"[오류] {self.symbol} 런타임 오류: {exc}")

            self._stop_event.wait(self.tick_seconds)

    def _warmup_strategy(self) -> None:
        """과거 데이터로 전략을 워밍업합니다."""
        try:
            candles = fetch_candles(
                self.symbol,
                interval=self.interval,
                period=self.history_period,
            )
            # 마지막 캔들은 실제 틱 처리에서 사용하므로 제외
            for candle in candles[:-1]:
                self.strategy.on_price(candle.close)
            self._safe_notify(
                f"[준비완료] {self.symbol} 전략 워밍업 완료 ({len(candles)}개 캔들)"
            )
        except Exception as exc:
            self._safe_notify(f"[경고] 워밍업 실패: {exc} | 실시간 데이터만 사용합니다.")

    def _process_tick(self) -> None:
        """현재 시장 가격을 가져와 전략 신호를 처리합니다."""
        price, timestamp = fetch_latest_price(self.symbol)

        signal = self.strategy.on_price(price)
        fill_message = ""
        now = datetime.now(timezone.utc).isoformat()

        if signal == Signal.BUY:
            current_pos = self.broker.position_qty(self.symbol)
            if current_pos + self.quantity <= self.max_position_qty:
                try:
                    fill = self.broker.submit_order(
                        Order(symbol=self.symbol, side=Side.BUY, qty=self.quantity),
                        price=price,
                        timestamp=timestamp,
                    )
                    fill_message = (
                        f"[체결] 매수 {fill.qty}주 {fill.symbol} @ ${fill.price:,.2f}"
                    )
                    with self._lock:
                        self._status.trades += 1
                except ValueError as e:
                    fill_message = f"[건너뜀] 매수 실패: {e}"
            else:
                fill_message = (
                    f"[건너뜀] 최대 보유 수량 초과 "
                    f"(현재={current_pos}, 최대={self.max_position_qty})"
                )

        elif signal == Signal.SELL:
            current_pos = self.broker.position_qty(self.symbol)
            if current_pos >= self.quantity:
                try:
                    fill = self.broker.submit_order(
                        Order(symbol=self.symbol, side=Side.SELL, qty=self.quantity),
                        price=price,
                        timestamp=timestamp,
                    )
                    fill_message = (
                        f"[체결] 매도 {fill.qty}주 {fill.symbol} @ ${fill.price:,.2f}"
                    )
                    with self._lock:
                        self._status.trades += 1
                except ValueError as e:
                    fill_message = f"[건너뜀] 매도 실패: {e}"

        cash = self.broker.cash_balance()
        position_qty = self.broker.position_qty(self.symbol)
        equity = cash + position_qty * price
        pnl = equity - self._initial_cash
        pnl_pct = (pnl / self._initial_cash) * 100 if self._initial_cash > 0 else 0.0

        with self._lock:
            self._status.last_signal = signal.value
            self._status.last_tick_at = now
            self._status.last_price = price
            self._status.cash = cash
            self._status.position_qty = position_qty
            self._status.equity = equity
            self._status.pnl = pnl
            self._status.pnl_pct = pnl_pct
            self._status.loop_count += 1

        if signal != Signal.HOLD:
            self._safe_notify(
                f"[신호] {self.company_name}({self.symbol}) {self._signal_to_korean(signal)}\n"
                f"전략: {self.strategy.name} | 가격: ${price:,.2f}\n"
                f"자산: ${equity:,.2f} | 손익: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
            )
        if fill_message:
            self._safe_notify(fill_message)

    def _is_paused(self) -> bool:
        with self._lock:
            return self._status.paused

    def _safe_notify(self, message: str) -> None:
        try:
            self.notifier.send(message)
        except Exception:
            pass

    @staticmethod
    def _signal_to_korean(signal: Signal) -> str:
        mapping = {Signal.BUY: "매수", Signal.SELL: "매도", Signal.HOLD: "대기"}
        return mapping.get(signal, "대기")
