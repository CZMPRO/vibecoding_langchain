#!/usr/bin/env node
/**
 * Claude Code PostToolUse（matcher: Bash）
 * 若刚执行的是成功的 git push，则删除双通行证。
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
const toolResult = data.tool_result || data.toolResult || data.response || {}

if (toolName && toolName !== 'Bash') {
  process.exit(0)
}

const bare = command
  .replace(/\\./g, ' ')
  .replace(/"[^"]*"/g, '""')
  .replace(/'[^']*'/g, "''")
const isPush = /\bgit\s+push\b/.test(bare)
if (!isPush) {
  process.exit(0)
}

const exitCode =
  toolResult.exit_code ??
  toolResult.exitCode ??
  data.exit_code ??
  data.exitCode
if (exitCode !== undefined && exitCode !== null && Number(exitCode) !== 0) {
  process.exit(0)
}

const root = findRoot(process.cwd())
const clearer = path.join(root, '.claude', 'hooks', 'clear-pass-gate.js')
spawnSync(process.execPath, [clearer], {
  env: { ...process.env, LANGCHAINRAG_ROOT: root, NAILONG_ROOT: root },
  encoding: 'utf8',
  stdio: 'inherit',
})
process.exit(0)
