# SECURITY.MD

보안 검토 및 대응 상태를 추적하는 문서입니다.

## 검토 기준일
- 2026-02-16

## 핵심 이슈 및 상태
1. 제어 API 인증 부재 + 외부 바인딩 기본값
- 위험도: High
- 현재 상태: **부분 대응 완료**
- 반영 내용:
  - 선택형 API 토큰 인증 추가 (`BOT_API_TOKEN`)
  - 인증 시 `Authorization: Bearer <token>` 또는 `X-API-Token` 사용 가능
- 남은 작업:
  - 운영 시 `BOT_API_TOKEN` 실제 값 설정
  - API 바인딩 정책(`127.0.0.1` vs 외부 공개) 최종 확정

2. Telegram 명령 권한 통제 범위(`chat_id` 기반)
- 위험도: High
- 현재 상태: **예외 처리(사용자 정책)**
- 사유:
  - 현재는 개인 봇 용도로 사용하여 그룹 다중 사용자 위협 시나리오를 운영 범위에서 제외
- 비고:
  - 향후 그룹 운영 전환 시 `user_id allowlist` 추가 필요

3. OpenClaw/트레이딩봇 토큰 공유 리스크
- 위험도: Medium~High
- 현재 상태: **분리 완료**
- 목표:
  - 트레이딩봇 Telegram 토큰과 OpenClaw Telegram 토큰 분리
  - 장애/권한/레이트리밋 영향 분리

4. 감사 추적(로깅) 부족
- 위험도: Medium
- 현재 상태: 미대응
- 계획:
  - 제어 API 호출 로그(요청 IP, endpoint, 성공/실패) 추가
  - Telegram 명령 처리 실패 사유 로그 개선

## 구현된 제어 기능 (미래 OpenClaw 운영용)
- 트레이딩봇 Telegram 명령 수행 On/Off 제어 API 추가:
  - `GET /telegram-commands`
  - `POST /telegram-commands/enable`
  - `POST /telegram-commands/disable`
- 현재 정책:
  - 테스트 단계에서는 Telegram 명령 수신 기본 ON 유지
  - OpenClaw 전환 완료 시 OFF 전환 가능

## 운영 체크리스트
1. 토큰 분리 확인
- 트레이딩봇 토큰과 OpenClaw 토큰이 서로 다른지 확인

2. API 인증 적용
- `BOT_API_TOKEN` 설정
- 운영 스크립트/도구(OpenClaw 포함)에서 인증 헤더 전달

3. API 노출 범위 확인
- 외부 공개가 필요 없으면 `BOT_SERVER_HOST=127.0.0.1` 사용
- 외부 공개가 필요하면 방화벽/리버스프록시/TLS와 함께 운영

4. OpenClaw Telegram 사용자 제한
- `jabberwocker0` 사용자 제한 요구가 있으나, 현재 OpenClaw Telegram 채널 CLI는 사용자 allowlist 설정을 직접 지원하지 않음
- 우회 방안:
  - 운영 절차상 DM 전용 사용
  - 명령 처리 시점에 별도 검증 레이어(브리지/미들웨어) 도입
