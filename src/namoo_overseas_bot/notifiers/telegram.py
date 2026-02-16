from __future__ import annotations

import json
import urllib.error
import urllib.request

from namoo_overseas_bot.notifiers.base import NotifierClient


class TelegramNotifier(NotifierClient):
    def __init__(self, *, bot_token: str, chat_id: str, timeout_seconds: float = 10.0) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds

    def send(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": message,
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if status >= 300:
                    raise RuntimeError(f"telegram send failed with status={status}")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"telegram send failed: {exc}") from exc
