import Link from "next/link";
import { Icon } from "./icons";

export function PageHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div>{eyebrow && <p className="mb-2 text-[10px] font-black uppercase tracking-[.18em] text-[#5d7e72]">{eyebrow}</p>}<h1 className="text-[28px] font-semibold tracking-[-.04em] md:text-[34px]">{title}</h1><p className="mt-2 text-sm text-[#707a76]">{description}</p></div>{action}</div>;
}

export function PrimaryButton({ children }: { children: React.ReactNode }) { return <button className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#234e43] px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-[#234e43]/10 transition hover:-translate-y-0.5 hover:bg-[#193c34]"><Icon name="plus" className="h-4 w-4" />{children}</button>; }

export function StatusPill({ status }: { status: string }) {
  const tone = status === "重点跟进" ? "bg-[#e2f0e6] text-[#2e654c]" : status === "准备面试" ? "bg-[#fff0dc] text-[#93602e]" : status === "运行中" ? "bg-[#e4f1e4] text-[#347042]" : "bg-[#eef0ed] text-[#6d7672]";
  return <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-bold ${tone}`}>{status === "运行中" && <span className="h-1.5 w-1.5 rounded-full bg-[#5b9a62]"/>}{status}</span>;
}

export function Score({ value }: { value: number | null }) { return value === null
  ? <span className="text-xs font-semibold text-[#9aa29f]">—</span>
  : <div className="flex items-center gap-2"><div className="h-1.5 w-12 overflow-hidden rounded-full bg-[#e7ebe5]"><div className="h-full rounded-full bg-[#6c9477]" style={{ width: `${value}%` }}/></div><strong className="text-sm">{value}</strong></div>; }

export function JobRow({ job }: { job: { id: string; company: string; role: string; status: string; score: number | null; location: string; date: string; accent: string } }) {
  return <Link href={`/jobs/${job.id}`} className="grid grid-cols-[1fr_auto] items-center gap-4 border-t border-[#edf0eb] px-5 py-4 transition hover:bg-[#f9fbf8] md:grid-cols-[minmax(260px,1.3fr)_1fr_110px_100px_24px]">
    <div className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#edf2eb] text-[11px] font-black text-[#466157]">{job.accent}</span><div className="min-w-0"><p className="truncate text-sm font-bold">{job.role}</p><p className="mt-1 truncate text-xs text-[#7d8682]">{job.company} · {job.location}</p></div></div>
    <div className="hidden md:block"><StatusPill status={job.status}/></div><div className="hidden md:block"><Score value={job.score}/></div><p className="hidden text-xs text-[#8a938f] md:block">{job.date}</p><Icon name="arrow" className="h-4 w-4 text-[#9aa29f]" />
  </Link>;
}
