import unittest

from namoo_overseas_bot.runtime.telegram_commands import TelegramCommandHandler


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


if __name__ == "__main__":
    unittest.main()
