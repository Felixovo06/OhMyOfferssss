"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useBanks, useCreateBank, useDeleteBank } from "@/lib/query/banks"
import { useGroups } from "@/lib/query/groups"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Plus, Loader2, Trash2, Library } from "lucide-react"
import { toast } from "sonner"

const createBankSchema = z.object({
  name: z.string().min(1, "请输入题库名称").max(100, "名称不超过 100 个字符"),
  description: z.string().max(500, "描述不超过 500 个字符").optional(),
  group_id: z.string().optional(),
  target_positions: z.string().optional(),
  skill_keywords: z.string().optional(),
  domain_tags: z.string().optional(),
})

type CreateBankForm = z.infer<typeof createBankSchema>

export default function BanksPage() {
  const router = useRouter()
  const { data: banks, isLoading } = useBanks()
  const { data: groups } = useGroups()
  const createBank = useCreateBank()
  const deleteBank = useDeleteBank()

  const [open, setOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const form = useForm<CreateBankForm>({
    resolver: zodResolver(createBankSchema),
    defaultValues: { name: "", description: "", group_id: "" },
  })

  function onSubmit(data: CreateBankForm) {
    createBank.mutate(
      {
        name: data.name,
        description: data.description || undefined,
        group_id: data.group_id || undefined,
      },
      {
        onSuccess: () => {
          toast.success("题库创建成功")
          setOpen(false)
          form.reset()
        },
        onError: (err) => {
          toast.error(err.message || "创建失败")
        },
      },
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">题库</h1>
          <p className="mt-1 text-sm text-muted-foreground">管理和维护你的面试题目</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-1 h-4 w-4" />
            创建题库
          </Button>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>创建题库</DialogTitle>
              <DialogDescription>创建一个新的题库来组织面试题目</DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>题库名称</FormLabel>
                      <FormControl>
                        <Input placeholder="例如：前端基础" {...field} />
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
                        <Textarea placeholder="题库说明..." className="resize-none" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="group_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>关联小组（可选）</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="不关联小组" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {groups?.map((g) => (
                            <SelectItem key={g.id} value={g.id}>
                              {g.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                  <Separator className="my-2" />
                  <p className="text-xs font-medium text-muted-foreground">题库画像（可选）</p>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="target_positions"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>适配岗位</FormLabel>
                          <FormControl>
                            <Input placeholder="前端工程师, Node.js 后端" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="skill_keywords"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>技能关键词</FormLabel>
                          <FormControl>
                            <Input placeholder="React, TypeScript, CSS" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  <FormField
                    control={form.control}
                    name="domain_tags"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>领域标签</FormLabel>
                        <FormControl>
                          <Input placeholder="前端, 性能优化, 工程化" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                <DialogFooter>
                  <Button type="submit" disabled={createBank.isPending}>
                    {createBank.isPending ? "创建中..." : "创建"}
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Delete confirmation */}
      <Dialog open={!!deleteId} onOpenChange={(o) => !o && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>删除后题库中的题目也将被移除，此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              disabled={deleteBank.isPending}
              onClick={() => {
                if (deleteId) {
                  deleteBank.mutate(deleteId, { onSettled: () => setDeleteId(null) })
                }
              }}
            >
              {deleteBank.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : banks && banks.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {banks.map((bank) => (
            <Card
              key={bank.id}
              className="group relative cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => router.push(`/banks/${bank.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">{bank.name}</CardTitle>
                  <Badge variant="secondary" className="shrink-0">
                    {bank.question_count} 题
                  </Badge>
                </div>
                {bank.description && (
                  <CardDescription className="line-clamp-2">{bank.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-center gap-1.5">
                  {bank.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-[10px]">
                      {tag}
                    </Badge>
                  ))}
                </div>
                {bank.target_positions && bank.target_positions.length > 0 && (
                  <div className="mt-2 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
                    适配 {bank.target_positions.slice(0, 3).join("、")}
                    {bank.target_positions.length > 3 && <span>等 {bank.target_positions.length} 个岗位</span>}
                  </div>
                )}
                <p className="mt-2 text-xs text-muted-foreground">
                  创建于 {new Date(bank.created_at).toLocaleDateString("zh-CN")}
                </p>
              </CardContent>
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 hidden group-hover:flex"
                onClick={(e) => {
                  e.stopPropagation()
                  setDeleteId(bank.id)
                }}
              >
                <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
              </Button>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <Library className="h-12 w-12 text-muted-foreground/50" />
          <div>
            <p className="text-lg font-medium">还没有题库</p>
            <p className="text-sm text-muted-foreground">创建你的第一个面试题库</p>
          </div>
          <Button onClick={() => setOpen(true)}>
            <Plus className="mr-1 h-4 w-4" />
            创建题库
          </Button>
        </div>
      )}
    </div>
  )
}
