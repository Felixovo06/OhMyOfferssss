"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useBanks } from "@/lib/query/banks"
import { useCreateSession } from "@/lib/query/interviews"
import { useResume, useResumes, useUploadResume } from "@/lib/query/resumes"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sparkles,
  Loader2,
  ArrowLeft,
  Check,
  BookOpen,
  FileText,
  AlertCircle,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { toast } from "sonner"

const BANKS_PER_PAGE = 6

const difficultyLabels: Record<number, string> = {
  1: "简单",
  2: "较易",
  3: "中等",
  4: "较难",
  5: "困难",
}

export default function NewInterviewPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const resumeId = searchParams.get("resume_id")
  const { data: banks, isLoading: banksLoading, error: banksError, refetch: refetchBanks } = useBanks()
  const { data: resumes } = useResumes()
  const createSession = useCreateSession()
  const uploadResume = useUploadResume()

  const [selectedBankIds, setSelectedBankIds] = useState<string[]>([])
  const [bankSelectionTouched, setBankSelectionTouched] = useState(false)
  const [bankPickerOpen, setBankPickerOpen] = useState(false)
  const [bankPage, setBankPage] = useState(0)
  const [mode, setMode] = useState<"normal" | "custom">(resumeId ? "custom" : "normal")
  const [selectedResumeId, setSelectedResumeId] = useState<string>(resumeId || "")
  const [selectedTags, setSelectedTags] = useState<string>("")
  const [difficulty, setDifficulty] = useState<string>("")
  const [questionCount, setQuestionCount] = useState("5")
  const [goal, setGoal] = useState("")
  const [flowMode, setFlowMode] = useState<"project" | "knowledge">("project")
  const { data: resume } = useResume(mode === "custom" && selectedResumeId ? selectedResumeId : null)

  const activeBankIds = bankSelectionTouched
    ? selectedBankIds
    : banks?.map((bank) => bank.id) ?? []
  const bankCount = banks?.length ?? 0
  const totalBankPages = Math.max(1, Math.ceil(bankCount / BANKS_PER_PAGE))
  const safeBankPage = Math.min(bankPage, totalBankPages - 1)
  const visibleBanks = banks?.slice(
    safeBankPage * BANKS_PER_PAGE,
    safeBankPage * BANKS_PER_PAGE + BANKS_PER_PAGE,
  )
  const selectedBanks = banks?.filter((bank) => activeBankIds.includes(bank.id)) ?? []

  function toggleBank(bankId: string) {
    setBankSelectionTouched(true)
    setSelectedBankIds(
      activeBankIds.includes(bankId)
        ? activeBankIds.filter((id) => id !== bankId)
        : [...activeBankIds, bankId],
    )
  }

  function handleStart() {
    if (activeBankIds.length === 0) {
      toast.error("请至少选择一个题库")
      return
    }
    if (mode === "custom" && !selectedResumeId) {
      toast.error("真实面试模拟需要先选择或上传一份简历")
      return
    }
    if (mode === "custom" && resume?.status === "failed") {
      toast.error(resume.error_message || "这份简历解析失败，请换一份")
      return
    }

    createSession.mutate(
      {
        bank_ids: bankSelectionTouched ? activeBankIds : [],
        tags: selectedTags
          ? selectedTags.split(/[,，\s]+/).filter(Boolean)
          : undefined,
        difficulty: difficulty ? Number(difficulty) : undefined,
        question_count: Number(questionCount),
        goal: goal || undefined,
        mode,
        resume_id: mode === "custom" ? selectedResumeId : undefined,
        flow_mode: mode === "custom" ? flowMode : undefined,
      },
      {
        onSuccess: (session) => {
          router.push(`/interviews/${session.id}`)
        },
        onError: (err) => {
          toast.error(err.message || "创建面试失败")
        },
      },
    )
  }

  function handleResumeUpload(file: File | undefined) {
    if (!file) return
    uploadResume.mutate(file, {
      onSuccess: (uploaded) => {
        setMode("custom")
        setSelectedResumeId(uploaded.id)
        toast.success("简历已上传")
      },
    })
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <Button variant="ghost" size="sm" onClick={() => router.push("/interviews")}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        返回面试
      </Button>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">配置面试</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          AI 将根据你的配置从题库中智能抽题
        </p>
      </div>

      <Separator />

      <section className="space-y-3">
        <h2 className="text-sm font-medium">面试模式</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => setMode("normal")}
            className={`rounded-lg border p-3 text-left transition-all ${
              mode === "normal" ? "border-primary bg-primary/5" : "hover:bg-accent/50"
            }`}
          >
            <p className="text-sm font-medium">普通抽选</p>
            <p className="mt-1 text-xs text-muted-foreground">按题库、标签和难度抽题练习</p>
          </button>
          <button
            type="button"
            onClick={() => setMode("custom")}
            className={`rounded-lg border p-3 text-left transition-all ${
              mode === "custom" ? "border-primary bg-primary/5" : "hover:bg-accent/50"
            }`}
          >
            <p className="text-sm font-medium">真实面试模拟</p>
            <p className="mt-1 text-xs text-muted-foreground">结合简历技能和经历生成追问方向</p>
          </button>
        </div>
      </section>

      {mode === "custom" && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium">选择简历</h2>
          <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <Select value={selectedResumeId} onValueChange={(value) => setSelectedResumeId(value || "")}>
              <SelectTrigger>
                <SelectValue placeholder="选择已有简历" />
              </SelectTrigger>
              <SelectContent>
                {resumes?.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.filename}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div>
              <input
                id="interview-resume-upload"
                type="file"
                className="hidden"
                accept=".txt,.md,.pdf,text/plain,application/pdf"
                onChange={(event) => handleResumeUpload(event.target.files?.[0])}
              />
              <Button
                type="button"
                variant="outline"
                disabled={uploadResume.isPending}
                onClick={() => document.getElementById("interview-resume-upload")?.click()}
              >
                {uploadResume.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="mr-2 h-4 w-4" />
                )}
                上传新简历
              </Button>
            </div>
          </div>
          {selectedResumeId && resume?.status === "completed" && resume.summary && (
            <Card className="border-primary/30 bg-primary/[0.03]">
              <CardContent className="flex items-start gap-4 p-4">
                <FileText className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">简历已关联</p>
                    <Badge variant="outline" className="text-[10px] text-muted-foreground">
                      {resume.filename}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>{resume.summary.name}</span>
                    <span>{resume.summary.email}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {resume.summary.skills.slice(0, 8).map((s) => (
                      <Badge key={s} variant="secondary" className="text-[10px]">
                        {s}
                      </Badge>
                    ))}
                    {resume.summary.skills.length > 8 && (
                      <Badge variant="outline" className="text-[10px]">
                        +{resume.summary.skills.length - 8}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          {selectedResumeId && resume?.status === "failed" && (
            <p className="text-xs text-destructive">{resume.error_message || "简历解析失败"}</p>
          )}
        </section>
      )}

      {/* Interview Flow Mode */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium">面试流程</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => setFlowMode("project")}
            className={`rounded-lg border p-3 text-left transition-all ${
              flowMode === "project" ? "border-primary bg-primary/5" : "hover:bg-accent/50"
            }`}
          >
            <p className="text-sm font-medium">项目优先</p>
            <p className="mt-1 text-xs text-muted-foreground">先围绕简历项目经历追问，再联动知识库题查漏补缺</p>
          </button>
          <button
            type="button"
            onClick={() => setFlowMode("knowledge")}
            className={`rounded-lg border p-3 text-left transition-all ${
              flowMode === "knowledge" ? "border-primary bg-primary/5" : "hover:bg-accent/50"
            }`}
          >
            <p className="text-sm font-medium">知识优先</p>
            <p className="mt-1 text-xs text-muted-foreground">先考察知识点掌握，再结合回答追问项目经历</p>
          </button>
        </div>
      </section>

      {/* Recommended Banks */}
      {mode === "custom" && banks && banks.length > 0 && (
        <section className="space-y-3 rounded-lg border border-primary/20 bg-primary/[0.02] p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <p className="text-sm font-medium">AI 推荐题库</p>
          </div>
          <p className="text-xs text-muted-foreground">根据你的简历和目标，以下题库与你的面试方向最匹配</p>
          <div className="space-y-2">
            {banks.slice(0, 3).map((bank, i) => {
              const reasons = [
                "技能关键词与简历高度匹配",
                "题目难度梯度适合该岗位",
                "覆盖目标岗位核心知识点",
              ]
              return (
                <div key={bank.id} className="flex items-start gap-3">
                  <div className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-medium ${
                    i === 0 ? "bg-primary text-primary-foreground" : "bg-primary/10 text-primary"
                  }`}>
                    {i + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{bank.name}</p>
                    <p className="text-xs text-muted-foreground">{reasons[i]}</p>
                  </div>
                  <Badge variant="secondary" className="shrink-0 text-[10px]">{bank.question_count} 题</Badge>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Select Banks */}
      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-medium">选择题库</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {bankCount > 0
                ? `已选择 ${activeBankIds.length}/${bankCount} 个题库`
                : "选择用于抽题的题库范围"}
            </p>
          </div>
          {banks && banks.length > 0 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setBankPickerOpen((open) => !open)}
            >
              {bankPickerOpen ? "收起" : "展开选择"}
              <ChevronDown
                className={`ml-1 h-4 w-4 transition-transform ${
                  bankPickerOpen ? "rotate-180" : ""
                }`}
              />
            </Button>
          )}
        </div>
        {banksLoading ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {[1, 2].map((i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border p-3">
                <Skeleton className="mt-0.5 h-4 w-4 shrink-0" />
                <div className="min-w-0 flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-48" />
                </div>
              </div>
            ))}
          </div>
        ) : banksError ? (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-500/50" />
            <p className="text-sm text-muted-foreground">题库加载失败</p>
            <Button size="sm" variant="outline" onClick={() => refetchBanks()}>重试</Button>
          </div>
        ) : banks && banks.length > 0 ? (
          <div className="space-y-3">
            {!bankPickerOpen ? (
              <div className="rounded-lg border bg-muted/20 p-3">
                <div className="flex flex-wrap gap-1.5">
                  {selectedBanks.slice(0, 5).map((bank) => (
                    <Badge key={bank.id} variant="secondary" className="max-w-full text-[10px]">
                      <span className="truncate">{bank.name}</span>
                    </Badge>
                  ))}
                  {selectedBanks.length > 5 && (
                    <Badge variant="outline" className="text-[10px]">
                      +{selectedBanks.length - 5}
                    </Badge>
                  )}
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  默认使用全部题库；需要精确控制时展开选择。
                </p>
              </div>
            ) : (
              <>
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-muted/20 p-2">
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setBankSelectionTouched(true)
                        setSelectedBankIds(banks.map((bank) => bank.id))
                      }}
                    >
                      全选
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setBankSelectionTouched(true)
                        setSelectedBankIds([])
                      }}
                    >
                      清空
                    </Button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      disabled={safeBankPage === 0}
                      onClick={() => setBankPage((page) => Math.max(0, page - 1))}
                      aria-label="上一页题库"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="min-w-14 text-center text-xs text-muted-foreground">
                      {safeBankPage + 1}/{totalBankPages}
                    </span>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      disabled={safeBankPage >= totalBankPages - 1}
                      onClick={() => setBankPage((page) => Math.min(totalBankPages - 1, page + 1))}
                      aria-label="下一页题库"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid gap-2 sm:grid-cols-2">
                  {visibleBanks?.map((bank) => {
                    const selected = activeBankIds.includes(bank.id)
                    return (
                      <button
                        key={bank.id}
                        type="button"
                        onClick={() => toggleBank(bank.id)}
                        className={`flex min-h-20 items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                          selected
                            ? "border-primary bg-primary/5"
                            : "hover:border-foreground/20 hover:bg-accent/50"
                        }`}
                      >
                        <div
                          className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border ${
                            selected ? "border-primary bg-primary text-primary-foreground" : ""
                          }`}
                        >
                          {selected && <Check className="h-3 w-3" />}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium">{bank.name}</p>
                          {bank.description && (
                            <p className="line-clamp-1 text-xs text-muted-foreground">
                              {bank.description}
                            </p>
                          )}
                          <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[10px] text-muted-foreground">
                            <span>{bank.question_count} 题</span>
                            {bank.target_positions && bank.target_positions.length > 0 && (
                              <span>适配 {bank.target_positions.slice(0, 2).join("、")}</span>
                            )}
                          </p>
                        </div>
                        {bank.target_positions &&
                          bank.target_positions.some((p) =>
                            goal.toLowerCase().includes(p.toLowerCase()),
                          ) && (
                            <Badge variant="secondary" className="shrink-0 text-[10px] text-primary">
                              推荐
                            </Badge>
                          )}
                      </button>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
              <BookOpen className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">请先在题库页面创建题目</p>
              <Button size="sm" variant="outline" onClick={() => router.push("/banks")}>
                去创建题库
              </Button>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Filters */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium">筛选条件</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted-foreground">标签（可选）</label>
            <Input
              placeholder="CSS, React..."
              value={selectedTags}
              onChange={(e) => setSelectedTags(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">最高难度（可选）</label>
            <Select value={difficulty} onValueChange={(v) => setDifficulty(v || "")}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="不限" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">不限</SelectItem>
                {[1, 2, 3, 4, 5].map((d) => (
                  <SelectItem key={d} value={String(d)}>
                    {difficultyLabels[d]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      {/* Questions Count + Goal */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium">面试设置</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted-foreground">题目数量</label>
            <Select value={questionCount} onValueChange={(v) => setQuestionCount(v || "5")}>
              <SelectTrigger className="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[3, 5, 10, 15, 20].map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    {n} 题
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">面试目标（可选）</label>
          <Textarea
            placeholder="例如：我准备应聘前端高级工程师，希望重点考察 React 和性能优化..."
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="mt-1 resize-none"
            rows={3}
          />
        </div>
      </section>

      <Button
        className="w-full"
        size="lg"
        onClick={handleStart}
        disabled={createSession.isPending || activeBankIds.length === 0}
      >
        {createSession.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            AI 正在抽题...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-4 w-4" />
            AI 智能抽题
          </>
        )}
      </Button>
    </div>
  )
}
