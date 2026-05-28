import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";
import { feishuBatches } from "@/lib/mock-data";

export default function ImportsPage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
          <StatusPill tone="warning">飞书导入</StatusPill>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-neutral-950">
            导入题库内容
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-neutral-600">
            这里会接飞书文档链接、导入进度、AI 抽题预览和确认入库流程。当前先把操作区和状态区搭出来。
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button type="button" className="inline-flex min-h-11 items-center rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white">
              输入飞书链接
            </button>
            <button type="button" className="inline-flex min-h-11 items-center rounded-xl border border-neutral-950/10 bg-white/45 px-4 text-sm font-medium text-neutral-700">
              查看导入确认
            </button>
          </div>
        </div>

        <div className="rounded-[28px] border border-white/75 bg-white/45 p-5 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
          <p className="text-sm font-semibold text-neutral-950">导入状态</p>
          <div className="mt-4 space-y-3">
            {feishuBatches.map((batch) => (
              <div key={batch.name} className="rounded-2xl border border-white/70 bg-white/38 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-neutral-950">{batch.name}</p>
                  <StatusPill>{batch.status}</StatusPill>
                </div>
                <p className="mt-2 text-sm text-neutral-600">进度 {batch.progress}</p>
                <p className="mt-1 text-sm text-neutral-600">置信度 {batch.confidence}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SectionCard
        title="导入确认流程"
        description="后续会支持编辑、删除、批量确认、低置信度提示和来源片段查看。"
      >
        <div className="grid gap-4 md:grid-cols-3">
          {[
            "解析飞书文档链接",
            "拉取 blocks 并生成预览",
            "AI 抽取题目、答案、标签、难度",
          ].map((item) => (
            <div key={item} className="rounded-2xl border border-white/70 bg-white/38 p-4 text-sm leading-6 text-neutral-700">
              {item}
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="导入结果确认页待接入"
        description="当前先把整套导入页面流铺出来，下一步可以直接接后端批次详情和项目列表。"
        actionLabel="去题库"
        actionHref="/banks"
      />
    </div>
  );
}
