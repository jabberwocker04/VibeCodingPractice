from __future__ import annotations

import argparse

from namoo_overseas_bot.brokers.paper import PaperBroker
from namoo_overseas_bot.config import BotConfig
from namoo_overseas_bot.market_data.csv_feed import load_candles
from namoo_overseas_bot.notifiers import NoOpNotifier, NotifierClient, TelegramNotifier
from namoo_overseas_bot.runtime import (
    BotApiServer,
    PaperTradingBot,
    TelegramCommandHandler,
    TelegramCommandPoller,
)
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Namoo overseas stock bot server (paper + telegram + control API)"
    )
    parser.add_argument("--csv", default="data/sample_us_stock.csv", help="OHLCV CSV path")
    parser.add_argument("--symbol", default=None, help="ticker symbol")
    parser.add_argument("--host", default=None, help="server host")
    parser.add_argument("--port", type=int, default=None, help="server port")
    return parser


def _build_notifier(config: BotConfig) -> NotifierClient:
    if not config.telegram_enabled:
        return NoOpNotifier()

    if not config.telegram_bot_token or not config.telegram_chat_id:
        raise ValueError(
            "telegram is enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty"
        )
    return TelegramNotifier(
        bot_token=config.telegram_bot_token,
        chat_id=config.telegram_chat_id,
    )


def main() -> None:
    args = build_parser().parse_args()
    config = BotConfig.from_env()

    symbol = args.symbol or config.symbol
    host = args.host or config.server_host
    port = args.port or config.server_port

    candles = load_candles(args.csv, symbol=symbol)
    strategy = SmaCrossStrategy(
        short_window=config.short_window,
        long_window=config.long_window,
    )
    broker = PaperBroker(initial_cash_usd=config.initial_cash_usd)
    notifier = _build_notifier(config)

    bot = PaperTradingBot(
        broker=broker,
        strategy=strategy,
        notifier=notifier,
        symbol=symbol,
        quantity=config.quantity,
        candles=candles,
        tick_seconds=config.tick_seconds,
        max_position_qty=config.max_position_qty,
    )

    bot.start()
    server = BotApiServer(bot=bot, host=host, port=port)
    command_poller: TelegramCommandPoller | None = None

    if config.telegram_enabled and config.telegram_commands_enabled:
        command_poller = TelegramCommandPoller(
            bot_token=config.telegram_bot_token,
            allowed_chat_id=config.telegram_chat_id,
            notifier=notifier,
            handler=TelegramCommandHandler(bot=bot),
            poll_seconds=config.telegram_poll_seconds,
        )
        command_poller.start()

    bound_host, bound_port = server.server_address
    print("=== Namoo Overseas Bot Server (Paper) ===")
    print(f"symbol: {symbol}")
    print(f"api: http://{bound_host}:{bound_port}")
    print("endpoints: GET /health, GET /status, POST /pause, POST /resume, POST /stop")
    if command_poller:
        print("telegram commands: /help, /status, /pause, /resume, /stop")

    try:
        server.serve_forever()
    finally:
        if command_poller:
            command_poller.stop()


if __name__ == "__main__":
    main()
