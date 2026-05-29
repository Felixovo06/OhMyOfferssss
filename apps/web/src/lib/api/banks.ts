import { api } from "./client"
import { mockBankApi } from "./mock-data"
import type {
  QuestionBank,
  CreateBankRequest,
  Question,
  CreateQuestionRequest,
  UpdateQuestionRequest,
} from "@/types/bank"

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"

export function getBanks() {
  if (USE_MOCK) return mockBankApi.getBanks()
  return api.get<QuestionBank[]>("/api/v1/banks")
}

export function getBank(id: string) {
  if (USE_MOCK) return mockBankApi.getBank(id)
  return api.get<QuestionBank>(`/api/v1/banks/${id}`)
}

export function createBank(data: CreateBankRequest) {
  if (USE_MOCK) return mockBankApi.createBank(data)
  return api.post<QuestionBank>("/api/v1/banks", data)
}

export function updateBank(id: string, data: Partial<CreateBankRequest>) {
  if (USE_MOCK) return mockBankApi.updateBank(id, data)
  return api.patch<QuestionBank>(`/api/v1/banks/${id}`, data)
}

export function deleteBank(id: string) {
  if (USE_MOCK) return mockBankApi.deleteBank(id)
  return api.delete<void>(`/api/v1/banks/${id}`)
}

export function getQuestions(
  bankId: string,
  filters?: { keyword?: string; difficulty?: number; tags?: string[]; status?: string },
) {
  if (USE_MOCK) return mockBankApi.getQuestions(bankId, filters)
  const params = new URLSearchParams()
  if (filters?.keyword) params.set("keyword", filters.keyword)
  if (filters?.difficulty) params.set("difficulty", String(filters.difficulty))
  if (filters?.status) params.set("status", filters.status)
  const qs = params.toString()
  return api.get<Question[]>(`/api/v1/banks/${bankId}/questions${qs ? `?${qs}` : ""}`)
}

export function createQuestion(bankId: string, data: CreateQuestionRequest) {
  if (USE_MOCK) return mockBankApi.createQuestion(bankId, data)
  return api.post<Question>(`/api/v1/banks/${bankId}/questions`, data)
}

export function updateQuestion(id: string, data: UpdateQuestionRequest) {
  if (USE_MOCK) return mockBankApi.updateQuestion(id, data)
  return api.patch<Question>(`/api/v1/questions/${id}`, data)
}

export function deleteQuestion(id: string) {
  if (USE_MOCK) return mockBankApi.deleteQuestion(id)
  return api.delete<void>(`/api/v1/questions/${id}`)
}
