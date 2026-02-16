import unittest

from namoo_overseas_bot.runtime.telegram_commands import (
    TelegramCommandHandler,
    TelegramCommandPoller,
)


class _FakeBot:
    def __init__(self) -> None:
        self.paused = False
        self.stopped = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def stop(self) -> None:
        self.stopped = True

    def status(self) -> dict[str, object]:
        return {
            "running": not self.stopped,
            "paused": self.paused,
            "symbol": "AAPL",
            "trades": 3,
            "position_qty": 1,
            "cash": 1000.0,
            "equity": 1010.0,
            "last_signal": "buy",
            "last_price": 101.0,
            "last_candle_timestamp": "2026-02-16T00:00:00Z",
        }


class _NoopNotifier:
    def send(self, message: str) -> None:
        _ = message


class TelegramCommandHandlerTests(unittest.TestCase):
    def test_help(self) -> None:
        handler = TelegramCommandHandler(bot=_FakeBot())
        text = handler.handle("/help")
        self.assertIn("/status", text)

    def test_status(self) -> None:
        handler = TelegramCommandHandler(bot=_FakeBot())
        text = handler.handle("/status")
        self.assertIn("AAPL", text)
        self.assertIn("equity=1010.00", text)

    def test_pause_resume_stop(self) -> None:
        bot = _FakeBot()
        handler = TelegramCommandHandler(bot=bot)

        _ = handler.handle("/pause")
        self.assertTrue(bot.paused)

        _ = handler.handle("/resume")
        self.assertFalse(bot.paused)

        _ = handler.handle("/stop")
        self.assertTrue(bot.stopped)

    def test_poller_command_enable_toggle(self) -> None:
        poller = TelegramCommandPoller(
            bot_token="dummy-token",
            allowed_chat_id="1",
            notifier=_NoopNotifier(),
            handler=TelegramCommandHandler(bot=_FakeBot()),
            commands_enabled=True,
        )
        self.assertTrue(poller.is_commands_enabled())

        poller.set_commands_enabled(False)
        self.assertFalse(poller.is_commands_enabled())

        poller.set_commands_enabled(True)
        self.assertTrue(poller.is_commands_enabled())


if __name__ == "__main__":
    unittest.main()
