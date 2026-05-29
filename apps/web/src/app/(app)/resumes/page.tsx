"use client"

import { useRouter } from "next/navigation"
import { useResumes } from "@/lib/query/resumes"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { FileText, Upload, Loader2, CheckCircle, AlertCircle, Clock, ArrowRight } from "lucide-react"

const statusConfig: Record<string, { label: string; icon: typeof Clock; color: string }> = {
  uploading: { label: "上传中", icon: Clock, color: "text-muted-foreground" },
  parsing: { label: "解析中", icon: Loader2, color: "text-blue-500" },
  completed: { label: "解析完成", icon: CheckCircle, color: "text-green-500" },
  failed: { label: "解析失败", icon: AlertCircle, color: "text-red-500" },
}

export default function ResumesPage() {
  const router = useRouter()
  const { data: resumes, isLoading, error, refetch } = useResumes()

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">简历</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            上传简历后，AI 将解析并基于简历内容进行客制化面试
          </p>
        </div>
        <Button onClick={() => router.push("/resumes/new")}>
          <Upload className="mr-1 h-4 w-4" />
          上传简历
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
              <Skeleton className="h-5 w-5 shrink-0" />
              <div className="min-w-0 flex-1 space-y-1.5">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <AlertCircle className="h-12 w-12 text-red-500/50" />
          <div>
            <p className="text-lg font-medium">加载失败</p>
            <p className="text-sm text-muted-foreground">{error.message || "请稍后重试"}</p>
          </div>
          <Button variant="outline" onClick={() => refetch()}>重试</Button>
        </div>
      ) : resumes && resumes.length > 0 ? (
        <div className="space-y-2">
          {resumes.map((resume) => {
            const config = statusConfig[resume.status] || statusConfig.uploading
            const Icon = config.icon
            return (
              <div
                key={resume.id}
                onClick={() => router.push(`/resumes/${resume.id}`)}
                className="flex cursor-pointer items-center gap-4 rounded-lg border p-4 transition-all hover:bg-accent/50 hover:border-primary/20 active:scale-[0.99]"
              >
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{resume.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(resume.created_at).toLocaleString("zh-CN")}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={resume.status === "completed" ? "text-green-600" : resume.status === "failed" ? "text-red-600" : ""}
                >
                  <Icon className={`mr-1 h-3 w-3 ${resume.status === "parsing" ? "animate-spin" : ""}`} />
                  {config.label}
                </Badge>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </div>
            )
          })}
        </div>
      ) : (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <FileText className="h-12 w-12 text-muted-foreground/50" />
            <div>
              <p className="text-lg font-medium">还没有上传简历</p>
              <p className="text-sm text-muted-foreground">
                上传 PDF 简历后，AI 将解析你的技能和经历，生成个性化面试
              </p>
            </div>
            <Button onClick={() => router.push("/resumes/new")}>
              <Upload className="mr-1 h-4 w-4" />
              上传简历
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
