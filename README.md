# VibeCodingPractice

나무증권(NH) 해외주식 자동매매를 목표로 한 주식봇 프로젝트입니다.
현재는 **1차 목표(페이퍼 + Telegram + 24/7 서버 제어)**까지 구현되었습니다.

## README 관리 규칙
- 최신 문서는 루트 `README.md`로 유지합니다.
- 구버전 문서는 `README/YYYY-MM-DD_REME.MD` 파일에 보관합니다.
- 같은 날짜에 여러 번 변경되면 해당 파일에 `HH:MM` 섹션을 추가해 시간순으로 누적 기록합니다.

## 보안/개인정보 원칙
- 개인 정보, 키, 토큰, 계정 식별값은 `README.md`에 기록하지 않습니다.
- 민감정보는 로컬 `.env`로만 관리하고 Git에 커밋하지 않습니다.

## 최신 업데이트 (2026-02-16)
- Telegram 알림 인터페이스 및 구현 추가 (`NoOpNotifier`, `TelegramNotifier`)
- 24/7 실행 런타임 추가 (`PaperTradingBot`)
- 제어 API 서버 추가 (`GET /health`, `GET /status`, `POST /pause`, `POST /resume`, `POST /stop`)
- 서버 실행 CLI 추가 (`namoo-bot-server`)
- Telegram 실알림 점검 CLI 추가 (`namoo-telegram-check`)
- README 아카이브 규칙을 `REME.MD` + `HH:MM` 누적 방식으로 변경
- `.env` 기준 Telegram 실알림 전송 및 서버 기동 점검 완료
- Telegram 알림 문구를 한국어 기준으로 통일(티커/고유 식별값은 원문 유지)
- Telegram 명령어 가이드 문서 추가 (`GUIME.MD`)
- Telegram 명령 수신 기능 추가 (`/help`, `/status`, `/pause`, `/resume`, `/stop`)

## 현재 구현 범위 (1차 목표)
- `SMA 크로스 전략` 신호 생성 (`BUY/SELL/HOLD`)
- `PaperBroker` 기반 페이퍼 주문 실행
- `Telegram` 알림 연동 (선택형)
- 지속 실행 런타임(루프 실행, pause/resume/stop)
- 상태 조회 및 제어 HTTP API
- Docker 기반 서버 실행 지원

## 프로젝트 구조
- `GUIME.MD`: Telegram 명령어 사용 가이드
- `src/namoo_overseas_bot/cli.py`: 단발성 백테스트 실행 CLI
- `src/namoo_overseas_bot/server_cli.py`: 24/7 서버 실행 CLI
- `src/namoo_overseas_bot/telegram_check_cli.py`: Telegram 실알림 점검 CLI
- `src/namoo_overseas_bot/runtime/paper_bot.py`: 페이퍼 런타임
- `src/namoo_overseas_bot/runtime/api_server.py`: 제어 API 서버
- `src/namoo_overseas_bot/notifiers/telegram.py`: Telegram 알림
- `src/namoo_overseas_bot/brokers/namoo_stub.py`: 나무 실연동 스텁

## 로컬 실행
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# .env에 Telegram 설정 입력 후
namoo-telegram-check
namoo-bot-server --csv data/sample_us_stock.csv --symbol AAPL
```

## 서버 제어 API
- `GET /health`: 서버 헬스 상태
- `GET /status`: 런타임 상태(현금, 포지션, equity, last_signal 등)
- `POST /pause`: 매매 루프 일시정지
- `POST /resume`: 매매 루프 재개
- `POST /stop`: 매매 루프 중지 + 서버 종료

## Docker 실행
```bash
cp .env.example .env
docker compose up --build -d
curl http://127.0.0.1:8080/status
```

## 환경변수
`.env.example` 참고:
- 전략/주문: `BOT_SYMBOL`, `BOT_QUANTITY`, `BOT_SHORT_WINDOW`, `BOT_LONG_WINDOW`
- 자금/제한: `BOT_INITIAL_CASH_USD`, `BOT_MAX_POSITION_QTY`
- 런타임: `BOT_TICK_SECONDS`, `BOT_SERVER_HOST`, `BOT_SERVER_PORT`
- Telegram: `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- 오타 호환(임시): `TELEGRAM_BOT_TOKE`, `TELEGERAM_CHAT_ID`

## 입력 대기 정보 (사용자 제공 예정)
- 이전 요청의 3번 항목(실사용 기본값):
  - `BOT_SYMBOL`
  - `BOT_QUANTITY`
  - `BOT_MAX_POSITION_QTY`
  - `BOT_TICK_SECONDS`

## 테스트
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 다음 단계 로드맵 (나무 실연동까지)
1. **2차 목표: 나무 API Read-Only 연동**
- `NamooOverseasBroker`에 잔고/포지션/주문조회(조회성) 우선 연결
- 장시간/타임존 체크, 재시도(backoff), 호출 제한 대응 추가
- 장애 시 fallback 로그/알림 강화

2. **3차 목표: 나무 실주문 최소단위 연동**
- 주문 TR 연동(`submit_order`) + 중복주문 방지 키 적용
- 리스크 정책 강화(최대포지션, 일손실 한도, 킬스위치)
- 소액 실거래로 단계적 검증

3. **4차 목표: 실연동 + Telegram 실사용 운영**
- 나무 실연동 완료 후 현재 봇을 Telegram 알림/제어와 함께 운영
- 실거래 체결/에러/요약 리포트를 Telegram으로 수신
- `/pause`, `/resume`, `/status` 기반 운영 절차 정착

## 주의사항
- 이 코드는 학습/개발용입니다. 실거래 손실 책임은 사용자에게 있습니다.
- 실거래 전 모의/소액 검증과 API 제한사항 확인이 필수입니다.
