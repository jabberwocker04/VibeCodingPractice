from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
from typing import Protocol

from namoo_overseas_bot.runtime.paper_bot import PaperTradingBot

_DASHBOARD_STATIC_DIR = Path(__file__).parent.parent.parent.parent / "dashboard" / "out"

_DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trading Bot Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 24px; min-height: 100vh; }
  h1 { color: #38bdf8; font-size: 1.6rem; margin-bottom: 20px; }
  h3 { color: #94a3b8; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
  .metric { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1e293b; }
  .metric:last-child { border-bottom: none; }
  .metric-label { color: #64748b; font-size: 0.9rem; }
  .metric-value { font-weight: 600; font-size: 0.95rem; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
  .badge-running { background: #166534; color: #4ade80; }
  .badge-paused  { background: #78350f; color: #fbbf24; }
  .badge-stopped { background: #7f1d1d; color: #f87171; }
  .signal-buy  { color: #4ade80; }
  .signal-sell { color: #f87171; }
  .signal-hold { color: #94a3b8; }
  .btn { padding: 9px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600; margin: 4px 4px 4px 0; transition: opacity 0.15s; }
  .btn:hover { opacity: 0.85; }
  .btn-pause  { background: #d97706; color: #fff; }
  .btn-resume { background: #16a34a; color: #fff; }
  .btn-stop   { background: #dc2626; color: #fff; }
  .token-wrap { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
  .token-input { flex: 1; background: #0f172a; border: 1px solid #334155; color: #e2e8f0; padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; }
  .token-input:focus { outline: 2px solid #38bdf8; }
  .btn-save { background: #334155; color: #e2e8f0; }
  .hint { color: #64748b; font-size: 0.8rem; margin-top: 4px; }
  .error-msg { color: #f87171; }
  .ctrl-msg { font-size: 0.85rem; margin-top: 10px; color: #94a3b8; min-height: 1.2em; }
  .last-update { color: #475569; font-size: 0.78rem; margin-top: 16px; text-align: right; }
  .spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #334155; border-top-color: #38bdf8; border-radius: 50%; animation: spin 0.7s linear infinite; margin-right: 6px; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<h1>Trading Bot Dashboard</h1>
<div class="grid">

  <div class="card" id="card-status">
    <h3><span class="spinner" id="spinner"></span>봇 상태</h3>
    <div id="statusContent"><div class="hint">로딩 중...</div></div>
  </div>

  <div class="card">
    <h3>제어</h3>
    <button class="btn btn-pause"  onclick="control('pause')">일시정지</button>
    <button class="btn btn-resume" onclick="control('resume')">재개</button>
    <button class="btn btn-stop"   onclick="control('stop')" onclick="return confirm('정말 중지합니까?')">중지</button>
    <div class="ctrl-msg" id="ctrlMsg"></div>
  </div>

  <div class="card">
    <h3>API 토큰</h3>
    <div class="token-wrap">
      <input type="password" id="apiToken" class="token-input" placeholder="토큰 없으면 비워두세요">
      <button class="btn btn-save" onclick="saveToken()">저장</button>
    </div>
    <div class="hint" id="tokenHint">브라우저 localStorage에만 저장됩니다.</div>
  </div>

</div>
<div class="last-update" id="lastUpdate"></div>

<script>
(function () {
  var token = localStorage.getItem('botApiToken') || '';
  if (token) document.getElementById('apiToken').value = token;

  function saveToken() {
    token = document.getElementById('apiToken').value.trim();
    localStorage.setItem('botApiToken', token);
    document.getElementById('tokenHint').textContent = '저장 완료.';
    fetchStatus();
  }
  window.saveToken = saveToken;

  function headers() {
    var h = {};
    if (token) h['Authorization'] = 'Bearer ' + token;
    return h;
  }

  function signalClass(s) {
    if (s === 'buy')  return 'signal-buy';
    if (s === 'sell') return 'signal-sell';
    return 'signal-hold';
  }
  function signalText(s) {
    if (s === 'buy')  return '매수';
    if (s === 'sell') return '매도';
    return '대기';
  }
  function badge(running, paused) {
    if (!running) return '<span class="badge badge-stopped">정지</span>';
    if (paused)   return '<span class="badge badge-paused">일시정지</span>';
    return '<span class="badge badge-running">실행중</span>';
  }
  function row(label, value) {
    return '<div class="metric"><span class="metric-label">' + label +
           '</span><span class="metric-value">' + value + '</span></div>';
  }

  function fetchStatus() {
    fetch('/status', {headers: headers()})
      .then(function(r) {
        if (r.status === 401) throw new Error('401');
        return r.json();
      })
      .then(function(d) {
        var sigClass = signalClass(d.last_signal);
        var html = row('상태', badge(d.running, d.paused))
          + row('심볼', d.symbol || '-')
          + row('신호', '<span class="' + sigClass + '">' + signalText(d.last_signal) + '</span>')
          + row('가격', '$' + (d.last_price || 0).toFixed(2))
          + row('현금', '$' + (d.cash || 0).toFixed(2))
          + row('평가금액', '$' + (d.equity || 0).toFixed(2))
          + row('포지션 수량', d.position_qty)
          + row('총 거래', d.trades)
          + row('루프 수', d.loop_count)
          + row('시작 (UTC)', d.started_at_utc || '-')
          + row('마지막 캔들', d.last_candle_timestamp || '-');
        if (d.last_error) html += row('오류', '<span class="error-msg">' + d.last_error + '</span>');
        document.getElementById('statusContent').innerHTML = html;
        document.getElementById('lastUpdate').textContent = '갱신: ' + new Date().toLocaleTimeString();
        document.getElementById('spinner').style.display = '';
      })
      .catch(function(e) {
        var msg = e.message === '401'
          ? '<div class="error-msg">인증 실패 — API 토큰을 확인하세요.</div>'
          : '<div class="error-msg">서버 연결 실패</div>';
        document.getElementById('statusContent').innerHTML = msg;
        document.getElementById('spinner').style.display = 'none';
      });
  }

  function control(action) {
    var el = document.getElementById('ctrlMsg');
    el.textContent = action + ' 요청 중...';
    fetch('/' + action, {method: 'POST', headers: headers()})
      .then(function(r) {
        if (r.status === 401) throw new Error('401');
        return r.json();
      })
      .then(function() {
        el.textContent = action + ' 완료';
        fetchStatus();
      })
      .catch(function(e) {
        el.innerHTML = e.message === '401'
          ? '<span class="error-msg">인증 실패</span>'
          : '<span class="error-msg">요청 실패</span>';
      });
  }
  window.control = control;

  fetchStatus();
  setInterval(fetchStatus, 3000);
})();
</script>
</body>
</html>
"""


class TelegramCommandsToggle(Protocol):
    def is_commands_enabled(self) -> bool: ...

    def set_commands_enabled(self, enabled: bool) -> None: ...


def _make_handler(
    bot: PaperTradingBot,
    *,
    telegram_commands: TelegramCommandsToggle | None,
    api_token: str,
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path in ("/", "/dashboard"):
                self._send_html(200, _DASHBOARD_HTML)
                return

            if self.path == "/health":
                self._send_json(200, {"status": "ok", "running": bot.status()["running"]})
                return

            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/status":
                self._send_json(200, bot.status())
                return
            if self.path == "/telegram-commands":
                enabled = telegram_commands.is_commands_enabled() if telegram_commands else False
                self._send_json(
                    200,
                    {
                        "available": telegram_commands is not None,
                        "enabled": enabled,
                    },
                )
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/pause":
                bot.pause()
                self._send_json(200, {"ok": True, "paused": True})
                return
            if self.path == "/resume":
                bot.resume()
                self._send_json(200, {"ok": True, "paused": False})
                return
            if self.path == "/stop":
                bot.stop()
                self._send_json(200, {"ok": True, "stopped": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if self.path == "/telegram-commands/enable":
                if telegram_commands is None:
                    self._send_json(409, {"error": "telegram commands controller unavailable"})
                    return
                telegram_commands.set_commands_enabled(True)
                self._send_json(200, {"ok": True, "enabled": True})
                return
            if self.path == "/telegram-commands/disable":
                if telegram_commands is None:
                    self._send_json(409, {"error": "telegram commands controller unavailable"})
                    return
                telegram_commands.set_commands_enabled(False)
                self._send_json(200, {"ok": True, "enabled": False})
                return
            self._send_json(404, {"error": "not found"})

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

        def _send_html(self, code: int, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, code: int, payload: dict[str, object]) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _is_authorized(self) -> bool:
            if not api_token:
                return True

            auth_header = self.headers.get("Authorization", "").strip()
            expected_bearer = f"Bearer {api_token}"
            if auth_header and hmac.compare_digest(auth_header, expected_bearer):
                return True

            x_api_token = self.headers.get("X-API-Token", "").strip()
            if x_api_token and hmac.compare_digest(x_api_token, api_token):
                return True

            return False

    return Handler


class BotApiServer:
    def __init__(
        self,
        *,
        bot: PaperTradingBot,
        host: str,
        port: int,
        telegram_commands: TelegramCommandsToggle | None = None,
        api_token: str = "",
    ) -> None:
        self.bot = bot
        self.host = host
        self.port = port
        self._server = ThreadingHTTPServer(
            (host, port),
            _make_handler(
                bot,
                telegram_commands=telegram_commands,
                api_token=api_token,
            ),
        )

    @property
    def server_address(self) -> tuple[str, int]:
        host, port = self._server.server_address
        return str(host), int(port)

    def serve_forever(self) -> None:
        try:
            self._server.serve_forever()
        finally:
            self._server.server_close()
            self.bot.stop()

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()


# ------------------------------------------------------------------ #
# LiveBotApiServer - LiveTradingBot용 확장 API 서버
# ------------------------------------------------------------------ #


def _make_live_handler(
    bot: "LiveTradingBot",  # type: ignore[name-defined]
    *,
    telegram_commands: TelegramCommandsToggle | None,
    api_token: str,
) -> type[BaseHTTPRequestHandler]:
    from namoo_overseas_bot.strategies import build_strategy, STRATEGY_NAMES

    class LiveHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            # Next.js 정적 빌드 서빙 (dashboard/out/)
            if self.path in ("/", "/index.html") or not self.path.startswith("/api"):
                if self._try_serve_static():
                    return

            if self.path == "/health":
                self._send_json(200, {"status": "ok", "running": bot.status()["running"]})
                return

            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/status":
                self._send_json(200, bot.status())
                return
            if self.path == "/history":
                self._send_json(200, {"prices": bot.get_price_history(), "trades": bot.get_trade_history()})
                return
            if self.path == "/config":
                self._send_json(200, bot.get_trading_config())
                return
            if self.path == "/strategy":
                self._send_json(200, bot.get_strategy_info())
                return
            if self.path == "/telegram-commands":
                enabled = telegram_commands.is_commands_enabled() if telegram_commands else False
                self._send_json(200, {"available": telegram_commands is not None, "enabled": enabled})
                return
            if self.path == "/strategies":
                from namoo_overseas_bot.strategies import STRATEGY_DESCRIPTIONS, STRATEGY_DEFAULT_PARAMS
                self._send_json(200, {
                    "names": STRATEGY_NAMES,
                    "descriptions": STRATEGY_DESCRIPTIONS,
                    "defaults": STRATEGY_DEFAULT_PARAMS,
                })
                return
            self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return

            if self.path == "/pause":
                bot.pause()
                self._send_json(200, {"ok": True, "paused": True})
                return
            if self.path == "/resume":
                bot.resume()
                self._send_json(200, {"ok": True, "paused": False})
                return
            if self.path == "/stop":
                bot.stop()
                self._send_json(200, {"ok": True, "stopped": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if self.path == "/telegram-commands/enable":
                if telegram_commands is None:
                    self._send_json(409, {"error": "telegram commands controller unavailable"})
                    return
                telegram_commands.set_commands_enabled(True)
                self._send_json(200, {"ok": True, "enabled": True})
                return
            if self.path == "/telegram-commands/disable":
                if telegram_commands is None:
                    self._send_json(409, {"error": "telegram commands controller unavailable"})
                    return
                telegram_commands.set_commands_enabled(False)
                self._send_json(200, {"ok": True, "enabled": False})
                return

            body = self._read_json()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return

            if self.path == "/strategy":
                name = str(body.get("name", "")).strip().lower()
                if name not in STRATEGY_NAMES:
                    self._send_json(400, {"error": f"unknown strategy '{name}'. available: {STRATEGY_NAMES}"})
                    return
                try:
                    new_strat = build_strategy(name, body.get("params"))
                    bot.swap_strategy(new_strat)
                    self._send_json(200, {"ok": True, **bot.get_strategy_info()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return

            if self.path in ("/strategy/params", "/strategy/params/"):
                try:
                    bot.update_strategy_params(**{k: v for k, v in body.items()})
                    self._send_json(200, {"ok": True, **bot.get_strategy_info()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return

            if self.path == "/config":
                try:
                    bot.update_trading_config(
                        quantity=int(body["quantity"]) if "quantity" in body else None,
                        max_position_qty=int(body["max_position_qty"]) if "max_position_qty" in body else None,
                        tick_seconds=float(body["tick_seconds"]) if "tick_seconds" in body else None,
                    )
                    self._send_json(200, {"ok": True, **bot.get_trading_config()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return

            self._send_json(404, {"error": "not found"})

        def do_PATCH(self) -> None:  # noqa: N802
            if not self._is_authorized():
                self._send_json(401, {"error": "unauthorized"})
                return
            if self.path in ("/strategy/params", "/strategy/params/"):
                body = self._read_json()
                if body is None:
                    self._send_json(400, {"error": "invalid JSON body"})
                    return
                try:
                    bot.update_strategy_params(**{k: v for k, v in body.items()})
                    self._send_json(200, {"ok": True, **bot.get_strategy_info()})
                except (ValueError, TypeError) as e:
                    self._send_json(400, {"error": str(e)})
                return
            self._send_json(404, {"error": "not found"})

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-API-Token")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

        def _try_serve_static(self) -> bool:
            """Next.js out/ 디렉토리에서 정적 파일을 서빙합니다."""
            static_dir = _DASHBOARD_STATIC_DIR
            if not static_dir.exists():
                return False

            path = self.path.split("?")[0]
            if path == "/":
                path = "/index.html"

            file_path = static_dir / path.lstrip("/")
            if not file_path.exists():
                # SPA fallback: index.html
                index = static_dir / "index.html"
                if index.exists():
                    file_path = index
                else:
                    return False

            if not file_path.is_file():
                return False

            data = file_path.read_bytes()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return True

        def _read_json(self) -> dict | None:
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                return json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                return None

        def _send_json(self, code: int, payload: dict[str, object]) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def _is_authorized(self) -> bool:
            if not api_token:
                return True
            auth_header = self.headers.get("Authorization", "").strip()
            expected_bearer = f"Bearer {api_token}"
            if auth_header and hmac.compare_digest(auth_header, expected_bearer):
                return True
            x_api_token = self.headers.get("X-API-Token", "").strip()
            if x_api_token and hmac.compare_digest(x_api_token, api_token):
                return True
            return False

    return LiveHandler


class LiveBotApiServer:
    """LiveTradingBot용 REST API 서버.

    확장 엔드포인트: 전략 교체·파라미터 수정·설정 변경·차트 히스토리.
    Next.js 정적 빌드(dashboard/out/)가 존재하면 GET / 에서 서빙합니다.
    """

    def __init__(
        self,
        *,
        bot: "LiveTradingBot",  # type: ignore[name-defined]
        host: str,
        port: int,
        telegram_commands: TelegramCommandsToggle | None = None,
        api_token: str = "",
    ) -> None:
        self.bot = bot
        self._server = ThreadingHTTPServer(
            (host, port),
            _make_live_handler(bot, telegram_commands=telegram_commands, api_token=api_token),
        )

    @property
    def server_address(self) -> tuple[str, int]:
        host, port = self._server.server_address
        return str(host), int(port)

    def serve_forever(self) -> None:
        try:
            self._server.serve_forever()
        finally:
            self._server.server_close()

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
