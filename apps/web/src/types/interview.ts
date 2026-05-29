export interface InterviewConfig {
  bank_ids: string[]
  tags?: string[]
  difficulty?: number
  question_count: number
  goal?: string
}

export interface InterviewSession {
  id: string
  bank_ids: string[]
  tags: string[]
  difficulty?: number
  question_count: number
  goal?: string
  status: "pending" | "in_progress" | "completed"
  current_index: number
  total_questions: number
  created_at: string
  updated_at: string
}

export interface InterviewQuestion {
  id: string
  session_id: string
  question_id: string
  index: number
  content: string
  tags: string[]
  difficulty: number
  ai_reason?: string
  status: "pending" | "answered" | "skipped"
  score?: number
  answer?: string
  feedback?: QuestionFeedback
}

export interface QuestionFeedback {
  score: number
  missing_points: string[]
  reference_answer: string
  follow_up?: string
}

export interface InterviewSummary {
  session: InterviewSession
  questions: InterviewQuestion[]
  overall_score: number
  weak_tags: string[]
  recommendations: string[]
}
