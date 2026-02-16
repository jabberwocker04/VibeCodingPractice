from __future__ import annotations

import argparse

from namoo_overseas_bot.brokers.paper import PaperBroker
from namoo_overseas_bot.config import BotConfig
from namoo_overseas_bot.engine import TradingEngine
from namoo_overseas_bot.market_data.csv_feed import load_candles
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Namoo overseas stock bot (paper mode)")
    parser.add_argument("--csv", default="data/sample_us_stock.csv", help="OHLCV CSV path")
    parser.add_argument("--symbol", default=None, help="ticker symbol")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = BotConfig.from_env()
    symbol = args.symbol or config.symbol

    strategy = SmaCrossStrategy(
        short_window=config.short_window,
        long_window=config.long_window,
    )
    broker = PaperBroker(initial_cash_usd=config.initial_cash_usd)
    candles = load_candles(args.csv, symbol=symbol)

    engine = TradingEngine(
        broker=broker,
        strategy=strategy,
        symbol=symbol,
        quantity=config.quantity,
    )
    result = engine.run(candles)

    print("=== Namoo Overseas Bot (Paper) ===")
    print(f"symbol: {symbol}")
    print(f"trades: {result.trades}")
    print(f"cash: ${result.cash:.2f}")
    print(f"position: {result.position_qty} shares")
    print(f"last_price: ${result.last_price:.2f}")
    print(f"equity: ${result.equity:.2f}")


if __name__ == "__main__":
    main()
