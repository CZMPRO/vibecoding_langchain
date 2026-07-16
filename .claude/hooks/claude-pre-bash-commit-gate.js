#!/usr/bin/env node
/**
 * Claude Code PreToolUse（matcher: Bash）
 * 若即将执行 git commit，则校验双通行证；否则放行。
 * 拒绝：exit 2 + stderr
 */
const fs = require('fs')
const path = require('path')
const { spawnSync } = require('child_process')
const { findRoot } = require('./project-root')

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8')
  } catch {
    return ''
  }
}

const raw = readStdin()
let data = {}
try {
  data = raw ? JSON.parse(raw) : {}
} catch {
  process.exit(0)
}

const toolName = data.tool_name || data.toolName || ''
const input = data.tool_input || data.toolInput || {}
const command = String(input.command || input.cmd || '')

if (toolName && toolName !== 'Bash') {
  process.exit(0)
}

function stripQuoted(s) {
  return s
    .replace(/\\./g, ' ')
    .replace(/"[^"]*"/g, '""')
    .replace(/'[^']*'/g, "''")
}

const bare = stripQuoted(command)

function statementIsGitCommit(stmt) {
  const t = stmt.trim().replace(/^\s*\d+\s*<\s*/, '')
  if (/^(echo|printf|cat|grep|rg|sed|awk|head|tail|less|more)\b/i.test(t)) {
    return false
  }
  return (
    /(?:^|[;&|]\s*)git(?:\s+-c\s+\S+)?\s+commit\b/.test(t) ||
    /^git(?:\s+-c\s+\S+)?\s+commit\b/.test(t)
  )
}

const isCommit = bare.split(/(?:&&|\|\||;|\n)/).some(statementIsGitCommit)

if (!isCommit) {
  process.exit(0)
}

if (/(--no-verify|\s-n\b)/.test(bare)) {
  console.error('[错误] 禁止使用 --no-verify / -n 绕过提交门禁。请先取得 tester 与 quality 通行证。')
  process.exit(2)
}

const root = findRoot(process.cwd())
const checker = path.join(root, '.claude', 'hooks', 'check-pass-gate.js')
const result = spawnSync(process.execPath, [checker], {
  env: { ...process.env, LANGCHAINRAG_ROOT: root, NAILONG_ROOT: root },
  encoding: 'utf8',
})

if (result.stdout) process.stderr.write(result.stdout)
if (result.stderr) process.stderr.write(result.stderr)

if (result.status !== 0) {
  process.exit(2)
}
process.exit(0)
