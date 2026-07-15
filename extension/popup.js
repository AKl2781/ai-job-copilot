const healthCheckButton = document.querySelector("#health-check");
const readJobButton = document.querySelector("#read-job");
const analyzeJobButton = document.querySelector("#analyze-job");
const pageTitle = document.querySelector("#page-title");
const pageUrl = document.querySelector("#page-url");
const jobDescription = document.querySelector("#job-description");
const candidateProfile = document.querySelector("#candidate-profile");
const analysisResult = document.querySelector("#analysis-result");
const result = document.querySelector("#result");
let jobDescriptionEdited = false;

const CANDIDATE_PROFILE_STORAGE_KEY = "aiJobCopilot.candidateProfile";
const DEFAULT_CANDIDATE_PROFILE =
  "大数据专业学生，掌握 Python、FastAPI、Git，使用过 Linux，完成过 AI Agent 项目。" +
  "了解 SQL，Docker 处于基础学习阶段，暂无正式开发实习经历。";

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

loadCandidateProfile();
candidateProfile.addEventListener("input", saveCandidateProfile);
jobDescription.addEventListener("input", () => {
  jobDescriptionEdited = true;
});

function setStatus(message, type = "") {
  result.className = "result";
  if (type) {
    result.classList.add(type);
  }
  result.textContent = message;
}

function renderList(elementId, items) {
  const list = document.querySelector(`#${elementId}`);
  list.replaceChildren();
  for (const item of items) {
    const listItem = document.createElement("li");
    listItem.textContent = item;
    list.append(listItem);
  }
}

function renderAnalysis(analysis) {
  document.querySelector("#analysis-score").textContent = `${analysis.score} / 100`;
  document.querySelector("#analysis-summary").textContent = analysis.summary;
  renderList("matched-skills", analysis.matched_skills);
  renderList("missing-skills", analysis.missing_skills);
  renderList("learning-plan", analysis.learning_plan);
  renderList("analysis-reasoning", analysis.reasoning);
  document.querySelector("#analysis-greeting").textContent = analysis.greeting;
  document.querySelector("#analysis-confidence").textContent =
    `开发信息：confidence ${analysis.confidence}`;
  analysisResult.hidden = false;
}

async function readCurrentJob({ automatic = false } = {}) {
  if (!automatic && jobDescriptionEdited) {
    const shouldReplace = window.confirm("重新读取会覆盖当前编辑的岗位 JD，是否继续？");
    if (!shouldReplace) {
      return;
    }
  }

  readJobButton.disabled = true;
  setStatus("正在读取当前网页…");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      throw new Error("No active tab is available");
    }

    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractJobContent,
    });

    const page = injectionResults[0]?.result;
    if (!page) {
      throw new Error("The page did not return readable content");
    }

    console.debug("Job content extraction", {
      source: page.source,
      candidateCount: page.debug?.candidateCount ?? 0,
      score: page.debug?.score ?? null,
      textLength: page.debug?.textLength ?? page.text.length,
    });

    pageTitle.textContent = page.title || "未获取到页面标题";
    pageUrl.textContent = page.url || "未获取到页面 URL";
    pageUrl.title = page.url || "";

    if (automatic && jobDescriptionEdited) {
      setStatus("已保留手动编辑的岗位 JD", "success");
      return;
    }

    jobDescription.value = page.text;
    jobDescriptionEdited = false;

    if (!page.text) {
      setStatus("页面正文为空，可手动填写岗位 JD", "error");
    } else if (page.source === "selection") {
      setStatus("已读取当前选中的岗位内容", "success");
    } else if (page.source === "smart-job-detail") {
      setStatus("已智能识别岗位详情，请检查后再分析", "success");
    } else if (["main", "article", "role-main"].includes(page.source)) {
      setStatus("已自动读取页面主要内容", "success");
    } else {
      setStatus("未准确识别岗位详情，已读取整页内容，请手动删除无关内容", "error");
    }
  } catch (error) {
    console.error("Reading the active page failed:", error);
    setStatus("无法读取当前网页，请确认页面允许扩展访问后重试", "error");
  } finally {
    readJobButton.disabled = false;
  }
}

readJobButton.addEventListener("click", () => readCurrentJob());
readCurrentJob({ automatic: true });

analyzeJobButton.addEventListener("click", async () => {
  const description = jobDescription.value.trim();
  const candidateProfileText = candidateProfile.value.trim();
  if (!description) {
    setStatus("请先读取当前岗位或手动填写岗位 JD", "error");
    return;
  }
  if (!candidateProfileText) {
    setStatus("请先填写个人技能或简历简介", "error");
    return;
  }

  analyzeJobButton.disabled = true;
  analysisResult.hidden = true;
  setStatus("正在进行 AI 岗位分析…");

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

    if (!response.ok) {
      throw new Error(`Unexpected HTTP status: ${response.status}`);
    }

    const analysis = await response.json();
    renderAnalysis(analysis);
    setStatus("AI 岗位分析完成", "success");
  } catch (error) {
    console.error("AI job analysis failed:", error);
    setStatus("AI 分析失败。请稍后重试。", "error");
  } finally {
    analyzeJobButton.disabled = false;
  }
});

healthCheckButton.addEventListener("click", async () => {
  healthCheckButton.disabled = true;
  setStatus("正在检查连接…");

  try {
    const response = await fetch("http://localhost:8000/health");
    if (!response.ok) {
      throw new Error(`Unexpected HTTP status: ${response.status}`);
    }

    const data = await response.json();
    if (data.status !== "ok") {
      throw new Error("Unexpected health response");
    }

    setStatus("后端连接正常", "success");
  } catch (error) {
    console.error("Backend health check failed:", error);
    setStatus("无法连接后端，请确认 FastAPI 已启动", "error");
  } finally {
    healthCheckButton.disabled = false;
  }
});
