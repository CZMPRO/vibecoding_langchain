/**
 * 定位 LangChainRAG 仓库根目录（含 backend/ + frontend/）。
 * 兼容：尚未 init git、cwd 在 backend/frontend 子目录等情况。
 */
const fs = require('fs')
const path = require('path')

function isLangChainRoot(dir) {
  const backendRun = path.join(dir, 'backend', 'run.py')
  const frontendPkg = path.join(dir, 'frontend', 'package.json')
  const readme = path.join(dir, 'README.md')
  // 主判定：双端骨架
  if (fs.existsSync(backendRun) && fs.existsSync(frontendPkg)) {
    return true
  }
  // 兜底：git + README + backend
  if (
    fs.existsSync(path.join(dir, '.git')) &&
    fs.existsSync(readme) &&
    fs.existsSync(path.join(dir, 'backend'))
  ) {
    return true
  }
  return false
}

function findRoot(start) {
  let dir = path.resolve(start || process.cwd())
  for (let i = 0; i < 24; i++) {
    if (isLangChainRoot(dir)) return dir
    const parent = path.dirname(dir)
    if (parent === dir) break
    dir = parent
  }
  return path.resolve(start || process.cwd())
}

module.exports = { findRoot, isLangChainRoot }
