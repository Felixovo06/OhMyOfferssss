"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useImportBatches, useCreateImport } from "@/lib/query/imports"
import { useBanks } from "@/lib/query/banks"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"
import { Loader2, FileInput, Link, CheckCircle, Clock, AlertCircle, LoaderPinwheel, ArrowRight } from "lucide-react"
import { toast } from "sonner"

const statusConfig: Record<string, { label: string; icon: typeof Clock; color: string }> = {
  pending: { label: "等待处理", icon: Clock, color: "text-muted-foreground" },
  processing: { label: "正在导入", icon: LoaderPinwheel, color: "text-blue-500" },
  completed: { label: "导入完成", icon: CheckCircle, color: "text-green-500" },
  failed: { label: "导入失败", icon: AlertCircle, color: "text-red-500" },
}

export default function ImportsPage() {
  const router = useRouter()
  const { data: batches, isLoading } = useImportBatches()
  const { data: banks } = useBanks()
  const createImport = useCreateImport()

  const [importOpen, setImportOpen] = useState(false)
  const [importUrl, setImportUrl] = useState("")
  const [selectedBank, setSelectedBank] = useState("")

  function handleStartImport() {
    if (!importUrl.trim()) {
      toast.error("请输入飞书文档链接")
      return
    }

    createImport.mutate(
      {
        url: importUrl.trim(),
        bank_id: selectedBank || undefined,
      },
      {
        onSuccess: (batch) => {
          toast.success("导入请求已提交")
          setImportOpen(false)
          setImportUrl("")
          setSelectedBank("")
          router.push(`/imports/${batch.id}`)
        },
      },
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">飞书导入</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            从飞书文档导入题目，AI 自动抽取并生成待确认题目
          </p>
        </div>
        <Button onClick={() => setImportOpen(true)}>
          <Link className="mr-1 h-4 w-4" />
          导入文档
        </Button>
      </div>

      {/* Import Dialog */}
      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>导入飞书文档</DialogTitle>
            <DialogDescription>
              输入飞书文档链接，系统将自动提取内容并生成题目
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">飞书文档链接</label>
              <Input
                placeholder="https://example.feishu.cn/doc/..."
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">导入到题库（可选）</label>
              <Select value={selectedBank} onValueChange={(v) => setSelectedBank(v || "")}>
                <SelectTrigger className="mt-1 w-full">
                  <SelectValue placeholder="不指定题库" />
                </SelectTrigger>
                <SelectContent>
                  {banks?.map((b) => (
                    <SelectItem key={b.id} value={b.id}>
                      {b.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={handleStartImport}
              disabled={createImport.isPending || !importUrl.trim()}
            >
              {createImport.isPending ? "提交中..." : "开始导入"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Separator />

      {/* Batch List */}
      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">导入记录</h2>
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : batches && batches.length > 0 ? (
          <div className="space-y-2">
            {batches.map((batch) => {
              const config = statusConfig[batch.status] || statusConfig.pending
              const Icon = config.icon
              return (
                <div
                  key={batch.id}
                  onClick={() => router.push(`/imports/${batch.id}`)}
                  className="flex cursor-pointer items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent/50"
                >
                  <div className={config.color}>
                    <Icon className={`h-5 w-5 ${batch.status === "processing" ? "animate-spin" : ""}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{batch.source_url}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(batch.created_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline">
                      {batch.confirmed_count}/{batch.total_count}
                    </Badge>
                    <p className="mt-0.5 text-[10px] text-muted-foreground">{config.label}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
              )
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 py-16 text-center">
            <FileInput className="h-12 w-12 text-muted-foreground/50" />
            <div>
              <p className="text-lg font-medium">还没有导入记录</p>
              <p className="text-sm text-muted-foreground">
                粘贴飞书文档链接开始导入题目
              </p>
            </div>
            <Button onClick={() => setImportOpen(true)}>
              <Link className="mr-1 h-4 w-4" />
              导入文档
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
