# skill

모든 Claude Code 대화창에 같은 스킬과 플러그인을 적용하기 위한 허브 저장소.

## 구성

- `plugins.txt` 전역 설치할 플러그인 목록 (아래 표)
- `skills/` 직접 만든 스킬 폴더 (폴더마다 `SKILL.md`)
- `install.sh` 위 두 가지를 사용자 범위(`~/.claude`)에 설치

## 설치되는 플러그인

| 플러그인 | 하는 일 |
|---|---|
| ponytail | 기존 설치 항목 |
| andrej-karpathy-skills | 카파시식 코딩 원칙으로 과한 수정과 추측 코딩 방지 |
| caveman | 짧은 말투로 토큰 사용량 절감 |
| ui-ux-pro-max | UI와 UX 디자인 지식 제공 |
| mattpocock-skills | handoff 포함 실무용 스킬 모음 |
| superpowers | 브레인스토밍과 계획과 TDD와 디버깅 흐름 |
| claude-mem | 지난 세션 작업을 기억해 다음 세션에 전달 |
| planning-with-files | 계획과 진행 상황을 파일로 남겨 긴 작업 유지 |
| example-skills | 앤트로픽 공식 스킬 (skill-creator 프론트엔드 디자인 웹앱 테스트 등) |
| cloudflare | Workers · D1 · R2 · Durable Objects 개발 스킬 (이 프로젝트의 워커) |
| claude-md-management | CLAUDE.md 점검과 갱신 |
| claude-code-setup | 코드베이스에 맞는 훅 · 스킬 · 자동화 추천 |
| code-simplifier | 코드를 읽기 쉽게 다듬는 에이전트 |
| commit-commands | 커밋 · 푸시 · PR 명령 모음 |
| security-guidance | 쓰는 코드의 보안 위험을 바로 알려 줌 |
| feature-dev | 기능 개발 흐름 (탐색 · 설계 · 구현 · 검토) |
| pr-review-toolkit | PR 검토 에이전트 모음 |
| hookify | 원치 않는 동작을 막는 훅을 쉽게 만들기 |
| frontend-design | 화면 디자인 품질을 높이는 스킬 |
| instagram-agent | 인스타그램 릴스 · 캡션 · 캐러셀 · 프로필 점검 · 휴머나이저 스킬 13종 |

## 적용

로컬 PC에서 한 번 실행하면 그 PC의 모든 대화창에 적용된다.

```
git clone https://github.com/my0z/skill ~/skill && ~/skill/install.sh
```

클라우드(claude.ai/code) 세션은 컨테이너가 매번 새로 만들어지므로 환경 설정의 Setup script에 아래 한 줄을 넣는다. 그 환경으로 여는 모든 세션에 적용된다.

```
git clone --depth 1 https://github.com/my0z/skill /tmp/skill && /tmp/skill/install.sh
```

## 새 스킬 또는 플러그인 추가

- 플러그인은 `plugins.txt`에 `owner/repo 플러그인@마켓플레이스` 한 줄 추가
- 스킬은 `skills/<이름>/SKILL.md` 추가
- 푸시 후 로컬은 `cd ~/skill && git pull && ./install.sh` 실행 / 클라우드는 새 세션부터 자동 반영
