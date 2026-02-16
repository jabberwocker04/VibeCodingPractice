import json
import threading
import time
import unittest
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


def _json_get(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _json_post(url: str) -> dict[str, object]:
    req = urllib.request.Request(url=url, method="POST")
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


class BotApiServerTests(unittest.TestCase):
    def test_health_status_and_control_endpoints(self) -> None:
        bot = DummyBot()
        try:
            server = BotApiServer(bot=bot, host="127.0.0.1", port=0)
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

        _ = _json_post(f"{base_url}/stop")
        time.sleep(0.1)
        thread.join(timeout=2)

        self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
