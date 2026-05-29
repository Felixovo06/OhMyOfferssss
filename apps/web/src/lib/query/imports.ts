import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getImportBatches,
  getImportDetail,
  createImport,
  confirmImportItem,
  rejectImportItem,
  confirmAllImportItems,
} from "@/lib/api/imports"
import type { ImportRequest } from "@/types/import"
import { toast } from "sonner"

export function useImportBatches() {
  return useQuery({
    queryKey: ["imports"],
    queryFn: () => getImportBatches(),
  })
}

export function useImportDetail(batchId: string | null) {
  return useQuery({
    queryKey: ["imports", batchId],
    queryFn: () => getImportDetail(batchId!),
    enabled: !!batchId,
  })
}

export function useCreateImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ImportRequest) => createImport(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["imports"] })
    },
    onError: (err) => {
      toast.error(err.message || "导入失败")
    },
  })
}

export function useConfirmImportItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (itemId: string) => confirmImportItem(itemId),
    onSuccess: (_data, itemId) => {
      queryClient.invalidateQueries({ queryKey: ["imports"] })
    },
  })
}

export function useRejectImportItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (itemId: string) => rejectImportItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["imports"] })
    },
  })
}

export function useConfirmAllImportItems() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (batchId: string) => confirmAllImportItems(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["imports"] })
    },
  })
}
