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

