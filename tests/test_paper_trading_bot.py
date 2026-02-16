import unittest

from namoo_overseas_bot.brokers.paper import PaperBroker
from namoo_overseas_bot.models import Candle
from namoo_overseas_bot.notifiers.noop import NoOpNotifier
from namoo_overseas_bot.runtime.paper_bot import PaperTradingBot
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


def _candles() -> list[Candle]:
    values = [100, 101, 102, 103, 99, 98, 97, 104]
    candles: list[Candle] = []
    for idx, close in enumerate(values):
        candles.append(
            Candle(
                symbol="AAPL",
                timestamp=f"2026-01-{idx + 1:02d}T00:00:00Z",
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000,
            )
        )
    return candles


class PaperTradingBotTests(unittest.TestCase):
    def test_process_updates_status_and_respects_max_position(self) -> None:
        bot = PaperTradingBot(
            broker=PaperBroker(initial_cash_usd=10000),
            strategy=SmaCrossStrategy(short_window=2, long_window=3),
            notifier=NoOpNotifier(),
            symbol="AAPL",
            quantity=1,
            candles=_candles(),
            tick_seconds=1,
            max_position_qty=1,
        )

        for _ in range(12):
            bot.process_next_candle()

        status = bot.status()
        self.assertGreater(status["loop_count"], 0)
        self.assertLessEqual(status["position_qty"], 1)
        self.assertIn(status["last_signal"], {"buy", "sell", "hold"})

    def test_pause_resume_flags(self) -> None:
        bot = PaperTradingBot(
            broker=PaperBroker(initial_cash_usd=10000),
            strategy=SmaCrossStrategy(short_window=2, long_window=3),
            notifier=NoOpNotifier(),
            symbol="AAPL",
            quantity=1,
            candles=_candles(),
            tick_seconds=1,
            max_position_qty=1,
        )

        bot.pause()
        self.assertTrue(bot.status()["paused"])

        bot.resume()
        self.assertFalse(bot.status()["paused"])


if __name__ == "__main__":
    unittest.main()
