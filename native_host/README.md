# Native Messaging Host

此目录提供仅限 Microsoft Edge 的短生命周期 Native Messaging Host。每次
`sendNativeMessage` 启动一次 Host，处理一条 `status`、`start` 或 `stop` 消息后退出。

Host 不接受命令、脚本文本、路径、URL 或参数拼接。`start` 与 `stop` 只会调用当前项目
固定的 `scripts/start_backend.ps1` 和 `scripts/stop_backend.ps1`；进程归属安全判断由现有脚本负责。

`run_host.bat` 是 Windows MVP 的固定启动包装器。它使用 `@echo off`，只启动同目录的
`host.py`，避免命令回显污染 Native Messaging 二进制 stdout。机器上需要已有可从
`PATH` 调用的 Python；本项目不提交 exe，也不新增构建依赖。

安装与卸载请从项目根目录运行 `install_native_host.bat <扩展ID>` 与
`uninstall_native_host.bat`。安装器仅写入当前用户的 Edge 注册表位置。
