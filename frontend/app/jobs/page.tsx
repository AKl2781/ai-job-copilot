import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icons";
import { JobRow, PageHeading, PrimaryButton } from "@/components/ui";
import { jobs } from "@/lib/data";

export default function JobsPage() {
  return <AppShell><div className="animate-rise"><PageHeading eyebrow="Job pipeline" title="岗位管理" description="集中管理从浏览器扩展和手动添加的目标岗位。" action={<PrimaryButton>添加岗位</PrimaryButton>}/>
    <div className="mb-4 flex flex-wrap items-center gap-2">{["全部 24", "重点跟进 5", "准备面试 3", "待评估 7", "已归档 9"].map((label, i) => <button key={label} className={`rounded-full px-3.5 py-2 text-xs font-bold ${i === 0 ? "bg-[#234e43] text-white" : "border border-[#dfe5dd] bg-white text-[#6e7874]"}`}>{label}</button>)}<button className="ml-auto hidden items-center gap-2 rounded-xl border border-[#dfe5dd] bg-white px-3 py-2 text-xs font-bold text-[#6e7874] sm:flex"><Icon name="settings" className="h-3.5 w-3.5"/>筛选</button></div>
    <section className="soft-shadow overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white"><div className="hidden grid-cols-[minmax(260px,1.3fr)_1fr_110px_100px_24px] px-5 py-4 text-[9px] font-black uppercase tracking-[.12em] text-[#9aa29f] md:grid"><span>岗位</span><span>状态</span><span>匹配度</span><span>更新时间</span><span/></div>{jobs.map((job) => <JobRow key={job.id} job={job}/>)}</section>
    <p className="mt-4 pb-20 text-center text-[11px] text-[#8a938f] lg:pb-0">Demo 数据 · 共展示 4 个岗位</p>
  </div></AppShell>;
}
