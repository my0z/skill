#!/usr/bin/env bash
# plugins.txt 의 플러그인과 skills/ 의 스킬을 사용자 전역(~/.claude)에 설치한다.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# movie-trailer 스킬 의존성 (ffmpeg bc 한글 폰트)
if ! command -v ffmpeg >/dev/null || ! command -v bc >/dev/null || [ -z "$(fc-list :lang=ko 2>/dev/null)" ]; then
  SUDO=$([ "$(id -u)" = 0 ] || echo sudo)
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg bc fonts-nanum fontconfig || echo "movie-trailer 의존성 설치 실패 (수동 설치 필요)"
fi

command -v claude >/dev/null || { echo "claude CLI 없음"; exit 1; }

grep -vE '^\s*(#|$)' "$DIR/plugins.txt" | while read -r market plugin; do
  claude plugin marketplace add "$market" </dev/null || true
  claude plugin marketplace update "${plugin#*@}" </dev/null || true
  claude plugin install "$plugin" --scope user </dev/null
done

mkdir -p "$HOME/.claude/skills"
for s in "$DIR"/skills/*/; do
  [ -f "$s/SKILL.md" ] && cp -r "$s" "$HOME/.claude/skills/"
done
echo "완료"
