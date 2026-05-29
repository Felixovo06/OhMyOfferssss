"use client"

import { useParams, useRouter } from "next/navigation"
import { useState } from "react"
import {
  useImportDetail,
  useConfirmImportItem,
  useRejectImportItem,
  useConfirmAllImportItems,
  useRejectAllImportItems,
} from "@/lib/query/imports"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
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
  ArrowLeft,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  LoaderPinwheel,
  CheckSquare,
  FileInput,
} from "lucide-react"
import { toast } from "sonner"

const difficultyLabels: Record<string, string> = {
  easy: "简单",
  medium: "中等",
  hard: "困难",
}

const statusIcons: Record<string, typeof CheckCircle> = {
  pending: Clock,
  confirmed: CheckCircle,
  rejected: XCircle,
}

const statusLabels: Record<string, string> = {
  pending: "待确认",
  confirmed: "已确认",
  rejected: "已拒绝",
}

const statusColors: Record<string, string> = {
  pending: "text-muted-foreground",
  confirmed: "text-green-500",
  rejected: "text-red-500",
}

const batchStatusConfig: Record<string, { label: string; icon: typeof Clock; color: string }> = {
  pending: { label: "等待处理", icon: Clock, color: "text-muted-foreground" },
  processing: { label: "提取中", icon: LoaderPinwheel, color: "text-blue-500" },
  pending_confirmation: { label: "待确认入库", icon: Clock, color: "text-yellow-600" },
  confirming: { label: "入库中", icon: LoaderPinwheel, color: "text-blue-500" },
  confirmed: { label: "已入库", icon: CheckCircle, color: "text-green-500" },
  completed: { label: "导入完成", icon: CheckCircle, color: "text-green-500" },
  failed: { label: "导入失败", icon: AlertCircle, color: "text-red-500" },
}

export default function ImportDetailPage() {
  const params = useParams()
  const router = useRouter()
  const batchId = params.id as string

  const { data, isLoading } = useImportDetail(batchId)
  const confirmItem = useConfirmImportItem()
  const rejectItem = useRejectImportItem()
  const confirmAll = useConfirmAllImportItems()
  const rejectAll = useRejectAllImportItems()

  const batch = data?.batch
  const items = data?.items || []

  const pendingItems = items.filter((i) => i.status === "pending")
  const hasPending = pendingItems.length > 0

  const [rejectId, setRejectId] = useState<string | null>(null)
  const [showConfirmAll, setShowConfirmAll] = useState(false)
  const [showRejectAll, setShowRejectAll] = useState(false)

  function handleConfirmAll() {
    setShowConfirmAll(true)
  }

  return (
    <>
    <div className="space-y-6 p-6">
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => router.push("/imports")}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        返回导入记录
      </Button>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : !batch ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <FileInput className="h-12 w-12 text-muted-foreground/50" />
          <div>
            <p className="text-lg font-medium">导入记录不存在</p>
            <p className="text-sm text-muted-foreground">该导入记录可能已被删除</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/imports")}>
            返回导入记录
          </Button>
        </div>
      ) : (
        <>
          {/* Batch Header */}
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold tracking-tight">导入详情</h1>
                {(() => {
                  const config = batchStatusConfig[batch.status] || batchStatusConfig.pending
                  const Icon = config.icon
                  return (
                    <Badge variant="outline" className={config.color}>
                      <Icon className={`mr-1 h-3 w-3 ${["processing", "confirming"].includes(batch.status) ? "animate-spin" : ""}`} />
                      {config.label}
                    </Badge>
                  )
                })()}
              </div>
              <p className="mt-1 text-sm text-muted-foreground truncate max-w-xl">
                {batch.source_url}
              </p>
              <p className="text-xs text-muted-foreground">
                {new Date(batch.created_at).toLocaleString("zh-CN")}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {hasPending && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setShowRejectAll(true)}
                    disabled={rejectAll.isPending}
                  >
                    <XCircle className="mr-1 h-4 w-4" />
                    批量删除
                  </Button>
                  <Button onClick={handleConfirmAll} disabled={confirmAll.isPending}>
                    <CheckSquare className="mr-1 h-4 w-4" />
                    全部确认入库
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Progress */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-6 text-sm">
                <span>
                  总题目：<strong>{batch.total_count}</strong>
                </span>
                <span className="text-green-500">
                  已确认：<strong>{batch.confirmed_count}</strong>
                </span>
                <span className="text-red-500">
                  已拒绝：<strong>{items.filter((i) => i.status === "rejected").length}</strong>
                </span>
                <span className="text-muted-foreground">
                  待确认：<strong>{pendingItems.length}</strong>
                </span>
              </div>
            </CardContent>
          </Card>

          <Separator />

          {/* Items */}
          {items.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-16 text-center">
              <FileInput className="h-12 w-12 text-muted-foreground/50" />
              <p className="text-lg font-medium">暂无题目</p>
              <p className="text-sm text-muted-foreground">导入处理中或未抽取到题目</p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item) => {
                const Icon = statusIcons[item.status] || Clock
                const statusColor = statusColors[item.status] || "text-muted-foreground"
                const isPending = item.status === "pending"

                return (
                  <Card key={item.id} className={item.status === "confirmed" ? "border-green-200 dark:border-green-900" : item.status === "rejected" ? "opacity-60" : ""}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium leading-relaxed">
                            {item.question_content}
                          </p>
                          {item.question_answer && (
                            <details className="mt-2">
                              <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                                查看答案
                              </summary>
                              <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">
                                {item.question_answer}
                              </p>
                            </details>
                          )}
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-[11px] font-medium text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
                              {difficultyLabels[item.difficulty_label || ""] || item.difficulty_label || "难度"} · {item.difficulty_score ?? item.difficulty}
                            </span>
                            {item.tags.map((tag) => (
                              <Badge key={tag} variant="outline" className="text-[10px]">
                                {tag}
                              </Badge>
                            ))}
                            <Badge
                              variant="outline"
                              className={`text-[10px] ${item.confidence >= 0.8 ? "text-green-600" : item.confidence >= 0.6 ? "text-yellow-600" : "text-red-600"}`}
                            >
                              置信度: {Math.round(item.confidence * 100)}%
                            </Badge>
                          </div>
                        </div>
                        <div className="flex shrink-0 flex-col items-center gap-2">
                          <Icon className={`h-5 w-5 ${statusColor}`} />
                          <span className={`text-[10px] ${statusColor}`}>
                            {statusLabels[item.status]}
                          </span>
                          {isPending && (
                            <div className="flex gap-1">
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-7 px-2 text-xs"
                                onClick={() =>
                                  confirmItem.mutate(item.id, {
                                    onSuccess: () => toast.success("已确认"),
                                    onError: (err) => toast.error(err.message || "操作失败"),
                                  })
                                }
                                disabled={confirmItem.isPending}
                              >
                                确认
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-7 px-2 text-xs text-red-500 hover:text-red-600"
                                onClick={() => setRejectId(item.id)}
                                disabled={rejectItem.isPending}
                              >
                                拒绝
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>

      {/* Reject confirmation */}
      <Dialog open={!!rejectId} onOpenChange={(o) => !o && setRejectId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认拒绝</DialogTitle>
            <DialogDescription>拒绝后该题目将从导入列表中移除，此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectId(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              disabled={rejectItem.isPending}
              onClick={() => {
                if (rejectId) {
                  rejectItem.mutate(rejectId, {
                    onSuccess: () => {
                      toast.success("已拒绝")
                      setRejectId(null)
                    },
                    onError: (err) => {
                      toast.error(err.message || "操作失败")
                      setRejectId(null)
                    },
                  })
                }
              }}
            >
              {rejectItem.isPending ? "拒绝中..." : "确认拒绝"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirm all dialog */}
      <Dialog open={showConfirmAll} onOpenChange={setShowConfirmAll}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>全部确认入库</DialogTitle>
            <DialogDescription>
              确定将 {pendingItems.length} 道待确认题目全部入库吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmAll(false)}>
              取消
            </Button>
            <Button
              disabled={confirmAll.isPending}
              onClick={() => {
                confirmAll.mutate(batchId, {
                  onSuccess: () => {
                    toast.success("已开始入库，稍后自动刷新状态")
                    setShowConfirmAll(false)
                  },
                  onError: (err) => {
                    toast.error(err.message || "批量确认失败")
                    setShowConfirmAll(false)
                  },
                })
              }}
            >
              {confirmAll.isPending ? "确认中..." : "确认入库"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject all dialog */}
      <Dialog open={showRejectAll} onOpenChange={setShowRejectAll}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量删除待确认题</DialogTitle>
            <DialogDescription>
              确定删除 {pendingItems.length} 道待确认题目吗？已确认入库的题目不会受影响。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectAll(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              disabled={rejectAll.isPending}
              onClick={() => {
                rejectAll.mutate(batchId, {
                  onSuccess: (data) => {
                    toast.success(`已删除 ${data.rejected_count} 道待确认题`)
                    setShowRejectAll(false)
                  },
                  onError: (err) => {
                    toast.error(err.message || "批量删除失败")
                    setShowRejectAll(false)
                  },
                })
              }}
            >
              {rejectAll.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
