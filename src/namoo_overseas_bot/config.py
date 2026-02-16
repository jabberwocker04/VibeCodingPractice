from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    telegram_commands_enabled: bool = True
    telegram_poll_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "BotConfig":
        if not _env_bool("BOT_DISABLE_DOTENV", default=False):
            _load_dotenv_if_exists(".env")
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
            telegram_bot_token=_first_env(
                "TELEGRAM_BOT_TOKEN",
                "TELEGRAM_BOT_TOKE",
                default="",
            ),
            telegram_chat_id=_first_env(
                "TELEGRAM_CHAT_ID",
                "TELEGERAM_CHAT_ID",
                default="",
            ),
            telegram_commands_enabled=_env_bool(
                "TELEGRAM_COMMANDS_ENABLED",
                default=True,
            ),
            telegram_poll_seconds=float(os.getenv("TELEGRAM_POLL_SECONDS", "1.0")),
        )


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        raw = os.getenv(name)
        if raw is not None and raw != "":
            return raw
    return default


def _load_dotenv_if_exists(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value
