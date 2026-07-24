# AI Job Copilot 2.0 最终 Demo 验收报告

## 1. 验收摘要

- 验收日期：2026-07-24（Asia/Shanghai）
- 验收范围：Demo Launcher、后端、前端、Extension、PostgreSQL、Embedding、RAG、Agent
- 被验收 Git commit：`c01fdf419cce252432c6caa3695fa3fbcfbd323f`
- 自动化与真实 API 验收结论：**PASS**
- 人工浏览器 Extension E2E 与人工视觉巡检：**NOT VERIFIED**
- FAIL 项：无

本报告只把实际执行并取得客观证据的检查记为 PASS。没有加载真实 Chrome/Edge Extension 并在招聘网站中人工点击，也没有进行人工视觉巡检，因此相关项目明确标记为 NOT VERIFIED。

## 2. 验收环境

| 项目 | 结果 |
| --- | --- |
| 操作系统 | Windows 11 build 26200 |
| Python | 3.13.7 |
| Node.js | 24.16.0 |
| npm | 11.13.0 |
| Docker Desktop | 4.82.0 |
| Docker Engine | Client 29.6.1 / Server 29.6.1 |
| Docker Compose | 5.3.0 |
| Docker context | `desktop-linux` |
| Alembic current | `20260723_0008 (head)` |
| Alembic heads | `20260723_0008 (head)` |

配置检查只记录“已配置/未配置”，未读取或写入 API Key、密码、Token 等敏感值。验收时 LLM 与 Embedding 所需配置均处于已配置状态。

## 3. 自动化测试与构建

| 检查 | 命令 | 结果 | 证据 |
| --- | --- | --- | --- |
| Backend 测试 | `python -m pytest -q` | PASS | 100 passed，1 skipped |
| Python 编译检查 | `python -m compileall -q backend/app` | PASS | exit code 0 |
| Frontend 测试 | `npm test` | PASS | 11 passed |
| Frontend typecheck | `npm run typecheck` | PASS | exit code 0 |
| Frontend production build | `npm run build` | PASS | Next.js 编译、TypeScript、静态页面生成成功 |
| Extension 测试 | `node --test extension/tests/content.test.js extension/tests/popup.test.js` | PASS | 2 passed |
| Docker Compose 配置 | `docker compose config --quiet` | PASS | exit code 0 |

自动测试合计：**113 passed，1 skipped**。Skipped 项不计为失败。

## 4. Docker Desktop 自动启动验收

执行过程：

1. 使用 Docker Desktop CLI 正常停止 Docker Desktop。
2. 确认 Desktop 相关进程停止，`docker info` 无法连接 Engine。
3. 执行 `start_demo.bat`。
4. Launcher 输出 `Docker Desktop is not running. Starting Docker Desktop...`。
5. Launcher 输出 `Waiting for Docker Desktop Engine...`。
6. Engine 在第一次 5 秒轮询后可用。
7. Launcher 继续完成镜像 build、Compose up、Alembic 检查及健康检查。

结果：**PASS**。本次完整批处理冷启动约 40 秒，未出现 named-pipe 原始错误直接退出。

## 5. 服务与 HTTP 健康状态

| 服务/端点 | 结果 | 证据 |
| --- | --- | --- |
| PostgreSQL | PASS | 容器 `healthy` |
| Backend | PASS | 容器 `healthy` |
| Frontend | PASS | 容器 `healthy` |
| `http://localhost:3000` | PASS | HTTP 200 |
| `http://localhost:3000/jobs` | PASS | HTTP 200 |
| `http://localhost:3000/resumes` | PASS | HTTP 200 |
| `http://localhost:3000/agents` | PASS | HTTP 200 |
| `http://localhost:8000/health` | PASS | HTTP 200，`{"status":"ok"}` |

## 6. 核心功能验收

### 6.1 Job fingerprint 与 Extension 保存

使用隔离验收用户调用运行中的真实 Backend 和 PostgreSQL：

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 手动新增岗位 | PASS | 首次 `POST /api/v1/jobs` 返回 `created` |
| 相同岗位重复保存 | PASS | 第二次返回 `duplicate`、返回相同 job ID，岗位数量不增加 |
| Job fingerprint 持久化 | PASS | 2 个不同岗位对应 2 个不同 fingerprint |
| Extension 来源岗位保存 | PASS | `source_type=extension` 的真实 API 保存返回 `created` |
| Extension 来源岗位重复保存 | PASS | 返回 `duplicate` 且复用原 job ID |
| Popup 保存/重复提示逻辑 | PASS | Extension Popup 自动测试覆盖成功提示、重复提示和重复时不继续分析 |
| 在真实招聘网站人工点击 Extension | NOT VERIFIED | 当前会话未加载已安装的 Chrome/Edge Extension，也未进行真实招聘网站人工操作 |

### 6.2 Resume、Embedding 与 RAG

使用本次动态生成的 DOCX 简历调用运行中的真实服务：

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 简历上传 | PASS | HTTP 201，状态 `ready`，生成 3 个 chunks |
| 重复简历提示 | PASS | 相同内容再次上传返回 HTTP 200、`duplicate`，复用原 document ID |
| 失败文档可重试 | PASS（自动化） | Backend 集成测试 `test_failed_document_can_be_retried_after_embedding_recovers` 通过 |
| 真实环境故障注入后重试 | NOT VERIFIED | 未在最终共享 Demo 环境中故意中断 Embedding 服务 |
| 文档删除 | PASS | DELETE 返回 HTTP 204，随后 GET 返回 HTTP 404 |
| Embedding 生成 | PASS | PostgreSQL 中 3 个 chunk 均为 1024 维向量 |
| RAG 检索 | PASS | 返回 3 条真实结果，其中 2 条明确来自本次上传简历；最高相似度约 0.6742 |

### 6.3 Agent

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| Agent 工作流运行 | PASS | 真实 Agent Run 状态 `completed` |
| Agent 持久化步骤 | PASS | 记录 6 个步骤 |
| Agent 真实证据 | PASS | 最终结果包含 14 条检索证据 |
| Agent 页面无虚假可点击功能 | PASS（自动检查） | Agent 页面无直接 button；AppShell 占位 button 均为 disabled；真实入口链接到 `/jobs` |
| Agent 页面人工视觉/点击巡检 | NOT VERIFIED | 未执行人工浏览器视觉验收 |

### 6.4 页面入口

Dashboard、Jobs、Resumes、Agent 四个页面均由运行中的 Frontend 返回 HTTP 200，结果为 **PASS**。页面的人工视觉一致性与全部交互点击为 **NOT VERIFIED**。

## 7. PASS / FAIL / NOT VERIFIED 清单

### PASS

- Docker Desktop 关闭时由 Demo Launcher 自动启动
- Docker Engine 等待和恢复
- Backend、Frontend、Extension 自动测试
- Python compileall、Frontend typecheck、Frontend build
- Docker Compose 配置
- PostgreSQL、Backend、Frontend 健康检查
- Alembic current 与 head 一致
- 手动来源岗位创建与 fingerprint 去重
- Extension 来源岗位 API 保存与去重
- 简历上传、重复识别与删除
- 失败文档恢复逻辑的自动化集成测试
- 真实 Embedding 生成
- 真实 RAG 证据检索
- 真实 Agent 工作流、步骤与证据
- Dashboard、Jobs、Resumes、Agent 页面 HTTP 入口
- Agent 页面虚假控件静态检查

### FAIL

- 无

### NOT VERIFIED

- 在真实招聘网站中加载 Chrome/Edge Extension 后的人工保存与重复提示
- 共享 Demo 环境中主动破坏 Embedding 服务后的失败文档人工重试
- Dashboard、Jobs、Resumes、Agent 页面的人工视觉与全量点击巡检

## 8. 数据清理与安全检查

- 验收使用隔离用户和动态测试数据。
- 文档通过产品 DELETE API 删除。
- 验收用户及其岗位、Profile、Analysis、Agent Run 和 Agent Steps 已从数据库清理。
- 清理后不存在本次验收用户记录。
- 报告不包含 API Key、密码、Token、用户目录或不必要的绝对本机路径。
- 旧的 `docs/demo-acceptance-report-2026-07-21.md` 已删除，不保留两个日期版本。

## 9. 已知风险

1. Extension 的真实浏览器/招聘网站人工 E2E 尚未执行；当前证据为 Extension 自动测试及真实 Backend API 集成。
2. 失败文档恢复已经由隔离集成测试覆盖，但未在共享 Demo 环境中主动破坏外部 Embedding 服务。
3. LLM 与 Embedding 为外部依赖；本次验收期间正常，但外部服务可用性仍会影响 Demo。
4. 页面入口和控件状态有自动证据，但不能替代人工视觉验收。

## 10. 最终结论

AI Job Copilot 2.0 的自动化测试、Docker 冷启动、数据库迁移、服务健康、岗位去重、简历处理、Embedding、RAG 和 Agent 真实运行链路均通过，**自动化与 API Demo 验收结论为 PASS**。

由于没有伪造人工操作，真实浏览器 Extension 点击及人工视觉巡检保留为 **NOT VERIFIED**。这些项目不构成本次自动化验收失败，但在正式现场演示前仍建议进行一次人工冒烟检查。
