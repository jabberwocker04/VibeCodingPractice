from __future__ import annotations

import json
import threading
import time
import urllib.parse
import urllib.request

from namoo_overseas_bot.notifiers.base import NotifierClient
from namoo_overseas_bot.runtime.paper_bot import PaperTradingBot


class TelegramCommandHandler:
    def __init__(self, *, bot: PaperTradingBot) -> None:
        self.bot = bot

    def handle(self, text: str) -> str:
        cmd = text.strip().split()[0].lower() if text.strip() else ""

        if cmd in {"/help", "help", "/명령어", "명령어"}:
            return self._help_message()

        if cmd == "/status":
            s = self.bot.status()
            return (
                f"[상태] {s['symbol']} | running={s['running']} paused={s['paused']}\n"
                f"trades={s['trades']} position={s['position_qty']} cash={s['cash']:.2f} equity={s['equity']:.2f}\n"
                f"last_signal={s['last_signal']} price={s['last_price']:.2f} ts={s['last_candle_timestamp']}"
            )

        if cmd == "/pause":
            self.bot.pause()
            return "[명령] 일시정지 요청 완료"

        if cmd == "/resume":
            self.bot.resume()
            return "[명령] 재개 요청 완료"

        if cmd == "/stop":
            self.bot.stop()
            return "[명령] 중지 요청 완료"

        return "[안내] 지원하지 않는 명령입니다. /help 또는 /명령어 를 입력하세요."

    @staticmethod
    def _help_message() -> str:
        return (
            "[명령어]\n"
            "/help - 명령어 목록\n"
            "/명령어 - 명령어 목록(한글)\n"
            "/status - 현재 상태 조회\n"
            "/pause - 매매 루프 일시정지\n"
            "/resume - 매매 루프 재개\n"
            "/stop - 매매 루프 중지"
        )


class TelegramCommandPoller:
    def __init__(
        self,
        *,
        bot_token: str,
        allowed_chat_id: str,
        notifier: NotifierClient,
        handler: TelegramCommandHandler,
        poll_seconds: float = 1.0,
        commands_enabled: bool = True,
    ) -> None:
        self.bot_token = bot_token
        self.allowed_chat_id = str(allowed_chat_id)
        self.notifier = notifier
        self.handler = handler
        self.poll_seconds = poll_seconds
        self._commands_enabled = commands_enabled

        self._offset = 0
        self._enabled_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def is_commands_enabled(self) -> bool:
        with self._enabled_lock:
            return self._commands_enabled

    def set_commands_enabled(self, enabled: bool) -> None:
        with self._enabled_lock:
            self._commands_enabled = enabled

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="telegram-command-poller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                updates = self._get_updates(offset=self._offset, timeout=20)
                for upd in updates:
                    self._offset = int(upd.get("update_id", 0)) + 1
                    message = upd.get("message") or upd.get("edited_message")
                    if not isinstance(message, dict):
                        continue

                    chat = message.get("chat", {})
                    chat_id = str(chat.get("id", ""))
                    if self.allowed_chat_id and chat_id != self.allowed_chat_id:
                        continue

                    text = str(message.get("text", "")).strip()
                    if not text.startswith("/"):
                        continue

                    if not self.is_commands_enabled():
                        continue

                    response = self.handler.handle(text)
                    if response:
                        self.notifier.send(response)

            except Exception:
                # Command polling failures should not break trading runtime.
                time.sleep(self.poll_seconds)
                continue

            time.sleep(self.poll_seconds)

    def _get_updates(self, *, offset: int, timeout: int) -> list[dict[str, object]]:
        query = urllib.parse.urlencode({"offset": offset, "timeout": timeout})
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?{query}"

        with urllib.request.urlopen(url, timeout=timeout + 10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not payload.get("ok"):
            return []
        results = payload.get("result", [])
        if not isinstance(results, list):
            return []
        return [r for r in results if isinstance(r, dict)]


# ------------------------------------------------------------------ #
# LiveBotCommandHandler - LiveTradingBot용 텔레그램 명령어 처리기
# ------------------------------------------------------------------ #

class LiveBotCommandHandler:
    """LiveTradingBot용 텔레그램 명령어 처리기.

    /help, /status, /pause, /resume, /stop,
    /strategy [name], /params [k=v], /config [k=v]
    """

    def __init__(self, *, bot: "LiveTradingBot") -> None:  # type: ignore[name-defined]
        self.bot = bot

    def handle(self, text: str) -> str:
        parts = text.strip().split()
        if not parts:
            return ""
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in {"/help", "/명령어", "help", "명령어"}:
            return self._help_message()
        if cmd == "/status":
            return self._status_message()
        if cmd == "/pause":
            self.bot.pause()
            return "[명령] 일시정지 완료"
        if cmd == "/resume":
            self.bot.resume()
            return "[명령] 재개 완료"
        if cmd == "/stop":
            self.bot.stop()
            return "[명령] 중지 완료"
        if cmd == "/strategy":
            return self._handle_strategy(args)
        if cmd == "/params":
            return self._handle_params(args)
        if cmd == "/config":
            return self._handle_config(args)
        return "[안내] 지원하지 않는 명령입니다. /help 를 입력하세요."

    def _status_message(self) -> str:
        s = self.bot.status()
        pnl_sign = "+" if float(str(s.get("pnl", 0))) >= 0 else ""
        return (
            f"[상태] {s.get('company_name')}({s.get('symbol')})\n"
            f"전략: {s.get('strategy')} | running={s.get('running')} paused={s.get('paused')}\n"
            f"가격: ${float(str(s.get('last_price', 0))):,.2f} | 신호: {s.get('last_signal')}\n"
            f"자산: ${float(str(s.get('equity', 0))):,.2f} | "
            f"손익: {pnl_sign}${float(str(s.get('pnl', 0))):,.2f} "
            f"({pnl_sign}{float(str(s.get('pnl_pct', 0))):.2f}%)\n"
            f"현금: ${float(str(s.get('cash', 0))):,.2f} | "
            f"보유: {s.get('position_qty')}주 | 거래: {s.get('trades')}회"
        )

    def _handle_strategy(self, args: list[str]) -> str:
        if not args:
            info = self.bot.get_strategy_info()
            return f"[전략] 현재: {info['name']}\n파라미터: {info['params']}"
        from namoo_overseas_bot.strategies import build_strategy, STRATEGY_NAMES
        name = args[0].lower()
        if name not in STRATEGY_NAMES:
            return f"[오류] 알 수 없는 전략: {name}\n사용 가능: {', '.join(STRATEGY_NAMES)}"
        try:
            new_strat = build_strategy(name)
            self.bot.swap_strategy(new_strat)
            info = self.bot.get_strategy_info()
            return f"[전략교체] {info['name']}으로 교체 완료\n파라미터: {info['params']}"
        except Exception as e:
            return f"[오류] 전략 교체 실패: {e}"

    def _handle_params(self, args: list[str]) -> str:
        if not args:
            info = self.bot.get_strategy_info()
            params = info["params"]
            lines = "\n".join(f"  {k} = {v}" for k, v in params.items())  # type: ignore[union-attr]
            return f"[파라미터] {info['name']}\n{lines}"
        kwargs: dict[str, object] = {}
        for arg in args:
            if "=" not in arg:
                continue
            k, v = arg.split("=", 1)
            try:
                kwargs[k.strip()] = float(v.strip()) if "." in v else int(v.strip())
            except ValueError:
                kwargs[k.strip()] = v.strip()
        if not kwargs:
            return "[오류] 파라미터 형식: /params key=value key2=value2"
        try:
            self.bot.update_strategy_params(**kwargs)
            info = self.bot.get_strategy_info()
            return f"[파라미터수정] {info['name']}\n새 파라미터: {info['params']}"
        except Exception as e:
            return f"[오류] 파라미터 수정 실패: {e}"

    def _handle_config(self, args: list[str]) -> str:
        if not args:
            cfg = self.bot.get_trading_config()
            return (
                f"[설정] 수량={cfg['quantity']}주 | 최대={cfg['max_position_qty']}주\n"
                f"틱={cfg['tick_seconds']}초 | 주기={cfg['interval']} | 기간={cfg['history_period']}"
            )
        kwargs: dict[str, object] = {}
        for arg in args:
            if "=" not in arg:
                continue
            k, v = arg.split("=", 1)
            kwargs[k.strip()] = v.strip()
        allowed = {"quantity", "max_position_qty", "tick_seconds"}
        filtered = {k: v for k, v in kwargs.items() if k in allowed}
        if not filtered:
            return f"[오류] 수정 가능한 설정: {', '.join(allowed)}"
        try:
            self.bot.update_trading_config(
                quantity=int(filtered["quantity"]) if "quantity" in filtered else None,
                max_position_qty=int(filtered["max_position_qty"]) if "max_position_qty" in filtered else None,
                tick_seconds=float(filtered["tick_seconds"]) if "tick_seconds" in filtered else None,
            )
            cfg = self.bot.get_trading_config()
            return (
                f"[설정변경] 수량={cfg['quantity']}주 | 최대={cfg['max_position_qty']}주\n"
                f"틱={cfg['tick_seconds']}초"
            )
        except Exception as e:
            return f"[오류] 설정 변경 실패: {e}"

    @staticmethod
    def _help_message() -> str:
        return (
            "[명령어]\n"
            "/help, /명령어  - 명령어 목록\n"
            "/status        - 현재 상태\n"
            "/pause         - 일시정지\n"
            "/resume        - 재개\n"
            "/stop          - 중지\n"
            "/strategy      - 전략 조회\n"
            "/strategy <name> - 전략 교체 (sma/rsi/macd/bollinger)\n"
            "/params        - 파라미터 조회\n"
            "/params k=v    - 파라미터 수정\n"
            "/config        - 설정 조회\n"
            "/config k=v    - 설정 수정 (quantity/max_position_qty/tick_seconds)"
        )
