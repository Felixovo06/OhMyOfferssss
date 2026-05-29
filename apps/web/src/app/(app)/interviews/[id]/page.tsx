"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useRef, useState } from "react"
import {
  useSession,
  useStartSession,
  useSubmitAnswer,
  useUpdateQuestionDifficulty,
  useNextQuestion,
  usePrefetchNextQuestion,
} from "@/lib/query/interviews"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Loader2,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  MessageSquare,
  Trophy,
  Lightbulb,
  Eye,
  Keyboard,
  Mic,
  Square,
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

const difficultyOptions = [
  { value: 20, label: "简单" },
  { value: 40, label: "较易" },
  { value: 60, label: "中等" },
  { value: 80, label: "较难" },
  { value: 95, label: "困难" },
]

function difficultyLabel(score?: number | null) {
  if (score == null) return "未设置"
  if (score <= 5) return difficultyLabels[score] ?? "未设置"
  if (score <= 30) return "简单"
  if (score <= 50) return "较易"
  if (score <= 70) return "中等"
  if (score <= 85) return "较难"
  return "困难"
}

function difficultyColor(score?: number | null) {
  if (score == null) return "bg-muted text-muted-foreground"
  const bucket = score <= 5 ? score : score <= 30 ? 1 : score <= 50 ? 2 : score <= 70 ? 3 : score <= 85 ? 4 : 5
  return difficultyColors[bucket]
}

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const { data, isLoading, error } = useSession(sessionId)
  const startSession = useStartSession()
  const submitAnswer = useSubmitAnswer()
  const updateDifficulty = useUpdateQuestionDifficulty()
  const nextQuestion = useNextQuestion()
  const prefetchNextQuestion = usePrefetchNextQuestion()

  const [answer, setAnswer] = useState("")
  const [difficulty, setDifficulty] = useState<string>("unchanged")
  const [showFeedback, setShowFeedback] = useState(false)
  const [answerMode, setAnswerMode] = useState<"read" | "type" | "voice">("read")
  const [isRecognizing, setIsRecognizing] = useState(false)
  const recognitionRef = useRef<{
    start: () => void
    stop: () => void
    continuous: boolean
    interimResults: boolean
    lang: string
    onresult: ((event: { results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }> }) => void) | null
    onend: (() => void) | null
    onerror: (() => void) | null
  } | null>(null)
  const autoStartRef = useRef(false)

  useEffect(() => {
    if (!data || data.session.status !== "pending" || autoStartRef.current) return
    autoStartRef.current = true
    startSession.mutate(sessionId)
  }, [data, sessionId, startSession])

  useEffect(() => {
    if (!data || data.session.status !== "in_progress") return
    const pendingCount = data.questions.filter((question) => question.status === "pending").length
    const canPrefetch = data.questions.length < data.session.total_questions
    if (pendingCount === 1 && canPrefetch && !prefetchNextQuestion.isPending) {
      prefetchNextQuestion.mutate(sessionId)
    }
  }, [data, prefetchNextQuestion, sessionId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <AlertCircle className="h-12 w-12 text-red-500/50" />
        <p className="text-lg font-medium">加载失败</p>
        <p className="text-sm text-muted-foreground">{error.message || "请稍后重试"}</p>
        <Button variant="outline" onClick={() => router.push("/interviews")}>返回面试</Button>
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

  // --- Preparing first question ---
  if (session.status === "pending") {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 p-6 py-24 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight">正在准备第一题</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            面试开始后只加载当前题，后续会根据上一题表现继续追问。
          </p>
        </div>
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
  const latestAnswered = [...questions].reverse().find((question) => question.feedback)

  function handleProceed() {
    const finalAnswer =
      answerMode === "read"
        ? "看题模式：用户选择只看题，未提交口述或文字回答。"
        : answer.trim()
    if (!finalAnswer.trim()) {
      toast.error("请输入你的回答")
      return
    }
    setShowFeedback(false)
    const difficultyValue = difficulty === "unchanged" ? undefined : parseDifficulty(difficulty)
    submitAnswer.mutate(
      { sessionId, questionId: currentQuestion.id, answer: finalAnswer, difficulty: difficultyValue },
      {
        onSuccess: () => {
          setAnswer("")
          setDifficulty("unchanged")
          nextQuestion.mutate(sessionId)
        },
      },
    )
  }

  function handleSaveDifficulty() {
    const difficultyValue = parseDifficulty(difficultySelectValue)
    updateDifficulty.mutate(
      { sessionId, questionId: currentQuestion.id, difficulty: difficultyValue },
      {
        onSuccess: () => {
          setDifficulty("unchanged")
          toast.success("难度已保存")
        },
      },
    )
  }

  function handleNext() {
    setAnswer("")
    setDifficulty("unchanged")
    setShowFeedback(false)
    nextQuestion.mutate(sessionId)
  }

  function toggleSpeechRecognition() {
    const SpeechRecognition =
      (window as typeof window & {
        SpeechRecognition?: new () => NonNullable<typeof recognitionRef.current>
        webkitSpeechRecognition?: new () => NonNullable<typeof recognitionRef.current>
      }).SpeechRecognition ??
      (window as typeof window & {
        webkitSpeechRecognition?: new () => NonNullable<typeof recognitionRef.current>
      }).webkitSpeechRecognition
    if (!SpeechRecognition) {
      toast.error("当前浏览器不支持语音转文字")
      return
    }
    if (isRecognizing) {
      recognitionRef.current?.stop()
      setIsRecognizing(false)
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = "zh-CN"
    recognition.continuous = true
    recognition.interimResults = true
    recognition.onresult = (event) => {
      let transcript = ""
      for (let index = 0; index < event.results.length; index += 1) {
        transcript += event.results[index][0].transcript
      }
      setAnswer(transcript)
    }
    recognition.onend = () => setIsRecognizing(false)
    recognition.onerror = () => setIsRecognizing(false)
    recognitionRef.current = recognition
    setAnswerMode("voice")
    setIsRecognizing(true)
    recognition.start()
  }

  function parseDifficulty(value: string) {
    return value === "unset" ? null : Number(value)
  }

  const difficultySelectValue =
    difficulty === "unchanged"
      ? currentQuestion.difficulty == null
        ? "unset"
        : String(currentQuestion.difficulty)
      : difficulty

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Stage context */}
      {currentQuestion.stage && (
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            {currentQuestion.stage}
          </Badge>
          {currentQuestion.related_project && (
            <span className="text-xs text-muted-foreground">
              关联项目：{currentQuestion.related_project}
            </span>
          )}
          {currentQuestion.intention && (
            <span className="text-xs text-muted-foreground">
              考察意图：{currentQuestion.intention}
            </span>
          )}
        </div>
      )}

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
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{
                width: `${((session.current_index + (showFeedback ? 1 : 0)) / session.total_questions) * 100}%`,
                background: "linear-gradient(90deg, hsl(var(--primary)), hsl(var(--primary) / 0.7))",
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
                <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${difficultyColor(currentQuestion.difficulty)}`}>
                  {difficultyLabel(currentQuestion.difficulty)}
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
          {latestAnswered?.feedback && latestAnswered.id !== currentQuestion.id && (
            <div className="rounded-lg border bg-muted/30 p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-medium text-muted-foreground">上一题快速评判</p>
                <Badge variant="secondary" className="text-[10px]">
                  {latestAnswered.feedback.score} 分
                </Badge>
              </div>
              <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                {latestAnswered.feedback.comment || latestAnswered.feedback.decision_reason || "已完成快速评判"}
              </p>
            </div>
          )}
          <div className="grid grid-cols-3 gap-2">
            <Button
              type="button"
              variant={answerMode === "read" ? "default" : "outline"}
              onClick={() => setAnswerMode("read")}
            >
              <Eye className="mr-1 h-4 w-4" />
              只看题
            </Button>
            <Button
              type="button"
              variant={answerMode === "type" ? "default" : "outline"}
              onClick={() => setAnswerMode("type")}
            >
              <Keyboard className="mr-1 h-4 w-4" />
              打字
            </Button>
            <Button
              type="button"
              variant={answerMode === "voice" ? "default" : "outline"}
              onClick={() => {
                setAnswerMode("voice")
                toggleSpeechRecognition()
              }}
            >
              {isRecognizing ? <Square className="mr-1 h-4 w-4" /> : <Mic className="mr-1 h-4 w-4" />}
              语音
            </Button>
          </div>
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="text-sm font-medium">题目难度</label>
              <Select
                value={difficultySelectValue}
                onValueChange={(value) => setDifficulty(value ?? "unset")}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="未设置" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unset">未设置</SelectItem>
                  {difficultyOptions.map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="outline"
              onClick={handleSaveDifficulty}
              disabled={updateDifficulty.isPending}
            >
              {updateDifficulty.isPending ? "保存中..." : "保存难度"}
            </Button>
          </div>
          {answerMode !== "read" && (
            <>
              <label className="text-sm font-medium">
                {answerMode === "voice" ? "语音转文字结果" : "你的回答"}
              </label>
              <Textarea
                placeholder={answerMode === "voice" ? "点击语音按钮后开始说话..." : "在此输入你的回答..."}
                className="min-h-[120px]"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
              />
            </>
          )}
          <Button
            onClick={handleProceed}
            disabled={submitAnswer.isPending || nextQuestion.isPending}
            className="w-full"
          >
            {submitAnswer.isPending || nextQuestion.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                AI 正在快速评判并准备下一题...
              </>
            ) : (
              isLast ? "完成并查看总结" : "下一题"
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
