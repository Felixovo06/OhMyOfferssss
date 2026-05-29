import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  createSession,
  getSession,
  startSession,
  submitAnswer,
  updateQuestionDifficulty,
  nextQuestion,
  getSummary,
} from "@/lib/api/interviews"
import type { InterviewConfig } from "@/types/interview"
import { toast } from "sonner"

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (config: InterviewConfig) => createSession(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] })
    },
  })
}

export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["interviews", sessionId],
    queryFn: () => getSession(sessionId!),
    enabled: !!sessionId,
  })
}

export function useStartSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => startSession(sessionId),
    onSuccess: (_data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["interviews", sessionId] })
    },
    onError: (err) => {
      toast.error(err.message || "开始面试失败")
    },
  })
}

export function useSubmitAnswer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sessionId,
      questionId,
      answer,
      difficulty,
    }: {
      sessionId: string
      questionId: string
      answer: string
      difficulty?: number | null
    }) => submitAnswer(sessionId, questionId, answer, difficulty),
    onSuccess: (_data, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ["interviews", sessionId] })
    },
    onError: (err) => {
      toast.error(err.message || "提交失败")
    },
  })
}

export function useUpdateQuestionDifficulty() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ questionId, difficulty }: {
      sessionId: string
      questionId: string
      difficulty?: number | null
    }) => updateQuestionDifficulty(questionId, difficulty),
    onSuccess: (_data, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ["interviews", sessionId] })
    },
    onError: (err) => {
      toast.error(err.message || "难度保存失败")
    },
  })
}

export function useNextQuestion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => nextQuestion(sessionId),
    onSuccess: (_data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["interviews", sessionId] })
    },
  })
}

export function usePrefetchNextQuestion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => nextQuestion(sessionId, { prefetch: true }),
    onSuccess: (_data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["interviews", sessionId] })
    },
  })
}

export function useSummary(sessionId: string | null) {
  return useQuery({
    queryKey: ["interviews", sessionId, "summary"],
    queryFn: () => getSummary(sessionId!),
    enabled: !!sessionId,
  })
}
