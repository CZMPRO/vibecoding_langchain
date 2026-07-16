---
name: git-save
description: >
  用 Git 将当前改动存档（暂存+中文提交）并推送到远程仓库。
  用户输入 /git-save，或说「存档」「提交并推送」「git 保存」「推到 GitHub」「保存进度」时务必使用本技能。
---

# Git 存档并推送到远程

本技能只负责：**看清改动 → 用中文提交说明存档 → 推到远程**。  
不做功能开发、不改业务逻辑。

## 目标仓库约定（LangChainRAG）

- 工作目录：项目根目录（有 `backend/`、`frontend/`、`README.md` 的 `LangChainRAG/`）
- 技术栈：FastAPI + Vue3 + SQLite + Chroma（**不是** Electron 桌面应用）
- 主分支通常为：`main`（以实际为准）
- **署名**：仅使用用户本机 Git 配置的个人署名；**禁止**添加 `Co-Authored-By: Claude` 或任何 AI 联合署名
- **语言**：提交说明、对用户汇报、工具 `description` 一律简体中文
- **门禁**：若启用双通行证，`git commit` 会被 hooks 拦截；应先跑 `tester` + `quality-engineer`，或走 `gitcommit-agent`

## 执行步骤（严格按顺序）

### 1. 摸清现状（先看再动）

并行收集：

```bash
git status
git diff
git diff --staged
git log -5 --oneline
git rev-parse --abbrev-ref HEAD
git remote -v
```

若尚未 `git init`：用大白话说明「还不是 Git 仓库」，询问是否初始化；**不要擅自** `git init` + 推送。

### 2. 决定「存什么」

- **默认**：业务代码、文档、`.claude` 技能/代理/钩子（不含 states 通行证）。
- **不要默认加入**：
  - `backend/.venv/`、`frontend/node_modules/`、`frontend/dist/`
  - `backend/data/app.db`、`backend/data/uploads/*`、`backend/data/chroma/*`
  - `.env`、真实 API Key、本机 token
  - `.claude/states/*`（通行证、日志）
  - `.claude/settings.local.json`
- 若工作区干净：说明无可存档内容；若仅有未推送提交，可只 push。
- 疑似敏感信息：先停问用户。

### 3. 起草提交说明（先给用户看再提交）

- 一句中文说清「做了什么、为什么」。
- 风格：`feat:` / `fix:` / `docs:` / `chore:` + 中文。
- 用户已说「直接存档」时可不再二次确认文案。

### 4. 暂存并提交

```bash
git add <具体路径>
git commit -m "$(cat <<'EOF'
<中文提交说明>

EOF
)"
```

- **禁止** `--no-verify` / `-n`
- **禁止** AI 联合署名
- 钩子失败：贴原文 + 大白话，引导跑 `gitcommit-agent` 或双代理

### 5. 推送到远程

```bash
git push -u origin HEAD
# 或
git push
```

- **禁止**默认 `git push --force`
- 失败：贴原文 + 解释

### 6. 汇报结果

1. 结论：存档/推送是否成功  
2. 提交：短哈希 + 说明  
3. 远程与分支  
4. 未纳入文件及原因  

## 与其它能力边界

| 需求 | 用什么 |
|------|--------|
| 存档推送 | **本技能** |
| 测后再提交 | `gitcommit-agent` |
| 只跑单测 | `tester` / `/unit-test` |
| 启动前后端 | `/run-app` |
| 前端生产构建 | `/rebuild-app` |

## 红线

- 不 `reset --hard` / `clean -fd` 除非用户明确要求  
- 不改写已推送历史除非用户明确要求  
- 不提交 `.env` 与向量库/上传数据  
