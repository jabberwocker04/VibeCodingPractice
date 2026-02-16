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
    tick_seconds: float = 3.0
    max_position_qty: int = 5
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @classmethod
    def from_env(cls) -> "BotConfig":
        return cls(
            symbol=os.getenv("BOT_SYMBOL", "AAPL"),
            quantity=int(os.getenv("BOT_QUANTITY", "1")),
            short_window=int(os.getenv("BOT_SHORT_WINDOW", "5")),
            long_window=int(os.getenv("BOT_LONG_WINDOW", "20")),
            initial_cash_usd=float(os.getenv("BOT_INITIAL_CASH_USD", "10000")),
            tick_seconds=float(os.getenv("BOT_TICK_SECONDS", "3")),
            max_position_qty=int(os.getenv("BOT_MAX_POSITION_QTY", "5")),
            server_host=os.getenv("BOT_SERVER_HOST", "0.0.0.0"),
            server_port=int(os.getenv("BOT_SERVER_PORT", "8080")),
            telegram_enabled=_env_bool("TELEGRAM_ENABLED", default=False),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        )


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
