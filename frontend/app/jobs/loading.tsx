import { AppShell } from "@/components/app-shell";

export default function JobsLoading() {
  return <AppShell><div className="animate-pulse"><div className="mb-7 h-20 rounded-2xl bg-[#e8ece6]"/><div className="mb-4 h-9 w-64 rounded-full bg-[#e8ece6]"/><section className="soft-shadow overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white">{[1,2,3,4].map((item) => <div key={item} className="flex items-center gap-4 border-t border-[#edf0eb] px-5 py-4"><div className="h-10 w-10 rounded-xl bg-[#e8ece6]"/><div className="h-8 flex-1 rounded-lg bg-[#eef1ec]"/></div>)}</section><p className="mt-4 text-center text-xs text-[#8a938f]">正在读取岗位…</p></div></AppShell>;
}
