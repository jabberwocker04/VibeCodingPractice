from __future__ import annotations

"""trade_cli - 자동매매 CLI 진입점

사용법:
    trade --ticker AAPL --strategy sma
    trade --company "Apple" --strategy rsi
    trade --ticker TSLA --strategy macd --quantity 2
    trade --ticker NVDA --strategy bollinger --cash 50000 --interval 1h
    trade --ticker AAPL --strategy sma --backtest  # 백테스트 모드
"""

import argparse
import signal
import sys
import time

from namoo_overseas_bot.brokers.kis_broker import KisBroker, resolve_kis_exchange
from namoo_overseas_bot.brokers.paper import PaperBroker
from namoo_overseas_bot.config import BotConfig
from namoo_overseas_bot.market_data.symbol_resolver import resolve_symbol, get_company_info
from namoo_overseas_bot.market_data.yfinance_feed import fetch_candles, VALID_INTERVALS
from namoo_overseas_bot.models import Signal
from namoo_overseas_bot.notifiers.base import NotifierClient
from namoo_overseas_bot.notifiers.noop import NoOpNotifier
from namoo_overseas_bot.notifiers.telegram import TelegramNotifier
from namoo_overseas_bot.runtime.live_bot import LiveTradingBot
from namoo_overseas_bot.strategies.base import BaseStrategy
from namoo_overseas_bot.strategies.bollinger_strategy import BollingerStrategy
from namoo_overseas_bot.strategies.macd_strategy import MacdStrategy
from namoo_overseas_bot.strategies.rsi_strategy import RsiStrategy
from namoo_overseas_bot.strategies.sma_cross import SmaCrossStrategy


STRATEGY_CHOICES = ["sma", "rsi", "macd", "bollinger"]
STRATEGY_DESCRIPTIONS = {
    "sma": "SMA 크로스 (단기/장기 이동평균 교차)",
    "rsi": "RSI (과매수/과매도 반전)",
    "macd": "MACD (지수이동평균 수렴/발산)",
    "bollinger": "볼린저 밴드 (가격 밴드 이탈)",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="자동주식매매 봇 - 티커 또는 회사명으로 자동매매",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  trade --ticker AAPL --strategy sma
  trade --company "Apple" --strategy rsi --quantity 3
  trade --ticker TSLA --strategy macd --cash 50000
  trade --ticker NVDA --strategy bollinger --interval 1h
  trade --ticker AAPL --strategy sma --backtest

전략 목록:
  sma       SMA 크로스 (단기/장기 이동평균 교차)
  rsi       RSI (과매수/과매도 반전)
  macd      MACD (지수이동평균 수렴/발산)
  bollinger 볼린저 밴드 (가격 밴드 이탈)
        """,
    )

    # 종목 지정 (둘 중 하나 필수)
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument("--ticker", "-t", help="티커 심볼 (예: AAPL, TSLA, 005930.KS)")
    symbol_group.add_argument("--company", "-c", help="회사명 (예: Apple, 삼성전자, Tesla)")

    # 전략 선택
    parser.add_argument(
        "--strategy", "-s",
        choices=STRATEGY_CHOICES,
        default="sma",
        help="매매 전략 (기본값: sma)",
    )

    # 거래 설정
    parser.add_argument("--quantity", "-q", type=int, default=None, help="1회 거래 수량 (기본: config)")
    parser.add_argument("--cash", type=float, default=None, help="초기 자금 USD (기본: config)")
    parser.add_argument("--max-qty", type=int, default=None, help="최대 보유 수량 (기본: config)")

    # 데이터 설정
    parser.add_argument(
        "--interval", "-i",
        choices=list(VALID_INTERVALS.keys()),
        default="1d",
        help="캔들 주기 (기본: 1d)",
    )
    parser.add_argument("--period", default="6mo", help="히스토리 데이터 기간 (기본: 6mo)")

    # 브로커 선택
    parser.add_argument(
        "--broker", "-b",
        choices=["paper", "kis"],
        default="paper",
        help="브로커 선택: paper(모의, 기본), kis(한국투자증권 실계좌)",
    )

    # 실행 모드
    parser.add_argument("--backtest", action="store_true", help="백테스트 모드 (과거 데이터만 사용)")
    parser.add_argument("--tick", type=float, default=None, help="틱 간격 초 (라이브 모드, 기본: 60)")
    parser.add_argument("--serve", action="store_true", help="API 서버 + 웹 대시보드 함께 실행")
    parser.add_argument("--host", default=None, help="API 서버 호스트 (기본: config)")
    parser.add_argument("--port", type=int, default=None, help="API 서버 포트 (기본: config)")

    # 전략 파라미터
    parser.add_argument("--short-window", type=int, default=5, help="SMA 단기 윈도우 (기본: 5)")
    parser.add_argument("--long-window", type=int, default=20, help="SMA 장기 윈도우 (기본: 20)")
    parser.add_argument("--rsi-period", type=int, default=14, help="RSI 기간 (기본: 14)")
    parser.add_argument("--rsi-oversold", type=float, default=30.0, help="RSI 과매도 기준 (기본: 30)")
    parser.add_argument("--rsi-overbought", type=float, default=70.0, help="RSI 과매수 기준 (기본: 70)")
    parser.add_argument("--macd-fast", type=int, default=12, help="MACD 단기 EMA (기본: 12)")
    parser.add_argument("--macd-slow", type=int, default=26, help="MACD 장기 EMA (기본: 26)")
    parser.add_argument("--macd-signal", type=int, default=9, help="MACD 시그널 (기본: 9)")
    parser.add_argument("--bb-period", type=int, default=20, help="볼린저 밴드 기간 (기본: 20)")
    parser.add_argument("--bb-std", type=float, default=2.0, help="볼린저 밴드 표준편차 배수 (기본: 2.0)")

    return parser


def build_strategy(args: argparse.Namespace) -> BaseStrategy:
    if args.strategy == "sma":
        return SmaCrossStrategy(
            short_window=args.short_window,
            long_window=args.long_window,
        )
    elif args.strategy == "rsi":
        return RsiStrategy(
            period=args.rsi_period,
            oversold=args.rsi_oversold,
            overbought=args.rsi_overbought,
        )
    elif args.strategy == "macd":
        return MacdStrategy(
            fast_period=args.macd_fast,
            slow_period=args.macd_slow,
            signal_period=args.macd_signal,
        )
    elif args.strategy == "bollinger":
        return BollingerStrategy(
            period=args.bb_period,
            std_dev=args.bb_std,
        )
    raise ValueError(f"알 수 없는 전략: {args.strategy}")


def run_backtest(
    symbol: str,
    company_name: str,
    strategy: BaseStrategy,
    broker: PaperBroker,
    interval: str,
    period: str,
    quantity: int,
    max_position_qty: int,
) -> None:
    """히스토리 데이터로 백테스트를 실행합니다."""
    print(f"\n[백테스트] {company_name}({symbol}) | 전략: {strategy.name}")
    print(f"기간: {period} | 주기: {interval} ({VALID_INTERVALS.get(interval, interval)})")
    print("데이터 로딩 중...", end="", flush=True)

    candles = fetch_candles(symbol, interval=interval, period=period)
    print(f" {len(candles)}개 캔들 로드 완료")

    initial_cash = broker.cash_balance()
    trades = 0
    buy_count = 0
    sell_count = 0

    for candle in candles:
        sig = strategy.on_price(candle.close)
        if sig == Signal.BUY:
            current_pos = broker.position_qty(symbol)
            if current_pos + quantity <= max_position_qty:
                try:
                    from namoo_overseas_bot.models import Order, Side
                    broker.submit_order(
                        Order(symbol=symbol, side=Side.BUY, qty=quantity),
                        price=candle.close,
                        timestamp=candle.timestamp,
                    )
                    trades += 1
                    buy_count += 1
                except ValueError:
                    pass
        elif sig == Signal.SELL:
            current_pos = broker.position_qty(symbol)
            if current_pos >= quantity:
                try:
                    from namoo_overseas_bot.models import Order, Side
                    broker.submit_order(
                        Order(symbol=symbol, side=Side.SELL, qty=quantity),
                        price=candle.close,
                        timestamp=candle.timestamp,
                    )
                    trades += 1
                    sell_count += 1
                except ValueError:
                    pass

    last_price = candles[-1].close if candles else 0.0
    position_qty = broker.position_qty(symbol)
    cash = broker.cash_balance()
    equity = cash + position_qty * last_price
    pnl = equity - initial_cash
    pnl_pct = (pnl / initial_cash) * 100 if initial_cash > 0 else 0.0

    print("\n" + "=" * 50)
    print(f"  백테스트 결과: {company_name}({symbol})")
    print("=" * 50)
    print(f"  전략         : {strategy.name}")
    print(f"  데이터 기간  : {period} ({VALID_INTERVALS.get(interval, interval)})")
    print(f"  총 캔들 수   : {len(candles)}개")
    print(f"  총 거래 횟수 : {trades}회 (매수:{buy_count} 매도:{sell_count})")
    print(f"  최종 가격    : ${last_price:,.2f}")
    print(f"  현금         : ${cash:,.2f}")
    print(f"  보유 수량    : {position_qty}주")
    print(f"  총 자산      : ${equity:,.2f}")
    print(f"  초기 자금    : ${initial_cash:,.2f}")
    print(f"  손익         : ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
    print("=" * 50)


def run_live(
    symbol: str,
    company_name: str,
    strategy: BaseStrategy,
    broker: PaperBroker | KisBroker,
    notifier: NotifierClient,
    interval: str,
    period: str,
    quantity: int,
    max_position_qty: int,
    tick_seconds: float,
    serve: bool = False,
    server_host: str = "127.0.0.1",
    server_port: int = 8080,
    api_token: str = "",
) -> None:
    """실시간 자동매매를 실행합니다."""
    from namoo_overseas_bot.runtime.api_server import LiveBotApiServer
    from namoo_overseas_bot.runtime.telegram_commands import LiveBotCommandHandler

    bot = LiveTradingBot(
        broker=broker,
        strategy=strategy,
        notifier=notifier,
        symbol=symbol,
        company_name=company_name,
        quantity=quantity,
        interval=interval,
        history_period=period,
        tick_seconds=tick_seconds,
        max_position_qty=max_position_qty,
    )

    api_server: LiveBotApiServer | None = None
    if serve:
        api_server = LiveBotApiServer(
            bot=bot,
            host=server_host,
            port=server_port,
            api_token=api_token,
        )

    def _shutdown(signum, frame):
        print("\n\n[종료] 봇을 안전하게 종료합니다...")
        bot.stop()
        if api_server:
            api_server.shutdown()
        status = bot.status()
        print(f"최종 자산: ${status['equity']:,.2f} | 손익: ${status['pnl']:+,.2f} ({status['pnl_pct']:+.2f}%)")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print(f"\n[라이브] {company_name}({symbol}) 자동매매 시작")
    print(f"전략: {strategy.name} | 주기: {interval} | 틱 간격: {tick_seconds}초")
    print(f"초기 자금: ${broker.cash_balance():,.2f} | 1회 수량: {quantity}주")
    if serve and api_server:
        h, p = api_server.server_address
        print(f"웹 대시보드: http://{h}:{p}")
        print(f"API: http://{h}:{p}/status")
    print("종료하려면 Ctrl+C를 누르세요.\n")

    bot.start()

    if api_server:
        import threading as _threading
        _threading.Thread(target=api_server.serve_forever, name="api-server", daemon=True).start()

    try:
        while True:
            time.sleep(5)
            status = bot.status()
            print(
                f"\r  [{status['loop_count']}틱] "
                f"가격=${status['last_price']:,.2f} | "
                f"신호={status['last_signal']} | "
                f"자산=${status['equity']:,.2f} | "
                f"손익=${status['pnl']:+,.2f} ({status['pnl_pct']:+.2f}%)",
                end="",
                flush=True,
            )
    except KeyboardInterrupt:
        _shutdown(None, None)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = BotConfig.from_env()

    # 심볼 해석
    query = args.ticker if args.ticker else args.company
    print(f"심볼 검색 중: '{query}'...")
    try:
        symbol = resolve_symbol(query)  # type: ignore[arg-type]
    except ValueError as e:
        print(f"오류: {e}")
        sys.exit(1)

    # 회사 정보 조회
    print(f"회사 정보 조회 중: {symbol}...")
    info = get_company_info(symbol)
    company_name = info["name"]

    print(f"\n종목: {company_name} ({symbol})")
    print(f"섹터: {info['sector']} | 거래소: {info['exchange']} | 통화: {info['currency']}")

    # 설정값
    quantity = args.quantity or config.quantity
    cash = args.cash or config.initial_cash_usd
    max_qty = args.max_qty or config.max_position_qty
    tick_seconds = args.tick or config.tick_seconds

    # 전략 생성
    strategy = build_strategy(args)
    print(f"전략: {strategy.name} ({STRATEGY_DESCRIPTIONS.get(args.strategy, '')})")

    # 브로커 생성
    broker: PaperBroker | KisBroker
    if args.broker == "kis":
        if not config.kis_app_key or not config.kis_app_secret or not config.kis_account_no:
            print(
                "오류: KIS 브로커를 사용하려면 .env에 다음 항목을 설정하세요:\n"
                "  KIS_APP_KEY=...\n"
                "  KIS_APP_SECRET=...\n"
                "  KIS_ACCOUNT_NO=...\n"
                "KIS Developers 가입: https://apiportal.koreainvestment.com"
            )
            sys.exit(1)
        # 거래소 코드: .env 설정 우선, 그 다음 yfinance 거래소 정보 자동 감지
        exchange_code = config.kis_exchange_code
        if exchange_code == "NASD" and info.get("exchange") not in ("N/A", ""):
            exchange_code = resolve_kis_exchange(info["exchange"])
        broker = KisBroker(
            app_key=config.kis_app_key,
            app_secret=config.kis_app_secret,
            account_no=config.kis_account_no,
            is_virtual=config.kis_is_virtual,
            exchange_code=exchange_code,
        )
        mode = "모의투자" if config.kis_is_virtual else "실전투자"
        print(f"브로커: 한국투자증권 KIS ({mode}) | 계좌: {config.kis_account_no} | 거래소: {exchange_code}")
    else:
        broker = PaperBroker(initial_cash_usd=cash)
        print(f"브로커: Paper (모의매매) | 초기자금: ${cash:,.2f}")

    # 알리미 생성
    if config.telegram_enabled and config.telegram_bot_token and config.telegram_chat_id:
        notifier: NotifierClient = TelegramNotifier(
            bot_token=config.telegram_bot_token,
            chat_id=config.telegram_chat_id,
        )
        print("텔레그램 알림: 활성화")
    else:
        notifier = NoOpNotifier()
        print("텔레그램 알림: 비활성화 (.env 파일에서 TELEGRAM_ENABLED=true로 설정)")

    if args.backtest:
        if args.broker == "kis":
            print("안내: 백테스트는 KIS 브로커를 지원하지 않습니다. paper 브로커로 자동 전환합니다.")
            broker = PaperBroker(initial_cash_usd=cash)
        run_backtest(
            symbol=symbol,
            company_name=company_name,
            strategy=strategy,
            broker=broker,  # type: ignore[arg-type]
            interval=args.interval,
            period=args.period,
            quantity=quantity,
            max_position_qty=max_qty,
        )
    else:
        run_live(
            symbol=symbol,
            company_name=company_name,
            strategy=strategy,
            broker=broker,
            notifier=notifier,
            interval=args.interval,
            period=args.period,
            quantity=quantity,
            max_position_qty=max_qty,
            tick_seconds=tick_seconds,
            serve=args.serve,
            server_host=args.host or config.server_host,
            server_port=args.port or config.server_port,
            api_token=config.api_token,
        )


if __name__ == "__main__":
    main()
