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
} from "lucide-react"

const difficultyLabels: Record<number, string> = {
  1: "简单",
  2: "较易",
  3: "中等",
  4: "较难",
  5: "困难",
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

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      {/* Header */}
      <div className="text-center">
        <Trophy className="mx-auto h-12 w-12 text-yellow-500" />
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">面试总结</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          已完成 {answered.length}/{summary.session.total_questions} 题
        </p>
      </div>

      <Separator />

      {/* Overall Score */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-8">
            <div className="text-center">
              <div className={`text-4xl font-bold ${
                summary.overall_score >= 8 ? "text-green-500" :
                summary.overall_score >= 6 ? "text-yellow-500" : "text-red-500"
              }`}>
                {summary.overall_score}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">综合评分</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-muted-foreground">
                {answered.filter((q) => (q.score || 0) >= 6).length}/{answered.length}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">达标题数</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-muted-foreground">
                {summary.session.total_questions}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">总题数</p>
            </div>
          </div>
        </CardContent>
      </Card>

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
                  {q.tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {q.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-[10px]">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="shrink-0 text-right">
                  {q.status === "answered" ? (
                    <div className="flex items-center gap-1.5">
                      <span className={`text-lg font-bold ${
                        (q.score || 0) >= 8 ? "text-green-500" :
                        (q.score || 0) >= 6 ? "text-yellow-500" : "text-red-500"
                      }`}>
                        {q.score}
                      </span>
                      <CheckCircle className="h-4 w-4 text-green-500" />
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

      {/* Weak Tags */}
      {summary.weak_tags.length > 0 && (
        <section className="space-y-3">
          <h2 className="flex items-center gap-2 text-sm font-medium">
            <TrendingUp className="h-4 w-4 text-amber-500" />
            薄弱环节
          </h2>
          <div className="flex flex-wrap gap-2">
            {summary.weak_tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        </section>
      )}

      {/* Recommendations */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-sm font-medium">
          <Lightbulb className="h-4 w-4 text-primary" />
          提升建议
        </h2>
        <div className="space-y-2">
          {summary.recommendations.map((rec, i) => (
            <div key={i} className="flex items-start gap-3 rounded-lg border p-3">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-medium text-primary">
                {i + 1}
              </span>
              <p className="text-sm text-muted-foreground">{rec}</p>
            </div>
          ))}
        </div>
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
