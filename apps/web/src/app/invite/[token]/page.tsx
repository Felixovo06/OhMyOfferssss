"use client"

import { useParams, useRouter } from "next/navigation"
import { Loader2, UserPlus } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useAcceptInvitation, useInvitation } from "@/lib/query/groups"
import { useAuthStore } from "@/lib/store/auth"

export default function InvitePage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string
  const { token: authToken } = useAuthStore()
  const invitation = useInvitation(token)
  const acceptInvitation = useAcceptInvitation()

  function handleAccept() {
    if (!authToken) {
      router.push("/login")
      return
    }

    acceptInvitation.mutate(token, {
      onSuccess: (res) => {
        toast.success("已加入小组")
        router.push(`/groups/${res.group.id}`)
      },
      onError: (err) => {
        toast.error(err.message || "加入失败")
      },
    })
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-11 w-11 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <UserPlus className="h-5 w-5" />
          </div>
          <CardTitle>加入面试练习小组</CardTitle>
          <CardDescription>
            {invitation.data
              ? `你正在加入「${invitation.data.group_name}」`
              : "正在读取邀请信息"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {invitation.isLoading ? (
            <div className="flex justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : invitation.isError ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              邀请链接无效或已过期
            </div>
          ) : (
            <Button
              className="w-full"
              onClick={handleAccept}
              disabled={acceptInvitation.isPending}
            >
              {acceptInvitation.isPending ? "加入中..." : "接受邀请"}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
