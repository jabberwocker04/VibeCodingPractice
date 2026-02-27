from __future__ import annotations

import json
import urllib.parse
import urllib.request


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
    """회사명 또는 티커 심볼을 입력받아 유효한 티커 심볼을 반환합니다."""
    query = query.strip()
    if not query:
        raise ValueError("심볼 또는 회사명을 입력하세요.")

    upper = query.upper()
    if _is_valid_ticker(upper):
        return upper

    lower = query.lower()
    if lower in WELL_KNOWN_SYMBOLS:
        return WELL_KNOWN_SYMBOLS[lower]

    found = _search_yahoo_finance(query)
    if found:
        return found

    raise ValueError(
        f"'{query}'에 해당하는 주식 심볼을 찾을 수 없습니다.\n"
        "팁: 직접 티커 심볼(예: AAPL, TSLA)을 입력해보세요."
    )


def _is_valid_ticker(symbol: str) -> bool:
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = getattr(info, "last_price", None)
        return price is not None and price > 0
    except Exception:
        return False


def _search_yahoo_finance(query: str) -> str | None:
    try:
        encoded = urllib.parse.quote(query)
        url = (
            f"https://query1.finance.yahoo.com/v1/finance/search"
            f"?q={encoded}&quotesCount=5&newsCount=0&enableFuzzyQuery=true"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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
        return {"name": symbol, "sector": "N/A", "exchange": "N/A", "currency": "USD"}
