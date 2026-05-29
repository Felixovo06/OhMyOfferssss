"use client"

import type { ReactNode } from "react"
import { QueryProvider } from "@/lib/query/provider"
import { AuthInitializer } from "@/components/layout/auth-initializer"

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <AuthInitializer />
      {children}
    </QueryProvider>
  )
}
