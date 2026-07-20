import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icons";
import { JobRow, PageHeading, PrimaryButton } from "@/components/ui";
import { api } from "@/lib/api";
import { latestAnalysesByJob, toJobListItem } from "@/lib/jobs";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [jobs, analyses] = await Promise.all([api.getJobs(), api.getAnalyses()]);
  const analysisByJob = latestAnalysesByJob(analyses);
  const scored = [...analysisByJob.values()].filter((item) => item.score !== null);
  const average = scored.length
    ? Math.round(scored.reduce((sum, item) => sum + (item.score ?? 0), 0) / scored.length)
    : null;
  const pending = jobs.filter((job) => !analysisByJob.has(job.id)).length;
  const highMatches = scored.filter((item) => (item.score ?? 0) >= 80).length;
  const coverage = jobs.length ? Math.round((analysisByJob.size / jobs.length) * 100) : 0;
  const recentJobs = jobs.slice(0, 3).map((job) => toJobListItem(job, analysisByJob.get(job.id)));
  const funnel = [
    ["已保存", jobs.length],
    ["已分析", analysisByJob.size],
    ["高匹配", highMatches],
    ["待分析", pending],
  ] as const;
  const maxFunnel = Math.max(...funnel.map(([, value]) => value), 1);

  return <AppShell><div className="animate-rise">
    <PageHeading title="求职工作台" description={`已同步 ${jobs.length} 个岗位，${pending} 个岗位等待分析。`} action={<PrimaryButton>添加岗位</PrimaryButton>} />

    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {[
        ["岗位总数", String(jobs.length), "实时", "briefcase", "bg-[#e7efe8] text-[#315d4f]"],
        ["平均匹配度", average === null ? "—" : `${average}%`, `${scored.length} 份评分`, "trend", "bg-[#edf2d1] text-[#5f6f2d]"],
        ["待分析岗位", String(pending), "等待处理", "clock", "bg-[#f7e9dd] text-[#8d5a35]"],
        ["分析记录", String(analyses.length), "累计", "spark", "bg-[#e9e8f3] text-[#5f587d]"],
      ].map(([label, value, meta, icon, tone], i) => <article key={label} className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5" style={{ animationDelay: `${i * 50}ms` }}><div className="mb-5 flex items-start justify-between"><span className={`grid h-9 w-9 place-items-center rounded-xl ${tone}`}><Icon name={icon} className="h-[18px] w-[18px]" /></span><span className="text-[10px] font-bold text-[#7f8985]">{meta}</span></div><p className="text-[11px] font-semibold text-[#77817d]">{label}</p><p className="mt-1 text-[28px] font-semibold tracking-[-.04em]">{value}</p></article>)}
    </section>

    <section className="mt-5 grid gap-5 xl:grid-cols-[1.6fr_1fr]">
      <article className="soft-shadow overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white">
        <div className="flex items-center justify-between px-5 py-5"><div><h2 className="text-[15px] font-bold">最近岗位</h2><p className="mt-1 text-xs text-[#89928e]">按最近更新时间排序</p></div><Link href="/jobs" className="flex items-center gap-2 text-xs font-bold text-[#315d4f]">查看全部 <Icon name="arrow" className="h-3.5 w-3.5" /></Link></div>
        {recentJobs.length > 0 && <div className="hidden grid-cols-[minmax(260px,1.3fr)_1fr_110px_100px_24px] px-5 pb-2 text-[9px] font-black uppercase tracking-[.12em] text-[#9aa29f] md:grid"><span>岗位</span><span>状态</span><span>匹配度</span><span>更新时间</span><span /></div>}
        {recentJobs.map((job) => <JobRow key={job.id} job={job}/>) }
        {recentJobs.length === 0 && <div className="border-t border-[#edf0eb] px-5 py-12 text-center"><p className="text-sm font-bold text-[#52605a]">还没有岗位</p><p className="mt-2 text-xs text-[#89928e]">添加或从浏览器扩展同步岗位后，会显示在这里。</p></div>}
      </article>

      <article className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-[#234e43] p-5 text-white">
        <div className="flex items-center justify-between"><div><h2 className="text-[15px] font-bold">分析覆盖率</h2><p className="mt-1 text-xs text-white/55">基于已保存岗位与最新分析</p></div><span className="grid h-9 w-9 place-items-center rounded-xl bg-white/10 text-[#d9ef84]"><Icon name="file" className="h-[18px] w-[18px]" /></span></div>
        <div className="my-6 flex items-end justify-between"><div><span className="text-4xl font-semibold tracking-[-.06em]">{coverage}</span><span className="ml-1 text-sm text-white/50">%</span></div><span className="rounded-full bg-[#d9ef84] px-2.5 py-1 text-[10px] font-black text-[#234e43]">{analysisByJob.size} / {jobs.length}</span></div>
        <div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-[#d9ef84]" style={{ width: `${coverage}%` }}/></div>
        <p className="mt-5 text-xs leading-6 text-white/65">匹配分数、模型和分析状态均来自真实 analyses 数据。</p>
        <Link href="/resumes" className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-white/10 py-2.5 text-xs font-bold transition hover:bg-white/15">查看候选人资料 <Icon name="arrow" className="h-3.5 w-3.5" /></Link>
      </article>
    </section>

    <section className="mt-5 grid gap-5 pb-20 xl:grid-cols-[1fr_1.6fr] lg:pb-0">
      <article className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5"><div className="flex items-center justify-between"><div><h2 className="text-[15px] font-bold">求职进度</h2><p className="mt-1 text-xs text-[#89928e]">当前真实数据概览</p></div><span className="text-[10px] font-bold text-[#668176]">实时</span></div><div className="mt-7 flex h-32 items-end justify-between gap-3">{funnel.map(([label, value]) => <div key={label} className="flex h-full flex-1 flex-col items-center gap-2"><strong className="text-xs">{value}</strong><div className="flex min-h-0 w-full flex-1 items-end justify-center"><div className="w-full max-w-14 rounded-t-lg bg-[#b9cdbf]" style={{height: `${value === 0 ? 2 : Math.max(12, (value / maxFunnel) * 100)}%`, backgroundColor: label === "高匹配" ? "#d9ef84" : undefined}}/></div><span className="text-[10px] text-[#7f8985]">{label}</span></div>)}</div></article>
      <article className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5"><div className="flex items-center justify-between"><div><h2 className="text-[15px] font-bold">Agent 能力预览</h2><p className="mt-1 text-xs text-[#89928e]">未来能力，当前版本不会执行自动任务</p></div><span className="rounded-full bg-[#eef0ed] px-2.5 py-1 text-[10px] font-bold text-[#6d7672]">即将推出</span></div><div className="mt-5 space-y-4">{[
        ["岗位自动研究", "整理岗位要求与公司信息", "search"],
        ["简历定制建议", "根据证据生成可审阅的修改建议", "file"],
        ["面试准备清单", "按岗位生成问题与准备方向", "check"],
      ].map(([title, desc, icon]) => <div key={title} className="flex gap-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#f0f2ee] text-[#75807b]"><Icon name={icon} className="h-4 w-4" /></span><div><p className="text-xs font-bold">{title}</p><p className="mt-1 text-[11px] text-[#7f8985]">{desc}</p></div></div>)}</div><Link href="/agents" className="mt-5 inline-flex text-xs font-bold text-[#315d4f]">查看能力预览</Link></article>
    </section>
  </div></AppShell>;
}
