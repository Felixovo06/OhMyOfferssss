"use client"

import { useParams, useRouter } from "next/navigation"
import { useResume } from "@/lib/query/resumes"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import {
  Loader2,
  ArrowLeft,
  FileText,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Briefcase,
  GraduationCap,
  Code,
  Lightbulb,
  User,
  Mail,
  Phone,
  Scan,
} from "lucide-react"

export default function ResumeDetailPage() {
  const params = useParams()
  const router = useRouter()
  const resumeId = params.id as string

  const { data: resume, isLoading } = useResume(resumeId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!resume) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/50" />
        <p className="text-lg font-medium">简历不存在</p>
        <Button variant="outline" onClick={() => router.push("/resumes")}>
          返回简历列表
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <Button variant="ghost" size="sm" onClick={() => router.push("/resumes")}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        返回简历列表
      </Button>

      {/* Resume Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <FileText className="mt-1 h-6 w-6 text-muted-foreground" />
          <div>
            <h1 className="text-xl font-semibold tracking-tight">{resume.filename}</h1>
            <p className="text-xs text-muted-foreground">
              {new Date(resume.created_at).toLocaleString("zh-CN")}
            </p>
          </div>
        </div>
        {resume.status === "completed" && resume.summary && (
          <Button onClick={() => router.push(`/interviews/new?resume_id=${resume.id}`)}>
            <Sparkles className="mr-1 h-4 w-4" />
            基于此简历面试
          </Button>
        )}
      </div>

      {/* Scanning notice */}
      {resume.is_scanned && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/30 dark:bg-amber-950/20">
          <Scan className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
          <div>
            <p className="text-sm font-medium text-amber-700 dark:text-amber-400">扫描件识别</p>
            <p className="text-xs text-amber-600 dark:text-amber-500">
              这份简历可能是扫描件或图片型 PDF，AI 提取的信息可能存在误差，建议核对关键内容
            </p>
          </div>
        </div>
      )}

      {/* Status: parsing */}
      {resume.status === "parsing" && (
        <div className="flex flex-col items-center gap-4 py-12 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <div>
            <p className="text-sm font-medium">正在解析简历...</p>
            <p className="text-xs text-muted-foreground">AI 正在提取技能、经历和项目信息</p>
          </div>
        </div>
      )}

      {/* Status: failed */}
      {resume.status === "failed" && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div>
              <p className="text-sm font-medium">解析失败</p>
              <p className="text-xs text-muted-foreground">
                {resume.error_message || "无法解析该简历，请确认文件是否为有效 PDF"}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      {resume.status === "completed" && resume.summary && (
        <>
          {/* Basic Info */}
          <Card>
            <CardContent className="p-5">
              <div className="flex flex-wrap gap-6">
                <div className="flex items-center gap-2 text-sm">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span>{resume.summary.name}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{resume.summary.email}</span>
                </div>
                {resume.summary.phone && (
                  <div className="flex items-center gap-2 text-sm">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{resume.summary.phone}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Skills */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-medium">
              <Code className="h-4 w-4 text-primary" />
              技能
            </h2>
            <div className="flex flex-wrap gap-2">
              {resume.summary.skills.map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
          </section>

          <Separator />

          {/* Experience */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-medium">
              <Briefcase className="h-4 w-4 text-primary" />
              工作经历
            </h2>
            <div className="space-y-4">
              {resume.summary.experience.map((exp, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium">{exp.title}</p>
                        <p className="text-xs text-muted-foreground">{exp.company}</p>
                      </div>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {exp.start_date} — {exp.end_date || "至今"}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                      {exp.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator />

          {/* Education */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-medium">
              <GraduationCap className="h-4 w-4 text-primary" />
              教育背景
            </h2>
            {resume.summary.education.map((edu, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium">{edu.school}</p>
                      <p className="text-xs text-muted-foreground">{edu.degree} · {edu.major}</p>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {edu.start_date} — {edu.end_date || "至今"}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </section>

          <Separator />

          {/* Projects */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-medium">
              <Code className="h-4 w-4 text-primary" />
              项目经历
            </h2>
            <div className="space-y-4">
              {resume.summary.projects.map((proj, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <p className="text-sm font-medium">{proj.name}</p>
                    <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                      {proj.description}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {proj.technologies.map((t) => (
                        <Badge key={t} variant="outline" className="text-[10px]">
                          {t}
                        </Badge>
                      ))}
                    </div>
                    {proj.highlights.length > 0 && (
                      <ul className="mt-2 space-y-0.5">
                        {proj.highlights.map((h, j) => (
                          <li key={j} className="text-xs text-muted-foreground">
                            • {h}
                          </li>
                        ))}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator />

          {/* Follow-up Directions */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-medium">
              <Lightbulb className="h-4 w-4 text-primary" />
              可追问方向
            </h2>
            <div className="space-y-2">
              {resume.summary.follow_up_directions.map((dir, i) => (
                <div key={i} className="flex items-start gap-3 rounded-lg border p-3">
                  <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                  <p className="text-sm text-muted-foreground">{dir}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Bottom Action */}
          <div className="pt-2">
            <Button
              className="w-full"
              size="lg"
              onClick={() => router.push(`/interviews/new?resume_id=${resume.id}`)}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              基于此简历开始面试
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
