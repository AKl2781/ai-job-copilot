import { AppShell } from "@/components/app-shell";
import { Icon } from "@/components/icons";
import { PageHeading } from "@/components/ui";
import { api, ApiError, type Profile } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ResumesPage() {
  let profile: Profile | null = null;
  try {
    profile = await api.getMyProfile();
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 404)) throw error;
  }

  return <AppShell><div className="animate-rise"><PageHeading eyebrow="Candidate profile" title="候选人资料" description="从真实候选人 Profile 展示求职方向、简介和技能。"/>
    {!profile ? <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white px-6 py-16 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#e8efe8] text-[#3d6758]"><Icon name="file"/></span><h2 className="mt-4 text-sm font-bold">尚未创建候选人资料</h2><p className="mt-2 text-xs text-[#858e8a]">通过 Profile API 创建资料后，这里会自动显示。</p></section> : <div className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
      <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-6"><div className="flex items-start justify-between"><div className="flex gap-4"><span className="grid h-12 w-12 place-items-center rounded-xl bg-[#e8efe8] text-sm font-black text-[#3d6758]">{profile.name.slice(0, 2).toUpperCase()}</span><div><h2 className="text-lg font-bold">{profile.name}</h2><p className="mt-1 text-xs text-[#858e8a]">{profile.target_role || "暂未设置目标岗位"}</p></div></div><span className="rounded-full bg-[#e7f0e9] px-2.5 py-1 text-[10px] font-bold text-[#3d6c50]">API 已同步</span></div><div className="mt-7 border-t border-[#edf0eb] pt-5"><h3 className="text-xs font-bold">个人简介</h3><p className="mt-3 whitespace-pre-line text-sm leading-7 text-[#626d68]">{profile.summary || "暂未填写个人简介。"}</p></div><p className="mt-6 text-[10px] text-[#929a96]">更新于 {new Date(profile.updated_at).toLocaleString("zh-CN")}</p></section>
      <section className="soft-shadow rounded-2xl border border-[#e4e9e2] bg-white p-6"><h2 className="text-[15px] font-bold">技能</h2><p className="mt-1 text-xs text-[#858e8a]">来自候选人 Profile 的技能列表。</p>{profile.skills.length > 0 ? <div className="mt-5 flex flex-wrap gap-2">{profile.skills.map((skill) => <span key={skill} className="rounded-lg bg-[#e7f0e9] px-3 py-2 text-xs font-semibold text-[#3d6c50]">{skill}</span>)}</div> : <p className="mt-5 rounded-xl bg-[#f5f7f3] p-4 text-xs text-[#858e8a]">暂未添加技能。</p>}</section>
    </div>}
  </div></AppShell>;
}
