export interface InterviewConfig {
  bank_ids: string[]
  tags?: string[]
  difficulty?: number
  question_count: number
  duration_minutes?: number
  goal?: string
  mode?: "normal" | "custom"
  resume_id?: string
  flow_mode?: "project" | "knowledge"
}

export interface InterviewSession {
  id: string
  bank_ids: string[]
  tags: string[]
  difficulty?: number
  question_count: number
  duration_minutes?: number
  goal?: string
  mode?: "normal" | "custom"
  resume_id?: string
  flow_mode?: "project" | "knowledge"
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
  difficulty?: number | null
  ai_reason?: string
  status: "pending" | "answered" | "skipped"
  score?: number
  answer?: string
  feedback?: QuestionFeedback
  related_project?: string
  related_skills?: string[]
  intention?: string
  stage?: string
}

export interface QuestionFeedback {
  score: number
  missing_points: string[]
  reference_answer: string
  follow_up?: string
  comment?: string
  next_action?: string
  next_stage?: string | null
  decision_reason?: string | null
}

export interface ProjectPerformance {
  project_name: string
  score: number
  comment: string
}

export interface KnowledgePerformance {
  tag: string
  mastery: number
}

export interface ReviewPlan {
  topic: string
  suggestion: string
}

export interface InterviewSummary {
  session: InterviewSession
  questions: InterviewQuestion[]
  overall_score: number
  weak_tags: string[]
  recommendations: string[]
  project_performance?: ProjectPerformance[]
  knowledge_performance?: KnowledgePerformance[]
  strengths?: string[]
  weaknesses?: string[]
  review_plan?: ReviewPlan[]
}
