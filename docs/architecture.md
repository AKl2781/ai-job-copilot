# 项目架构

## 架构目标

AI Job Copilot 将页面读取、用户交互和 AI 服务分成浏览器扩展与本地后端两层。这样既能保留浏览器内的轻量体验，也能让 DeepSeek API Key 只存在于后端运行环境中。

```mermaid
flowchart TB
    subgraph Browser["Microsoft Edge / Google Chrome"]
        Page["招聘详情页"]
        Extractor["content.js\n岗位内容提取"]
        Popup["popup.html / popup.js\n资料输入与结果展示"]
        Storage["localStorage\ncandidate_profile"]
        Page --> Extractor --> Popup
        Storage <--> Popup
    end

    subgraph Local["本地 FastAPI"]
        API["main.py\n接口与请求校验"]
        Service["llm.py\nDeepSeek 调用与异常处理"]
        Validator["JobAnalysis\n严格 JSON 校验"]
        API --> Service --> Validator --> API
    end

    DeepSeek["DeepSeek API"]
    Popup -->|"job_title + job_description + candidate_profile"| API
    Service -->|"后端环境中的 API Key"| DeepSeek
    DeepSeek --> Service
    API -->|"结构化 JobAnalysis"| Popup
```

## 组件职责

| 组件 | 真实职责 | 不承担的职责 |
| --- | --- | --- |
| `extension/content.js` | 读取选中文字；寻找并评分岗位详情候选区域；清理部分噪声；执行语义区域回退 | 不持续监听页面，不调用模型，不绕过页面权限 |
| `extension/popup.js` | 自动/手动触发读取；保存候选人资料；请求后端；渲染结构化结果 | 不保存 API Key，不在前端实现评分算法 |
| `extension/manifest.json` | 声明 Manifest V3、`activeTab`、`scripting`、本地后端访问和 `Alt+J` | 不申请 `<all_urls>` |
| `backend/app/main.py` | 提供根接口、健康检查和 `/api/analyze-job`；校验三项请求字段；转换服务异常 | 不抓取招聘网页 |
| `backend/app/services/llm.py` | 读取后端配置；调用 DeepSeek；解析并严格校验 JSON；转换上游异常 | 不持久化用户数据，不提供客观招聘结论 |

## 岗位内容提取顺序

```mermaid
flowchart TD
    A["开始读取"] --> B{"选中文字长度 ≥ 20?"}
    B -->|是| C["selection"]
    B -->|否| D["收集 div / section / article / main\n及岗位语义选择器"]
    D --> E["按关键词、文本长度、交互占比、\n页面占比和父子关系评分"]
    E --> F{"最高分 ≥ 30?"}
    F -->|是| G["smart-job-detail"]
    F -->|否| H{"main 文本 ≥ 100?"}
    H -->|是| I["main"]
    H -->|否| J{"article 文本 ≥ 100?"}
    J -->|是| K["article"]
    J -->|否| L{"role=main 文本 ≥ 100?"}
    L -->|是| M["role-main"]
    L -->|否| N["body"]
```

提取结果最长为 8,000 字符。清理逻辑会删除“立即沟通”“收藏”等完全匹配的噪声行，并在正文已足够长时裁掉“推荐职位”“猜你喜欢”“相似职位”等尾部区域。它是通用启发式识别，不等同于对所有招聘网站做了专用适配。

## API 契约

请求：

```json
{
  "job_title": "Python 后端开发",
  "job_description": "岗位职责与任职要求……",
  "candidate_profile": "掌握 Python、FastAPI 和 Git……"
}
```

响应：

```json
{
  "score": 78,
  "summary": "匹配摘要",
  "matched_skills": ["Python"],
  "missing_skills": ["Redis 未体现，需要确认"],
  "learning_plan": ["完成一个 Redis 缓存练习"],
  "reasoning": ["候选人资料明确提到 Python"],
  "greeting": "你好，我掌握 Python……",
  "confidence": 0.86
}
```

上例仅展示字段结构，不是固定输出或效果承诺。请求字段会去除首尾空白并限制长度；响应模型开启严格模式、禁止额外字段，并约束 `score` 为 0–100、`confidence` 为 0–1。

## 安全与异常边界

- API Key 从项目根目录 `.env` 或操作系统环境变量读取，不发送到扩展端。
- 环境变量优先于 `.env`，文件加载不会覆盖已有环境变量。
- 缺少 Key 或配置不完整返回 503；认证、连接或上游状态异常转换为安全提示；超时返回 504；模型 JSON 无法通过校验返回 502。
- 扩展只声明 `activeTab` 和 `scripting`，并仅为本地 `8000` 端口声明 host permission。
- 当前没有数据库、登录、鉴权、数据加密、服务端持久化或云端部署配置，也未进行大规模用户验证，因此定位为本地 MVP，而非生产系统；模型评分仅供参考。
