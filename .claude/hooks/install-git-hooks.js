#!/usr/bin/env node
/**
 * 为本仓库启用 Git 原生钩子：
 *   git config core.hooksPath .claude/hooks/git
 *
 * 之后 git commit / git push 会走双通行证校验。
 */
const { spawnSync } = require('child_process')
const fs = require('fs')
const path = require('path')
const { findRoot } = require('./project-root')

const root = findRoot(process.cwd())
const hooksPath = '.claude/hooks/git'
const absHooks = path.join(root, hooksPath)

if (!fs.existsSync(path.join(absHooks, 'pre-commit'))) {
  console.error('[错误] 找不到 ' + path.join(hooksPath, 'pre-commit'))
  process.exit(1)
}

const r = spawnSync('git', ['config', 'core.hooksPath', hooksPath], {
  cwd: root,
  encoding: 'utf8',
})

if (r.status !== 0) {
  console.error('[错误] 设置 core.hooksPath 失败：' + (r.stderr || r.stdout || ''))
  process.exit(1)
}

// 确保钩子可执行（Git Bash / macOS / Linux）
for (const name of ['pre-commit', 'pre-push']) {
  const p = path.join(absHooks, name)
  try {
    fs.chmodSync(p, 0o755)
  } catch {
    // Windows 可能忽略 chmod
  }
}

const check = spawnSync('git', ['config', '--get', 'core.hooksPath'], {
  cwd: root,
  encoding: 'utf8',
})
console.log('[成功] 已启用 Git 原生门禁钩子')
console.log('  项目根: ' + root)
console.log('  core.hooksPath = ' + String(check.stdout || '').trim())
console.log('  生效钩子: pre-commit, pre-push（校验 tester-pass + quality-pass）')
console.log('')
console.log('说明：Claude Code 的 PreToolUse 钩子（settings.json）仍保留，用于对话里执行 git 时拦截。')
process.exit(0)
