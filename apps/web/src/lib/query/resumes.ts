import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { deleteResume, getResumes, getResume, uploadResume } from "@/lib/api/resumes"
import { toast } from "sonner"

export function useResumes() {
  return useQuery({
    queryKey: ["resumes"],
    queryFn: () => getResumes(),
  })
}

export function useResume(resumeId: string | null) {
  return useQuery({
    queryKey: ["resumes", resumeId],
    queryFn: () => getResume(resumeId!),
    enabled: !!resumeId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && data.status === "parsing") return 2000
      return false
    },
  })
}

export function useUploadResume() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => uploadResume(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] })
    },
    onError: (err) => {
      toast.error(err.message || "上传失败")
    },
  })
}

export function useDeleteResume() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (resumeId: string) => deleteResume(resumeId),
    onSuccess: (_data, resumeId) => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] })
      queryClient.removeQueries({ queryKey: ["resumes", resumeId] })
    },
    onError: (err) => {
      toast.error(err.message || "删除失败")
    },
  })
}
