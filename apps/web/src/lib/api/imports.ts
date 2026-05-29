import { api } from "./client"
import { mockImportApi } from "./mock-data"
import type { ImportBatch, ImportRequest, ImportItem } from "@/types/import"

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true"

export function getImportBatches() {
  if (USE_MOCK) return mockImportApi.getBatches()
  return api.get<ImportBatch[]>("/api/v1/imports")
}

export function getImportDetail(id: string) {
  if (USE_MOCK) return mockImportApi.getBatch(id)
  return api.get<{ batch: ImportBatch; items: ImportItem[] }>(`/api/v1/imports/${id}`)
}

export function createImport(data: ImportRequest) {
  if (USE_MOCK) return mockImportApi.createImport(data)
  return api.post<ImportBatch>("/api/v1/imports", data)
}

export function confirmImportItem(itemId: string) {
  if (USE_MOCK) return mockImportApi.confirmItem(itemId)
  return api.post<void>(`/api/v1/imports/items/${itemId}/confirm`)
}

export function rejectImportItem(itemId: string) {
  if (USE_MOCK) return mockImportApi.rejectItem(itemId)
  return api.post<void>(`/api/v1/imports/items/${itemId}/reject`)
}

export function rejectAllImportItems(batchId: string) {
  if (USE_MOCK) return mockImportApi.rejectAll(batchId)
  return api.post<{ rejected_count: number }>(`/api/v1/imports/${batchId}/reject`)
}

export function confirmAllImportItems(batchId: string) {
  if (USE_MOCK) return mockImportApi.confirmAll(batchId)
  return api.post<void>(`/api/v1/imports/${batchId}/confirm`)
}
