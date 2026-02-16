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

        if cmd in {"/help", "help"}:
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

        return "[안내] 지원하지 않는 명령입니다. /help 를 입력하세요."

    @staticmethod
    def _help_message() -> str:
        return (
            "[명령어]\n"
            "/help - 명령어 목록\n"
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
