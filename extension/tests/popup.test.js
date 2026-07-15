const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const popupHtml = fs.readFileSync("extension/popup.html", "utf8");
const popupCode = fs.readFileSync("extension/popup.js", "utf8");
const manifest = JSON.parse(fs.readFileSync("extension/manifest.json", "utf8"));

class FakeClassList {
  constructor(element) {
    this.element = element;
  }

  add(...names) {
    const values = new Set(this.element.className.split(/\s+/).filter(Boolean));
    names.forEach((name) => values.add(name));
    this.element.className = [...values].join(" ");
  }
}

class FakeElement {
  constructor(id = "", tagName = "div") {
    this.id = id;
    this.tagName = tagName.toUpperCase();
    this.textContent = "";
    this.value = "";
    this.title = "";
    this.className = "";
    this.hidden = false;
    this.disabled = false;
    this.children = [];
    this.listeners = {};
    this.classList = new FakeClassList(this);
    this.scrollCalls = [];
  }

  addEventListener(name, listener) {
    this.listeners[name] = listener;
  }

  append(...children) {
    this.children.push(...children);
  }

  replaceChildren(...children) {
    this.children = [...children];
  }

  querySelector(selector) {
    if (selector === "span:last-child") return this.children[this.children.length - 1] || null;
    return null;
  }

  scrollIntoView(options) {
    this.scrollCalls.push(options);
  }

  async trigger(name) {
    return this.listeners[name]?.({ target: this });
  }
}

function createHarness() {
  const ids = [...popupHtml.matchAll(/id="([^"]+)"/g)].map((match) => match[1]);
  const elements = Object.fromEntries(ids.map((id) => [id, new FakeElement(id)]));
  elements["backend-status"].children = [new FakeElement(), new FakeElement()];
  elements["page-title"].textContent = "Example job";
  const storage = new Map();
  const timers = [];
  const fetchQueue = [];
  const fetchCalls = [];
  const nativeQueue = [];
  const nativeCalls = [];
  let scriptRuns = 0;
  let copiedText = "";

  const document = {
    querySelector(selector) {
      return elements[selector.slice(1)] || null;
    },
    createElement(tagName) {
      return new FakeElement("", tagName);
    },
    createTextNode(text) {
      const node = new FakeElement("", "#text");
      node.textContent = text;
      return node;
    },
  };

  const context = {
    document,
    window: { confirm: () => true },
    localStorage: {
      getItem: (key) => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
    },
    navigator: {
      clipboard: {
        writeText: async (text) => {
          copiedText = text;
        },
      },
    },
    chrome: {
      tabs: { query: async () => [{ id: 7 }] },
      scripting: {
        executeScript: async () => {
          scriptRuns += 1;
          return [{
            result: {
              title: "Example job",
              url: "https://example.com/jobs/7",
              text: "Python developer job description",
              source: "smart-job-detail",
              debug: { candidateCount: 2, score: 80, textLength: 32 },
            },
          }];
        },
      },
      runtime: {
        lastError: null,
        sendMessage: (message, callback) => {
          nativeCalls.push(message);
          callback(nativeQueue.shift() || {
            ok: true,
            state: "stopped",
            message: "本地服务已停止",
          });
        },
      },
    },
    fetch: async (...args) => {
      fetchCalls.push(args);
      if (!fetchQueue.length) throw new TypeError("connection refused with traceback details");
      return fetchQueue.shift();
    },
    extractJobContent() {},
    console: { debug() {}, error() {} },
    setTimeout: (callback, delay) => {
      timers.push({ callback, delay });
      return timers.length;
    },
    clearTimeout() {},
    TypeError,
    Math,
    Number,
    Object,
    String,
    Array,
  };

  vm.createContext(context);
  vm.runInContext(popupCode, context);
  return {
    context,
    elements,
    storage,
    timers,
    fetchQueue,
    fetchCalls,
    nativeQueue,
    nativeCalls,
    getScriptRuns: () => scriptRuns,
    getCopiedText: () => copiedText,
  };
}

const nextTurn = () => new Promise((resolve) => setImmediate(resolve));

(async () => {
  for (const id of [
    "health-check",
    "read-job",
    "analyze-job",
    "page-title",
    "page-url",
    "read-source",
    "job-description",
    "candidate-profile",
    "analysis-result",
    "analysis-score",
    "analysis-summary",
    "analysis-greeting",
    "copy-greeting",
    "service-status",
    "service-control",
    "service-control-label",
    "service-spinner",
  ]) {
    assert.ok(popupHtml.includes(`id="${id}"`), `missing #${id}`);
  }

  const harness = createHarness();
  const { context, elements, storage, timers, fetchQueue, nativeQueue } = harness;
  await nextTurn();
  assert.strictEqual(harness.getScriptRuns(), 1, "popup should automatically read the active job");
  assert.strictEqual(elements["read-source"].textContent, "智能岗位详情识别");
  assert.strictEqual(elements["service-status"].textContent, "本地服务已停止");
  assert.strictEqual(elements["service-control-label"].textContent, "启动本地服务");

  elements["candidate-profile"].value = "真实候选人资料";
  await elements["candidate-profile"].trigger("input");
  assert.strictEqual(storage.get("aiJobCopilot.candidateProfile"), "真实候选人资料");

  await elements["read-job"].trigger("click");
  await nextTurn();
  assert.strictEqual(harness.getScriptRuns(), 2, "reread button should read the active job again");

  vm.runInContext("setLoadingState(true)", context);
  assert.strictEqual(elements["analyze-job"].disabled, true);
  assert.strictEqual(elements["analyze-spinner"].hidden, false);
  assert.strictEqual(elements["analyze-label"].textContent, "正在分析岗位……");
  vm.runInContext("setLoadingState(false)", context);

  const fullResponse = {
    score: 86,
    summary: "技能与岗位需求整体匹配。",
    matched_skills: ["Python", "FastAPI"],
    partial_skills: ["Docker"],
    missing_skills: ["Kubernetes"],
    unverified_skills: ["系统设计"],
    learning_plan: ["补充容器编排实践"],
    reasoning: ["后端项目经历相关"],
    greeting: "您好，我对这个岗位很感兴趣。",
    confidence: 0.88,
    score_breakdown: {
      core_skills: { score: 90, reason: "核心技能匹配", weight: 0.35 },
      preferred_skills: { score: 80, reason: "部分具备", weight: 0.15 },
      project_experience: { score: 85, reason: "项目相关", weight: 0.2 },
      education_background: { score: 75, reason: "专业相关", weight: 0.1 },
      work_experience: { score: 60, reason: "经历有限", weight: 0.2 },
    },
  };
  context.fullResponse = fullResponse;
  vm.runInContext("renderAnalysis(fullResponse)", context);
  assert.strictEqual(elements["analysis-result"].hidden, false);
  assert.strictEqual(elements["analysis-summary"].textContent, fullResponse.summary);
  assert.strictEqual(elements["matched-skills"].children.length, 2);
  assert.strictEqual(elements["missing-skills"].children.length, 1);
  assert.strictEqual(elements["partial-skills-section"].hidden, false);
  assert.strictEqual(elements["unverified-skills-section"].hidden, false);
  assert.strictEqual(elements["score-breakdown"].children.length, 5);
  assert.strictEqual(elements["score-breakdown-section"].hidden, false);

  context.legacyResponse = {
    score: 60,
    summary: "旧响应摘要",
    matched_skills: [],
    missing_skills: [],
    learning_plan: [],
    reasoning: [],
    greeting: "",
    confidence: 0.85,
  };
  assert.doesNotThrow(() => vm.runInContext("renderAnalysis(legacyResponse)", context));
  assert.strictEqual(elements["partial-skills-section"].hidden, true);
  assert.strictEqual(elements["unverified-skills-section"].hidden, true);
  assert.strictEqual(elements["score-breakdown-section"].hidden, true);
  assert.strictEqual(elements["matched-skills-section"].hidden, true);
  assert.strictEqual(elements["greeting-section"].hidden, true);
  assert.strictEqual(elements["copy-greeting"].disabled, true);

  vm.runInContext("renderAnalysis(fullResponse)", context);
  await elements["copy-greeting"].trigger("click");
  assert.strictEqual(harness.getCopiedText(), fullResponse.greeting);
  assert.strictEqual(elements["copy-greeting"].textContent, "已复制");
  assert.strictEqual(timers.at(-1).delay, 1800);
  timers.at(-1).callback();
  assert.strictEqual(elements["copy-greeting"].textContent, "复制打招呼文案");

  elements["job-description"].value = "A complete job description";
  elements["candidate-profile"].value = "A truthful candidate profile";
  fetchQueue.push({ ok: true, json: async () => ({ status: "ok" }) });
  fetchQueue.push({ ok: true, json: async () => fullResponse });
  await elements["analyze-job"].trigger("click");
  assert.strictEqual(elements["analysis-result"].scrollCalls.length, 1);
  assert.strictEqual(elements["analyze-job"].disabled, false);

  fetchQueue.push({ ok: true, json: async () => ({ status: "ok" }) });
  await elements["analyze-job"].trigger("click");
  assert.strictEqual(elements.result.textContent.includes("traceback"), false);
  assert.strictEqual(elements.result.textContent, "后端未连接，请先启动本地服务");

  vm.runInContext('setServiceState("stopped")', context);
  nativeQueue.push({ ok: true, state: "running", message: "正在启动" });
  fetchQueue.push({ ok: true, json: async () => ({ status: "ok" }) });
  await elements["service-control"].trigger("click");
  assert.strictEqual(elements["service-status"].textContent, "运行中");
  assert.strictEqual(elements["service-control"].disabled, false);

  nativeQueue.push({ ok: true, state: "stopped", message: "已停止" });
  fetchQueue.push({ ok: false, json: async () => ({}) });
  await elements["service-control"].trigger("click");
  assert.strictEqual(elements["service-status"].textContent, "已停止");

  const analysisCallsBefore = harness.fetchCalls.filter(
    ([url, options]) => url.includes("/api/analyze-job") && options?.method === "POST",
  ).length;
  context.window.confirm = () => true;
  nativeQueue.push({ ok: true, state: "running", message: "已启动" });
  fetchQueue.push({ ok: false, json: async () => ({}) });
  fetchQueue.push({ ok: true, json: async () => ({ status: "ok" }) });
  fetchQueue.push({ ok: true, json: async () => fullResponse });
  await elements["analyze-job"].trigger("click");
  const analysisCallsAfter = harness.fetchCalls.filter(
    ([url, options]) => url.includes("/api/analyze-job") && options?.method === "POST",
  ).length;
  assert.strictEqual(analysisCallsAfter, analysisCallsBefore + 1, "analysis should resume exactly once");

  vm.runInContext('setServiceState("stopped")', context);
  context.window.confirm = () => false;
  fetchQueue.push({ ok: false, json: async () => ({}) });
  const callsBeforeCancel = harness.fetchCalls.length;
  await elements["analyze-job"].trigger("click");
  assert.strictEqual(elements.result.textContent, "已取消启动，未发送分析请求");
  assert.strictEqual(harness.fetchCalls.length, callsBeforeCancel + 1, "cancel only performs health check");

  assert.ok(manifest.permissions.includes("nativeMessaging"));
  assert.strictEqual(manifest.background.service_worker, "background.js");
  assert.ok(!manifest.host_permissions.includes("<all_urls>"));
  console.log("popup UI behavior: valid");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
