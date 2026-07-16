#!/usr/bin/env node
/**
 * LangChainRAG — push 成功后删除双通行证（一次一检，用完作废）
 */
const fs = require('fs')
const path = require('path')
const { findRoot } = require('./project-root')

const root = process.env.LANGCHAINRAG_ROOT || process.env.NAILONG_ROOT || findRoot(process.cwd())
const states = path.join(root, '.claude', 'states')
for (const name of ['tester-pass.json', 'quality-pass.json']) {
  const p = path.join(states, name)
  try {
    fs.unlinkSync(p)
  } catch {
    // 文件不存在则忽略
  }
}
console.log('[门禁] 已删除本地通行证（下次提交需重新检查）。')
process.exit(0)
