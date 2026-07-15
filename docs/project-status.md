# 项目状态说明

## 当前结论

AI Job Copilot 已完成本地 MVP 的核心闭环：Edge 优先、Chrome 兼容的 Manifest V3 扩展读取岗位内容和候选人资料，本地 FastAPI 调用 DeepSeek，校验并返回结构化匹配结果，API Key 只保留在后端。仓库包含 pytest 和 Node 测试，且完成过真实 DeepSeek 联调。项目没有数据库或云端部署，未进行大规模用户验证；评分仅供参考。当前也没有自动投递或自动聊天，不具备生产系统所需的账号、鉴权、云端存储和运维能力。

## 功能状态矩阵

| 能力 | 状态 | 代码或验证依据 |
| --- | --- | --- |
| Edge 优先、Chrome 兼容的 Manifest V3 扩展 | 已实现 | `extension/manifest.json` |
| `Alt+J` 打开扩展 | 已实现 | manifest `_execute_action` |
| popup 打开后自动读取岗位 | 已实现 | `readCurrentJob({ automatic: true })` |
| 选中文字优先 | 已实现 | `extractJobContent()` 的 selection 分支 |
| 智能岗位详情区域识别 | 已实现 | 候选元素评分与阈值选择 |
| `main/article/role-main/body` 回退 | 已实现 | `content.js` 回退链 |
| 部分按钮与推荐职位噪声清理 | 已实现 | `noiseLines` 与尾部推荐标题集合 |
| JD 手动修改与重新读取保护 | 已实现 | 可编辑 textarea、覆盖确认和编辑状态 |
| `candidate_profile` 输入 | 已实现 | popup 表单与三字段请求 |
| 候选人资料 localStorage 保存 | 已实现 | `aiJobCopilot.candidateProfile` |
| FastAPI 根接口、健康检查和分析接口 | 已实现 | `backend/app/main.py` |
| DeepSeek API 接入 | 已实现 | `backend/app/services/llm.py` |
| API Key 后端隔离 | 已实现（本地边界） | Key 从后端环境或 `.env` 读取，扩展不包含 Key |
| Pydantic 请求/响应校验 | 已实现 | `JobAnalysisRequest`、严格 `JobAnalysis` |
| 结构化岗位匹配结果 | 已实现 | 8 个响应字段及 popup 渲染 |
| 上游与格式异常处理 | 已实现 | `LLMServiceError` 体系和 API 转换 |
| pytest 与 Node 测试 | 已实现 | 文档整理时 pytest 17 项通过，Node 测试通过 |
| 真实 DeepSeek 联调 | 已完成 | 依赖个人 Key 的手动联调，不属于默认测试 |
| 线上部署 / 生产可用 | 未实现 | 当前为本地 MVP |
| 自动投递 / 自动聊天 / 自动刷新岗位 | 未实现 | 不在当前功能范围 |
| 全招聘网站稳定适配 | 未实现 | 当前为通用启发式 + 手动兜底 |
| 账号、云同步、团队协作 | 未实现 | 当前无相关模块 |

## 已验证的自动化场景

- FastAPI 根接口与健康检查。
- `candidate_profile` 必填、去除首尾空白并进入模型服务。
- 合法 JSON、被文本包围的 JSON、非法 JSON 和安全错误响应。
- popup 中候选人资料输入、localStorage、自动读取、结构化字段渲染和快捷键配置。
- 选中文字优先、岗位详情与推荐区域竞争、尾部推荐裁剪、语义回退、父子候选选择、噪声行过滤和 8,000 字符上限。

## 仍需人工验证的内容

- 具体招聘网站在当前页面版本下的提取效果。
- Edge 与 Chrome 实际加载、权限提示和快捷键冲突情况。
- 真实网络环境中的 DeepSeek 延迟、限流和输出质量。
- 候选人对匹配结果、建议和打招呼文案的人工核验。

## 对外说明口径

推荐说法：

> 已完成一个 Edge 优先、兼容 Chrome 的本地 AI 求职助手 MVP，实现岗位内容提取、候选人资料保存、FastAPI + DeepSeek 分析、严格 JSON 校验、结构化结果展示和异常处理，并通过 pytest、Node 测试及真实 API 联调验证核心链路。

不推荐说法：

- “已上线并服务真实用户。”
- “适配所有招聘网站。”
- “拥有自主的客观匹配评分算法。”
- “AI 能准确判断是否会通过面试。”
- “候选人数据已经达到生产级安全合规。”
- “支持自动投递、自动聊天或绕过网站限制。”
