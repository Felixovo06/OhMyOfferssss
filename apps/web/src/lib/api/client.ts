const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

class ApiClient {
  private baseUrl: string
  private tokenGetter: (() => string | null) | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  setTokenGetter(getter: () => string | null) {
    this.tokenGetter = getter
  }

  private getHeaders(body?: unknown): Record<string, string> {
    const headers: Record<string, string> = {
    }
    if (!(body instanceof FormData)) {
      headers["Content-Type"] = "application/json"
    }
    const token = this.tokenGetter?.()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    return headers
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const res = await fetch(url, {
      method,
      headers: this.getHeaders(body),
      body: body ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
    })

    const json = await res.json()

    if (!res.ok) {
      throw new ApiRequestError(
        json.error?.message || "Request failed",
        json.error?.code || "UNKNOWN_ERROR",
        res.status,
        json,
      )
    }

    return json.data as T
  }

  get<T>(path: string) {
    return this.request<T>("GET", path)
  }

  post<T>(path: string, body?: unknown) {
    return this.request<T>("POST", path, body)
  }

  patch<T>(path: string, body?: unknown) {
    return this.request<T>("PATCH", path, body)
  }

  delete<T>(path: string) {
    return this.request<T>("DELETE", path)
  }
}

export class ApiRequestError extends Error {
  code: string
  status: number
  response: unknown

  constructor(message: string, code: string, status: number, response: unknown) {
    super(message)
    this.code = code
    this.status = status
    this.response = response
  }
}

export const api = new ApiClient(API_BASE_URL)
