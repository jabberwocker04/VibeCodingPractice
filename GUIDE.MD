# GUIDE.MD

Telegram에서 `namoo-overseas-bot` 제어에 사용하는 명령어 안내입니다.

## 사용 전 준비
1. `.env` 설정
- `TELEGRAM_ENABLED=true`
- `TELEGRAM_BOT_TOKEN=<BotFather에서 발급된 토큰>`
- `TELEGRAM_CHAT_ID=<명령을 허용할 chat id>`
- `TELEGRAM_COMMANDS_ENABLED=true`

2. 서버 실행
```bash
namoo-bot-server --csv data/sample_us_stock.csv --symbol AAPL
```

## Telegram 명령어
- `/help`: 지원 명령어 목록 출력
- `/명령어`: 지원 명령어 목록 출력(한글 별칭)
- `/status`: 현재 봇 상태 조회
  - 출력 항목: `running`, `paused`, `trades`, `position_qty`, `cash`, `equity`, `last_signal`, `last_price`
- `/pause`: 매매 루프 일시정지
- `/resume`: 매매 루프 재개
- `/stop`: 매매 루프 중지

## 동작 규칙
- 명령은 `.env`의 `TELEGRAM_CHAT_ID`와 일치하는 채팅에서만 처리됩니다.
- `/`로 시작하지 않는 일반 텍스트는 명령으로 처리되지 않습니다.
- 지원하지 않는 명령은 `/help` 안내 메시지가 반환됩니다.

## 빠른 연동 점검
```bash
namoo-telegram-check
```

나무 실조회/재기동 자동화 (Windows PowerShell)
아래는 `scripts/windows/` 기준 자동화입니다.

### 1) Phase1 실조회 검증 (권장 선행)
언제 실행:
- 최초 셋업 직후
- 계정/비밀번호/hash44 변경 직후
- 장 시작 전 상태 확인이 필요할 때

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\phase1_wmca_check.ps1 `
  -DllPath C:\wmca\bin\wmca.dll `
  -AccountIndex 1 `
  -AccountPasswordHash44 <계좌비밀번호_hash44> `
  -OrderDate 20260217 `
  -LoginId <OpenAPI_ID> -LoginPassword <OpenAPI_로그인비밀번호> -CertPassword <인증서비밀번호>
```

결과 로그:
- `data/wmca_phase1_logs/<timestamp>/summary.json`
- `data/wmca_phase1_logs/<timestamp>/balance.json`
- `data/wmca_phase1_logs/<timestamp>/positions.json`
- `data/wmca_phase1_logs/<timestamp>/orders.json`

### 2) 브리지/봇 재기동 자동화
언제 실행:
- 서버 장애 후 재기동 시
- 운영 시작 시 브리지와 봇을 순차 기동할 때

브리지만 기동:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_stack.ps1 `
  -DllPath C:\wmca\bin\wmca.dll `
  -AccountIndex 1 `
  -AccountPasswordHash44 <계좌비밀번호_hash44> `
  -OrderDate 20260217 `
  -LoginId <OpenAPI_ID> -LoginPassword <OpenAPI_로그인비밀번호> -CertPassword <인증서비밀번호> `
  -BridgeToken <브리지_API_토큰>
```

브리지 + 봇 동시 기동:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_stack.ps1 `
  -DllPath C:\wmca\bin\wmca.dll `
  -AccountIndex 1 `
  -AccountPasswordHash44 <계좌비밀번호_hash44> `
  -OrderDate 20260217 `
  -LoginId <OpenAPI_ID> -LoginPassword <OpenAPI_로그인비밀번호> -CertPassword <인증서비밀번호> `
  -BridgeToken <브리지_API_토큰> `
  -StartBotServer `
  -BotCsvPath data/sample_us_stock.csv `
  -BotSymbol AAPL
```

빠른 재기동(이미 장중 검증을 마친 경우):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_stack.ps1 `
  -SkipPhase1 `
  -DllPath C:\wmca\bin\wmca.dll `
  -AccountIndex 1 `
  -AccountPasswordHash44 <계좌비밀번호_hash44> `
  -BridgeToken <브리지_API_토큰> `
  -StartBotServer
```

## 장애 대응 가이드 (임시 운영안)
1. 명령을 보냈는데 반응이 없을 때
- 먼저 `/help`를 보내 기본 응답 여부를 확인합니다.
- `.env`의 `TELEGRAM_CHAT_ID`가 현재 채팅 ID와 일치하는지 확인합니다.
- `TELEGRAM_ENABLED=true`와 `TELEGRAM_COMMANDS_ENABLED=true`가 설정됐는지 확인합니다.

2. `/status`가 오래된 값으로 보일 때
- 봇 서버가 살아있는지 `GET /health`로 확인합니다.
- 장시간 네트워크 불안정 시 명령 폴링이 지연될 수 있으므로 서버를 재기동합니다.

3. 봇이 멈췄거나 비정상 동작할 때
- 제어 API `POST /stop`으로 안전 종료 후 재시작합니다.
- 재시작 후 첫 명령은 `/status`로 현재 상태를 확인한 뒤 운영을 재개합니다.

4. 권장 운영 절차
- 운영 시작 직후 `/status`
- 일시 중지 필요 시 `/pause`
- 재개 시 `/resume`
- 종료 시 `/stop`
