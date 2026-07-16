#!/bin/sh
# Git pre-commit / 手动调用：校验双通行证

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT" ]; then
  ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
fi

export LANGCHAINRAG_ROOT="$ROOT"
export NAILONG_ROOT="$ROOT"
node "$ROOT/.claude/hooks/check-pass-gate.js"
exit $?
