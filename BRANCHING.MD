# BRANCHING.MD

OpenClaw 기반 Vibe Coding 운영을 위한 브랜치 정책입니다.

## 브랜치 역할
- `main`: GPT(OpenAI) 기준 운영 브랜치
- `GPT`: GPT 기능 실험/검증 브랜치
- `Claude`: Claude(Anthropic) 기준 스냅샷 보관 브랜치

## 기본 원칙
- 일상 개발/운영 기준은 `main`으로 유지합니다.
- GPT 실험은 `GPT`에서 수행하고, 안정화 후 `main`으로 반영합니다.
- `Claude`는 비교/복구 용도로 보존하고 직접 개발 브랜치로 쓰지 않습니다.

## 브랜치 전환
```bash
git switch main
git switch GPT
git switch Claude
```

## 동기화 흐름
1. `main -> GPT` 동기화
```bash
git switch GPT
git merge --ff-only main
```

2. `GPT -> main` 반영
```bash
git switch main
git merge --ff-only GPT
```

## OpenClaw 모델 정책
- `main`/`GPT` 운영 시 기본 모델 제공자는 OpenAI를 사용합니다.
- `Claude`는 Anthropic 구성 참조용으로 유지합니다.
