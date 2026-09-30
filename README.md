# skill

모든 Claude Code 대화창에 같은 스킬과 플러그인을 적용하기 위한 허브 저장소.

## 구성

- `plugins.txt` 전역 설치할 플러그인 목록 (현재 ponytail)
- `skills/` 직접 만든 스킬 폴더 (폴더마다 `SKILL.md`)
- `install.sh` 위 두 가지를 사용자 범위(`~/.claude`)에 설치

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
