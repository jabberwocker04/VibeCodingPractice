from __future__ import annotations

from namoo_overseas_bot.brokers.base import BrokerClient
from namoo_overseas_bot.models import Fill, Order


class NamooOverseasBroker(BrokerClient):
    """
    Stub broker for Namoo (NH) overseas trading.

    Replace this stub with the real NH Open API implementation.
    Suggested implementation approach:
    1) keep your strategy engine in Python (Linux/macOS 가능)
    2) run a small Windows bridge process for NH Open API calls
    3) communicate via local HTTP or message queue
    """

    def __init__(self, *, account_no: str, product_code: str) -> None:
        self.account_no = account_no
        self.product_code = product_code

    def submit_order(self, order: Order, price: float, timestamp: str) -> Fill:
        raise NotImplementedError(
            "Implement real order submission to NH Open API for overseas stocks."
        )

    def cash_balance(self) -> float:
        raise NotImplementedError("Implement cash balance lookup via NH Open API.")

    def position_qty(self, symbol: str) -> int:
        raise NotImplementedError("Implement position query via NH Open API.")
