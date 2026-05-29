"use client"

import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { MessageSquare, Sparkles, ArrowRight } from "lucide-react"

export default function InterviewsPage() {
  const router = useRouter()

  return (
    <div className="space-y-8 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">面试</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            AI 驱动的面试练习，抽题、答题、反馈一站式完成
          </p>
        </div>
        <Button onClick={() => router.push("/interviews/new")}>
          <Sparkles className="mr-1 h-4 w-4" />
          开始新面试
        </Button>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
          <MessageSquare className="h-12 w-12 text-muted-foreground/50" />
          <div>
            <p className="text-lg font-medium">还没有面试记录</p>
            <p className="text-sm text-muted-foreground">
              选择题库和难度，AI 将为你智能抽题并给出反馈
            </p>
          </div>
          <Button onClick={() => router.push("/interviews/new")}>
            开始第一次面试
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
