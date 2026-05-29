export interface ImportBatch {
  id: string
  bank_id?: string
  source_url: string
  status: "pending" | "processing" | "completed" | "failed"
  total_count: number
  confirmed_count: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface ImportItem {
  id: string
  batch_id: string
  question_content: string
  question_answer?: string
  tags: string[]
  difficulty: number
  status: "pending" | "confirmed" | "rejected"
  confidence: number
}

export interface ImportRequest {
  url: string
  bank_id?: string
}
