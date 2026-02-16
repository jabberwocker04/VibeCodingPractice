from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class BotConfig:
    symbol: str = "AAPL"
    quantity: int = 1
    short_window: int = 5
    long_window: int = 20
    initial_cash_usd: float = 10_000.0

    @classmethod
    def from_env(cls) -> "BotConfig":
        return cls(
            symbol=os.getenv("BOT_SYMBOL", "AAPL"),
            quantity=int(os.getenv("BOT_QUANTITY", "1")),
            short_window=int(os.getenv("BOT_SHORT_WINDOW", "5")),
            long_window=int(os.getenv("BOT_LONG_WINDOW", "20")),
            initial_cash_usd=float(os.getenv("BOT_INITIAL_CASH_USD", "10000")),
        )
