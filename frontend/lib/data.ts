export type JobStatus = "重点跟进" | "准备面试" | "待评估" | "已收藏";

export const jobs = [
  { id: "deepseek-ai-product", company: "深思科技", role: "AI 产品经理", status: "重点跟进" as JobStatus, score: 92, location: "上海 · 混合办公", salary: "30–45K", date: "今天 09:42", accent: "DS" },
  { id: "flowmind-frontend", company: "FlowMind", role: "高级前端工程师", status: "准备面试" as JobStatus, score: 86, location: "杭州 · 远程友好", salary: "28–42K", date: "昨天", accent: "FM" },
  { id: "northstar-agent", company: "Northstar AI", role: "Agent 应用工程师", status: "待评估" as JobStatus, score: 79, location: "深圳 · 现场", salary: "25–40K", date: "7 月 17 日", accent: "NA" },
  { id: "matrix-growth", company: "矩阵引擎", role: "增长产品经理", status: "已收藏" as JobStatus, score: 73, location: "北京 · 混合办公", salary: "25–35K", date: "7 月 16 日", accent: "ME" },
];

export const skills = [
  { name: "产品策略", level: 91 },
  { name: "AI 应用", level: 88 },
  { name: "数据分析", level: 76 },
  { name: "B 端产品", level: 71 },
];
