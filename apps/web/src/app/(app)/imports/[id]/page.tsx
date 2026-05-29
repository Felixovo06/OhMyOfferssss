"use client"

import { useParams, useRouter } from "next/navigation"
import { useImportDetail, useConfirmImportItem, useRejectImportItem, useConfirmAllImportItems } from "@/lib/query/imports"
import { useAuthStore } from "@/lib/store/auth"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
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

const difficultyLabels: Record<number, string> = {
  1: "简单",
  2: "较易",
  3: "中等",
  4: "较难",
  5: "困难",
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
  processing: { label: "正在导入", icon: LoaderPinwheel, color: "text-blue-500" },
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

  const batch = data?.batch
  const items = data?.items || []

  const pendingItems = items.filter((i) => i.status === "pending")
  const hasPending = pendingItems.length > 0

  function handleConfirmAll() {
    confirmAll.mutate(batchId, {
      onSuccess: () => toast.success("已确认所有待入库题目"),
      onError: (err) => toast.error(err.message || "批量确认失败"),
    })
  }

  return (
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
                      <Icon className={`mr-1 h-3 w-3 ${batch.status === "processing" ? "animate-spin" : ""}`} />
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
                <Button onClick={handleConfirmAll} disabled={confirmAll.isPending}>
                  <CheckSquare className="mr-1 h-4 w-4" />
                  全部确认入库
                </Button>
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
                              {difficultyLabels[item.difficulty] || item.difficulty}
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
                                onClick={() =>
                                  rejectItem.mutate(item.id, {
                                    onSuccess: () => toast.success("已拒绝"),
                                    onError: (err) => toast.error(err.message || "操作失败"),
                                  })
                                }
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
  )
}
