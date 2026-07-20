"use client";

import { AppShell } from "@/components/app-shell";

export default function JobsError({ reset }: { error: Error; reset: () => void }) {
  return <AppShell><section className="soft-shadow rounded-2xl border border-[#eadbd4] bg-white px-6 py-16 text-center"><h1 className="text-lg font-bold">岗位加载失败</h1><p className="mt-2 text-sm text-[#7d8783]">请确认 FastAPI 服务和 API 地址可访问。</p><button onClick={reset} className="mt-5 rounded-xl bg-[#234e43] px-4 py-2.5 text-xs font-bold text-white">重新加载</button></section></AppShell>;
}
