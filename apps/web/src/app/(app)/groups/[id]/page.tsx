"use client"

import { useParams, useRouter } from "next/navigation"
import { useState } from "react"
import {
  useGroup,
  useGroupMembers,
  useCreateInvitation,
} from "@/lib/query/groups"
import { useAuthStore } from "@/lib/store/auth"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  ArrowLeft,
  Copy,
  Check,
  Loader2,
  Users,
  UserPlus,
  Calendar,
} from "lucide-react"
import { toast } from "sonner"

export default function GroupDetailPage() {
  const params = useParams()
  const router = useRouter()
  const groupId = params.id as string
  const { user } = useAuthStore()

  const { data: group, isLoading: groupLoading } = useGroup(groupId)
  const { data: members, isLoading: membersLoading } = useGroupMembers(groupId)
  const createInvitation = useCreateInvitation()

  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteUrl, setInviteUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const isOwner = group?.owner_id === user?.id

  async function handleGenerateInvite() {
    createInvitation.mutate(groupId, {
      onSuccess: (res) => {
        setInviteUrl(
          res.invite_url.startsWith("/")
            ? `${window.location.origin}${res.invite_url}`
            : res.invite_url,
        )
      },
      onError: (err) => {
        toast.error(err.message || "生成邀请链接失败")
      },
    })
  }

  function handleCopy() {
    if (inviteUrl) {
      navigator.clipboard.writeText(inviteUrl)
      setCopied(true)
      toast.success("已复制到剪贴板")
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (groupLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!group) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <Users className="h-12 w-12 text-muted-foreground/50" />
        <div>
          <p className="text-lg font-medium">小组不存在</p>
          <p className="text-sm text-muted-foreground">
            该小组可能已被删除或链接无效
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push("/groups")}>
          返回小组列表
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Back */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push("/groups")}
      >
        <ArrowLeft className="mr-1 h-4 w-4" />
        返回小组列表
      </Button>

      {/* Group Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              {group.name}
            </h1>
            <Badge variant="outline">{group.member_count} 名成员</Badge>
          </div>
          {group.description && (
            <p className="mt-1 text-sm text-muted-foreground">
              {group.description}
            </p>
          )}
        </div>
        {isOwner && (
          <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
            <Button onClick={() => setInviteOpen(true)}>
              <UserPlus className="mr-1 h-4 w-4" />
              邀请成员
            </Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>邀请成员</DialogTitle>
                <DialogDescription>
                  生成邀请链接，发送给要邀请的成员
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                {!inviteUrl ? (
                  <Button
                    onClick={handleGenerateInvite}
                    disabled={createInvitation.isPending}
                    className="w-full"
                  >
                    {createInvitation.isPending ? "生成中..." : "生成邀请链接"}
                  </Button>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 rounded-md border bg-muted/50 p-3">
                      <code className="flex-1 truncate text-sm">
                        {inviteUrl}
                      </code>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={handleCopy}
                      >
                        {copied ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      链接 7 天内有效，将链接发送给要邀请的成员
                    </p>
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <Separator />

      {/* Members */}
      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">
          成员列表
        </h2>
        {membersLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : members && members.length > 0 ? (
          <div className="space-y-2">
            {members.map((member) => (
              <div
                key={member.id}
                className="flex items-center gap-3 rounded-lg border p-3"
              >
                <Avatar className="h-9 w-9">
                  <AvatarFallback>
                    {(member.user.name || member.user.email).charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{member.user.name}</p>
                    {member.role === "owner" && (
                      <Badge variant="secondary" className="text-[10px]">
                        创建者
                      </Badge>
                    )}
                  </div>
                  <p className="truncate text-xs text-muted-foreground">
                    {member.user.email}
                  </p>
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {new Date(member.joined_at).toLocaleDateString("zh-CN")}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <Users className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">暂无成员</p>
          </div>
        )}
      </div>
    </div>
  )
}
