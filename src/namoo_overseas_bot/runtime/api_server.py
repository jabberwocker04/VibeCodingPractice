from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

from namoo_overseas_bot.runtime.paper_bot import PaperTradingBot


def _make_handler(bot: PaperTradingBot) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send_json(200, {"status": "ok", "running": bot.status()["running"]})
                return
            if self.path == "/status":
                self._send_json(200, bot.status())
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
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

    return Handler


class BotApiServer:
    def __init__(self, *, bot: PaperTradingBot, host: str, port: int) -> None:
        self.bot = bot
        self.host = host
        self.port = port
        self._server = ThreadingHTTPServer((host, port), _make_handler(bot))

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
