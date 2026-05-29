import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getBanks,
  getBank,
  createBank,
  updateBank,
  deleteBank,
  getQuestions,
  createQuestion,
  updateQuestion,
  deleteQuestion,
} from "@/lib/api/banks"
import type { CreateBankRequest, CreateQuestionRequest, UpdateQuestionRequest, QuestionFilters } from "@/types/bank"
import { toast } from "sonner"

export function useBanks() {
  return useQuery({
    queryKey: ["banks"],
    queryFn: () => getBanks(),
  })
}

export function useBank(bankId: string | null) {
  return useQuery({
    queryKey: ["banks", bankId],
    queryFn: () => getBank(bankId!),
    enabled: !!bankId,
  })
}

export function useCreateBank() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateBankRequest) => createBank(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] })
    },
  })
}

export function useUpdateBank() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateBankRequest> }) =>
      updateBank(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["banks"] })
      queryClient.invalidateQueries({ queryKey: ["banks", variables.id] })
    },
  })
}

export function useDeleteBank() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteBank(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] })
      toast.success("题库已删除")
    },
    onError: (err) => {
      toast.error(err.message || "删除失败")
    },
  })
}

export function useQuestions(bankId: string | null, filters?: QuestionFilters) {
  return useQuery({
    queryKey: ["banks", bankId, "questions", filters],
    queryFn: () => getQuestions(bankId!, filters),
    enabled: !!bankId,
  })
}

export function useCreateQuestion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ bankId, data }: { bankId: string; data: CreateQuestionRequest }) =>
      createQuestion(bankId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["banks", variables.bankId, "questions"] })
      queryClient.invalidateQueries({ queryKey: ["banks", variables.bankId] })
    },
  })
}

export function useUpdateQuestion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateQuestionRequest }) =>
      updateQuestion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] })
    },
  })
}

export function useDeleteQuestion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteQuestion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] })
    },
  })
}
