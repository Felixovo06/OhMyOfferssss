import { Banknote, BookOpenText, Clock3, Sparkles } from "lucide-react";
import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";
import { dashboardStats, practiceRoutes, recentPracticeSessions, taskChecklist } from "@/lib/mock-data";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <div className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <StatusPill tone="success">阶段 1 进行中</StatusPill>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight text-neutral-950">
                工作台
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-neutral-600 sm:text-base">
                这里汇总题库、导入、练习和小组状态。先从飞书导入和面试配置把核心流程跑顺。
              </p>
            </div>
            <div className="hidden rounded-2xl bg-neutral-950 px-4 py-3 text-right text-white sm:block">
              <p className="text-xs uppercase tracking-[0.2em] text-neutral-500">目标</p>
              <p className="mt-1 text-sm font-medium">完整前端闭环</p>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href="/practice/normal"
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white transition hover:bg-neutral-800"
            >
              <Sparkles className="h-4 w-4" />
              开始普通面试
            </a>
            <a
              href="/practice/custom"
              className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-neutral-950/10 bg-white/45 px-4 text-sm font-medium text-neutral-700 transition hover:bg-white/38"
            >
              <BookOpenText className="h-4 w-4" />
              上传简历开始客制化面试
            </a>
            <a
              href="/imports"
              className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-neutral-950/10 bg-white/45 px-4 text-sm font-medium text-neutral-700 transition hover:bg-white/38"
            >
              <Clock3 className="h-4 w-4" />
              导入飞书文档
            </a>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
          {dashboardStats.map((item) => (
            <div key={item.label} className="rounded-[28px] border border-white/75 bg-white/45 p-5 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">{item.label}</p>
              <p className="mt-3 text-3xl font-semibold text-neutral-950">{item.value}</p>
              <p className="mt-2 text-sm leading-6 text-neutral-600">{item.hint}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionCard
          title="最近练习记录"
          description="这部分后续会接 /api/practice-sessions/recent。现在先把展示和筛选位摆好。"
          action={<a href="/practice/summaries" className="text-sm font-medium text-neutral-700">查看总结</a>}
        >
          <div className="space-y-3">
            {recentPracticeSessions.map((item) => (
              <div key={item.title} className="flex items-start justify-between gap-4 rounded-2xl border border-white/70 bg-white/38 px-4 py-4">
                <div>
                  <p className="font-medium text-neutral-950">{item.title}</p>
                  <p className="mt-1 text-sm text-neutral-600">{item.meta}</p>
                </div>
                <StatusPill>{item.status}</StatusPill>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="薄弱标签与任务"
          description="把弱项和下一步操作放在一起，方便快速推进。"
        >
          <div className="space-y-4">
            <div className="rounded-2xl border border-neutral-950/10 bg-white/38 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]">
              <div className="flex items-center gap-2 text-neutral-900">
                <Banknote className="h-4 w-4" />
                <p className="text-sm font-medium">当前薄弱标签</p>
              </div>
              <p className="mt-2 text-sm leading-6 text-neutral-600">
                React、浏览器渲染、性能优化。建议先从这几个标签的题目做一轮专项练习。
              </p>
            </div>
            <ul className="space-y-2">
              {taskChecklist.map((item) => (
                <li key={item} className="flex items-start gap-3 rounded-2xl border border-white/75 bg-white/45 px-4 py-3 text-sm text-neutral-700">
                  <span className="mt-1 h-2 w-2 rounded-full bg-neutral-400" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </SectionCard>
      </div>

      <SectionCard
        title="功能入口"
        description="这些入口覆盖前端第一版的核心页面，后续会逐步接到真实数据。"
      >
        <div className="grid gap-4 md:grid-cols-3">
          {practiceRoutes.map((item) => (
            <a key={item.href} href={item.href} className="rounded-2xl border border-white/70 bg-white/38 p-5 transition hover:border-neutral-950/15 hover:bg-white">
              <p className="text-base font-semibold text-neutral-950">{item.title}</p>
              <p className="mt-2 text-sm leading-6 text-neutral-600">{item.description}</p>
            </a>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="还没有接入真实统计数据"
        description="当前先用结构化占位信息把整站前端跑通，后续接入后端接口后，这里会自动显示题库、会话和导入的真实状态。"
        actionLabel="去飞书导入"
        actionHref="/imports"
      />
    </div>
  );
}
