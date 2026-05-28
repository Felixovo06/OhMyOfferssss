import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";
import { banks } from "@/lib/mock-data";

export default function BanksPage() {
  return (
    <div className="space-y-6">
      <section className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-neutral-950">题库</h1>
          <p className="mt-2 text-sm leading-6 text-neutral-600">
            管理个人题库和小组题库，后续接入搜索、筛选和编辑能力。
          </p>
        </div>
        <button type="button" className="inline-flex min-h-11 items-center rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white">
          新建题库
        </button>
      </section>

      <SectionCard
        title="题库列表"
        description="这里预留搜索、标签筛选和难度筛选，后续可接 /api/banks。"
      >
        <div className="space-y-3">
          {banks.map((bank) => (
            <div key={bank.name} className="rounded-2xl border border-white/70 bg-white/38 p-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-base font-semibold text-neutral-950">{bank.name}</p>
                    <StatusPill>{bank.scope}</StatusPill>
                  </div>
                  <p className="mt-2 text-sm text-neutral-600">{bank.questions} 道题目</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {bank.tags.map((tag) => (
                    <span key={tag} className="rounded-full bg-white px-3 py-1 text-xs font-medium text-neutral-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="题库详情页待接入"
        description="阶段 2 会补上题库详情、题目列表、标签筛选、编辑与删除。当前先把列表与入口统一起来。"
        actionLabel="查看导入"
        actionHref="/imports"
      />
    </div>
  );
}
