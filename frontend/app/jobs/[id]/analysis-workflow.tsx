"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { StatusPill } from "@/components/ui";
import { api, type Analysis } from "@/lib/api";

type Phase = "waiting" | "analyzing" | "completed" | "failed";

const phaseLabels: Record<Phase, string> = {
  waiting: "等待分析",
  analyzing: "分析中",
  completed: "完成",
  failed: "失败",
};

function initialPhase(analysis?: Analysis): Phase {
  if (!analysis) return "waiting";
  if (analysis.status.toLowerCase() === "failed") return "failed";
  return analysis.status.toLowerCase() === "completed" ? "completed" : "waiting";
}

function stringList(result: Record<string, unknown>, key: string): string[] {
  const value = result[key];
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function scoreReasons(result: Record<string, unknown>): string[] {
  const breakdown = result.score_breakdown;
  if (typeof breakdown !== "object" || breakdown === null) return [];
  return Object.values(breakdown).flatMap((dimension) => {
    if (typeof dimension !== "object" || dimension === null) return [];
    const reason = (dimension as Record<string, unknown>).reason;
    const applicable = (dimension as Record<string, unknown>).applicable;
    return typeof reason === "string" && applicable !== false ? [reason] : [];
  });
}

export function AnalysisWorkflow({
  jobId,
  initialAnalysis,
}: {
  jobId: string;
  initialAnalysis?: Analysis;
}) {
  const router = useRouter();
  const [analysis, setAnalysis] = useState(initialAnalysis);
  const [phase, setPhase] = useState<Phase>(() => initialPhase(initialAnalysis));
  const [error, setError] = useState<string | null>(null);
  const result = analysis?.result_json ?? {};
  const modelReasons = stringList(result, "reasoning");
  const reasons = modelReasons.length > 0 ? modelReasons : scoreReasons(result);
  const gaps = stringList(result, "missing_skills");

  async function startAnalysis() {
    setPhase("analyzing");
    setError(null);
    try {
      const completed = await api.analyzeJob(jobId);
      setAnalysis(completed);
      setPhase("completed");
      router.refresh();
    } catch (caught) {
      setPhase("failed");
      setError(caught instanceof Error ? caught.message : "分析失败，请稍后重试");
    }
  }

  return <div className="space-y-5">
    <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-6">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[.14em] text-[#6b887c]">AI match report</p>
          <div className="mt-2 flex items-center gap-2">
            <h2 className="text-lg font-bold">岗位匹配分析</h2>
            <StatusPill status={phaseLabels[phase]}/>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right"><span className="text-4xl font-semibold tracking-[-.06em]">{analysis?.score ?? "—"}</span><span className="text-sm text-[#8b9490]"> / 100</span></div>
          <button
            type="button"
            onClick={startAnalysis}
            disabled={phase === "analyzing"}
            className="rounded-xl bg-[#234e43] px-4 py-2.5 text-xs font-bold text-white transition hover:bg-[#193c34] disabled:cursor-wait disabled:bg-[#8a9b95]"
          >{phase === "analyzing" ? "AI 分析中…" : "开始 AI 分析"}</button>
        </div>
      </div>
      {analysis?.score !== null && analysis?.score !== undefined && <div className="mt-5 h-2 overflow-hidden rounded-full bg-[#edf0eb]"><div className="h-full rounded-full bg-[#7ca383]" style={{width: `${analysis.score}%`}}/></div>}
      {phase === "waiting" && <p className="mt-4 text-sm leading-7 text-[#65706b]">该岗位尚未分析，点击“开始 AI 分析”生成匹配报告。</p>}
      {phase === "analyzing" && <p className="mt-4 text-sm leading-7 text-[#65706b]">正在提取岗位要求、匹配候选人证据并计算确定性分数…</p>}
      {phase === "failed" && <p role="alert" className="mt-4 rounded-xl bg-[#fff1ea] px-4 py-3 text-sm text-[#9b4e37]">{error || (typeof result.error === "string" ? result.error : "分析失败，请重试。")}</p>}
      {phase === "completed" && <p className="mt-4 text-sm leading-7 text-[#65706b]">{typeof result.summary === "string" ? result.summary : "分析已完成。"}</p>}
      {analysis && <p className="mt-4 text-[11px] text-[#929a96]">分析时间：{new Date(analysis.updated_at).toLocaleString("zh-CN")}</p>}
    </section>

    {phase === "completed" && <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-6">
      <div className="grid gap-6 sm:grid-cols-2">
        <div><h3 className="text-[15px] font-bold">匹配理由</h3>{reasons.length > 0 ? <ul className="mt-4 space-y-3">{reasons.map((reason) => <li key={reason} className="text-sm leading-6 text-[#65706b]">• {reason}</li>)}</ul> : <p className="mt-4 text-sm text-[#8a938f]">暂无额外匹配理由。</p>}</div>
        <div><h3 className="text-[15px] font-bold">缺口</h3>{gaps.length > 0 ? <div className="mt-4 flex flex-wrap gap-2">{gaps.map((gap) => <span key={gap} className="rounded-lg bg-[#f7eadf] px-2.5 py-1.5 text-[11px] font-semibold text-[#8b5e3b]">{gap}</span>)}</div> : <p className="mt-4 text-sm text-[#8a938f]">未识别到明确缺口。</p>}</div>
      </div>
    </section>}
  </div>;
}
