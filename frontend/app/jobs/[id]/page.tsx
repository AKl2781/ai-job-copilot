import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icons";
import { api, ApiError, type Analysis } from "@/lib/api";
import { latestAnalysesByJob } from "@/lib/jobs";
import { AnalysisWorkflow } from "./analysis-workflow";

export const dynamic = "force-dynamic";

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = await api.getJob(id).catch((error) => {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  });
  const analyses = await api.getAnalyses();
  const analysis: Analysis | undefined = latestAnalysesByJob(analyses).get(job.id);
  const company = job.company || "未填写公司";
  const accent = company === "未填写公司" ? job.title.slice(0, 2) : company.slice(0, 2);

  return <AppShell><div className="animate-rise pb-20 lg:pb-0">
    <Link href="/jobs" className="mb-5 inline-flex items-center gap-2 text-xs font-bold text-[#65716c]"><span className="rotate-180"><Icon name="arrow" className="h-3.5 w-3.5"/></span>返回岗位管理</Link>
    <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5 md:p-7"><div className="flex flex-col justify-between gap-5 md:flex-row md:items-start"><div className="flex gap-4"><span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-[#edf2eb] text-sm font-black text-[#466157]">{accent.toUpperCase()}</span><div><h1 className="text-2xl font-semibold tracking-[-.04em]">{job.title}</h1><p className="mt-2 text-sm text-[#6f7975]">{company} · 来源：{job.source_type}</p>{job.source_url && <a href={job.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex text-xs font-bold text-[#315d4f]">查看原始岗位 <Icon name="arrow" className="ml-1 h-3.5 w-3.5"/></a>}</div></div><button disabled className="cursor-not-allowed rounded-xl bg-[#e8ece6] px-4 py-2.5 text-xs font-bold text-[#7d8783]">定制简历 · 即将推出</button></div></section>
    <div className="mt-5 grid gap-5 xl:grid-cols-[1.5fr_1fr]">
      <div className="space-y-5">
        <AnalysisWorkflow jobId={job.id} initialAnalysis={analysis}/>
        <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-6"><h2 className="text-[15px] font-bold">岗位描述</h2><p className="mt-4 whitespace-pre-line text-sm leading-7 text-[#68736e]">{job.description}</p></section>
      </div>
      <aside><section className="rounded-2xl bg-[#d9ef84] p-5"><Icon name="spark" className="h-5 w-5 text-[#234e43]"/><div className="mt-4 flex items-center justify-between gap-3"><h2 className="text-[15px] font-bold text-[#234e43]">Agent 能力预览</h2><span className="rounded-full bg-white/60 px-2 py-1 text-[9px] font-black text-[#234e43]">未来能力</span></div><p className="mt-2 text-xs leading-5 text-[#436358]">未来可自动完成资料整理、简历建议和面试准备；当前版本不会创建或运行任务。</p><button disabled className="mt-4 w-full cursor-not-allowed rounded-xl bg-[#234e43]/60 py-2.5 text-xs font-bold text-white">暂未开放</button></section></aside>
    </div>
  </div></AppShell>;
}
