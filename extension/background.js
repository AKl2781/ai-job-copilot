const NATIVE_HOST_NAME = "com.ai_job_copilot.service_control";
const ALLOWED_ACTIONS = new Set(["status", "start", "stop"]);

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "native-service-control" || !ALLOWED_ACTIONS.has(message.action)) {
    return false;
  }

  chrome.runtime.sendNativeMessage(
    NATIVE_HOST_NAME,
    { action: message.action },
    (response) => {
      if (chrome.runtime.lastError) {
        sendResponse({
          ok: false,
          state: "error",
          code: "native_host_unavailable",
          message: "Native Messaging Host 尚未安装",
        });
        return;
      }
      const validStates = new Set(["stopped", "starting", "running", "stopping", "error"]);
      if (!response || typeof response.ok !== "boolean" || !validStates.has(response.state)) {
        sendResponse({ ok: false, state: "error", message: "本地连接组件响应无效" });
        return;
      }
      sendResponse({ ok: response.ok, state: response.state, message: String(response.message || "") });
    },
  );
  return true;
});
