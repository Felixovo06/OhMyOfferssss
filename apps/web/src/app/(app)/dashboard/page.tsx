"use client"

import { useGroups } from "@/lib/query/groups"
import { useAuthStore } from "@/lib/store/auth"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  BookOpen,
  Users,
  Target,
  TrendingUp,
  ArrowRight,
  FileInput,
  Sparkles,
} from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

export default function DashboardPage() {
  const { user } = useAuthStore()
  const { data: groups } = useGroups()
  const router = useRouter()

  const totalQuestions = 0
  const totalPracticed = 0
  const weakTags: string[] = []

  return (
    <div className="space-y-8 p-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          欢迎回来，{user?.name || "同学"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          今天的面试准备情况一览
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">小组</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{groups?.length || 0}</div>
            <p className="text-xs text-muted-foreground">
              已加入的小组数量
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">题目</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalQuestions}</div>
            <p className="text-xs text-muted-foreground">题库总题数</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">练习</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPracticed}</div>
            <p className="text-xs text-muted-foreground">已完成练习次数</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">薄弱点</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {weakTags.length || "—"}
            </div>
            <p className="text-xs text-muted-foreground">需加强的标签</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Groups */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">我的小组</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/groups")}
              >
                查看全部 <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </div>
            <CardDescription>你加入的面试练习小组</CardDescription>
          </CardHeader>
          <CardContent>
            {groups && groups.length > 0 ? (
              <div className="space-y-3">
                {groups.slice(0, 5).map((group) => (
                  <div
                    key={group.id}
                    onClick={() => router.push(`/groups/${group.id}`)}
                    className="flex cursor-pointer items-center justify-between rounded-lg border p-3 transition-colors hover:bg-accent"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{group.name}</p>
                      {group.description && (
                        <p className="truncate text-xs text-muted-foreground">
                          {group.description}
                        </p>
                      )}
                    </div>
                    <div className="ml-4 flex items-center gap-2">
                      <Badge variant="secondary" className="shrink-0">
                        {group.member_count} 人
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3 py-8 text-center">
                <Users className="h-8 w-8 text-muted-foreground/50" />
                <div>
                  <p className="text-sm font-medium">还没有小组</p>
                  <p className="text-xs text-muted-foreground">
                    创建小组开始面试练习
                  </p>
                </div>
                <Button size="sm" onClick={() => router.push("/groups")}>
                  创建小组
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">快捷操作</CardTitle>
            <CardDescription>快速开始面试练习</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full justify-start gap-3"
              variant="outline"
              onClick={() => toast.info("飞书导入功能即将开放")}
            >
              <FileInput className="h-4 w-4" />
              从飞书导入题目
            </Button>
            <Button
              className="w-full justify-start gap-3"
              variant="outline"
              onClick={() => toast.info("题库管理功能即将开放")}
            >
              <BookOpen className="h-4 w-4" />
              管理题库
            </Button>
            <Button
              className="w-full justify-start gap-3"
              variant="default"
              onClick={() => toast.info("AI 抽题练习即将开放")}
            >
              <Sparkles className="h-4 w-4" />
              AI 智能抽题练习
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
