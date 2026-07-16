---
name: unit-test
description: >
  为 LangChainRAG 电商知识库问答系统智能补写/更新单元测试，用 pytest 执行，
  并输出大白话中文测试报告。用户输入 /unit-test，或说「单元测试」「跑测试」
  「写测试」「测试报告」「帮我测一下代码」时务必使用本技能。
---

# 单元测试（智能补测 + 执行 + 中文报告）

本技能在**本仓库**完成三件事：

1. **创建/更新**单元测试  
2. **执行**测试  
3. **给出**零基础可读的中文测试报告  

默认**不**在本技能内直接拦截 Git 提交、不自动改业务功能“为了让测试凑合通过”（发现业务 bug 先报告；修代码需符合项目协作规范）。

**通行证：** 仓库若启用双通行证门禁，由子代理 **`tester`** 在全部用例真实通过后写入 `.claude/states/tester-pass.json`。失败时不得写 `passed`。

---

## 技术栈（本项目固定）

| 项 | 约定 |
|----|------|
| 被测主体 | `backend/`（FastAPI + LangChain + SQLite + Chroma） |
| 测试框架 | **pytest** + **httpx**（FastAPI TestClient） |
| 用例位置 | `backend/tests/test_*.py` |
| 运行命令 | 见下方「如何执行」 |
| 前端 | 默认不测 Vue 组件观感（除非用户明确要求） |

### 首次脚手架（仅当缺失）

若 `backend/requirements.txt` 无 pytest，或 `backend/tests` 不存在：

1. 安装（在 backend 虚拟环境）：`pip install pytest httpx`  
2. 可增加 `backend/pytest.ini` 或 `backend/pyproject.toml` 中的 pytest 配置  
3. 在 README 中补充：`cd backend && .venv\Scripts\activate && pytest -q`  

用户明确要求写/跑单元测试时，可视为同意安装测试依赖（pytest 属开发依赖，不改变线上业务依赖选型）。

---

## 测试范围（默认）

### 优先（默认要做）

- `app/core/security.py`：密码哈希、JWT 签发与解析  
- `app/utils/cache.py` / `rate_limit.py`：缓存键、限流  
- `app/rag/embeddings.py`：`LocalHashEmbeddings` 维度与稳定性  
- `app/rag/loaders.py` / `splitter.py`：多格式加载与切块（用临时文件）  
- `app/services/chat_service.py`：会话标题、引用解析、用户隔离相关逻辑  
- `app/api/auth.py` 等：用 TestClient 测注册/登录/权限（**临时 SQLite**，不碰业务 `data/app.db`）  

### 默认不做（除非用户明确要求）

- 真实调用第三方 LLM / Embedding 网关（费钱、不稳定）  
- Chroma 全链路依赖本机 GPU/网络的集成测试（可对纯函数 mock）  
- Vue 页面点击流、Element Plus 观感  
- 启动完整前后端窗口（那是运行说明，不是单测）  

### 怎么选“测什么”

1. 看本次改动的逻辑优先补测  
2. 无改动时：对鉴权、会话隔离、向量哈希、文档加载做回归  
3. 一次会话范围克制：宁可少而稳  

---

## 执行步骤（严格顺序）

### 1. 摸底

- 确认在仓库 `LangChainRAG` 根目录或 `backend`  
- 查看是否已有 pytest、`tests/`、已有 `test_*.py`  
- 用中文一句话说明：将测哪些模块  

### 2. 脚手架（按需）

- 缺 pytest → 安装到 backend 虚拟环境  
- 已具备 → 跳过  

### 3. 创建或更新测试

- 有对应 `test_*.py`：按改动更新/补充  
- 无：新建，例如 `tests/test_security.py`  
- 用例应包含：正常路径 + 1～2 个边界  
- 测试代码注释用**简体中文**；`test_` 函数名可英文，`docstring`/`assert` 消息可用中文  
- **不要**污染 `backend/data/app.db` 与用户上传目录；使用临时目录 + 测试专用 SQLite  
- **不要**把真实 API Key 写进测试文件  

### 4. 执行测试

优先顺序：

1. `cd backend && .venv\Scripts\python -m pytest -q`  
2. `cd backend && .venv\Scripts\python -m pytest tests/ -v`  
3. 单文件：`python -m pytest tests/test_security.py -v`  

注意：

- 工具 `description` 用中文  
- 保留完整终端输出，供报告引用  
- 工作目录必须是 `backend`（保证 `app` 包可导入）  

### 5. 输出中文测试报告（必须）

```markdown
## 测试结论
- 通过 / 失败（一句话）

## 测了什么
- 模块与用例范围（大白话）

## 结果一览
- 总数 / 通过 / 失败 / 耗时（若日志有）

## 失败详情（如有）
- 哪个用例：期望 vs 实际
- 可能原因（通俗）
- 建议下一步

## 本次新增或修改的测试文件
- 路径列表

## 说明
- 未覆盖的范围
- 是否动过依赖 / 配置
- 通行证状态（若由 tester 执行）
```

- **失败时**：不伪装成功  
- **通过时**：可提示存档，但不自动提交  

### 6. 失败后的修复策略

- 若是**测试写错**：改正测试，再跑一轮  
- 若是**产品代码疑似 bug**：用大白话说明，先报告  
- 同一轮最多自动「改测试并重跑」到结果稳定  

---

## 与其它技能的边界

| 事项 | 关系 |
|------|------|
| Git 提交 | 本技能默认不提交；门禁提交用 `gitcommit-agent` |
| 质检/安全/注释 | `quality-engineer`（`/security-audit`、`/comments-check`） |
| 启动前后端 | `/run-app` |
| 前端生产构建 | `/rebuild-app` |
| 真机联调 / 浏览器演示 | 不代替单元测试 |
| 真实 LLM 调用 | 默认 mock 或跳过 |

---

## 沟通与安全

- 全程简体中文；结论 → 原因 → 下一步  
- 不删除用户真实业务数据目录（除非测完清理**自己创建的临时目录**）  
- 不把密钥写进测试  
- 不强制推送、不 `reset --hard`  

## 成功标准

- 有可运行的 pytest 用例覆盖核心逻辑  
- 已实际执行测试并引用真实输出  
- 用户能看懂的中文报告已给出  
