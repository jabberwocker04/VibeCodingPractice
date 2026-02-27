import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from namoo_overseas_bot.runtime.api_server import BotApiServer


class DummyBot:
    def __init__(self) -> None:
        self._paused = False
        self._stopped = False

    def status(self) -> dict[str, object]:
        return {
            "running": not self._stopped,
            "paused": self._paused,
            "symbol": "AAPL",
        }

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._stopped = True


class DummyTelegramCommands:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def is_commands_enabled(self) -> bool:
        return self.enabled

    def set_commands_enabled(self, enabled: bool) -> None:
        self.enabled = enabled


def _raw_get(url: str, *, token: str | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url=url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=2) as resp:
        return resp.status, resp.read().decode("utf-8")


def _json_get(url: str, *, token: str | None = None) -> dict[str, object]:
    req = urllib.request.Request(url=url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _json_post(url: str, *, token: str | None = None) -> dict[str, object]:
    req = urllib.request.Request(url=url, method="POST")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


class BotApiServerTests(unittest.TestCase):
    def test_health_status_and_control_endpoints(self) -> None:
        bot = DummyBot()
        telegram_commands = DummyTelegramCommands(enabled=True)
        try:
            server = BotApiServer(
                bot=bot,
                host="127.0.0.1",
                port=0,
                telegram_commands=telegram_commands,
            )
        except PermissionError:
            self.skipTest("socket bind is not permitted in this environment")

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        base_url = f"http://{host}:{port}"

        health = _json_get(f"{base_url}/health")
        self.assertEqual(health["status"], "ok")

        status = _json_get(f"{base_url}/status")
        self.assertEqual(status["symbol"], "AAPL")

        pause_res = _json_post(f"{base_url}/pause")
        self.assertTrue(pause_res["paused"])

        resume_res = _json_post(f"{base_url}/resume")
        self.assertFalse(resume_res["paused"])

        tg_status = _json_get(f"{base_url}/telegram-commands")
        self.assertTrue(tg_status["available"])
        self.assertTrue(tg_status["enabled"])

        tg_disable = _json_post(f"{base_url}/telegram-commands/disable")
        self.assertTrue(tg_disable["ok"])
        self.assertFalse(tg_disable["enabled"])

        tg_enable = _json_post(f"{base_url}/telegram-commands/enable")
        self.assertTrue(tg_enable["ok"])
        self.assertTrue(tg_enable["enabled"])

        _ = _json_post(f"{base_url}/stop")
        time.sleep(0.1)
        thread.join(timeout=2)

        self.assertFalse(thread.is_alive())

    def test_api_token_protects_control_endpoints(self) -> None:
        bot = DummyBot()
        telegram_commands = DummyTelegramCommands(enabled=True)
        token = "secret-token"

        try:
            server = BotApiServer(
                bot=bot,
                host="127.0.0.1",
                port=0,
                telegram_commands=telegram_commands,
                api_token=token,
            )
        except PermissionError:
            self.skipTest("socket bind is not permitted in this environment")

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        base_url = f"http://{host}:{port}"

        health = _json_get(f"{base_url}/health")
        self.assertEqual(health["status"], "ok")

        with self.assertRaises(urllib.error.HTTPError) as unauth_status:
            _ = _json_get(f"{base_url}/status")
        self.assertEqual(unauth_status.exception.code, 401)

        status = _json_get(f"{base_url}/status", token=token)
        self.assertEqual(status["symbol"], "AAPL")

        with self.assertRaises(urllib.error.HTTPError) as unauth_toggle:
            _ = _json_post(f"{base_url}/telegram-commands/disable")
        self.assertEqual(unauth_toggle.exception.code, 401)

        tg_disable = _json_post(f"{base_url}/telegram-commands/disable", token=token)
        self.assertFalse(tg_disable["enabled"])

        _ = _json_post(f"{base_url}/stop", token=token)
        time.sleep(0.1)
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())


class DashboardEndpointTests(unittest.TestCase):
    def _start_server(self, *, api_token: str = "") -> tuple[BotApiServer, str]:
        bot = DummyBot()
        try:
            server = BotApiServer(bot=bot, host="127.0.0.1", port=0, api_token=api_token)
        except PermissionError:
            self.skipTest("socket bind is not permitted in this environment")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        host, port = server.server_address
        return server, f"http://{host}:{port}"

    def test_dashboard_root_returns_html(self) -> None:
        server, base = self._start_server()
        status, body = _raw_get(f"{base}/")
        self.assertEqual(status, 200)
        self.assertIn("<!DOCTYPE html>", body)
        self.assertIn("Trading Bot Dashboard", body)
        server.shutdown()

    def test_dashboard_alias_returns_html(self) -> None:
        server, base = self._start_server()
        status, body = _raw_get(f"{base}/dashboard")
        self.assertEqual(status, 200)
        self.assertIn("<!DOCTYPE html>", body)
        server.shutdown()

    def test_dashboard_accessible_without_token(self) -> None:
        """Dashboard page itself requires no auth even when api_token is set."""
        server, base = self._start_server(api_token="secret")
        status, body = _raw_get(f"{base}/")
        self.assertEqual(status, 200)
        self.assertIn("<!DOCTYPE html>", body)
        server.shutdown()


if __name__ == "__main__":
    unittest.main()
