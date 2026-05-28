import { EmptyState, SectionCard, StatusPill } from "@/components/ui/empty-state";

const resumeHighlights = [
  "支持 PDF 上传状态",
  "展示简历解析结果",
  "区分文本 PDF 和扫描件提示",
  "为客制化抽题准备简历摘要",
];

export default function CustomPracticePage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-white/75 bg-white/45 p-6 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
        <StatusPill tone="warning">客制化面试</StatusPill>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-neutral-950">上传简历并配置练习</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-neutral-600">
          这部分会围绕简历解析、题库选择和项目追问展开，先把入口和信息结构搭出来。
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button type="button" className="inline-flex min-h-11 items-center rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white">上传 PDF 简历</button>
          <a href="/practice/normal" className="inline-flex min-h-11 items-center rounded-xl border border-neutral-950/10 bg-white/45 px-4 text-sm font-medium text-neutral-700">回到普通面试</a>
        </div>
      </section>

      <SectionCard
        title="简历解析关注点"
        description="后续会接解析状态、技能、经历、项目和追问方向。"
      >
        <div className="grid gap-4 md:grid-cols-2">
          {resumeHighlights.map((item) => (
            <div key={item} className="rounded-2xl border border-white/70 bg-white/38 p-4 text-sm text-neutral-700">
              {item}
            </div>
          ))}
        </div>
      </SectionCard>

      <EmptyState
        title="客制化会话创建页待完成"
        description="当前先给客制化面试的全流程留出位置，后续会接上传、解析和抽题。"
        actionLabel="去飞书导入"
        actionHref="/imports"
      />
    </div>
  );
}
