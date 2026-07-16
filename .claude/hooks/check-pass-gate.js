#!/usr/bin/env node
/**
 * LangChainRAG — 双通行证校验（供 Git pre-commit 与 Claude PreToolUse 共用）
 * 退出码 0 = 放行；非 0 = 拒绝
 */
const fs = require('fs')
const path = require('path')
const { findRoot } = require('./project-root')

const MAX_AGE_SEC = 300

const root = process.env.LANGCHAINRAG_ROOT || process.env.NAILONG_ROOT || findRoot(process.cwd())
const testerPass = path.join(root, '.claude', 'states', 'tester-pass.json')
const qualityPass = path.join(root, '.claude', 'states', 'quality-pass.json')

function fail(msg) {
  console.error('')
  console.error('[错误] 提交门禁拦截：' + msg)
  console.error('')
  console.error('请先完成检查并取得通行证，推荐：')
  console.error('  1) 运行子代理 gitcommit-agent（并行测试+质检后存档），或')
  console.error('  2) 分别运行 tester 与 quality-engineer，通过后再提交')
  console.error('')
  console.error('通行证文件（本地，勿提交）：')
  console.error('  .claude/states/tester-pass.json')
  console.error('  .claude/states/quality-pass.json')
  console.error('有效条件：status 为 passed，且 at 时间在 ' + MAX_AGE_SEC + ' 秒内。')
  console.error('禁止使用 --no-verify 绕过本门禁。')
  console.error('项目根：' + root)
  console.error('')
  process.exit(1)
}

if (!fs.existsSync(testerPass)) {
  fail('缺少单元测试通行证 tester-pass.json')
}
if (!fs.existsSync(qualityPass)) {
  fail('缺少质量检查通行证 quality-pass.json')
}

const now = Date.now()
const files = [
  { path: testerPass, label: '单元测试' },
  { path: qualityPass, label: '质量检查' },
]

for (const f of files) {
  let data
  try {
    data = JSON.parse(fs.readFileSync(f.path, 'utf8'))
  } catch {
    fail('无法解析 ' + f.label + ' 通行证 JSON')
  }
  if (data.status !== 'passed') {
    fail(f.label + ' 通行证 status 不是 passed（当前: ' + data.status + '）')
  }
  if (!data.at) {
    fail(f.label + ' 通行证缺少 at 时间字段')
  }
  const t = Date.parse(data.at)
  if (Number.isNaN(t)) {
    fail(f.label + ' 通行证 at 时间无法解析: ' + data.at)
  }
  const ageSec = (now - t) / 1000
  if (ageSec > MAX_AGE_SEC) {
    fail(f.label + ' 通行证已过期（约 ' + Math.floor(ageSec) + ' 秒前，上限 ' + MAX_AGE_SEC + ' 秒）')
  }
  if (ageSec < -60) {
    fail(f.label + ' 通行证时间异常（at 在未来）')
  }
}

console.log('[成功] 单元测试与质量检查通行证均有效，允许提交。')
process.exit(0)
