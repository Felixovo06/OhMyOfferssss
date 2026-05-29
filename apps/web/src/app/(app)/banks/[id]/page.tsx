"use client"

import { useParams, useRouter } from "next/navigation"
import { useState, useMemo } from "react"
import { useBank, useQuestions, useCreateQuestion, useUpdateQuestion, useDeleteQuestion } from "@/lib/query/banks"
import { useAuthStore } from "@/lib/store/auth"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import {
  ArrowLeft,
  Loader2,
  Plus,
  Trash2,
  Search,
  BookOpen,
  Library,
  Eye,
  EyeOff,
} from "lucide-react"
import { toast } from "sonner"

const difficultyLabels: Record<number, string> = {
  1: "简单",
  2: "较易",
  3: "中等",
  4: "较难",
  5: "困难",
}

const difficultyColors: Record<number, string> = {
  1: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  2: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  3: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  4: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  5: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
}

function difficultyLabel(score?: number | null) {
  if (score == null) return "未设置"
  return difficultyLabels[score] ?? "未设置"
}

function difficultyColor(score?: number | null) {
  if (score == null) return "bg-muted text-muted-foreground"
  return difficultyColors[score] ?? "bg-muted text-muted-foreground"
}

const questionSchema = z.object({
  content: z.string().min(1, "请输入题目内容"),
  answer: z.string().optional(),
  tags: z.string().optional(),
  difficulty: z.number().min(1).max(5),
})

type QuestionForm = z.infer<typeof questionSchema>

export default function BankDetailPage() {
  const params = useParams()
  const router = useRouter()
  const bankId = params.id as string
  const { user } = useAuthStore()

  const { data: bank, isLoading: bankLoading } = useBank(bankId)
  const { data: questions, isLoading: questionsLoading } = useQuestions(bankId)
  const createQuestion = useCreateQuestion()
  const updateQuestion = useUpdateQuestion()
  const deleteQuestion = useDeleteQuestion()

  const isOwner = bank?.owner_id === user?.id

  const [searchKeyword, setSearchKeyword] = useState("")
  const [difficultyFilter, setDifficultyFilter] = useState<number | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const [createOpen, setCreateOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const filteredQuestions = useMemo(() => {
    if (!questions) return []
    let list = [...questions]
    if (searchKeyword) {
      list = list.filter((q) => q.content.includes(searchKeyword))
    }
    if (difficultyFilter) {
      list = list.filter((q) => q.difficulty === difficultyFilter)
    }
    if (statusFilter) {
      list = list.filter((q) => q.status === statusFilter)
    }
    return list
  }, [questions, searchKeyword, difficultyFilter, statusFilter])

  const createForm = useForm<QuestionForm>({
    resolver: zodResolver(questionSchema),
    defaultValues: { content: "", answer: "", tags: "", difficulty: 3 },
  })

  const editForm = useForm<QuestionForm>({
    resolver: zodResolver(questionSchema),
    defaultValues: { content: "", answer: "", tags: "", difficulty: 3 },
  })

  function handleCreate(data: QuestionForm) {
    createQuestion.mutate(
      {
        bankId,
        data: {
          content: data.content,
          answer: data.answer || undefined,
          tags: data.tags ? data.tags.split(/[,，\s]+/).filter(Boolean) : [],
          difficulty: data.difficulty,
        },
      },
      {
        onSuccess: () => {
          toast.success("题目创建成功")
          setCreateOpen(false)
          createForm.reset()
        },
        onError: (err) => {
          toast.error(err.message || "创建失败")
        },
      },
    )
  }

  function openEdit(questionId: string) {
    const q = questions?.find((x) => x.id === questionId)
    if (!q) return
    setEditTarget(questionId)
    editForm.reset({
      content: q.content,
      answer: q.answer || "",
      tags: q.tags.join(", "),
      difficulty: q.difficulty ?? 3,
    })
  }

  function handleEdit(data: QuestionForm) {
    if (!editTarget) return
    updateQuestion.mutate(
      {
        id: editTarget,
        data: {
          content: data.content,
          answer: data.answer || undefined,
          tags: data.tags ? data.tags.split(/[,，\s]+/).filter(Boolean) : [],
          difficulty: data.difficulty,
        },
      },
      {
        onSuccess: () => {
          toast.success("题目已更新")
          setEditTarget(null)
        },
        onError: (err) => {
          toast.error(err.message || "更新失败")
        },
      },
    )
  }

  function handleToggleStatus(questionId: string, currentStatus: string) {
    const newStatus = currentStatus === "active" ? "disabled" : "active"
    updateQuestion.mutate(
      { id: questionId, data: { status: newStatus as "active" | "disabled" } },
      {
        onSuccess: () => {
          toast.success(newStatus === "active" ? "题目已启用" : "题目已禁用")
        },
      },
    )
  }

  function handleDelete(questionId: string) {
    deleteQuestion.mutate(questionId, {
      onSuccess: () => {
        toast.success("题目已删除")
        setDeleteTarget(null)
      },
      onError: (err) => {
        toast.error(err.message || "删除失败")
      },
    })
  }

  if (bankLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!bank) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <Library className="h-12 w-12 text-muted-foreground/50" />
        <div>
          <p className="text-lg font-medium">题库不存在</p>
          <p className="text-sm text-muted-foreground">该题库可能已被删除</p>
        </div>
        <Button variant="outline" onClick={() => router.push("/banks")}>
          返回题库列表
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => router.push("/banks")}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        返回题库列表
      </Button>

      {/* Bank Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{bank.name}</h1>
            <Badge variant="outline">{bank.question_count} 题</Badge>
          </div>
          {bank.description && (
            <p className="mt-1 text-sm text-muted-foreground">{bank.description}</p>
          )}
          {bank.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {bank.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-[11px]">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
          {bank.target_positions && bank.target_positions.length > 0 && (
            <p className="mt-2 text-xs text-muted-foreground">
              适配岗位：{bank.target_positions.join("、")}
            </p>
          )}
          {bank.skill_keywords && bank.skill_keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {bank.skill_keywords.map((s) => (
                <Badge key={s} variant="outline" className="text-[10px] text-primary">
                  {s}
                </Badge>
              ))}
            </div>
          )}
        </div>
        {isOwner && (
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-1 h-4 w-4" />
            添加题目
          </Button>
        )}
      </div>

      <Separator />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索题目..."
            className="pl-8"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
          />
        </div>
        <Select
          value={difficultyFilter ? String(difficultyFilter) : ""}
          onValueChange={(v) => setDifficultyFilter(v ? Number(v) : null)}
        >
          <SelectTrigger className="w-[100px]">
            <SelectValue placeholder="难度" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">全部难度</SelectItem>
            {[1, 2, 3, 4, 5].map((d) => (
              <SelectItem key={d} value={String(d)}>
                {difficultyLabels[d]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter || ""} onValueChange={(v) => setStatusFilter(v || null)}>
          <SelectTrigger className="w-[100px]">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">全部状态</SelectItem>
            <SelectItem value="active">已启用</SelectItem>
            <SelectItem value="disabled">已禁用</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Question List */}
      {questionsLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : filteredQuestions.length > 0 ? (
        <div className="space-y-3">
          {filteredQuestions.map((q) => (
            <Card key={q.id} className={q.status === "disabled" ? "opacity-60" : ""}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium leading-relaxed">{q.content}</p>
                    {q.answer && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                          查看答案
                        </summary>
                        <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">
                          {q.answer}
                        </p>
                      </details>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${difficultyColor(q.difficulty)}`}>
                        {difficultyLabel(q.difficulty)}
                      </span>
                      {q.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-[10px]">
                          {tag}
                        </Badge>
                      ))}
                      {q.status === "disabled" && (
                        <Badge variant="outline" className="text-[10px] text-muted-foreground">
                          已禁用
                        </Badge>
                      )}
                    </div>
                  </div>
                  {isOwner && (
                    <div className="flex shrink-0 items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleToggleStatus(q.id, q.status)}
                        title={q.status === "active" ? "禁用" : "启用"}
                      >
                        {q.status === "active" ? (
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 text-xs"
                        onClick={() => openEdit(q.id)}
                      >
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setDeleteTarget(q.id)}
                      >
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <BookOpen className="h-12 w-12 text-muted-foreground/50" />
          <div>
            <p className="text-lg font-medium">
              {searchKeyword || difficultyFilter || statusFilter ? "没有匹配的题目" : "还没有题目"}
            </p>
            <p className="text-sm text-muted-foreground">
              {searchKeyword || difficultyFilter || statusFilter
                ? "尝试调整筛选条件"
                : "添加第一道面试题目"}
            </p>
          </div>
          {isOwner && !searchKeyword && !difficultyFilter && !statusFilter && (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="mr-1 h-4 w-4" />
              添加题目
            </Button>
          )}
        </div>
      )}

      {/* Create Question Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>添加题目</DialogTitle>
            <DialogDescription>为题库添加新的面试题目</DialogDescription>
          </DialogHeader>
          <Form {...createForm}>
            <form onSubmit={createForm.handleSubmit(handleCreate)} className="space-y-4">
              <FormField
                control={createForm.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>题目内容</FormLabel>
                    <FormControl>
                      <Textarea placeholder="输入题目内容..." className="min-h-[100px]" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={createForm.control}
                name="answer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>参考答案（可选）</FormLabel>
                    <FormControl>
                      <Textarea placeholder="输入参考答案..." className="min-h-[80px]" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={createForm.control}
                  name="difficulty"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>难度</FormLabel>
                      <Select onValueChange={(v) => field.onChange(Number(v))} value={String(field.value)}>
                        <FormControl>
                          <SelectTrigger>
                            <span>{difficultyLabels[field.value] ?? "请选择难度"}</span>
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {[1, 2, 3, 4, 5].map((d) => (
                            <SelectItem key={d} value={String(d)}>
                              {difficultyLabels[d]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={createForm.control}
                  name="tags"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>标签（可选，逗号分隔）</FormLabel>
                      <FormControl>
                        <Input placeholder="React, TypeScript" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createQuestion.isPending}>
                  {createQuestion.isPending ? "添加中..." : "添加"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Edit Question Dialog */}
      <Dialog open={!!editTarget} onOpenChange={(o) => !o && setEditTarget(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑题目</DialogTitle>
            <DialogDescription>修改题目内容</DialogDescription>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit(handleEdit)} className="space-y-4">
              <FormField
                control={editForm.control}
                name="content"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>题目内容</FormLabel>
                    <FormControl>
                      <Textarea className="min-h-[100px]" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={editForm.control}
                name="answer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>参考答案</FormLabel>
                    <FormControl>
                      <Textarea className="min-h-[80px]" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={editForm.control}
                  name="difficulty"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>难度</FormLabel>
                      <Select onValueChange={(v) => field.onChange(Number(v))} value={String(field.value)}>
                        <FormControl>
                          <SelectTrigger>
                            <span>{difficultyLabels[field.value] ?? "请选择难度"}</span>
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {[1, 2, 3, 4, 5].map((d) => (
                            <SelectItem key={d} value={String(d)}>
                              {difficultyLabels[d]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={editForm.control}
                  name="tags"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>标签（逗号分隔）</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <DialogFooter>
                <Button type="submit" disabled={updateQuestion.isPending}>
                  {updateQuestion.isPending ? "保存中..." : "保存"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>删除后无法恢复，确定要删除这道题吗？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              disabled={deleteQuestion.isPending}
              onClick={() => deleteTarget && handleDelete(deleteTarget)}
            >
              {deleteQuestion.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
