import unittest

from namoo_overseas_bot.brokers.paper import PaperBroker
from namoo_overseas_bot.models import Order, Side


class PaperBrokerTests(unittest.TestCase):
    def test_buy_and_sell_updates_balances(self) -> None:
        broker = PaperBroker(initial_cash_usd=1000)

        broker.submit_order(Order(symbol="AAPL", side=Side.BUY, qty=2), price=100, timestamp="t1")
        self.assertEqual(broker.cash_balance(), 800)
        self.assertEqual(broker.position_qty("AAPL"), 2)

        broker.submit_order(Order(symbol="AAPL", side=Side.SELL, qty=1), price=120, timestamp="t2")
        self.assertEqual(broker.cash_balance(), 920)
        self.assertEqual(broker.position_qty("AAPL"), 1)

    def test_rejects_oversell(self) -> None:
        broker = PaperBroker(initial_cash_usd=1000)
        with self.assertRaises(ValueError):
            broker.submit_order(Order(symbol="AAPL", side=Side.SELL, qty=1), price=100, timestamp="t1")


if __name__ == "__main__":
    unittest.main()
