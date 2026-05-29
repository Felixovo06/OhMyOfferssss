export interface ApiResponse<T = unknown> {
  success: true
  data: T
  request_id: string
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
  request_id: string
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
