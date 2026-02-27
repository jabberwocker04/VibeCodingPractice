from __future__ import annotations

from datetime import timezone

from namoo_overseas_bot.models import Candle


VALID_INTERVALS = {
    "1m": "1분봉",
    "5m": "5분봉",
    "15m": "15분봉",
    "30m": "30분봉",
    "1h": "1시간봉",
    "1d": "일봉",
    "1wk": "주봉",
}


def fetch_candles(
    symbol: str,
    interval: str = "1d",
    period: str = "6mo",
) -> list[Candle]:
    """Fetch OHLCV candles from Yahoo Finance.

    Args:
        symbol:   티커 심볼 (예: AAPL, TSLA, 005930.KS)
        interval: 캔들 주기 (1m, 5m, 15m, 30m, 1h, 1d, 1wk)
        period:   데이터 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)

    Returns:
        Candle 리스트 (오래된 순서)
    """
    try:
        import yfinance as yf
    except ImportError:
        raise RuntimeError(
            "yfinance가 설치되지 않았습니다. 'pip install yfinance'를 실행하세요."
        )

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval, auto_adjust=True)

    if df.empty:
        raise ValueError(
            f"'{symbol}'에 대한 데이터를 가져올 수 없습니다. "
            "티커 심볼이 올바른지 확인하세요."
        )

    candles: list[Candle] = []
    for ts, row in df.iterrows():
        if hasattr(ts, "to_pydatetime"):
            dt = ts.to_pydatetime()
        else:
            dt = ts
        timestamp = dt.astimezone(timezone.utc).isoformat()
        candles.append(
            Candle(
                symbol=symbol,
                timestamp=timestamp,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
        )
    return candles


def fetch_latest_price(symbol: str) -> tuple[float, str]:
    """Fetch the latest price for a symbol.

    Returns:
        (price, timestamp) tuple
    """
    try:
        import yfinance as yf
    except ImportError:
        raise RuntimeError("yfinance가 설치되지 않았습니다.")

    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1d", interval="1m")
    if df.empty:
        df = ticker.history(period="5d", interval="1d")
    if df.empty:
        raise ValueError(f"'{symbol}'의 최신 가격을 가져올 수 없습니다.")

    last_row = df.iloc[-1]
    ts = df.index[-1]
    if hasattr(ts, "to_pydatetime"):
        dt = ts.to_pydatetime()
    else:
        dt = ts
    timestamp = dt.astimezone(timezone.utc).isoformat()
    return float(last_row["Close"]), timestamp
