import { AppShell } from "@/components/app-shell";
import { JobRow, PageHeading } from "@/components/ui";
import { api } from "@/lib/api";
import { latestAnalysesByJob, toJobListItem } from "@/lib/jobs";
import { JobCreateForm } from "./job-create-form";

export const dynamic = "force-dynamic";

export default async function JobsPage() {
  const [jobs, analyses] = await Promise.all([api.getJobs(), api.getAnalyses()]);
  const analysisByJob = latestAnalysesByJob(analyses);
  const rows = jobs.map((job) => toJobListItem(job, analysisByJob.get(job.id)));
  const analyzed = rows.filter((job) => job.score !== null).length;
  const pending = rows.filter((job) => job.score === null).length;

  return <AppShell><div className="animate-rise"><PageHeading eyebrow="Job pipeline" title="岗位管理" description="集中管理从浏览器扩展和手动添加的目标岗位。" action={<JobCreateForm />}/>
    <div className="mb-4 flex flex-wrap items-center gap-2">{[`全部 ${rows.length}`, `已评分 ${analyzed}`, `待评分 ${pending}`].map((label, i) => <span key={label} className={`rounded-full px-3.5 py-2 text-xs font-bold ${i === 0 ? "bg-[#234e43] text-white" : "border border-[#dfe5dd] bg-white text-[#6e7874]"}`}>{label}</span>)}</div>
    <section className="soft-shadow overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white">
      {rows.length > 0 && <div className="hidden grid-cols-[minmax(260px,1.3fr)_1fr_110px_100px_24px] px-5 py-4 text-[9px] font-black uppercase tracking-[.12em] text-[#9aa29f] md:grid"><span>岗位</span><span>状态</span><span>匹配度</span><span>更新时间</span><span/></div>}
      {rows.map((job) => <JobRow key={job.id} job={job}/>)}
      {rows.length === 0 && <div className="px-6 py-16 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#edf2eb] text-[#466157]">0</span><h2 className="mt-4 text-sm font-bold">暂无岗位</h2><p className="mt-2 text-xs text-[#858e8a]">添加岗位后，真实数据会显示在这里。</p></div>}
    </section>
    <p className="mt-4 pb-20 text-center text-[11px] text-[#8a938f] lg:pb-0">来自 API · 共 {rows.length} 个岗位</p>
  </div></AppShell>;
}
