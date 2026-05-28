import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";

const options = [
  "选择题库：个人 / 小组",
  "选择标签：React / 浏览器 / 性能",
  "设置题量：5 / 10 / 15",
  "设置难度倾向：偏基础 / 均衡 / 偏进阶",
];

export default function NormalPracticePage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
        <StatusPill tone="success">普通面试</StatusPill>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-neutral-950">配置练习参数</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-neutral-600">
          先把普通面试的配置页搭起来，后面再接题库、标签和抽题理由。
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button type="button" className="inline-flex min-h-11 items-center rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white">开始练习</button>
          <a href="/practice/custom" className="inline-flex min-h-11 items-center rounded-xl border border-neutral-950/10 bg-white/45 px-4 text-sm font-medium text-neutral-700">切到客制化面试</a>
        </div>
      </section>

      <SectionCard
        title="配置项"
        description="这些控件后续会变成真正的表单、选择器和筛选器。"
      >
        <div className="grid gap-4 md:grid-cols-2">
          {options.map((item) => (
            <div key={item} className="rounded-2xl border border-white/70 bg-white/38 p-4 text-sm text-neutral-700">
              {item}
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="练习详情页暂未接入"
        description="这个页面先把进入练习的入口、配置和后续落点铺好，后续会接 session 详情和题目流。"
        actionLabel="去总结页"
        actionHref="/practice/summaries"
      />
    </div>
  );
}
