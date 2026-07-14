# AI Job Copilot

AI Job Copilot 是一个基于 Manifest V3 的 Chromium 浏览器扩展和 FastAPI 后端组成的 AI 求职助手原型，主要在 Microsoft Edge 中开发和测试，同时兼容 Google Chrome。当前版本聚焦于建立可运行、可验证的开发基础，不包含真实岗位分析或大模型调用。

## 当前状态

**v0.1 项目骨架**

已实现：

- FastAPI 根接口和健康检查接口
- Manifest V3 Chromium 浏览器扩展最小界面
- 扩展到本地后端的连接检查
- 后端基础自动化测试
- 后端 Docker 镜像和 Docker Compose 配置

计划功能：

- 从当前招聘页面读取岗位描述（JD）
- 管理用户简历信息
- 分析岗位匹配度、优势和不足
- 生成学习建议和招聘沟通话术
- 在扩展弹窗中展示完整分析结果

## 项目结构

```text
backend/           FastAPI 应用、测试和 Dockerfile
  app/             后端应用代码
  tests/           后端测试
extension/         原生 HTML、CSS、JavaScript Chromium 浏览器扩展
docs/              项目文档预留目录
docker-compose.yml 本地容器编排配置
```

## 本地启动后端

建议使用 Python 3.10 或更高版本。在项目根目录创建并激活你自己的虚拟环境，然后运行：

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查地址为 <http://localhost:8000/health>。运行测试：

```bash
python -m pytest backend/tests
```

## 使用 Docker 启动

在项目根目录运行：

```bash
docker compose up --build
```

服务将监听 <http://localhost:8000>。

## 在 Microsoft Edge 中加载扩展

1. 打开 Microsoft Edge 扩展页面 `edge://extensions/`。
2. 开启“开发人员模式”。
3. 点击“加载解压缩的扩展”。
4. 选择本项目的 `extension` 文件夹。
5. 将 AI Job Copilot 固定到浏览器工具栏。
6. 打开普通招聘网页，然后点击扩展中的“读取当前岗位”进行测试。

Google Chrome 用户可以在 `chrome://extensions/` 中以相同方式加载。

## 验证扩展与后端连接

1. 使用本地命令或 Docker 启动后端。
2. 打开 AI Job Copilot 扩展弹窗。
3. 点击“检查后端连接”。
4. 弹窗显示“后端连接正常”即表示连接成功。

## 当前限制

当前版本尚未实现真实岗位解析、AI 匹配分析、自动发送消息或自动刷新岗位。项目也不会执行自动投递、自动聊天或任何绕过网站风控与反爬机制的操作。
