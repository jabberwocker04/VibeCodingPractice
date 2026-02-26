from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
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


# ------------------------------------------------------------------ #
# LiveBotApiServer - LiveTradingBot용 확장 API 서버
# ------------------------------------------------------------------ #

_STATIC_DIR = Path(__file__).parent.parent / "static"


def _make_live_handler(
    bot: "LiveTradingBot",  # type: ignore[name-defined]
    *,
    telegram_commands: TelegramCommandsToggle | None,
    api_token: str,
) -> type[BaseHTTPRequestHandler]:
    from namoo_overseas_bot.strategies import build_strategy, STRATEGY_NAMES

    class LiveHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            # 프론트엔드 HTML 서빙
            if self.path in ("/", "/index.html"):
                self._serve_html()
                return

            if self.path == "/health":
                self._send_json(200, {"status": "ok", "running": bot.status()["running"]})
                return

            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/status":
                self._send_json(200, bot.status())
                return
            if self.path == "/history":
                self._send_json(200, {
                    "prices": bot.get_price_history(),
                    "trades": bot.get_trade_history(),
                })
                return
            if self.path == "/config":
                self._send_json(200, bot.get_trading_config())
                return
            if self.path == "/strategy":
                self._send_json(200, bot.get_strategy_info())
                return
            if self.path == "/telegram-commands":
                enabled = telegram_commands.is_commands_enabled() if telegram_commands else False
                self._send_json(200, {"available": telegram_commands is not None, "enabled": enabled})
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

            body = self._read_json()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return

            if self.path == "/strategy":
                name = str(body.get("name", "")).strip().lower()
                if name not in STRATEGY_NAMES:
                    self._send_json(400, {"error": f"unknown strategy '{name}'. available: {STRATEGY_NAMES}"})
                    return
                try:
                    new_strat = build_strategy(name, body.get("params"))
                    bot.swap_strategy(new_strat)
                    self._send_json(200, {"ok": True, **bot.get_strategy_info()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return

            if self.path in ("/strategy/params", "/strategy/params/"):
                try:
                    bot.update_strategy_params(**{k: v for k, v in body.items()})
                    self._send_json(200, {"ok": True, **bot.get_strategy_info()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return

            if self.path == "/config":
                try:
                    bot.update_trading_config(
                        quantity=int(body["quantity"]) if "quantity" in body else None,
                        max_position_qty=int(body["max_position_qty"]) if "max_position_qty" in body else None,
                        tick_seconds=float(body["tick_seconds"]) if "tick_seconds" in body else None,
                    )
                    self._send_json(200, {"ok": True, **bot.get_trading_config()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return

            self._send_json(404, {"error": "not found"})

        # PATCH: strategy params
        def do_PATCH(self) -> None:  # noqa: N802
            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return
            if self.path in ("/strategy/params", "/strategy/params/"):
                body = self._read_json()
                if body is None:
                    self._send_json(400, {"error": "invalid JSON body"})
                    return
                try:
                    bot.update_strategy_params(**{k: v for k, v in body.items()})
                    self._send_json(200, {"ok": True, **bot.get_strategy_info()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return
            self._send_json(404, {"error": "not found"})

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

        def _serve_html(self) -> None:
            html_path = _STATIC_DIR / "index.html"
            if not html_path.exists():
                self._send_json(404, {"error": "frontend not found"})
                return
            data = html_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_json(self) -> dict | None:
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                return json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                return None

        def _send_json(self, code: int, payload: dict[str, object]) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
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

    return LiveHandler


class LiveBotApiServer:
    """LiveTradingBot용 REST API 서버.

    기본 엔드포인트 외에 전략 교체, 파라미터 수정, 설정 변경,
    차트 히스토리 등 확장 엔드포인트를 제공합니다.
    프론트엔드 HTML은 GET / 로 서빙됩니다.
    """

    def __init__(
        self,
        *,
        bot: "LiveTradingBot",  # type: ignore[name-defined]
        host: str,
        port: int,
        telegram_commands: TelegramCommandsToggle | None = None,
        api_token: str = "",
    ) -> None:
        self.bot = bot
        self._server = ThreadingHTTPServer(
            (host, port),
            _make_live_handler(bot, telegram_commands=telegram_commands, api_token=api_token),
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

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
