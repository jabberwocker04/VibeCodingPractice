# GUIME.MD

Telegram에서 주식봇을 운영할 때 쓰는 명령어 가이드입니다.

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
- `/help`: 명령어 목록 확인
- `/명령어`: 명령어 목록 확인(한글 별칭)
- `/status`: 현재 상태 조회
  - running/paused, trades, position, cash, equity, last_signal, last_price
- `/pause`: 매매 루프 일시정지
- `/resume`: 매매 루프 재개
- `/stop`: 매매 루프 중지

## 운영 규칙
- 명령은 `.env`의 `TELEGRAM_CHAT_ID`와 일치하는 채팅에서만 처리됩니다.
- 지원하지 않는 명령은 안내 메시지로 응답합니다.
- 알림 문구는 한국어 기준이며, 티커/수치/식별값은 원문으로 표시됩니다.

## 빠른 점검
```bash
namoo-telegram-check
```
- 위 명령이 성공하면 Telegram 알림 기본 연동은 정상입니다.
