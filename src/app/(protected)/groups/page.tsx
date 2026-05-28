import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";
import { mockGroup, mockUser } from "@/lib/mock-data";

const members = [
  { name: "Klot", role: "OWNER", status: "在线" },
  { name: "Alex", role: "MEMBER", status: "已加入" },
  { name: "Mia", role: "MEMBER", status: "待练习" },
  { name: "Chen", role: "MEMBER", status: "待确认" },
];

export default function GroupsPage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
          <StatusPill tone="success">当前空间</StatusPill>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-neutral-950">
            {mockGroup.name}
          </h1>
          <p className="mt-3 text-sm leading-7 text-neutral-600">
            当前登录用户是 {mockUser.name}，正在使用个人空间 + 小组共享题库模式。后续会接小组切换、邀请链接和成员管理。
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <div className="rounded-[28px] border border-white/75 bg-white/45 p-5 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">成员数</p>
            <p className="mt-3 text-3xl font-semibold text-neutral-950">{mockGroup.members}</p>
          </div>
          <div className="rounded-[28px] border border-white/75 bg-white/45 p-5 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">邀请中</p>
            <p className="mt-3 text-3xl font-semibold text-neutral-950">{mockGroup.invitations}</p>
          </div>
        </div>
      </section>

      <SectionCard
        title="成员列表"
        description="预留成员状态、角色和邀请处理入口。"
        action={<button type="button" className="text-sm font-medium text-neutral-700">生成邀请链接</button>}
      >
        <div className="space-y-3">
          {members.map((member) => (
            <div key={member.name} className="flex items-center justify-between rounded-2xl border border-white/70 bg-white/38 px-4 py-4">
              <div>
                <p className="font-medium text-neutral-950">{member.name}</p>
                <p className="mt-1 text-sm text-neutral-600">{member.role}</p>
              </div>
              <StatusPill>{member.status}</StatusPill>
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="邀请页和接受邀请页稍后补齐"
        description="当前已经把小组这一层的壳子摆出来，后续会补 /invite/:token 和邀请确认流程。"
        actionLabel="回到工作台"
        actionHref="/dashboard"
      />
    </div>
  );
}
