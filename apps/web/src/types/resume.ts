export interface ResumeExperience {
  company: string
  title: string
  start_date: string
  end_date: string | null
  description: string
}

export interface ResumeEducation {
  school: string
  degree: string
  major: string
  start_date: string
  end_date: string | null
}

export interface ResumeProject {
  name: string
  description: string
  technologies: string[]
  highlights: string[]
}

export interface ResumeSummary {
  name: string
  email: string
  phone?: string
  skills: string[]
  experience: ResumeExperience[]
  education: ResumeEducation[]
  projects: ResumeProject[]
  follow_up_directions: string[]
}

export interface Resume {
  id: string
  filename: string
  status: "uploading" | "parsing" | "completed" | "failed"
  is_scanned?: boolean
  summary?: ResumeSummary
  error_message?: string
  created_at: string
  updated_at: string
}
