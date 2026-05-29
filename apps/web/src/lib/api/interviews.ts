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
  return api.get<{ session: InterviewSession; questions: InterviewQuestion[] }>(
    `/api/v1/interviews/${id}`,
  )
}

export function startSession(id: string) {
  if (USE_MOCK) return mockInterviewApi.startSession(id)
  return api.post<InterviewSession>(`/api/v1/interviews/${id}/start`)
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

export function nextQuestion(sessionId: string) {
  if (USE_MOCK) return mockInterviewApi.nextQuestion(sessionId)
  return api.post<InterviewSession>(`/api/v1/interviews/${sessionId}/next`)
}

export function getSummary(id: string) {
  if (USE_MOCK) return mockInterviewApi.getSummary(id)
  return api.get<InterviewSummary>(`/api/v1/interviews/${id}/summary`)
}
