const healthCheckButton = document.querySelector("#health-check");
const readJobButton = document.querySelector("#read-job");
const analyzeJobButton = document.querySelector("#analyze-job");
const analyzeLabel = document.querySelector("#analyze-label");
const analyzeSpinner = document.querySelector("#analyze-spinner");
const backendStatus = document.querySelector("#backend-status");
const pageTitle = document.querySelector("#page-title");
const pageUrl = document.querySelector("#page-url");
const readSource = document.querySelector("#read-source");
const jobDescription = document.querySelector("#job-description");
const candidateProfile = document.querySelector("#candidate-profile");
const analysisResult = document.querySelector("#analysis-result");
const greetingSection = document.querySelector("#greeting-section");
const greetingTextarea = document.querySelector("#analysis-greeting");
const copyGreetingButton = document.querySelector("#copy-greeting");
const result = document.querySelector("#result");
let jobDescriptionEdited = false;
let analysisInProgress = false;
let copyFeedbackTimer;

const CANDIDATE_PROFILE_STORAGE_KEY = "aiJobCopilot.candidateProfile";
const DEFAULT_CANDIDATE_PROFILE =
  "大数据专业学生，掌握 Python、FastAPI、Git，使用过 Linux，完成过 AI Agent 项目。" +
  "了解 SQL，Docker 处于基础学习阶段，暂无正式开发实习经历。";

const SCORE_BREAKDOWN_LABELS = {
  core_skills: "核心技能",
  preferred_skills: "优先技能",
  project_experience: "项目经验",
  education_background: "教育背景",
  work_experience: "工作经验",
};

function asArray(value) {
  return Array.isArray(value) ? value.filter((item) => item !== null && item !== undefined) : [];
}

function safeText(value, fallback = "") {
  return value === null || value === undefined ? fallback : String(value);
}

function loadCandidateProfile() {
  try {
    candidateProfile.value =
      localStorage.getItem(CANDIDATE_PROFILE_STORAGE_KEY) ?? DEFAULT_CANDIDATE_PROFILE;
  } catch (error) {
    console.error("Loading candidate profile failed:", error);
    candidateProfile.value = DEFAULT_CANDIDATE_PROFILE;
  }
}

function saveCandidateProfile() {
  try {
    localStorage.setItem(CANDIDATE_PROFILE_STORAGE_KEY, candidateProfile.value);
  } catch (error) {
    console.error("Saving candidate profile failed:", error);
  }
}

function showStatus(message, type = "info") {
  result.className = "status-message";
  if (message) {
    result.classList.add(type);
  }
  result.textContent = message;
}

function setBackendStatus(label, type = "idle") {
  backendStatus.className = `backend-status status-${type}`;
  const labelElement = backendStatus.querySelector("span:last-child");
  if (labelElement) {
    labelElement.textContent = label;
  }
}

function setLoadingState(isLoading) {
  analysisInProgress = isLoading;
  analyzeJobButton.disabled = isLoading;
  analyzeSpinner.hidden = !isLoading;
  analyzeLabel.textContent = isLoading ? "正在分析岗位……" : "分析岗位";
}

function renderSkillTags(elementId, sectionId, items) {
  const list = document.querySelector(`#${elementId}`);
  const section = document.querySelector(`#${sectionId}`);
  const values = asArray(items);
  list.replaceChildren();
  section.hidden = values.length === 0;

  for (const item of values) {
    const listItem = document.createElement("li");
    listItem.textContent = safeText(item);
    list.append(listItem);
  }
}

function renderListSection(elementId, sectionId, items) {
  const list = document.querySelector(`#${elementId}`);
  const section = document.querySelector(`#${sectionId}`);
  const values = asArray(items);
  list.replaceChildren();
  section.hidden = values.length === 0;

  for (const item of values) {
    const listItem = document.createElement("li");
    listItem.textContent = safeText(item);
    list.append(listItem);
  }
}

function getScoreLabel(score) {
  if (score >= 80) return "匹配度较高";
  if (score >= 60) return "部分匹配";
  if (score >= 40) return "存在明显差距";
  return "当前匹配较低";
}

function renderScore(score) {
  const numericScore = Number(score);
  const normalizedScore = Number.isFinite(numericScore)
    ? Math.min(100, Math.max(0, numericScore))
    : 0;
  const scoreElement = document.querySelector("#analysis-score");
  scoreElement.replaceChildren();
  scoreElement.append(document.createTextNode(`${normalizedScore} `));
  const suffix = document.createElement("small");
  suffix.textContent = "/ 100";
  scoreElement.append(suffix);
  document.querySelector("#score-label").textContent = getScoreLabel(normalizedScore);
}

function renderScoreBreakdown(scoreBreakdown) {
  const section = document.querySelector("#score-breakdown-section");
  const container = document.querySelector("#score-breakdown");
  container.replaceChildren();

  if (!scoreBreakdown || typeof scoreBreakdown !== "object") {
    section.hidden = true;
    return;
  }

  for (const [key, label] of Object.entries(SCORE_BREAKDOWN_LABELS)) {
    const entry = scoreBreakdown[key];
    if (!entry || typeof entry !== "object") continue;

    const item = document.createElement("section");
    item.className = "breakdown-item";
    const title = document.createElement("p");
    title.className = "breakdown-title";
    const name = document.createElement("span");
    name.textContent = label;
    const score = document.createElement("span");
    score.textContent = safeText(entry.score, "—");
    title.append(name, score);
    item.append(title);

    if (entry.reason) {
      const reason = document.createElement("p");
      reason.className = "breakdown-reason";
      reason.textContent = safeText(entry.reason);
      item.append(reason);
    }
    if (entry.weight !== null && entry.weight !== undefined && entry.weight !== "") {
      const weight = document.createElement("p");
      weight.className = "breakdown-meta";
      weight.textContent = `权重 ${safeText(entry.weight)}`;
      item.append(weight);
    }
    container.append(item);
  }

  section.hidden = container.children.length === 0;
}

function renderAnalysis(analysis = {}) {
  renderScore(analysis.score);
  document.querySelector("#analysis-summary").textContent = safeText(
    analysis.summary,
    "暂无摘要",
  );
  renderSkillTags("matched-skills", "matched-skills-section", analysis.matched_skills);
  renderSkillTags("partial-skills", "partial-skills-section", analysis.partial_skills);
  renderSkillTags("missing-skills", "missing-skills-section", analysis.missing_skills);
  renderSkillTags("unverified-skills", "unverified-skills-section", analysis.unverified_skills);
  renderListSection("learning-plan", "learning-plan-section", analysis.learning_plan);
  renderListSection("analysis-reasoning", "reasoning-section", analysis.reasoning);
  renderScoreBreakdown(analysis.score_breakdown);

  const confidence = Number(analysis.confidence);
  document.querySelector("#analysis-confidence").textContent = Number.isFinite(confidence)
    ? `参考置信度 ${Math.round(confidence * 100)}%`
    : "";

  const greeting = safeText(analysis.greeting).trim();
  greetingTextarea.value = greeting;
  greetingSection.hidden = !greeting;
  copyGreetingButton.disabled = !greeting;
  analysisResult.hidden = false;
}

function setReadSource(source, successful) {
  const labels = {
    selection: "当前选中文本",
    "smart-job-detail": "智能岗位详情识别",
    main: "页面主要内容",
    article: "页面主要内容",
    "role-main": "页面主要内容",
    body: "整页正文回退",
  };
  readSource.textContent = labels[source] || (successful ? "页面内容" : "读取失败");
}

async function readCurrentJob({ automatic = false } = {}) {
  if (!automatic && jobDescriptionEdited) {
    const shouldReplace = window.confirm("重新读取会覆盖当前编辑的岗位 JD，是否继续？");
    if (!shouldReplace) return;
  }

  readJobButton.disabled = true;
  showStatus("正在读取当前网页……", "loading");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("No active tab is available");

    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractJobContent,
    });
    const page = injectionResults[0]?.result;
    if (!page) throw new Error("The page did not return readable content");

    console.debug("Job content extraction", {
      source: page.source,
      candidateCount: page.debug?.candidateCount ?? 0,
      score: page.debug?.score ?? null,
      textLength: page.debug?.textLength ?? page.text.length,
    });
    pageTitle.textContent = page.title || "未获取到页面标题";
    pageUrl.textContent = page.url || "未获取到页面 URL";
    pageUrl.title = page.url || "";
    setReadSource(page.source, Boolean(page.text));

    if (automatic && jobDescriptionEdited) {
      showStatus("已保留手动编辑的岗位 JD", "success");
      return;
    }

    jobDescription.value = page.text;
    jobDescriptionEdited = false;
    if (!page.text) {
      showStatus("岗位内容为空，请先读取或填写 JD", "warning");
    } else if (page.source === "selection") {
      showStatus("已读取当前选中的岗位内容", "success");
    } else if (page.source === "smart-job-detail") {
      showStatus("已智能识别岗位详情，请检查后再分析", "success");
    } else if (["main", "article", "role-main"].includes(page.source)) {
      showStatus("已自动读取页面主要内容", "success");
    } else {
      showStatus("未准确识别岗位详情，已读取整页内容，请手动删除无关内容", "warning");
    }
  } catch (error) {
    console.error("Reading the active page failed:", error);
    setReadSource("", false);
    showStatus("无法读取当前网页，请确认页面允许扩展访问后重试", "error");
  } finally {
    readJobButton.disabled = false;
  }
}

async function copyGreeting() {
  const text = greetingTextarea.value.trim();
  if (!text) {
    copyGreetingButton.disabled = true;
    showStatus("暂无可复制的打招呼文案", "warning");
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    clearTimeout(copyFeedbackTimer);
    copyGreetingButton.textContent = "已复制";
    showStatus("打招呼文案已复制", "success");
    copyFeedbackTimer = setTimeout(() => {
      copyGreetingButton.textContent = "复制打招呼文案";
    }, 1800);
  } catch (error) {
    console.error("Copying greeting failed:", error);
    showStatus("复制失败，请手动选择文案复制", "error");
  }
}

loadCandidateProfile();
candidateProfile.addEventListener("input", saveCandidateProfile);
jobDescription.addEventListener("input", () => {
  jobDescriptionEdited = true;
});
greetingTextarea.addEventListener("input", () => {
  copyGreetingButton.disabled = !greetingTextarea.value.trim();
});
copyGreetingButton.addEventListener("click", copyGreeting);
readJobButton.addEventListener("click", () => readCurrentJob());
readCurrentJob({ automatic: true });

analyzeJobButton.addEventListener("click", async () => {
  if (analysisInProgress) return;

  const description = jobDescription.value.trim();
  const candidateProfileText = candidateProfile.value.trim();
  if (!description) {
    showStatus("岗位内容为空，请先读取或填写 JD", "warning");
    return;
  }
  if (!candidateProfileText) {
    showStatus("请先填写真实的个人技能或简历简介", "warning");
    return;
  }

  setLoadingState(true);
  analysisResult.hidden = true;
  greetingSection.hidden = true;
  showStatus("正在分析岗位……", "loading");

  try {
    const response = await fetch("http://127.0.0.1:8000/api/analyze-job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_title: pageTitle.textContent.trim() || "未命名岗位",
        job_description: description,
        candidate_profile: candidateProfileText,
      }),
    });
    if (!response.ok) throw new Error(`Unexpected HTTP status: ${response.status}`);

    const analysis = await response.json();
    renderAnalysis(analysis);
    showStatus("AI 岗位分析完成", "success");
    if (typeof analysisResult.scrollIntoView === "function") {
      analysisResult.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    console.error("AI job analysis failed:", error);
    const isConnectionError = error instanceof TypeError;
    showStatus(
      isConnectionError
        ? "后端未连接，请先启动本地服务"
        : "AI 分析失败，请稍后重试",
      "error",
    );
  } finally {
    setLoadingState(false);
  }
});

healthCheckButton.addEventListener("click", async () => {
  healthCheckButton.disabled = true;
  setBackendStatus("正在检查", "idle");
  showStatus("正在检查后端连接……", "loading");

  try {
    const response = await fetch("http://localhost:8000/health");
    if (!response.ok) throw new Error(`Unexpected HTTP status: ${response.status}`);
    const data = await response.json();
    if (data.status !== "ok") throw new Error("Unexpected health response");

    setBackendStatus("后端正常", "success");
    showStatus("后端连接正常", "success");
  } catch (error) {
    console.error("Backend health check failed:", error);
    setBackendStatus("后端异常", "error");
    showStatus("后端未连接，请先启动本地服务", "error");
  } finally {
    healthCheckButton.disabled = false;
  }
});
