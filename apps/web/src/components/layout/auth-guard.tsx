"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuthStore } from "@/lib/store/auth"
import { useMe } from "@/lib/query/auth"
import { Loader2 } from "lucide-react"

const publicPaths = ["/login", "/register", "/invite/"]

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuthStore()
  useMe()
  const router = useRouter()
  const pathname = usePathname()

  const isPublic = publicPaths.some((p) => pathname.startsWith(p))

  useEffect(() => {
    if (isLoading) return
    if (!token && !isPublic) {
      router.replace("/login")
    }
    if (token && isPublic && pathname !== "/invite/") {
      router.replace("/dashboard")
    }
  }, [token, isLoading, isPublic, pathname, router])

  if (isLoading || (!token && !isPublic)) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return <>{children}</>
}
