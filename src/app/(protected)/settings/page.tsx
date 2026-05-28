import { EmptyState, SectionCard } from "@/components/ui/empty-state";

const preferences = [
  "主题偏好",
  "默认工作空间",
  "登录态",
  "通知和总结提醒",
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-950">设置</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-neutral-600">
          这里先放用户偏好和基础设置，后续可以接账号、通知和空间配置。
        </p>
      </section>

      <SectionCard title="偏好设置" description="为后续的个性化和多空间协作预留入口。">
        <div className="grid gap-4 md:grid-cols-2">
          {preferences.map((item) => (
            <div key={item} className="rounded-2xl border border-white/70 bg-white/38 p-4 text-sm text-neutral-700">
              {item}
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="当前版本以业务流程为主"
        description="设置页先保持轻量，方便后续扩展账号信息、偏好和系统通知。"
        actionLabel="返回工作台"
        actionHref="/dashboard"
      />
    </div>
  );
}
