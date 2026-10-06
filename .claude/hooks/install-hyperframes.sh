#!/bin/bash
# Installiert HeyGen HyperFrames (CLI, Chrome Headless Shell, Agent-Skills) in Cloud-Sessions.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

command -v hyperframes >/dev/null 2>&1 || npm install -g hyperframes >/dev/null 2>&1

if ! command -v ffmpeg >/dev/null 2>&1; then
  (apt-get update -qq && apt-get install -y -qq ffmpeg) >/dev/null 2>&1 || true
fi

hyperframes browser ensure >/dev/null 2>&1 || true
[ -d "$HOME/.claude/skills/hyperframes" ] || hyperframes skills >/dev/null 2>&1 || true
