import { api } from "./client"
import { mockInterviewApi } from "./mock-data"
import type { InterviewConfig, InterviewQuestion, InterviewSession, InterviewSummary } from "@/types/interview"

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"

export function createSession(config: InterviewConfig) {
  if (USE_MOCK) return mockInterviewApi.createSession(config)
  return api.post<InterviewSession>("/api/v1/interviews", config)
}

export function getSession(id: string) {
  if (USE_MOCK) return mockInterviewApi.getSession(id)
  return api.get<BackendInterviewSession>(`/api/v1/interviews/${id}`).then(normalizeSession)
}

export function startSession(id: string) {
  if (USE_MOCK) return mockInterviewApi.startSession(id)
  return api
    .post<BackendInterviewSession>(`/api/v1/interviews/${id}/start`)
    .then((session) => normalizeSession(session).session)
}

export function submitAnswer(
  sessionId: string,
  questionId: string,
  answer: string,
  difficulty?: number | null,
) {
  if (USE_MOCK) return mockInterviewApi.submitAnswer(sessionId, questionId, answer)
  return api.post<InterviewQuestion>(
    `/api/v1/interviews/items/${questionId}/answer`,
    { answer, difficulty },
  )
}

export function updateQuestionDifficulty(questionId: string, difficulty?: number | null) {
  return api.patch<InterviewQuestion>(
    `/api/v1/interviews/items/${questionId}/difficulty`,
    { difficulty },
  )
}

export function nextQuestion(sessionId: string, options?: { prefetch?: boolean }) {
  if (USE_MOCK) return mockInterviewApi.nextQuestion(sessionId)
  const qs = options?.prefetch ? "?prefetch=true" : ""
  return api
    .post<BackendInterviewSession>(`/api/v1/interviews/${sessionId}/next${qs}`)
    .then((session) => normalizeSession(session).session)
}

export function getSummary(id: string) {
  if (USE_MOCK) return mockInterviewApi.getSummary(id)
  return api.get<InterviewSummary>(`/api/v1/interviews/${id}/summary`)
}

interface BackendInterviewSession {
  id: string
  mode?: "normal" | "custom"
  target?: string | null
  resume_id?: string | null
  config?: Partial<InterviewConfig>
  flow_mode?: "project" | "knowledge"
  status: "ready" | "in_progress" | "completed"
  created_at: string
  updated_at: string
  items?: BackendInterviewItem[]
}

interface BackendInterviewItem {
  id: string
  session_id: string
  position: number
  selection_reason?: string
  status: "pending" | "answered" | "skipped"
  answer?: string | null
  feedback?: InterviewQuestion["feedback"]
  question: {
    id: string
    content: string
    tags: string[]
    difficulty?: number | null
  }
  stage?: string
  related_project?: string | null
  related_skills?: string[]
  intention?: string
}

function normalizeSession(raw: BackendInterviewSession): {
  session: InterviewSession
  questions: InterviewQuestion[]
} {
  const questions = (raw.items ?? []).map((item, index) => ({
    id: item.id,
    session_id: item.session_id,
    question_id: item.id,
    index,
    content: item.question.content,
    tags: item.question.tags,
    difficulty: item.question.difficulty,
    ai_reason: item.selection_reason,
    status: item.status,
    answer: item.answer ?? undefined,
    feedback: item.feedback,
    related_project: item.related_project ?? undefined,
    related_skills: item.related_skills ?? [],
    intention: item.intention,
    stage: item.stage,
  }))
  const firstPendingIndex = questions.findIndex((question) => question.status !== "answered")
  const currentIndex = raw.status === "completed"
    ? questions.length
    : firstPendingIndex >= 0
      ? firstPendingIndex
      : Math.max(0, questions.length - 1)
  const targetCount = raw.config?.question_count ?? questions.length
  return {
    session: {
      id: raw.id,
      bank_ids: raw.config?.bank_ids ?? [],
      tags: raw.config?.tags ?? [],
      difficulty: raw.config?.difficulty,
      question_count: targetCount,
      goal: raw.target ?? raw.config?.goal,
      mode: raw.mode,
      resume_id: raw.resume_id ?? undefined,
      flow_mode: raw.flow_mode,
      status: raw.status === "ready" ? "pending" : raw.status,
      current_index: currentIndex,
      total_questions: targetCount,
      created_at: raw.created_at,
      updated_at: raw.updated_at,
    },
    questions,
  }
}
