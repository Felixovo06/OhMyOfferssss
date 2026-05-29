import { api } from "./client"
import { mockResumeApi } from "./mock-data"
import type { Resume } from "@/types/resume"

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"

export function getResumes() {
  if (USE_MOCK) return mockResumeApi.getResumes()
  return api.get<Resume[]>("/api/v1/resumes")
}

export function getResume(id: string) {
  if (USE_MOCK) return mockResumeApi.getResume(id)
  return api.get<Resume>(`/api/v1/resumes/${id}`)
}

export function uploadResume(file: File) {
  if (USE_MOCK) return mockResumeApi.uploadResume(file)
  const form = new FormData()
  form.append("file", file)
  return api.post<Resume>("/api/v1/resumes", form)
}

export function deleteResume(id: string) {
  if (USE_MOCK) return mockResumeApi.deleteResume(id)
  return api.delete<{ deleted: boolean }>(`/api/v1/resumes/${id}`)
}
