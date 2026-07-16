---
name: run-app
description: >
  启动 LangChainRAG 本机双进程：FastAPI 后端 + Vue 前端开发服务器。
  用户输入 /run-app，或说「启动应用」「打开项目」「运行项目」「启动开发环境」「跑起来」时务必使用本技能。
---

# 启动 LangChainRAG（本机双进程）

本技能只负责把**后端 + 前端**以开发模式跑起来，让用户浏览器可访问问答系统。  
**不用 Docker。**

## 默认方式

需要 **两个终端/后台进程**：

### 终端 A — 后端（端口 8000）

```bash
cd backend
# 若无虚拟环境：
.venv\Scripts\activate
python run.py
```

成功标志：访问 `http://127.0.0.1:8000/health` 返回 ok。

### 终端 B — 前端（端口 5173，被占用时 Vite 可能用 5174）

```bash
cd frontend
npm run dev
```

浏览器打开终端打印的 Local 地址（一般为 `http://localhost:5173`）。

## 执行步骤

1. **确认仓库根**  
   存在 `backend/run.py` 与 `frontend/package.json`。

2. **后端依赖**  
   - 无 `.venv` 时：`python -m venv .venv` 后 `pip install -r requirements.txt`  
   - 确认 `backend/.env` 存在（可从 `.env.example` 复制）；缺 Key 时聊天会失败但可先起服务  

3. **前端依赖**  
   - 无 `node_modules`：`cd frontend && npm install`  

4. **启动顺序**  
   - **先后端、后前端**（避免代理 `ECONNREFUSED 8000`）  
   - 两进程均用**后台**启动，避免卡死对话  
   - 启动后 `curl` 健康检查 + 说明前端 URL  

5. **默认账号**  
   - 管理员：`admin` / `123456`  

6. **汇报**  
   - 成功：后端 health、前端地址、如何登录  
   - 失败：贴报错 + 大白话（端口占用、缺依赖、.env、网关 8317 未开等）  

## 不要做的事

- 用户只想「打包/构建」→ 用 `/rebuild-app`，不要只当启动  
- 不要默认 `git commit` / `push`  
- 不要删除 `backend/data` 业务库/向量库  
- 不要把 `.env` 里的 Key 打进聊天记录全文  

## 与 rebuild 区别

| 技能 | 目的 | 结果 |
|------|------|------|
| `/run-app` | 日常调试 | 8000 + 5173 热更新 |
| `/rebuild-app` | 前端生产构建等 | `frontend/dist` 等产物 |

## 沟通

- 全程简体中文；结论 → 地址 → 下一步  
- 工具 `description` 用中文  
