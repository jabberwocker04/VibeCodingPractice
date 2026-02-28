from __future__ import annotations

"""KIS (한국투자증권) Developers REST API 브로커 - 해외주식 매매

인증 방식: OAuth2 (AppKey + AppSecret → Access Token)
지원 거래소: NASD(나스닥), NYSE(뉴욕), AMEX(아멕스)
실전/모의 모두 지원

공식 문서: https://apiportal.koreainvestment.com
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from namoo_overseas_bot.brokers.base import BrokerClient
from namoo_overseas_bot.models import Fill, Order, Side


# yfinance exchange 이름 → KIS 거래소 코드 매핑
_EXCHANGE_MAP: dict[str, str] = {
    "NasdaqGS": "NASD",
    "NasdaqGM": "NASD",
    "NasdaqCM": "NASD",
    "NASDAQ": "NASD",
    "NAS": "NASD",
    "NYSE": "NYSE",
    "NYSEArca": "AMEX",
    "AMEX": "AMEX",
    "PCX": "AMEX",
}


def resolve_kis_exchange(yfinance_exchange: str) -> str:
    """yfinance 거래소 이름을 KIS 거래소 코드로 변환합니다."""
    return _EXCHANGE_MAP.get(yfinance_exchange, "NASD")


class KisBroker(BrokerClient):
    """한국투자증권 KIS Developers REST API 브로커 (해외주식).

    사용 전 KIS Developers(https://apiportal.koreainvestment.com)에서
    앱을 등록하고 AppKey / AppSecret을 발급받아야 합니다.

    Args:
        app_key:      KIS AppKey
        app_secret:   KIS AppSecret
        account_no:   계좌번호 (형식: "12345678-01", 앞8자리-상품코드)
        is_virtual:   True=모의투자, False=실전투자 (기본: True)
        exchange_code: KIS 거래소 코드 (NASD/NYSE/AMEX, 기본: NASD)
    """

    _REAL_BASE = "https://openapi.koreainvestment.com:9443"
    _VIRTUAL_BASE = "https://openapivts.koreainvestment.com:29443"

    # tr_id - 실전
    _TR_BUY_REAL = "TTTT1002U"
    _TR_SELL_REAL = "TTTT1006U"
    _TR_BALANCE_REAL = "TTTS3012R"

    # tr_id - 모의
    _TR_BUY_VIRTUAL = "VTTT1002U"
    _TR_SELL_VIRTUAL = "VTTT1006U"
    _TR_BALANCE_VIRTUAL = "VTTS3012R"

    def __init__(
        self,
        *,
        app_key: str,
        app_secret: str,
        account_no: str,
        is_virtual: bool = True,
        exchange_code: str = "NASD",
    ) -> None:
        if not app_key or not app_secret:
            raise ValueError("KIS app_key와 app_secret을 입력하세요.")
        if not account_no:
            raise ValueError("account_no를 입력하세요. (형식: 12345678-01)")

        self._app_key = app_key
        self._app_secret = app_secret
        self._is_virtual = is_virtual
        self._exchange_code = exchange_code.upper()
        self._base_url = self._VIRTUAL_BASE if is_virtual else self._REAL_BASE

        # 계좌번호 파싱: "12345678-01" → cano="12345678", acnt_prdt_cd="01"
        parts = account_no.split("-", 1)
        self._cano = parts[0].strip()
        self._acnt_prdt_cd = parts[1].strip() if len(parts) > 1 else "01"

        self._access_token: str = ""
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------ #
    # 인증 (OAuth2)
    # ------------------------------------------------------------------ #

    def _ensure_token(self) -> None:
        """토큰이 없거나 만료 1분 전이면 재발급합니다."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return
        self._issue_token()

    def _issue_token(self) -> None:
        """Access Token 발급."""
        payload = {
            "grant_type": "client_credentials",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/oauth2/tokenP",
            data=data,
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"KIS 토큰 발급 실패 HTTP {e.code}: {body}") from e

        token = result.get("access_token")
        if not token:
            raise RuntimeError(f"KIS 토큰 발급 실패: {result.get('error_description', result)}")

        expires_in = int(result.get("expires_in", 86400))
        self._access_token = token
        self._token_expires_at = time.time() + expires_in

    # ------------------------------------------------------------------ #
    # 공통 헤더
    # ------------------------------------------------------------------ #

    def _headers(self, *, tr_id: str) -> dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._access_token}",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    # ------------------------------------------------------------------ #
    # BrokerClient 구현
    # ------------------------------------------------------------------ #

    def submit_order(self, order: Order, price: float, timestamp: str) -> Fill:
        """해외주식 매수/매도 주문을 제출합니다.

        지정가 주문(ORD_DVSN=00)으로 현재가 기준 주문합니다.
        """
        self._ensure_token()

        if order.side == Side.BUY:
            tr_id = self._TR_BUY_VIRTUAL if self._is_virtual else self._TR_BUY_REAL
        elif order.side == Side.SELL:
            tr_id = self._TR_SELL_VIRTUAL if self._is_virtual else self._TR_SELL_REAL
        else:
            raise ValueError(f"지원하지 않는 주문 방향: {order.side}")

        body = {
            "CANO": self._cano,
            "ACNT_PRDT_CD": self._acnt_prdt_cd,
            "OVRS_EXCG_CD": self._exchange_code,
            "PDNO": order.symbol,
            "ORD_DVSN": "00",           # 지정가
            "ORD_QTY": str(order.qty),
            "OVRS_ORD_UNPR": f"{price:.2f}",  # 주문단가
            "CTAC_TLNO": "",
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": "0",
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/uapi/overseas-stock/v1/trading/order",
            data=data,
            headers=self._headers(tr_id=tr_id),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_err = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"KIS 주문 HTTP {e.code}: {body_err}") from e

        rt_cd = result.get("rt_cd", "1")
        if rt_cd != "0":
            msg = result.get("msg1", "알 수 없는 오류")
            raise RuntimeError(f"KIS 주문 실패 [{rt_cd}]: {msg}")

        output = result.get("output", {}) or {}
        fill_price = float(output.get("ord_unpr", 0) or 0)

        return Fill(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=fill_price if fill_price > 0 else price,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
        )

    def cash_balance(self) -> float:
        """USD 주문가능 예수금을 조회합니다."""
        self._ensure_token()
        tr_id = self._TR_BALANCE_VIRTUAL if self._is_virtual else self._TR_BALANCE_REAL

        params = {
            "CANO": self._cano,
            "ACNT_PRDT_CD": self._acnt_prdt_cd,
            "OVRS_EXCG_CD": self._exchange_code,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{self._base_url}/uapi/overseas-stock/v1/trading/inquire-balance?{query}",
            headers=self._headers(tr_id=tr_id),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"KIS 잔고조회 HTTP {e.code}: {body}") from e

        rt_cd = result.get("rt_cd", "1")
        if rt_cd != "0":
            msg = result.get("msg1", "잔고조회 실패")
            raise RuntimeError(f"KIS 잔고조회 실패 [{rt_cd}]: {msg}")

        # output2: 잔고 요약 (USD 예수금 포함)
        output2 = result.get("output2", [])
        if isinstance(output2, list) and output2:
            summary = output2[0]
        elif isinstance(output2, dict):
            summary = output2
        else:
            return 0.0

        # frcr_dncl_amt_2: 외화예수금 (USD)
        usd_cash = float(summary.get("frcr_dncl_amt_2", 0) or 0)
        return usd_cash

    def position_qty(self, symbol: str) -> int:
        """특정 종목의 보유 수량을 조회합니다."""
        self._ensure_token()
        tr_id = self._TR_BALANCE_VIRTUAL if self._is_virtual else self._TR_BALANCE_REAL

        params = {
            "CANO": self._cano,
            "ACNT_PRDT_CD": self._acnt_prdt_cd,
            "OVRS_EXCG_CD": self._exchange_code,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{self._base_url}/uapi/overseas-stock/v1/trading/inquire-balance?{query}",
            headers=self._headers(tr_id=tr_id),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError:
            return 0

        rt_cd = result.get("rt_cd", "1")
        if rt_cd != "0":
            return 0

        output1 = result.get("output1", [])
        if not isinstance(output1, list):
            return 0

        for item in output1:
            if isinstance(item, dict) and item.get("ovrs_pdno", "").upper() == symbol.upper():
                return int(item.get("ovrs_cblc_qty", 0) or 0)

        return 0

    # ------------------------------------------------------------------ #
    # 편의 메서드
    # ------------------------------------------------------------------ #

    @property
    def is_virtual(self) -> bool:
        """모의투자 여부."""
        return self._is_virtual

    @property
    def account_summary(self) -> str:
        mode = "모의" if self._is_virtual else "실전"
        return f"{self._cano}-{self._acnt_prdt_cd} ({mode}투자, {self._exchange_code})"
