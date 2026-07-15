// This function is injected only when the popup opens or the user requests a
// reread. It does not register a listener or continuously inspect the page.
function extractJobContent() {
  const noiseLines = new Set(["立即沟通", "感兴趣", "收藏", "举报", "分享", "查看更多", "展开", "收起"]);
  const trailingRecommendationHeadings = new Set([
    "推荐职位",
    "猜你喜欢",
    "相似职位",
    "热门职位",
    "查看更多职位",
    "其他职位",
    "其他公司职位",
    "看过该职位的人还看了",
  ]);
  const normalizeText = (value) => {
    const lines = value
      .replace(/\r\n?/g, "\n")
      .replace(/[ \t]+$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .split("\n")
      .filter((line) => !noiseLines.has(line.trim()))
      .map((line) => line.trimEnd());
    const trailingBoundary = lines.findIndex((line, index) => {
      if (!trailingRecommendationHeadings.has(line.trim())) {
        return false;
      }
      return lines.slice(0, index).join("\n").trim().length >= 100;
    });
    const retainedLines = trailingBoundary >= 0 ? lines.slice(0, trailingBoundary) : lines;
    return retainedLines
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  };
  const cleanText = (value) =>
    normalizeText(value)
      .trim()
      .slice(0, 8000);

  const pageInfo = (text, source, debug = {}) => ({
    title: document.title.trim(),
    url: window.location.href,
    text,
    source,
    debug: {
      candidateCount: debug.candidateCount ?? 0,
      score: debug.score ?? null,
      textLength: text.length,
    },
  });

  const selectedText = cleanText(window.getSelection()?.toString() ?? "");
  if (selectedText.length >= 20) {
    return pageInfo(selectedText, "selection");
  }

  const positiveKeywords = [
    "职位描述", "岗位描述", "岗位职责", "工作职责", "任职要求", "职位要求",
    "岗位要求", "技能要求", "工作内容", "岗位内容", "职位详情", "任职资格",
    "我们希望你", "你需要", "加分项", "工作地点", "学历要求", "经验要求",
    "job description", "responsibilities", "requirements", "qualifications", "skills",
  ];
  const negativeKeywords = [
    "推荐职位", "猜你喜欢", "相似职位", "热门职位", "消息", "我的", "登录", "注册",
    "首页", "公司详情", "工商信息", "举报", "隐私政策", "用户协议", "客户端下载",
    "查看更多职位", "立即沟通", "在线沟通",
  ];
  const responsibilityKeywords = ["岗位职责", "工作职责", "工作内容", "responsibilities"];
  const requirementKeywords = [
    "任职要求", "职位要求", "岗位要求", "技能要求", "任职资格", "你需要",
    "requirements", "qualifications", "skills",
  ];
  const ignoredAncestors = "script,style,nav,header,footer,aside,button,input,textarea";
  const semanticSelectors = [
    ".job-detail",
    ".job-description",
    '[class*="job-detail"]',
    '[class*="job-description"]',
    '[data-testid*="job-detail"]',
    '[data-testid*="job-description"]',
  ];

  const bodyText = normalizeText(document.body?.innerText ?? "");
  const visible = (element) => {
    if (!element || element === document.body || element === document.documentElement) {
      return false;
    }
    if (element.closest?.(ignoredAncestors)) {
      return false;
    }
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      Number(style.opacity || 1) !== 0 &&
      rect.width > 0 &&
      rect.height > 0
    );
  };

  const semanticElements = new Set();
  for (const selector of semanticSelectors) {
    for (const element of document.querySelectorAll(selector)) {
      semanticElements.add(element);
    }
  }

  const elements = new Set([
    ...semanticElements,
    ...document.querySelectorAll("div,section,article,main"),
  ]);
  const candidates = [];

  for (const element of elements) {
    if (!visible(element)) {
      continue;
    }

    const text = normalizeText(element.innerText ?? "");
    if (text.length < 100 || text.length > 12000) {
      continue;
    }

    const lowerText = text.toLowerCase();
    const positiveCount = positiveKeywords.filter((keyword) => lowerText.includes(keyword)).length;
    const negativeCount = negativeKeywords.filter((keyword) => lowerText.includes(keyword)).length;
    const paragraphCount = text.split("\n").filter((line) => line.trim()).length;
    const interactiveElements = [...element.querySelectorAll("a,button")];
    const interactiveTextLength = interactiveElements.reduce(
      (total, item) => total + normalizeText(item.innerText ?? "").length,
      0,
    );
    const interactiveRatio = interactiveTextLength / Math.max(text.length, 1);
    const pageRatio = text.length / Math.max(bodyText.length, text.length, 1);
    const hasResponsibilities = responsibilityKeywords.some((keyword) => lowerText.includes(keyword));
    const hasRequirements = requirementKeywords.some((keyword) => lowerText.includes(keyword));

    let score = positiveCount * 9 - negativeCount * 8;
    score += Math.min(14, text.length / 250);
    score += Math.min(10, paragraphCount * 0.8);
    score += hasResponsibilities && hasRequirements ? 14 : 0;
    score += semanticElements.has(element) ? 8 : 0;
    score += pageRatio < 0.65 ? 6 : 0;
    score -= interactiveRatio > 0.2 ? interactiveRatio * 35 : 0;
    score -= interactiveElements.length > 12 ? 8 : 0;
    score -= pageRatio > 0.78 ? 18 : 0;
    score -= text.length > 6000 && positiveCount < 2 ? 12 : 0;
    score -= positiveCount === 0 ? 14 : 0;

    candidates.push({ element, text, score });
  }

  for (const parent of candidates) {
    for (const child of candidates) {
      if (parent === child || !parent.element.contains(child.element)) {
        continue;
      }
      const similarity = child.text.length / Math.max(parent.text.length, 1);
      if (similarity >= 0.7 && parent.text.includes(child.text)) {
        parent.score -= 14;
        child.score += 4;
      }
    }
  }

  candidates.sort((left, right) => right.score - left.score || left.text.length - right.text.length);
  const bestCandidate = candidates[0];
  if (bestCandidate?.score >= 30) {
    return pageInfo(cleanText(bestCandidate.text), "smart-job-detail", {
      candidateCount: candidates.length,
      score: Math.round(bestCandidate.score * 10) / 10,
    });
  }

  const contentAreas = [
    { selector: "main", source: "main" },
    { selector: "article", source: "article" },
    { selector: '[role="main"]', source: "role-main" },
  ];

  for (const area of contentAreas) {
    const text = cleanText(document.querySelector(area.selector)?.innerText ?? "");
    if (text.length >= 100) {
      return pageInfo(text, area.source, { candidateCount: candidates.length });
    }
  }

  return pageInfo(cleanText(bodyText), "body", { candidateCount: candidates.length });
}
