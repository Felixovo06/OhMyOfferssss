"use client"

import { useState, type ReactNode } from "react"
import { Sidebar } from "./sidebar"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Menu, Sparkles } from "lucide-react"

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile header */}
      <div className="fixed inset-x-0 top-0 z-40 flex h-14 items-center gap-2 border-b bg-card px-4 md:hidden">
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetTrigger render={<Button variant="ghost" size="icon" />}>
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-56 p-0">
            <Sidebar onNavClick={() => setMobileMenuOpen(false)} />
          </SheetContent>
        </Sheet>
        <Sparkles className="h-5 w-5 text-primary" />
        <span className="text-sm font-semibold tracking-tight">OhMyOffer</span>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      <main className="flex-1 overflow-y-auto bg-muted/30 pt-14 md:pt-0">
        {children}
      </main>
    </div>
  )
}
