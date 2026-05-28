import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";

const summaryRows = [
  { label: "总体评分", value: "78", hint: "较上次提升 6 分" },
  { label: "薄弱标签", value: "React / 事件循环", hint: "建议专项复习" },
  { label: "下一轮建议", value: "加大中高难度占比", hint: "补足原理题" },
];

export default function PracticeSummariesPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
        <StatusPill>练习总结</StatusPill>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-neutral-950">复盘与推荐</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-neutral-600">
          这里会汇总分数、薄弱标签和下一轮建议，帮助形成练习闭环。
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        {summaryRows.map((item) => (
          <div key={item.label} className="rounded-[28px] border border-white/75 bg-white/45 p-5 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">{item.label}</p>
            <p className="mt-3 text-3xl font-semibold text-neutral-950">{item.value}</p>
            <p className="mt-2 text-sm leading-6 text-neutral-600">{item.hint}</p>
          </div>
        ))}
      </div>

      <SectionCard title="每题表现" description="后续会展示每题得分、缺失点、参考表达和追问。">
        <div className="space-y-3">
          {["JavaScript 基础", "React 渲染机制", "浏览器缓存"].map((item) => (
            <div key={item} className="flex items-center justify-between rounded-2xl border border-white/70 bg-white/38 px-4 py-4">
              <p className="font-medium text-neutral-950">{item}</p>
              <StatusPill tone="warning">待补充</StatusPill>
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="总结数据还未接真实会话"
        description="当前先把总结页结构准备好，等练习页和 AI 反馈接上后，这里可以直接展示完整复盘。"
        actionLabel="回到工作台"
        actionHref="/dashboard"
      />
    </div>
  );
}
