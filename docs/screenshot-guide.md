# Phase 8.2 截图素材

## 已采集页面

截图来自本地 Docker Compose Demo 的真实 HTTP 页面，统一使用 1440×1000 无私人浏览器资料的无头 Edge：

| 文件 | 页面 | 证明点 |
| --- | --- | --- |
| `01-dashboard.png` | Dashboard | 全局指标、岗位漏斗、最近岗位 |
| `02-jobs.png` | Jobs | PostgreSQL 中的真实 Demo 岗位列表 |
| `03-job-detail.png` | Job Detail | 分析结果与 Agent Workflow 入口 |
| `04-resumes.png` | Resume | 简历知识库与文档处理状态 |

目录：

```text
docs/screenshots/
  01-dashboard.png
  02-jobs.png
  03-job-detail.png
  04-resumes.png
```

## 采集规范

- 必须从真实运行页面采集，不用设计稿冒充功能。
- 截图前确认 `postgres`、`backend`、`frontend` 均 healthy。
- 使用专门的临时浏览器 profile，避免私人书签、账号、头像和历史记录。
- 不打开 `.env`、请求头、Docker inspect 环境变量或任何真实 API Key。
- Demo 数据不得包含真实姓名、电话、邮箱或公司内部信息。
- 页面更新后重新采集全部截图，避免不同版本 UI 混用。
- README 使用的截图保持相同尺寸与主题，必要时只做无损裁剪，不修改页面内容。

## 可选补充素材

- `05-agent-run.png`：已完成 Agent Run 的节点状态与结果。
- `06-semantic-search.png`：Resume Detail 中的 pgvector 语义检索结果。
- `07-compose-healthy.png`：终端中的三个 healthy 服务，不显示环境变量。
- `08-architecture.png`：从 Mermaid 架构图导出的演示版图片。

补充素材必须来自真实运行结果；若外部 LLM / Embedding 未配置，应明确展示已有结果，不伪造一次新的成功调用。
