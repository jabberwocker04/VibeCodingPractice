from __future__ import annotations

import csv
from pathlib import Path

from namoo_overseas_bot.models import Candle


def load_candles(csv_path: str | Path, symbol: str) -> list[Candle]:
    candles: list[Candle] = []
    with Path(csv_path).open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append(
                Candle(
                    symbol=symbol,
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
    return candles
