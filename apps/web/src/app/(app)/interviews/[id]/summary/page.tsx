"use client"

import { useParams, useRouter } from "next/navigation"
import { useSummary } from "@/lib/query/interviews"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import {
  Loader2,
  Trophy,
  ArrowLeft,
  Home,
  TrendingUp,
  Lightbulb,
  CheckCircle,
  XCircle,
  Target,
  BookOpen,
  UserCheck,
  Star,
  AlertTriangle,
} from "lucide-react"
import { cn } from "@/lib/utils"

function ScoreBadge({ score, size = "md" }: { score: number; size?: "sm" | "md" | "lg" }) {
  const sizeClasses = { sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-14 w-14 text-xl" }
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full font-bold",
        sizeClasses[size],
        score >= 8 ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
        score >= 6 ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
        "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
      )}
    >
      {score}
    </div>
  )
}

export default function SummaryPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const { data: summary, isLoading } = useSummary(sessionId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <Trophy className="h-12 w-12 text-muted-foreground/50" />
        <p className="text-lg font-medium">总结不存在</p>
        <Button variant="outline" onClick={() => router.push("/interviews")}>
          返回面试
        </Button>
      </div>
    )
  }

  const answered = summary.questions.filter((q) => q.status === "answered")
  const avgScore = answered.length > 0
    ? Math.round(answered.reduce((s, q) => s + (q.score || 0), 0) / answered.length * 10) / 10
    : 0

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-xl border bg-gradient-to-b from-background to-muted/20 p-8 text-center">
        <div className="relative">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/30">
            <Trophy className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight">面试完成</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            已完成 {answered.length}/{summary.session.total_questions} 题
          </p>
        </div>
      </div>

      {/* Score Overview */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex flex-col items-center gap-2 p-5">
            <ScoreBadge score={Math.round(summary.overall_score)} size="lg" />
            <p className="text-xs text-muted-foreground">综合评分</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center gap-2 p-5">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted text-xl font-bold text-foreground">
              {avgScore}
            </div>
            <p className="text-xs text-muted-foreground">平均分</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center gap-2 p-5">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted text-xl font-bold text-foreground">
              {answered.filter((q) => (q.score || 0) >= 6).length}
              <span className="text-sm text-muted-foreground">/{answered.length}</span>
            </div>
            <p className="text-xs text-muted-foreground">达标题数</p>
          </CardContent>
        </Card>
      </div>

      {/* Project Performance */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-sm font-medium">
          <UserCheck className="h-4 w-4 text-primary" />
          项目表现
        </h2>
        <Card className="border-l-4 border-l-primary/40">
          <CardContent className="p-5">
            {summary.project_performance && summary.project_performance.length > 0 ? (
              <div className="space-y-4">
                {summary.project_performance.map((p, i) => (
                  <div key={i} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">{p.project_name}</p>
                      <ScoreBadge score={p.score} size="sm" />
                    </div>
                    <p className="text-xs text-muted-foreground">{p.comment}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">暂无项目表现数据</p>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Knowledge Performance */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-sm font-medium">
          <BookOpen className="h-4 w-4 text-primary" />
          知识点掌握
        </h2>
        {summary.knowledge_performance && summary.knowledge_performance.length > 0 ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {summary.knowledge_performance.map((k, i) => (
              <Card key={i}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{k.tag}</p>
                    <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${k.mastery * 100}%`,
                          background: k.mastery >= 0.7
                            ? "oklch(0.527 0.154 150.069)"
                            : k.mastery >= 0.4
                            ? "oklch(0.681 0.162 75.834)"
                            : "oklch(0.577 0.245 27.325)",
                        }}
                      />
                    </div>
                  </div>
                  <span className="ml-3 text-sm font-medium text-muted-foreground">
                    {Math.round(k.mastery * 100)}%
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                  <Target className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">暂无知识点掌握数据</p>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      <Separator />

      {/* Score Breakdown */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-sm font-medium">
          <Target className="h-4 w-4 text-primary" />
          逐题得分
        </h2>
        <div className="space-y-2">
          {summary.questions.map((q, i) => (
            <Card key={q.id}>
              <CardContent className="flex items-start gap-3 p-4">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm">{q.content}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    {q.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {q.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-[10px]">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {q.related_project && (
                      <span className="text-[10px] text-muted-foreground">
                        关联项目：{q.related_project}
                      </span>
                    )}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  {q.status === "answered" ? (
                    <div className="flex items-center gap-1.5">
                      <ScoreBadge score={q.score || 0} size="sm" />
                      <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm text-muted-foreground">未答</span>
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Strengths & Weaknesses */}
      <section className="grid gap-4 sm:grid-cols-2">
        {/* Strengths */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-green-500" />
              <p className="text-sm font-medium">优势</p>
            </div>
            {summary.strengths && summary.strengths.length > 0 ? (
              <ul className="mt-3 space-y-1.5">
                {summary.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-green-500" />
                    {s}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-xs text-muted-foreground">暂无数据</p>
            )}
          </CardContent>
        </Card>

        {/* Weaknesses */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <p className="text-sm font-medium">短板</p>
            </div>
            {summary.weaknesses && summary.weaknesses.length > 0 ? (
              <ul className="mt-3 space-y-1.5">
                {summary.weaknesses.map((w, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-amber-500" />
                    {w}
                  </li>
                ))}
              </ul>
            ) : summary.weak_tags.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {summary.weak_tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-[10px]">
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-xs text-muted-foreground">暂无数据</p>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Recommendations */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-sm font-medium">
          <Lightbulb className="h-4 w-4 text-primary" />
          提升建议
        </h2>
        <div className="space-y-2">
          {summary.recommendations.length > 0 ? (
            summary.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border p-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-medium text-primary">
                  {i + 1}
                </span>
                <p className="text-sm text-muted-foreground">{rec}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">暂无建议</p>
          )}
        </div>
      </section>

      {/* Review Plan */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-sm font-medium">
          <TrendingUp className="h-4 w-4 text-primary" />
          后续复习建议
        </h2>
        <Card className="border-dashed">
          <CardContent className="p-5">
            {summary.review_plan && summary.review_plan.length > 0 ? (
              <div className="space-y-3">
                {summary.review_plan.map((plan, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium text-muted-foreground">
                      {i + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{plan.topic}</p>
                      <p className="text-xs text-muted-foreground">{plan.suggestion}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">
                  针对薄弱知识点多加练习，建议重新练习得分较低的题目
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <Separator />

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => router.push("/interviews")}
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          返回面试
        </Button>
        <Button
          className="flex-1"
          onClick={() => router.push("/interviews/new")}
        >
          <Home className="mr-1 h-4 w-4" />
          再来一轮
        </Button>
      </div>
    </div>
  )
}
