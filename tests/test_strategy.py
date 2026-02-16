import unittest

from namoo_overseas_bot.models import Signal
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


class SmaCrossStrategyTests(unittest.TestCase):
    def test_emits_buy_then_sell(self) -> None:
        strategy = SmaCrossStrategy(short_window=2, long_window=3)

        prices = [1.0, 1.1, 1.2, 1.3, 1.0, 0.9]
        signals = [strategy.on_price(p) for p in prices]

        self.assertIn(Signal.BUY, signals)
        self.assertIn(Signal.SELL, signals)


if __name__ == "__main__":
    unittest.main()
