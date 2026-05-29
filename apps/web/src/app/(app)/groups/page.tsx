"use client"

import { useState } from "react"
import { useGroups, useCreateGroup } from "@/lib/query/groups"
import Link from "next/link"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Users, Plus, AlertCircle } from "lucide-react"
import { toast } from "sonner"

const createGroupSchema = z.object({
  name: z.string().min(2, "小组名称至少 2 个字符").max(50, "小组名称不超过 50 个字符"),
  description: z.string().max(200, "描述不超过 200 个字符").optional(),
})

type CreateGroupForm = z.infer<typeof createGroupSchema>

export default function GroupsPage() {
  const { data: groups, isLoading, error, refetch } = useGroups()
  const createGroup = useCreateGroup()
  const [open, setOpen] = useState(false)

  const form = useForm<CreateGroupForm>({
    resolver: zodResolver(createGroupSchema),
    defaultValues: { name: "", description: "" },
  })

  function onSubmit(data: CreateGroupForm) {
    createGroup.mutate(data, {
      onSuccess: () => {
        toast.success("小组创建成功")
        setOpen(false)
        form.reset()
      },
      onError: (err) => {
        toast.error(err.message || "创建失败")
      },
    })
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">小组</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            管理和加入面试练习小组
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-1 h-4 w-4" />
            创建小组
          </Button>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>创建小组</DialogTitle>
              <DialogDescription>
                创建一个新的面试练习小组
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>小组名称</FormLabel>
                      <FormControl>
                        <Input placeholder="例如：前端面试组" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>描述（可选）</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="小组的目标和说明..."
                          className="resize-none"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button
                    type="submit"
                    disabled={createGroup.isPending}
                  >
                    {createGroup.isPending ? "创建中..." : "创建"}
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-5 w-12 rounded-full" />
                </div>
                <Skeleton className="mt-2 h-4 w-48" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-3 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <AlertCircle className="h-12 w-12 text-red-500/50" />
          <div>
            <p className="text-lg font-medium">加载失败</p>
            <p className="text-sm text-muted-foreground">{error.message || "请稍后重试"}</p>
          </div>
          <Button variant="outline" onClick={() => refetch()}>重试</Button>
        </div>
      ) : groups && groups.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((group) => (
            <Link key={group.id} href={`/groups/${group.id}`}>
              <Card className="transition-colors hover:bg-accent/50">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{group.name}</CardTitle>
                    <Badge variant="secondary" className="shrink-0">
                      {group.member_count} 人
                    </Badge>
                  </div>
                  {group.description && (
                    <CardDescription className="line-clamp-2">
                      {group.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    创建于{" "}
                    {new Date(group.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <Users className="h-12 w-12 text-muted-foreground/50" />
          <div>
            <p className="text-lg font-medium">还没有小组</p>
            <p className="text-sm text-muted-foreground">
              创建你的第一个面试练习小组
            </p>
          </div>
          <Button
            onClick={() => setOpen(true)}
          >
            <Plus className="mr-1 h-4 w-4" />
            创建小组
          </Button>
        </div>
      )}
    </div>
  )
}
