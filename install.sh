#!/usr/bin/env bash
# plugins.txt 의 플러그인과 skills/ 의 스킬을 사용자 전역(~/.claude)에 설치한다.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v claude >/dev/null || { echo "claude CLI 없음"; exit 1; }

# 한 줄이 실패해도 나머지는 계속 설치한다 (세션 시작이 막히지 않게)
grep -vE '^\s*(#|$)' "$DIR/plugins.txt" | while read -r market plugin; do
  claude plugin marketplace add "$market" </dev/null || true
  claude plugin marketplace update "${plugin#*@}" </dev/null || true
  claude plugin install "$plugin" --scope user </dev/null || echo "설치 실패 (건너뜀): $plugin"
done

mkdir -p "$HOME/.claude/skills"
for s in "$DIR"/skills/*/; do
  [ -f "$s/SKILL.md" ] && cp -r "$s" "$HOME/.claude/skills/"
done
echo "완료"
