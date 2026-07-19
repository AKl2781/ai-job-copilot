import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icons";
import { JobRow, PageHeading, PrimaryButton } from "@/components/ui";
import { jobs, skills } from "@/lib/data";

export default function DashboardPage() {
  return <AppShell><div className="animate-rise">
    <PageHeading title="早上好，流水" description="今天有 3 个岗位值得关注，Agent 已为你完成 7 项任务。" action={<PrimaryButton>添加岗位</PrimaryButton>} />

    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {[
        ["岗位总数", "24", "+4 本周", "briefcase", "bg-[#e7efe8] text-[#315d4f]"],
        ["平均匹配度", "82%", "+6%", "trend", "bg-[#edf2d1] text-[#5f6f2d]"],
        ["待处理任务", "5", "2 项紧急", "clock", "bg-[#f7e9dd] text-[#8d5a35]"],
        ["Agent 已节省", "6.8h", "本周", "spark", "bg-[#e9e8f3] text-[#5f587d]"],
      ].map(([label, value, meta, icon, tone], i) => <article key={label} className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5" style={{ animationDelay: `${i * 50}ms` }}><div className="mb-5 flex items-start justify-between"><span className={`grid h-9 w-9 place-items-center rounded-xl ${tone}`}><Icon name={icon} className="h-[18px] w-[18px]" /></span><span className="text-[10px] font-bold text-[#7f8985]">{meta}</span></div><p className="text-[11px] font-semibold text-[#77817d]">{label}</p><p className="mt-1 text-[28px] font-semibold tracking-[-.04em]">{value}</p></article>)}
    </section>

    <section className="mt-5 grid gap-5 xl:grid-cols-[1.6fr_1fr]">
      <article className="soft-shadow overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white">
        <div className="flex items-center justify-between px-5 py-5"><div><h2 className="text-[15px] font-bold">最近岗位</h2><p className="mt-1 text-xs text-[#89928e]">按最近更新时间排序</p></div><Link href="/jobs" className="flex items-center gap-2 text-xs font-bold text-[#315d4f]">查看全部 <Icon name="arrow" className="h-3.5 w-3.5" /></Link></div>
        <div className="hidden grid-cols-[minmax(260px,1.3fr)_1fr_110px_100px_24px] px-5 pb-2 text-[9px] font-black uppercase tracking-[.12em] text-[#9aa29f] md:grid"><span>岗位</span><span>状态</span><span>匹配度</span><span>更新时间</span><span /></div>
        {jobs.slice(0, 3).map((job) => <JobRow key={job.id} job={job}/>) }
      </article>

      <article className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-[#234e43] p-5 text-white">
        <div className="flex items-center justify-between"><div><h2 className="text-[15px] font-bold">简历竞争力</h2><p className="mt-1 text-xs text-white/55">基于目标岗位动态评估</p></div><span className="grid h-9 w-9 place-items-center rounded-xl bg-white/10 text-[#d9ef84]"><Icon name="file" className="h-[18px] w-[18px]" /></span></div>
        <div className="my-6 flex items-end justify-between"><div><span className="text-4xl font-semibold tracking-[-.06em]">84</span><span className="ml-1 text-sm text-white/50">/ 100</span></div><span className="rounded-full bg-[#d9ef84] px-2.5 py-1 text-[10px] font-black text-[#234e43]">表现优秀</span></div>
        <div className="space-y-3">{skills.map((skill) => <div key={skill.name}><div className="mb-1.5 flex justify-between text-[11px]"><span className="text-white/70">{skill.name}</span><span className="font-bold">{skill.level}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-[#d9ef84]" style={{ width: `${skill.level}%` }}/></div></div>)}</div>
        <Link href="/resumes" className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-white/10 py-2.5 text-xs font-bold transition hover:bg-white/15">查看优化建议 <Icon name="arrow" className="h-3.5 w-3.5" /></Link>
      </article>
    </section>

    <section className="mt-5 grid gap-5 pb-20 xl:grid-cols-[1fr_1.6fr] lg:pb-0">
      <article className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5"><div className="flex items-center justify-between"><div><h2 className="text-[15px] font-bold">求职进度</h2><p className="mt-1 text-xs text-[#89928e]">本月岗位转化漏斗</p></div><span className="text-[10px] font-bold text-[#668176]">7 月</span></div><div className="mt-7 flex h-32 items-end justify-between gap-3">{[["收藏",24,100],["分析",18,77],["跟进",9,48],["面试",3,25]].map(([label, value, height]) => <div key={label} className="flex h-full flex-1 flex-col items-center gap-2"><strong className="text-xs">{value}</strong><div className="flex min-h-0 w-full flex-1 items-end justify-center"><div className="h-full w-full max-w-14 rounded-t-lg bg-[#b9cdbf]" style={{height: `${height}%`, backgroundColor: label === "面试" ? "#d9ef84" : undefined}}/></div><span className="text-[10px] text-[#7f8985]">{label}</span></div>)}</div></article>
      <article className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-5"><div className="flex items-center justify-between"><div><h2 className="text-[15px] font-bold">Agent 运行动态</h2><p className="mt-1 text-xs text-[#89928e]">自动任务实时记录</p></div><Link href="/agents" className="text-xs font-bold text-[#315d4f]">查看详情</Link></div><div className="mt-5 space-y-4">{[
        ["岗位分析完成", "完成「AI 产品经理」的技能匹配与差距分析", "2 分钟前", "check"],
        ["简历建议已生成", "针对 FlowMind 岗位生成 4 条优化建议", "26 分钟前", "file"],
        ["新岗位已同步", "从浏览器扩展导入 3 个岗位", "1 小时前", "link"],
      ].map(([title, desc, time, icon], i) => <div key={title} className="flex gap-3"><span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${i === 0 ? "bg-[#e5f0e7] text-[#447254]" : "bg-[#f0f2ee] text-[#75807b]"}`}><Icon name={icon} className="h-4 w-4" /></span><div className="min-w-0 flex-1"><div className="flex justify-between gap-3"><p className="text-xs font-bold">{title}</p><time className="whitespace-nowrap text-[10px] text-[#9aa29f]">{time}</time></div><p className="mt-1 truncate text-[11px] text-[#7f8985]">{desc}</p></div></div>)}</div></article>
    </section>
  </div></AppShell>;
}
