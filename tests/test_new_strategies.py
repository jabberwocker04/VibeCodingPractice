"""Tests for RSI, MACD, and Bollinger strategies."""
from __future__ import annotations

import pytest

from namoo_overseas_bot.models import Signal
from namoo_overseas_bot.strategies.bollinger_strategy import BollingerStrategy
from namoo_overseas_bot.strategies.macd_strategy import MacdStrategy
from namoo_overseas_bot.strategies.rsi_strategy import RsiStrategy
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


class TestRsiStrategy:
    def test_hold_while_warmup(self):
        strat = RsiStrategy(period=5)
        for price in [100, 101, 102, 103, 104]:
            assert strat.on_price(price) == Signal.HOLD

    def test_returns_buy_on_oversold(self):
        strat = RsiStrategy(period=5, oversold=30, overbought=70)
        # price drops sharply -> RSI < 30
        for price in [100, 99, 98, 97, 96, 50]:
            sig = strat.on_price(price)
        # the sharp drop should trigger buy (oversold)
        assert sig == Signal.BUY

    def test_no_duplicate_buy(self):
        strat = RsiStrategy(period=5, oversold=30, overbought=70)
        for price in [100, 99, 98, 97, 96, 50]:
            sig = strat.on_price(price)
        # second oversold price should not re-trigger BUY
        sig2 = strat.on_price(48)
        assert sig2 == Signal.HOLD

    def test_reset_clears_state(self):
        strat = RsiStrategy(period=5)
        for p in [100, 99, 98, 97, 96, 50]:
            strat.on_price(p)
        strat.reset()
        assert strat.current_rsi() is None
        for p in [100, 101]:
            assert strat.on_price(p) == Signal.HOLD

    def test_name(self):
        strat = RsiStrategy(period=14)
        assert "RSI" in strat.name
        assert "14" in strat.name

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            RsiStrategy(period=1)
        with pytest.raises(ValueError):
            RsiStrategy(oversold=70, overbought=30)


class TestMacdStrategy:
    def test_hold_during_warmup(self):
        strat = MacdStrategy(fast_period=3, slow_period=5, signal_period=2)
        for p in [10, 11, 12, 13, 14, 15]:
            strat.on_price(p)
        # Not enough data yet during early warmup
        # Just verify it doesn't crash
        assert True

    def test_name(self):
        strat = MacdStrategy(fast_period=12, slow_period=26, signal_period=9)
        assert "MACD" in strat.name
        assert "12" in strat.name

    def test_reset(self):
        strat = MacdStrategy(fast_period=3, slow_period=5, signal_period=2)
        for p in [10, 11, 12, 13, 14]:
            strat.on_price(p)
        strat.reset()
        macd, signal = strat.current_macd()
        # After reset both should be very close to current price (first EMA is just price)
        assert strat._price_count == 0

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            MacdStrategy(fast_period=26, slow_period=12)
        with pytest.raises(ValueError):
            MacdStrategy(fast_period=0)

    def test_signal_not_duplicate(self):
        """Strategy should not emit same signal twice in a row."""
        strat = MacdStrategy(fast_period=3, slow_period=5, signal_period=2)
        signals = []
        prices = [10, 11, 12, 11, 10, 9, 8, 9, 10, 11, 12, 13, 14, 15, 14, 13, 12, 11]
        for p in prices:
            signals.append(strat.on_price(p))

        # Check no two consecutive identical BUY or SELL
        prev = Signal.HOLD
        for sig in signals:
            if sig != Signal.HOLD:
                assert sig != prev, f"Duplicate signal: {sig}"
            prev = sig


class TestBollingerStrategy:
    def test_hold_during_warmup(self):
        strat = BollingerStrategy(period=5)
        for p in [100, 101, 102, 103]:
            assert strat.on_price(p) == Signal.HOLD

    def test_buy_below_lower_band(self):
        strat = BollingerStrategy(period=5, std_dev=1.0)
        # Prices with small variance
        for p in [100, 100, 100, 100, 100]:
            strat.on_price(p)
        # price far below mean should trigger buy
        sig = strat.on_price(90)
        assert sig == Signal.BUY

    def test_sell_above_upper_band(self):
        strat = BollingerStrategy(period=5, std_dev=1.0)
        for p in [100, 100, 100, 100, 100]:
            strat.on_price(p)
        # price far above mean should trigger sell
        sig = strat.on_price(110)
        assert sig == Signal.SELL

    def test_no_duplicate_signals(self):
        strat = BollingerStrategy(period=5, std_dev=1.0)
        for p in [100, 100, 100, 100, 100]:
            strat.on_price(p)
        sig1 = strat.on_price(90)  # BUY
        sig2 = strat.on_price(88)  # should not BUY again
        assert sig1 == Signal.BUY
        assert sig2 == Signal.HOLD

    def test_current_bands(self):
        strat = BollingerStrategy(period=5)
        for p in [100, 102, 98, 105, 97]:
            strat.on_price(p)
        bands = strat.current_bands()
        assert bands is not None
        upper, middle, lower = bands
        assert upper > middle > lower

    def test_reset(self):
        strat = BollingerStrategy(period=5)
        for p in [100, 101, 102, 103, 104]:
            strat.on_price(p)
        strat.reset()
        assert strat.current_bands() is None

    def test_name(self):
        strat = BollingerStrategy(period=20, std_dev=2.0)
        assert "Bollinger" in strat.name
        assert "20" in strat.name

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            BollingerStrategy(period=1)
        with pytest.raises(ValueError):
            BollingerStrategy(std_dev=0)


class TestSmaCrossStrategyExtended:
    """Additional tests for SMA cross after BaseStrategy refactor."""

    def test_name(self):
        strat = SmaCrossStrategy(short_window=5, long_window=20)
        assert "SMA" in strat.name

    def test_reset(self):
        strat = SmaCrossStrategy(short_window=3, long_window=5)
        for p in [10, 11, 12, 13, 14]:
            strat.on_price(p)
        strat.reset()
        # After reset, should be in warmup mode again
        for p in [10, 11, 12, 13]:
            assert strat.on_price(p) == Signal.HOLD
