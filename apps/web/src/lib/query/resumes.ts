import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getResumes, getResume, uploadResume } from "@/lib/api/resumes"
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
