# 基于 LangChain 的电商企业级知识库 RAG 问答系统

毕设项目：用户在浏览器中管理商品知识库、进行多用户多会话问答，回答可展示知识库引用片段。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router |
| 后端 | FastAPI + SQLAlchemy + SQLite + JWT |
| RAG | LangChain + OpenAI 兼容 LLM/Embedding + Chroma |
| 部署 | Windows 本机双进程（**不需要 Docker**） |

## 功能清单

1. 管理员知识库管理（上传/删除/状态/重试）
2. 知识库问答 + **引用片段展示** + **SSE 流式输出**
3. 多用户多会话，数据按用户隔离
4. 会话历史持久化，重新登录可找回
5. 注册 / 登录 / 修改密码
6. 默认管理员 `admin` / `123456`（仅管理员可进知识库管理）
7. 企业级优化：异步入库、检索缓存、单例客户端、限流、分页等
8. 加分：会话重命名、点赞点踩、运营统计面板

## 环境要求

- Windows 10/11
- Python 3.11+（推荐 3.12）
- Node.js 18+（推荐 20/22）
- 可用的 **OpenAI 兼容** 第三方接口（聊天模型 + Embedding 模型）

## 快速开始

### 1. 配置后端密钥

```bash
cd backend
copy .env.example .env
```

用记事本打开 `backend/.env`，填入你的：

```env
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://你的地址/v1
OPENAI_CHAT_MODEL=你的聊天模型名
# 若第三方没有 embedding 接口，保持下面配置即可（本地哈希向量，免下载）
EMBEDDING_PROVIDER=local
# 若有 embedding 接口，可改为：
# EMBEDDING_PROVIDER=openai
# OPENAI_EMBEDDING_MODEL=你的向量模型名
JWT_SECRET=请改成一串足够长的随机字符
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

成功后访问：http://127.0.0.1:8000/health  
接口文档：http://127.0.0.1:8000/docs

### 3. 启动前端

新开一个终端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：http://127.0.0.1:5173

### 4. 演示路径（答辩可用）

1. 用 `admin` / `123456` 登录
2. 左侧进入 **知识库管理**，上传 `docs/sample_products.md`
3. 等待状态变为 **就绪**
4. 返回问答页，提问例如：
   - 「星辰智能手表支持游泳吗？」
   - 「云朵耳机续航多久？保修政策是什么？」
5. 观察流式回答与下方 **引用片段**
6. 注册一个普通用户：确认其 **看不到** 知识库管理页
7. 刷新浏览器：历史会话仍在

## 默认账号

| 用户名 | 密码 | 权限 |
|--------|------|------|
| admin | 123456 | 管理员（知识库 + 统计 + 问答） |
| 自行注册 | ≥6 位 | 仅问答与会话 |

## 目录结构（简）

```
LangChainRAG/
├── backend/          # FastAPI + LangChain
├── frontend/         # Vue3 管理与问答界面
├── docs/             # 示例知识库与说明
└── README.md
```

## 单元测试

从 bookkeeping 项目迁移了 `/unit-test` 技能（已适配本仓库的 **pytest** 栈）。

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -v
```

当前覆盖：密码/JWT、缓存限流、本地向量、文档加载切块、会话隔离、登录注册改密、知识库权限、会话 API、RAG 辅助函数。

**默认不测**：真实第三方 LLM 调用、Vue 界面点击。

### Claude 技能 / 代理 / 门禁（自 bookkeeping 迁移并适配本栈）

| 类型 | 名称 | 用途 |
|------|------|------|
| 技能 | `/unit-test` | pytest 补测与中文报告 |
| 技能 | `/run-app` | 启动后端 8000 + 前端 5173 |
| 技能 | `/rebuild-app` | 前端 production build（+ 可选 pytest） |
| 技能 | `/git-save` | 中文提交并推送（禁 AI 署名、禁 --no-verify） |
| 技能 | `/security-audit` | FastAPI/JWT/上传/XSS 等安全审计 |
| 技能 | `/comments-check` | 注释充足性与小白可读性 |
| 代理 | `tester` | 跑单测并写 `tester-pass.json` |
| 代理 | `quality-engineer` | 安全+注释并写 `quality-pass.json` |
| 代理 | `gitcommit-agent` | 并行双检 → git-save → 清章 |
| 钩子 | `.claude/hooks/*` | Claude Bash 提交前验双章、push 后清章 |
| Git 钩子 | `.claude/hooks/git/` | 原生 `pre-commit` / `pre-push`（`core.hooksPath`） |

通行证目录：`.claude/states/`（已 gitignore，**勿提交**）。

#### 启用 Git 原生门禁（克隆后执行一次）

```bash
node .claude/hooks/install-git-hooks.js
```

会设置 `git config core.hooksPath .claude/hooks/git`。之后在终端直接 `git commit` / `git push` 也会校验双通行证（不仅 Claude 对话里）。

## 常见问题

### 1. 登录提示用户名或密码错误？

确认后端已启动，并看控制台是否打印「已创建管理员账号」。

### 2. 上传后一直「处理中/失败」？

- 打开文档的「错误信息」列
- 常见原因：`.env` 配置错误、网络不通、文件无文字（扫描版 PDF）
- 当前默认 `EMBEDDING_PROVIDER=local`（本地哈希向量），**不依赖**第三方 embedding 接口

### 3. 回答说「知识库暂未找到」？

- 文档状态是否为「就绪」
- 问题是否与文档内容相关
- 可先用示例问题测试

### 4. 前端跨域？

开发模式请用 `npm run dev`（已配置代理 `/api` → `8000`），不要直接用错误端口访问 API。

## 安全提醒

- **不要**把 `.env` 提交到 Git
- 答辩截图请打码 API Key
- 生产环境务必修改 `JWT_SECRET` 与管理员密码

## 论文可写技术点

1. LangChain RAG 流水线（加载-切块-向量化-检索-生成）
2. 引用可视化与可解释问答
3. JWT 多角色权限与多会话隔离
4. SSE 流式、异步入库、检索缓存等轻量企业级优化
5. OpenAI 兼容接入，便于更换模型供应商
