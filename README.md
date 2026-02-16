# VibeCodingPractice

나무증권(NH) 해외주식 자동매매를 목표로 한 주식봇 프로젝트입니다.
현재는 **1차 목표(페이퍼 + Telegram + 24/7 서버 제어)**까지 구현되었습니다.

## README 관리 규칙
- 최신 문서는 루트 `README.md`로 유지합니다.
- 구버전 문서는 `README/YYYY-MM-DD_README.MD` 파일에 보관합니다.
- 같은 날짜에 여러 번 변경되면 해당 파일에 `HH:MM` 섹션을 추가해 시간순으로 누적 기록합니다.
- 기존 오타 파일(`REME`)은 레거시 기록으로 유지하고, 신규 기록부터 `README` 형식을 사용합니다.

## 보안/개인정보 원칙
- 개인 정보, 키, 토큰, 계정 식별값은 `README.md`에 기록하지 않습니다.
- 민감정보는 로컬 `.env`로만 관리하고 Git에 커밋하지 않습니다.
- 제어 API는 로컬 전용(`BOT_SERVER_HOST=127.0.0.1`)으로 운영합니다.
- 제어 API에는 `BOT_API_TOKEN` 인증을 적용합니다.

## 최신 업데이트 (2026-02-16)
- Telegram 알림 인터페이스 및 구현 추가 (`NoOpNotifier`, `TelegramNotifier`)
- 24/7 실행 런타임 추가 (`PaperTradingBot`)
- 제어 API 서버 추가 (`GET /health`, `GET /status`, `POST /pause`, `POST /resume`, `POST /stop`)
- 서버 실행 CLI 추가 (`namoo-bot-server`)
- Telegram 실알림 점검 CLI 추가 (`namoo-telegram-check`)
- README 아카이브 규칙을 `README.MD` + `HH:MM` 누적 방식으로 변경
- `.env` 기준 Telegram 실알림 전송 및 서버 기동 점검 완료
- Telegram 알림 문구를 한국어 기준으로 통일(티커/고유 식별값은 원문 유지)
- Telegram 명령어 가이드 문서 추가 (`GUIME.MD`)
- Telegram 명령 수신 기능 추가 (`/help`, `/status`, `/pause`, `/resume`, `/stop`)
- OpenClaw 연동 정리 문서 분리 (`OPENCLAW.MD`)
- 보안 점검/대응 문서 분리 (`SECURITY.MD`)
- 트레이딩봇 Telegram 명령 On/Off 제어 API 추가
- 브랜치 운영 분리(`main/GPT/Claude`) 정책 추가

## 현재 구현 범위 (1차 목표)
- `SMA 크로스 전략` 신호 생성 (`BUY/SELL/HOLD`)
- `PaperBroker` 기반 페이퍼 주문 실행
- `Telegram` 알림 연동 (선택형)
- 지속 실행 런타임(루프 실행, pause/resume/stop)
- 상태 조회 및 제어 HTTP API
- Docker 기반 서버 실행 지원

## 프로젝트 구조
```text
VibeCodingPractice/
├── README.md
├── GUIDE.MD
├── GUIME.MD
├── OPENCLAW.MD
├── SECURITY.MD
├── BRANCHING.MD
├── .env.example
├── .gitignore
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── data/
│   └── sample_us_stock.csv
├── README/
│   ├── 2026-02-16_README.MD
│   └── 2026-02-16_REME.MD   # legacy
├── src/
│   └── namoo_overseas_bot/
│       ├── cli.py
│       ├── server_cli.py
│       ├── telegram_check_cli.py
│       ├── config.py
│       ├── engine.py
│       ├── models.py
│       ├── brokers/
│       │   ├── base.py
│       │   ├── paper.py
│       │   └── namoo_stub.py
│       ├── strategies/
│       │   └── sma_cross.py
│       ├── market_data/
│       │   └── csv_feed.py
│       ├── notifiers/
│       │   ├── base.py
│       │   ├── noop.py
│       │   └── telegram.py
│       └── runtime/
│           ├── paper_bot.py
│           ├── api_server.py
│           └── telegram_commands.py
├── tests/
│   ├── test_strategy.py
│   ├── test_paper_broker.py
│   ├── test_paper_trading_bot.py
│   ├── test_api_server.py
│   ├── test_config.py
│   └── test_telegram_command_handler.py
├── .openclaw/   # OpenClaw 상태/설정 (gitignore)
└── .tools/      # 로컬 Node/OpenClaw 실행 도구 (gitignore)
```

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
- `GET /telegram-commands`: Telegram 명령 수행 ON/OFF 상태 조회
- `POST /telegram-commands/enable`: Telegram 명령 수행 ON
- `POST /telegram-commands/disable`: Telegram 명령 수행 OFF
- 선택형 인증: `BOT_API_TOKEN` 설정 시 `Authorization: Bearer <token>` 또는 `X-API-Token` 필요

## Docker 실행
```bash
cp .env.example .env
docker compose up --build -d
curl http://127.0.0.1:8080/status
```
기본 포트 바인딩은 `127.0.0.1:8080:8080`(로컬 전용)입니다.

## 환경변수
`.env.example` 참고:
- 전략/주문: `BOT_SYMBOL`, `BOT_QUANTITY`, `BOT_SHORT_WINDOW`, `BOT_LONG_WINDOW`
- 자금/제한: `BOT_INITIAL_CASH_USD`, `BOT_MAX_POSITION_QTY`
- 런타임: `BOT_TICK_SECONDS`, `BOT_SERVER_HOST`, `BOT_SERVER_PORT`
- API 보안: `BOT_API_TOKEN` (선택형)
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

## 브랜치 운영 전략
- `main`: GPT(OpenAI) 기준 운영 브랜치
- `GPT`: GPT 실험/개선 브랜치(필요 시 `main`과 동기화)
- `Claude`: Claude(Anthropic) 기준 스냅샷 보관 브랜치

브랜치 전환 명령:
```bash
git switch main
git switch GPT
git switch Claude
```

`main`에서 `GPT` 동기화 예시:
```bash
git switch GPT
git merge --ff-only main
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

## 최종 목표 대비 현재 진행도 (2026-02-16)
- 대략 **42%**
- 기준: 1차 목표 구현 + OpenClaw 분리 연동 + 로컬 전용 보안 정책(토큰/루프백/명령 토글) 반영 완료, 2~4차 목표(나무 조회/실주문/실운영)는 본격 구현 전 단계

## 2026-02-16 작업 요약 (보안 우선)
반영 전 상태:
- 제어 API는 인증 없이 동작 가능한 기본 구성 위험이 있었고, 외부 바인딩 설정 여지가 있었습니다.
- OpenClaw는 Telegram 채널 연동은 되었지만, 코딩 에이전트 응답용 모델 인증이 준비되지 않았습니다.
- 트레이딩봇 Telegram 명령은 영문 `/help` 중심이었습니다.

반영 후 상태:
- 제어 API는 `BOT_API_TOKEN` 인증을 적용하고 로컬 전용(`127.0.0.1`) 정책으로 고정했습니다.
- Docker 포트도 루프백(`127.0.0.1:8080:8080`)으로 제한했습니다.
- OpenClaw와 트레이딩봇 Telegram 토큰을 분리 운영하도록 정리/적용했습니다.
- 트레이딩봇 Telegram 명령 제어 API(`GET/POST /telegram-commands*`)를 추가했습니다.
- `/명령어` 한글 명령 별칭을 추가해 명령 목록을 바로 확인 가능하게 했습니다.
- OpenClaw 워크스페이스를 프로젝트 루트(`/home/wsl/VibeCodingPractice`)로 전환했습니다.

장점:
- 외부 노출 면이 크게 줄어 운영 리스크가 낮아졌습니다.
- OpenClaw를 중심으로 Codex 작업/트레이딩봇 제어를 분리 운영할 기반이 생겼습니다.
- 실운영 전환 시 트레이딩봇 Telegram 명령 OFF 전환이 API로 즉시 가능합니다.

단점/트레이드오프:
- OpenClaw 코딩 대화는 모델 API 키 등록이 완료돼야 동작합니다.
- 로컬 전용 정책 때문에 원격 제어는 별도 터널/프록시 없이는 불가능합니다.
- 기존 `REME` 파일명 레거시가 남아 문서 규칙이 과거 기록과 혼재됩니다.

하루 Vibe Coding 요약:
- 봇 런타임/Telegram 제어/문서 체계를 확장하고, OpenClaw 연동을 실사용 기준으로 재정렬했습니다.
- 보안 정책은 “외부 비공개 + 토큰 인증 + 토큰 분리”로 수렴했습니다.
- 다음 실질 블로커는 OpenClaw 코딩 모델 인증(Anthropic/OpenAI 키 등록)입니다.
