"use client"

import type { ReactNode } from "react"
import { Sidebar } from "./sidebar"

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-muted/30">{children}</main>
    </div>
  )
}
