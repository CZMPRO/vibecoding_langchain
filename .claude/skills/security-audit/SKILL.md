---
name: security-audit
description: >
  LangChainRAG 专属安全审计：检查密码/密钥泄露、注入类风险、配置明文机密、
  以及 FastAPI/JWT/Vue 常见安全隐患，并输出大白话中文报告。
  用户输入 /security-audit，或说「安全审计」「安全检查」「有没有泄露密码」「检查漏洞」
  「敏感信息」「SQL 注入」「安全隐患」时务必使用本技能。
---

# 安全审计（security-audit）

对**本仓库源码与配置**做防御性检查，输出零基础中文报告。  
默认**只审计、不改代码**；用户明确要求修复时再改。

**不做：** 对外部系统的攻击、编写 exploit、绕过他人防护。

---

## 审计范围（四条主线 + Web 扩展）

### 1. 密码与敏感信息是否泄露

在源码、脚本、注释、示例、暂存区中查找硬编码：

| 类型 | 示例 |
|------|------|
| 密码 | `password`、`passwd`、默认 `admin/123456` 是否写进文档以外的可部署配置 |
| 密钥 | `api_key`、`OPENAI_API_KEY`、`JWT_SECRET`、`sk-`、Bearer token |
| 连接串 | 含账号密码的 DB URL |
| 其它 | Webhook 带密钥、私钥 PEM |

**方法：**

- Grep 扫 `backend/`、`frontend/src/`、根配置；排除 `.venv`、`node_modules`、`data/chroma`
- 核对 `.gitignore` 是否忽略 `.env`、`backend/data/*`、密钥
- **报告中脱敏**，勿完整回显真实 Key

**误报注意：** 字段名、测试假数据、`.env.example` 占位符、技能文档示例词。

### 2. 注入与 Web 风险

本项目使用 **SQLite + SQLAlchemy**、**FastAPI**、**Vue**：

| 检查项 | 说明 |
|--------|------|
| SQL 注入 | 是否字符串拼接 SQL；应使用 ORM/参数绑定 |
| 命令注入 | `subprocess`/`os.system` 是否拼接用户输入 |
| 路径穿越 | 上传文件路径是否限制在 `data/uploads`；文件名是否 UUID 化 |
| XSS | 前端 `v-html`（如 Markdown 渲染）是否仅渲染可信模型输出；是否可引入 DOMPurify 等加固建议 |
| JWT/鉴权 | 密钥是否够强；是否校验角色；普通用户能否越权访问知识库管理 API |
| CORS | `cors_origins` 是否过宽 |
| 限流 | 登录/问答是否有基础限流 |
| 上传 | 类型/大小限制是否生效 |

### 3. 配置文件明文机密

- `backend/.env`（应 gitignore）  
- `.env.example` 是否只有占位  
- CI、`.claude/settings.local.json`  
- 是否用 `git ls-files` 误跟踪 `.env`

### 4. 其它隐患（本栈）

- Chroma/上传目录权限与可清空风险  
- 默认管理员密码是否仅文档说明、生产须修改  
- 依赖轻量检查（不强制吓用户）  
- Git 历史是否曾提交密钥（提示即可）

---

## 执行步骤

1. **定范围**：用户点名 > `backend/app` + `frontend/src` + `.gitignore` + `.env.example`  
2. **扫描 + 精读**：`security.py`、`deps.py`、auth/kb 路由、上传与 `v-html`  
3. **分级**：严重 / 高 / 中 / 低  
4. **中文报告**（结构见下）  
5. **默认不修改**

### 报告模板

```markdown
## 安全审计结论
- 总体：通过 / 有风险 / 有严重问题

## 检查范围
- ...

## 1. 敏感信息与密码泄露
- ...

## 2. 注入与 Web 风险（SQL / 路径 / XSS / 鉴权）
- ...

## 3. 配置文件明文机密
- ...

## 4. 其它隐患
- ...

## 优先整改清单
1. ...

## 说明
- 静态检查局限；是否已改代码（默认否）
```

## 与其它技能

| 技能 | 关系 |
|------|------|
| `/unit-test` | 功能对错 |
| `/comments-check` | 注释质量 |
| `/git-save` | 发现密钥时阻止提交建议 |

## 红线

- 报告脱敏  
- 不提供攻击利用步骤  
- 不删用户业务数据、不擅自 `push --force`  
