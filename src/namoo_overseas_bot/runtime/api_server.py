from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from typing import Protocol

from namoo_overseas_bot.runtime.paper_bot import PaperTradingBot


class TelegramCommandsToggle(Protocol):
    def is_commands_enabled(self) -> bool: ...

    def set_commands_enabled(self, enabled: bool) -> None: ...


def _make_handler(
    bot: PaperTradingBot,
    *,
    telegram_commands: TelegramCommandsToggle | None,
    api_token: str,
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send_json(200, {"status": "ok", "running": bot.status()["running"]})
                return

            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/status":
                self._send_json(200, bot.status())
                return
            if self.path == "/telegram-commands":
                enabled = telegram_commands.is_commands_enabled() if telegram_commands else False
                self._send_json(
                    200,
                    {
                        "available": telegram_commands is not None,
                        "enabled": enabled,
                    },
                )
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/pause":
                bot.pause()
                self._send_json(200, {"ok": True, "paused": True})
                return
            if self.path == "/resume":
                bot.resume()
                self._send_json(200, {"ok": True, "paused": False})
                return
            if self.path == "/stop":
                bot.stop()
                self._send_json(200, {"ok": True, "stopped": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if self.path == "/telegram-commands/enable":
                if telegram_commands is None:
                    self._send_json(409, {"error": "telegram commands controller unavailable"})
                    return
                telegram_commands.set_commands_enabled(True)
                self._send_json(200, {"ok": True, "enabled": True})
                return
            if self.path == "/telegram-commands/disable":
                if telegram_commands is None:
                    self._send_json(409, {"error": "telegram commands controller unavailable"})
                    return
                telegram_commands.set_commands_enabled(False)
                self._send_json(200, {"ok": True, "enabled": False})
                return
            self._send_json(404, {"error": "not found"})

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

        def _send_json(self, code: int, payload: dict[str, object]) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _is_authorized(self) -> bool:
            if not api_token:
                return True

            auth_header = self.headers.get("Authorization", "").strip()
            expected_bearer = f"Bearer {api_token}"
            if auth_header and hmac.compare_digest(auth_header, expected_bearer):
                return True

            x_api_token = self.headers.get("X-API-Token", "").strip()
            if x_api_token and hmac.compare_digest(x_api_token, api_token):
                return True

            return False

    return Handler


class BotApiServer:
    def __init__(
        self,
        *,
        bot: PaperTradingBot,
        host: str,
        port: int,
        telegram_commands: TelegramCommandsToggle | None = None,
        api_token: str = "",
    ) -> None:
        self.bot = bot
        self.host = host
        self.port = port
        self._server = ThreadingHTTPServer(
            (host, port),
            _make_handler(
                bot,
                telegram_commands=telegram_commands,
                api_token=api_token,
            ),
        )

    @property
    def server_address(self) -> tuple[str, int]:
        host, port = self._server.server_address
        return str(host), int(port)

    def serve_forever(self) -> None:
        try:
            self._server.serve_forever()
        finally:
            self._server.server_close()
            self.bot.stop()

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
