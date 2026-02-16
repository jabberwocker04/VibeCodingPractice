from __future__ import annotations

from namoo_overseas_bot.notifiers.base import NotifierClient


class NoOpNotifier(NotifierClient):
    def send(self, message: str) -> None:
        # Intentionally no-op; useful in local runs without external notification.
        _ = message
