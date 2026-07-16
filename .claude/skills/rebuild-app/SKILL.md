---
name: rebuild-app
description: >
  为 LangChainRAG 做「可交付构建检查」：前端 Vite production build，可选跑后端 pytest。
  用户输入 /rebuild-app，或说「重新打包」「构建前端」「build 应用」「生产构建」「打安装包」时务必使用本技能。
---

# 构建 / 打包检查（LangChainRAG）

本项目是 **Web 双进程**，不是 Electron 桌面安装包。  
「打包」在本仓库含义：

1. **前端生产构建**：`frontend` → `npm run build` → 产物 `frontend/dist/`  
2. **（推荐）后端测试**：`backend` → `pytest` 确认核心逻辑仍绿  
3. **不**默认打 Docker 镜像、不生成 Windows `.exe` 安装程序  

## 默认命令

### 1. 前端构建

```bash
cd frontend
npm install
npm run build
```

### 2. 后端测试（构建检查的一部分，建议执行）

```bash
cd backend
.venv\Scripts\activate
python -m pytest -q
```

## 执行步骤

1. 确认根目录与 `frontend/package.json`  
2. 无 `node_modules` 则 `npm install`  
3. 执行 `npm run build`（超时给足，失败贴日志）  
4. 可选/推荐：跑 pytest  
5. 汇报：  
   - 成功：`frontend/dist` 是否生成、pytest 是否通过  
   - 失败：原文 + 通俗原因（类型/语法/缺环境变量不影响静态 build 时说明）  

## 不要做的事

- 用户只说「打开/启动」→ 用 `/run-app`  
- 不要把 `dist/`、`.venv` 提交进 Git  
- 不要删除用户 `backend/data`  
- 不要为了构建通过擅自大改业务；先报告  

## 与 run-app 区别

| 技能 | 目的 | 结果 |
|------|------|------|
| `/run-app` | 开发调试 | 热更新服务 |
| `/rebuild-app` | 生产构建检查 | `dist/` + 可选测试报告 |

## 沟通

- 简体中文；结论 → 产物路径 → 下一步（如何用预览 `npm run preview` 可提一句）  
