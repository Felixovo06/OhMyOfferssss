export interface QuestionBank {
  id: string
  name: string
  description?: string
  owner_id: string
  group_id?: string
  question_count: number
  tags: string[]
  created_at: string
  updated_at: string
}

export interface CreateBankRequest {
  name: string
  description?: string
  group_id?: string
}

export interface Question {
  id: string
  bank_id: string
  content: string
  answer?: string
  tags: string[]
  difficulty?: number | null
  status: "active" | "disabled"
  source?: string
  created_at: string
  updated_at: string
}

export interface CreateQuestionRequest {
  content: string
  answer?: string
  tags?: string[]
  difficulty?: number
}

export interface UpdateQuestionRequest {
  content?: string
  answer?: string
  tags?: string[]
  difficulty?: number
  status?: "active" | "disabled"
}

export interface QuestionFilters {
  keyword?: string
  difficulty?: number
  tags?: string[]
  status?: "active" | "disabled"
}
