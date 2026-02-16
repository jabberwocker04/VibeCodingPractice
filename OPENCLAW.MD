# OPENCLAW.MD

트레이딩 봇 운영 시 Telegram 기반 소통/자동화를 위해 OpenClaw를 로컬 연동한 기록입니다.

## 적용 범위
- OpenClaw CLI 로컬 설치
- 로컬 Gateway 실행
- Telegram 채널 연동 확인
- 테스트 메시지 송신 검증
- 트레이딩봇 Telegram 명령 수행 On/Off 제어 연동 준비

## 운영 역할 분리 (목표 운영 모델)
- 사용자 Telegram: OpenClaw 봇과 소통하는 단일 제어 채널
- OpenClaw 봇: Codex 작업 요청 + 트레이딩봇 제어 오케스트레이션
- 트레이딩봇: 주문/전략 실행 전담 런타임 (로컬 API + Telegram 알림)
- 테스트 단계 정책: 트레이딩봇 Telegram 명령 수신은 ON 유지
- 전환 단계 정책: OpenClaw 운영 안정화 후 트레이딩봇 Telegram 명령 수신 OFF

## 비대화형 온보딩으로 진행한 이유
- IDE/에이전트 실행 환경에서 동일 설정을 빠르게 재현하기 위해
- 세션 중단/재시작 시 동일 명령으로 복구 가능한 절차를 만들기 위해
- 대화형 프롬프트 수동 입력에서 발생하는 누락/오입력을 줄이기 위해

## 로컬 구성
- 로컬 Node: `.tools/node22`
- 로컬 OpenClaw CLI: `.tools/npm-global/bin/openclaw`
- OpenClaw 상태/설정: `.openclaw/`
  - 설정 파일: `.openclaw/openclaw.json`
  - 상태 디렉터리: `.openclaw/state`
  - 워크스페이스: `.openclaw/workspace`

## 실행 절차
1. 환경 변수 지정
```bash
export PATH="$PWD/.tools/node22/bin:$PWD/.tools/npm-global/bin:$PATH"
export OPENCLAW_STATE_DIR="$PWD/.openclaw/state"
export OPENCLAW_CONFIG_PATH="$PWD/.openclaw/openclaw.json"
```

2. Gateway 실행
```bash
openclaw gateway run --verbose
```

3. 채널 상태 확인
```bash
openclaw channels status --json
```

4. Telegram 테스트 메시지 송신
```bash
openclaw message send \
  --channel telegram \
  --target "$TELEGRAM_CHAT_ID" \
  --message "[OpenClaw] Telegram 연동 테스트 완료"
```

## 운영 메모
- 현재 구성은 로컬(loopback) 바인딩 기준입니다.
- 민감정보(토큰/키)는 `.env`와 OpenClaw 로컬 상태 파일에서만 관리합니다.
- `.openclaw/`, `.tools/`는 Git 추적에서 제외합니다.
- 트레이딩봇 Telegram 토큰과 OpenClaw Telegram 토큰은 분리 운영합니다.
- 참고: 현재 OpenClaw Telegram 채널은 CLI에서 사용자 allowlist(`jabberwocker0` 등) 직접 설정을 지원하지 않습니다.
- 트레이딩봇 제어 API는 `BOT_SERVER_HOST=127.0.0.1` + `BOT_API_TOKEN` 조합으로 운영합니다.

## 트레이딩봇 Telegram 명령 On/Off 제어 (미래 전환용)
1. 현재 상태 조회
```bash
curl -s http://127.0.0.1:8080/telegram-commands
```

2. 명령 수행 OFF
```bash
curl -s -X POST http://127.0.0.1:8080/telegram-commands/disable
```

3. 명령 수행 ON
```bash
curl -s -X POST http://127.0.0.1:8080/telegram-commands/enable
```

4. API 토큰 적용 시 호출 예시
```bash
curl -s \
  -H "Authorization: Bearer $BOT_API_TOKEN" \
  -X POST \
  http://127.0.0.1:8080/telegram-commands/disable
```
