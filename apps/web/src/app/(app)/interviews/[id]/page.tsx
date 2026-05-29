"use client"

import { useParams, useRouter } from "next/navigation"
import { useState } from "react"
import { useSession, useStartSession, useSubmitAnswer, useNextQuestion } from "@/lib/query/interviews"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import {
  Loader2,
  Sparkles,
  CheckCircle,
  ArrowRight,
  BrainCircuit,
  MessageSquare,
  Trophy,
  Lightbulb,
  Target,
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

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const { data, isLoading } = useSession(sessionId)
  const startSession = useStartSession()
  const submitAnswer = useSubmitAnswer()
  const nextQuestion = useNextQuestion()

  const [answer, setAnswer] = useState("")
  const [showFeedback, setShowFeedback] = useState(false)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <MessageSquare className="h-12 w-12 text-muted-foreground/50" />
        <p className="text-lg font-medium">面试不存在</p>
        <Button variant="outline" onClick={() => router.push("/interviews")}>
          返回面试
        </Button>
      </div>
    )
  }

  const { session, questions } = data
  const currentQuestion = questions?.[session.current_index]

  // --- Review State ---
  if (session.status === "pending") {
    return (
      <div className="mx-auto max-w-3xl space-y-6 p-6">
        <div>
          <div className="flex items-center gap-3">
            <BrainCircuit className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-semibold tracking-tight">AI 抽题结果</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            AI 已根据你的配置从题库中选出 {session.total_questions} 道题
          </p>
        </div>

        {session.goal && (
          <Card className="bg-muted/30">
            <CardContent className="flex items-start gap-3 p-4">
              <Target className="mt-0.5 h-4 w-4 text-primary" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">面试目标</p>
                <p className="mt-0.5 text-sm">{session.goal}</p>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-4">
          {questions?.map((q, i) => (
            <Card key={q.id} className="border-l-4" style={{ borderLeftColor: "hsl(var(--primary))" }}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{q.content}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${difficultyColors[q.difficulty]}`}>
                        {difficultyLabels[q.difficulty]}
                      </span>
                      {q.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-[10px]">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    {q.ai_reason && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                          <Lightbulb className="mr-1 inline h-3 w-3" />
                          AI 选本题理由
                        </summary>
                        <p className="mt-1 text-xs text-muted-foreground">{q.ai_reason}</p>
                      </details>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Button
          className="w-full"
          size="lg"
          onClick={() =>
            startSession.mutate(sessionId, {
              onSuccess: () => toast.success("面试开始"),
            })
          }
          disabled={startSession.isPending}
        >
          {startSession.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              准备中...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              开始面试
            </>
          )}
        </Button>
      </div>
    )
  }

  // --- Completed State ---
  if (session.status === "completed" && !currentQuestion) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <Trophy className="h-12 w-12 text-yellow-500" />
          <h1 className="text-2xl font-semibold tracking-tight">面试完成！</h1>
          <p className="text-sm text-muted-foreground">查看总结报告了解你的表现</p>
          <Button onClick={() => router.push(`/interviews/${sessionId}/summary`)}>
            查看总结
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  // --- Answer State ---
  if (!currentQuestion) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const feedback = currentQuestion.feedback
  const isLast = session.current_index >= session.total_questions - 1

  function handleSubmit() {
    if (!answer.trim()) {
      toast.error("请输入你的回答")
      return
    }
    setShowFeedback(false)
    submitAnswer.mutate(
      { sessionId, questionId: currentQuestion.id, answer },
      {
        onSuccess: () => {
          setShowFeedback(true)
        },
      },
    )
  }

  function handleNext() {
    setAnswer("")
    setShowFeedback(false)
    nextQuestion.mutate(sessionId)
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Progress */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              第 {session.current_index + 1} / {session.total_questions} 题
            </span>
            <span className="text-muted-foreground">
              {questions?.filter((q) => q.status === "answered").length || 0} 题已答
            </span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{
                width: `${((session.current_index + (showFeedback ? 1 : 0)) / session.total_questions) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Question */}
      <Card>
        <CardContent className="p-5">
          <div className="flex items-start gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
              {session.current_index + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-base font-medium leading-relaxed">{currentQuestion.content}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${difficultyColors[currentQuestion.difficulty]}`}>
                  {difficultyLabels[currentQuestion.difficulty]}
                </span>
                {currentQuestion.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-[10px]">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Answer Input */}
      {!showFeedback && currentQuestion.status === "pending" && (
        <div className="space-y-3">
          <label className="text-sm font-medium">你的回答</label>
          <Textarea
            placeholder="在此输入你的回答..."
            className="min-h-[120px]"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <Button onClick={handleSubmit} disabled={submitAnswer.isPending} className="w-full">
            {submitAnswer.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                AI 正在评分...
              </>
            ) : (
              "提交回答"
            )}
          </Button>
        </div>
      )}

      {/* Feedback */}
      {showFeedback && feedback && (
        <div className="space-y-4">
          <Separator />
          <div className="flex items-center gap-3">
            <div className={`flex h-12 w-12 items-center justify-center rounded-full text-lg font-bold ${
              feedback.score >= 8 ? "bg-green-100 text-green-700" :
              feedback.score >= 6 ? "bg-yellow-100 text-yellow-700" :
              "bg-red-100 text-red-700"
            }`}>
              {feedback.score}
            </div>
            <div>
              <p className="text-sm font-medium">AI 评分</p>
              <p className="text-xs text-muted-foreground">
                {feedback.score >= 8 ? "掌握良好" : feedback.score >= 6 ? "基本合格" : "需要加强"}
              </p>
            </div>
          </div>

          {feedback.missing_points.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/30 dark:bg-amber-950/20">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-amber-700 dark:text-amber-400">
                <Lightbulb className="h-3.5 w-3.5" />
                可以补充的点
              </p>
              <ul className="space-y-1">
                {feedback.missing_points.map((point, i) => (
                  <li key={i} className="text-xs text-amber-700 dark:text-amber-400">
                    • {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <details className="rounded-lg border p-4">
            <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
              查看参考答案
            </summary>
            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
              {feedback.reference_answer}
            </p>
          </details>

          <Button className="w-full" onClick={handleNext} disabled={nextQuestion.isPending}>
            {nextQuestion.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : isLast ? (
              <Trophy className="mr-2 h-4 w-4" />
            ) : (
              <ArrowRight className="mr-2 h-4 w-4" />
            )}
            {isLast ? "查看总结" : "下一题"}
          </Button>
        </div>
      )}

      {/* Already answered, waiting for next */}
      {currentQuestion.status === "answered" && !showFeedback && (
        <div className="flex flex-col items-center gap-4 py-8 text-center">
          <CheckCircle className="h-8 w-8 text-green-500" />
          <p className="text-sm text-muted-foreground">已回答，继续下一题</p>
          <Button onClick={handleNext} disabled={nextQuestion.isPending}>
            {nextQuestion.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : isLast ? (
              <Trophy className="mr-2 h-4 w-4" />
            ) : (
              <ArrowRight className="mr-2 h-4 w-4" />
            )}
            {isLast ? "查看总结" : "下一题"}
          </Button>
        </div>
      )}
    </div>
  )
}
