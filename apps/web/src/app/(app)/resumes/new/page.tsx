"use client"

import { useRouter } from "next/navigation"
import { useRef, useState } from "react"
import { useUploadResume } from "@/lib/query/resumes"
import { Button } from "@/components/ui/button"
import { Upload, FileText, Loader2, ArrowLeft } from "lucide-react"
import { toast } from "sonner"

export default function UploadResumePage() {
  const router = useRouter()
  const uploadResume = useUploadResume()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  function handleFile(file: File | undefined) {
    if (!file) return
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      toast.error("请上传 PDF 格式的简历文件")
      return
    }
    uploadResume.mutate(file, {
      onSuccess: (resume) => {
        toast.success("简历上传成功，正在解析...")
        router.push(`/resumes/${resume.id}`)
      },
    })
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="mx-auto max-w-xl space-y-8 p-6">
      <Button variant="ghost" size="sm" onClick={() => router.push("/resumes")}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        返回简历列表
      </Button>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">上传简历</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          支持 PDF 格式，AI 将自动解析并提取技能、经历和项目信息
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-4 rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-muted-foreground/50"
        } ${uploadResume.isPending ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />

        {uploadResume.isPending ? (
          <>
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <div>
              <p className="text-sm font-medium">正在上传...</p>
              <p className="text-xs text-muted-foreground">请稍候，文件上传中</p>
            </div>
          </>
        ) : (
          <>
            <Upload className="h-10 w-10 text-muted-foreground/50" />
            <div>
              <p className="text-sm font-medium">
                拖拽 PDF 到此处，或<span className="text-primary">点击选择文件</span>
              </p>
              <p className="mt-1 text-xs text-muted-foreground">仅支持 PDF 格式</p>
            </div>
          </>
        )}
      </div>

      {/* Tips */}
      <div className="space-y-2 rounded-lg border p-4">
        <p className="text-xs font-medium text-muted-foreground">上传说明</p>
        <ul className="space-y-1 text-xs text-muted-foreground">
          <li>• 支持标准文本型 PDF 简历</li>
          <li>• 扫描件或图片型 PDF 也能处理，但准确率可能降低</li>
          <li>• AI 将提取姓名、技能、工作经历、教育背景和项目信息</li>
          <li>• 解析完成后可基于简历内容进行个性化面试</li>
        </ul>
      </div>
    </div>
  )
}
