# AI Job Copilot 2.0

## 项目简介

AI Job Copilot 是一个基于浏览器扩展、FastAPI、Next.js 和 LLM 的 AI 求职助手。

当前版本面向本地 Demo，帮助用户捕获职位描述（JD）、管理岗位与候选人画像，并生成可解释的岗位匹配分析。项目只提供辅助分析，不代替用户判断，也不会自动投递职位。

## 当前能力

- JD 捕获
- 岗位管理
- 候选人画像
- AI 岗位匹配分析
- 确定性评分
- 分析结果持久化
- Demo 数据

## 技术架构

- Frontend：Next.js + TypeScript
- Backend：FastAPI
- Database：PostgreSQL
- Migration：Alembic
- AI：LLM Provider + Deterministic Scoring

LLM Provider 负责提取岗位要求与候选人证据，后端使用固定规则进行确定性评分，并将分析结果持久化到 PostgreSQL。

## 本地运行

开始前请准备 Python 3.10+、Node.js 和 Docker，并在项目根目录根据 `.env.example` 创建本地 `.env`。不要提交 `.env` 或真实 API Key。

1. 启动数据库：

   ```powershell
   docker compose up -d
   ```

2. 运行 migration：

   ```powershell
   python -m alembic -c alembic.ini upgrade head
   ```

3. 导入 Demo 数据：

   ```powershell
   python backend/scripts/seed_demo.py
   ```

   Demo Seed 仅允许在开发环境和本地数据库执行，可重复运行且不会重复创建 Demo 用户或岗位。它不会预先创建分析结果。

4. 启动 Backend：

   ```powershell
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```

5. 启动 Frontend：

   ```powershell
   cd frontend
   npm run dev
   ```

默认访问地址为 `http://localhost:3000`，Backend 健康检查地址为 `http://127.0.0.1:8000/health`。

## Demo 流程

打开网页

→ 岗位管理

→ 查看岗位

→ 打开岗位详情

→ 查看 AI 分析结果

## 验证

在项目根目录运行 Backend 检查：

```powershell
python -m compileall -q backend/app
python -m pytest -q
```

在 `frontend` 目录运行 Frontend 检查：

```powershell
npm test
npm run typecheck
npm run build
```

## 当前限制

- 尚未实现 RAG
- 尚未实现 Agent Runtime
- 尚未自动投递
- 尚未接入正式用户系统

当前 Demo 使用开发环境默认用户标识。未来接入登录系统时，应由认证层提供已验证的用户身份；CRUD 服务本身保持用户隔离，不承担认证职责。
