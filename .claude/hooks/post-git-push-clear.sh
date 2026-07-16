#!/bin/sh
# Git post-push / 手动调用：push 成功后删除通行证

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT" ]; then
  ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
fi

export LANGCHAINRAG_ROOT="$ROOT"
export NAILONG_ROOT="$ROOT"
node "$ROOT/.claude/hooks/clear-pass-gate.js"
exit 0
