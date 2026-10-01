#!/usr/bin/env bash
# plugins.txt 의 플러그인과 skills/ 의 스킬을 사용자 전역(~/.claude)에 설치한다.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v claude >/dev/null || { echo "claude CLI 없음"; exit 1; }

seen=" "
failed=""
while read -r market plugin; do
  name="${plugin#*@}"
  if [[ "$seen" != *" $name "* ]]; then
    claude plugin marketplace add "$market" </dev/null || true
    claude plugin marketplace update "$name" </dev/null || true
    seen+="$name "
  fi
  claude plugin install "$plugin" --scope user </dev/null || failed+=" $plugin"
done < <(grep -vE '^\s*(#|$)' "$DIR/plugins.txt")

mkdir -p "$HOME/.claude/skills"
for s in "$DIR"/skills/*/; do
  [ -f "$s/SKILL.md" ] && cp -r "$s" "$HOME/.claude/skills/"
done
[ -n "$failed" ] && echo "설치 실패:$failed"
echo "완료"
