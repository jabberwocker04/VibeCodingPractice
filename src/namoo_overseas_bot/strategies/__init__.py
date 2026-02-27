from __future__ import annotations

from namoo_overseas_bot.strategies.base import BaseStrategy
from namoo_overseas_bot.strategies.bollinger_strategy import BollingerStrategy
from namoo_overseas_bot.strategies.macd_strategy import MacdStrategy
from namoo_overseas_bot.strategies.rsi_strategy import RsiStrategy
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy

STRATEGY_NAMES = ["sma", "rsi", "macd", "bollinger"]

STRATEGY_DESCRIPTIONS = {
    "sma": "SMA 크로스 (단기/장기 이동평균 교차)",
    "rsi": "RSI (과매수/과매도 반전)",
    "macd": "MACD (지수이동평균 수렴/발산)",
    "bollinger": "볼린저 밴드 (가격 밴드 이탈)",
}

STRATEGY_DEFAULT_PARAMS: dict[str, dict[str, object]] = {
    "sma": {"short_window": 5, "long_window": 20},
    "rsi": {"period": 14, "oversold": 30.0, "overbought": 70.0},
    "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
    "bollinger": {"period": 20, "std_dev": 2.0},
}


def build_strategy(name: str, params: dict | None = None) -> BaseStrategy:
    """전략 이름과 파라미터로 전략 인스턴스를 생성합니다.

    Args:
        name:   전략 이름 (sma / rsi / macd / bollinger)
        params: 파라미터 dict. None이면 기본값 사용.

    Raises:
        ValueError: 알 수 없는 전략 이름 또는 잘못된 파라미터
    """
    p = dict(STRATEGY_DEFAULT_PARAMS.get(name, {}))
    if params:
        p.update(params)

    if name == "sma":
        return SmaCrossStrategy(
            short_window=int(p.get("short_window", 5)),
            long_window=int(p.get("long_window", 20)),
        )
    if name == "rsi":
        return RsiStrategy(
            period=int(p.get("period", 14)),
            oversold=float(p.get("oversold", 30.0)),
            overbought=float(p.get("overbought", 70.0)),
        )
    if name == "macd":
        return MacdStrategy(
            fast_period=int(p.get("fast_period", 12)),
            slow_period=int(p.get("slow_period", 26)),
            signal_period=int(p.get("signal_period", 9)),
        )
    if name == "bollinger":
        return BollingerStrategy(
            period=int(p.get("period", 20)),
            std_dev=float(p.get("std_dev", 2.0)),
        )
    raise ValueError(
        f"알 수 없는 전략: '{name}'. 사용 가능: {STRATEGY_NAMES}"
    )


__all__ = [
    "BaseStrategy",
    "BollingerStrategy",
    "MacdStrategy",
    "RsiStrategy",
    "SmaCrossStrategy",
    "STRATEGY_NAMES",
    "STRATEGY_DESCRIPTIONS",
    "STRATEGY_DEFAULT_PARAMS",
    "build_strategy",
]
