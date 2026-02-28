from __future__ import annotations

import json
import urllib.request
import urllib.parse


# 자주 사용하는 회사명 → 티커 심볼 매핑 (오프라인 폴백)
WELL_KNOWN_SYMBOLS: dict[str, str] = {
    # 미국 빅테크
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "intel": "INTC",
    "amd": "AMD",
    "qualcomm": "QCOM",
    "broadcom": "AVGO",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "ibm": "IBM",
    "paypal": "PYPL",
    "shopify": "SHOP",
    "uber": "UBER",
    "lyft": "LYFT",
    "airbnb": "ABNB",
    "coinbase": "COIN",
    "palantir": "PLTR",
    "snowflake": "SNOW",
    "zoom": "ZM",
    "twitter": "X",
    # 금융
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "bank of america": "BAC",
    "wells fargo": "WFC",
    "citigroup": "C",
    "visa": "V",
    "mastercard": "MA",
    "american express": "AXP",
    # 소비재/헬스
    "walmart": "WMT",
    "target": "TGT",
    "costco": "COST",
    "starbucks": "SBUX",
    "mcdonalds": "MCD",
    "nike": "NKE",
    "johnson": "JNJ",
    "johnson & johnson": "JNJ",
    "pfizer": "PFE",
    "moderna": "MRNA",
    "abbvie": "ABBV",
    "unitedhealth": "UNH",
    # 에너지
    "exxon": "XOM",
    "chevron": "CVX",
    # ETF
    "spy": "SPY",
    "qqq": "QQQ",
    "voo": "VOO",
    "arkk": "ARKK",
    # 한국 주식 (KRX)
    "삼성전자": "005930.KS",
    "samsung": "005930.KS",
    "삼성": "005930.KS",
    "sk하이닉스": "000660.KS",
    "sk hynix": "000660.KS",
    "하이닉스": "000660.KS",
    "lg에너지솔루션": "373220.KS",
    "현대차": "005380.KS",
    "hyundai": "005380.KS",
    "현대자동차": "005380.KS",
    "카카오": "035720.KS",
    "kakao": "035720.KS",
    "네이버": "035420.KS",
    "naver": "035420.KS",
    "셀트리온": "068270.KS",
    "포스코": "005490.KS",
    "posco": "005490.KS",
    "kb금융": "105560.KS",
    "신한지주": "055550.KS",
}


def resolve_symbol(query: str) -> str:
    """회사명 또는 티커 심볼을 입력받아 유효한 티커 심볼을 반환합니다.

    처리 순서:
    1. 이미 유효한 티커 심볼이면 그대로 반환
    2. 잘 알려진 이름 매핑 확인
    3. Yahoo Finance 검색 API를 통한 조회
    4. 실패 시 ValueError 발생
    """
    query = query.strip()
    if not query:
        raise ValueError("심볼 또는 회사명을 입력하세요.")

    # 1. 직접 yfinance로 확인 (이미 유효한 티커인 경우)
    upper = query.upper()
    if _is_valid_ticker(upper):
        return upper

    # 2. 잘 알려진 이름 테이블 조회
    lower = query.lower()
    if lower in WELL_KNOWN_SYMBOLS:
        return WELL_KNOWN_SYMBOLS[lower]

    # 3. Yahoo Finance 검색
    found = _search_yahoo_finance(query)
    if found:
        return found

    # 4. 원본을 대문자로 변환해서 마지막 시도
    raise ValueError(
        f"'{query}'에 해당하는 주식 심볼을 찾을 수 없습니다.\n"
        "팁: 직접 티커 심볼(예: AAPL, TSLA)을 입력해보세요."
    )


def _is_valid_ticker(symbol: str) -> bool:
    """yfinance로 심볼 유효성 검증."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        # fast_info의 last_price가 있으면 유효한 심볼
        price = getattr(info, "last_price", None)
        return price is not None and price > 0
    except Exception:
        return False


def _search_yahoo_finance(query: str) -> str | None:
    """Yahoo Finance 자동완성 API로 심볼 검색."""
    try:
        encoded = urllib.parse.quote(query)
        url = (
            f"https://query1.finance.yahoo.com/v1/finance/search"
            f"?q={encoded}&quotesCount=5&newsCount=0&enableFuzzyQuery=true"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        quotes = data.get("quotes", [])
        for quote in quotes:
            quote_type = quote.get("quoteType", "")
            if quote_type in ("EQUITY", "ETF"):
                return quote.get("symbol", "")
    except Exception:
        pass
    return None


def get_company_info(symbol: str) -> dict[str, str]:
    """심볼의 회사 정보 반환 (이름, 섹터, 거래소)."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector", "N/A"),
            "exchange": info.get("exchange", "N/A"),
            "currency": info.get("currency", "USD"),
        }
    except Exception:
        return {
            "name": symbol,
            "sector": "N/A",
            "exchange": "N/A",
            "currency": "USD",
        }
