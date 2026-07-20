import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icons";
import { PageHeading } from "@/components/ui";

const capabilities = [
  ["岗位研究", "提取核心要求、公司信息与岗位风险", "search"],
  ["候选人证据匹配", "把 Profile 中的技能和经历映射到岗位要求", "check"],
  ["简历优化建议", "生成可审阅、可追溯的定制建议", "file"],
  ["面试准备", "整理高频问题、回答框架与准备清单", "clock"],
];

export default function AgentsPage(){return <AppShell><div className="animate-rise"><PageHeading eyebrow="Agent preview" title="Agent 能力预览" description="此页面仅展示规划中的自动化能力，当前版本不会创建或执行 Agent 任务。"/><section className="rounded-2xl bg-[#234e43] p-6 text-white md:p-7"><div className="flex flex-col justify-between gap-5 md:flex-row md:items-center"><div className="flex items-center gap-4"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-[#d9ef84]"><Icon name="spark"/></span><div><div className="flex items-center gap-2"><h2 className="text-base font-bold">AI Job Agent</h2><span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold text-white/75">未来能力</span></div><p className="mt-1 text-xs text-white/55">尚未接入真实 Agent 服务</p></div></div><button disabled className="cursor-not-allowed rounded-xl bg-white/10 px-4 py-2.5 text-xs font-bold text-white/60">暂未开放</button></div></section><section className="soft-shadow mt-5 rounded-2xl border border-[#e4e9e2] bg-white p-6"><div><h2 className="text-[15px] font-bold">规划能力</h2><p className="mt-1 text-xs text-[#858e8a]">以下步骤为产品预览，不代表实时任务状态。</p></div><div className="mt-7 grid gap-4 md:grid-cols-2">{capabilities.map(([title, description, icon], i)=><article key={title} className="rounded-2xl border border-[#e6ebe4] p-5"><div className="flex items-start gap-3"><span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#eef2e9] text-[#557064]"><Icon name={icon} className="h-4 w-4"/></span><div><p className="text-xs font-bold"><span className="mr-2 text-[#91a09a]">0{i + 1}</span>{title}</p><p className="mt-2 text-[11px] leading-5 text-[#7d8783]">{description}</p></div></div></article>)}</div></section></div></AppShell>}
