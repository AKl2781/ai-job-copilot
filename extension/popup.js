const healthCheckButton = document.querySelector("#health-check");
const readJobButton = document.querySelector("#read-job");
const analyzeJobButton = document.querySelector("#analyze-job");
const pageTitle = document.querySelector("#page-title");
const pageUrl = document.querySelector("#page-url");
const jobDescription = document.querySelector("#job-description");
const analysisResult = document.querySelector("#analysis-result");
const result = document.querySelector("#result");

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

readJobButton.addEventListener("click", async () => {
  readJobButton.disabled = true;
  setStatus("正在读取当前网页…");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      throw new Error("No active tab is available");
    }

    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const rawText = document.body?.innerText ?? "";
        const cleanedText = rawText
          .replace(/\r\n?/g, "\n")
          .replace(/[ \t]+\n/g, "\n")
          .replace(/\n[ \t]*\n(?:[ \t]*\n)+/g, "\n\n")
          .trim()
          .slice(0, 8000);

        return {
          title: document.title.trim(),
          url: window.location.href,
          text: cleanedText,
        };
      },
    });

    const page = injectionResults[0]?.result;
    if (!page) {
      throw new Error("The page did not return readable content");
    }

    pageTitle.textContent = page.title || "未获取到页面标题";
    pageUrl.textContent = page.url || "未获取到页面 URL";
    pageUrl.title = page.url || "";
    jobDescription.value = page.text;
    setStatus(
      page.text ? "当前岗位内容读取成功，可继续手动编辑" : "页面正文为空，可手动填写岗位 JD",
      "success",
    );
  } catch (error) {
    console.error("Reading the active page failed:", error);
    setStatus("无法读取当前网页，请确认页面允许扩展访问后重试", "error");
  } finally {
    readJobButton.disabled = false;
  }
});

analyzeJobButton.addEventListener("click", async () => {
  const description = jobDescription.value.trim();
  if (!description) {
    setStatus("请先读取当前岗位或手动填写岗位 JD", "error");
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
