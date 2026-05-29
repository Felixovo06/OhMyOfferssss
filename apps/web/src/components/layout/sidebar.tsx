"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuthStore } from "@/lib/store/auth"
import { useLogout } from "@/lib/query/auth"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Users,
  BookOpen,
  FileInput,
  LogOut,
  ChevronRight,
  Sparkles,
  MessageSquare,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { useState } from "react"

const navItems = [
  { href: "/dashboard", label: "工作台", icon: LayoutDashboard },
  { href: "/interviews", label: "面试", icon: MessageSquare },
  { href: "/groups", label: "小组", icon: Users },
  { href: "/banks", label: "题库", icon: BookOpen },
  { href: "/imports", label: "飞书导入", icon: FileInput },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuthStore()
  const logout = useLogout()
  const [collapsed, setCollapsed] = useState(false)

  const initials = user?.name
    ? user.name.charAt(0).toUpperCase()
    : user?.email?.charAt(0).toUpperCase() || "?"

  return (
    <aside
      className={cn(
        "flex flex-col border-r bg-card transition-all duration-200",
        collapsed ? "w-16" : "w-56",
      )}
    >
      {/* Brand */}
      <div className="flex h-14 items-center gap-2 px-4">
        <Sparkles className="h-5 w-5 shrink-0 text-primary" />
        {!collapsed && (
          <span className="text-sm font-semibold tracking-tight">
            OhMyOffer
          </span>
        )}
      </div>

      <Separator />

      {/* Nav */}
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                collapsed && "justify-center px-2",
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      <Separator />

      {/* User */}
      <div className="p-2">
        <div
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2",
            collapsed && "justify-center",
          )}
        >
          <Avatar className="h-7 w-7">
            <AvatarFallback className="text-xs">{initials}</AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user?.name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {user?.email}
              </p>
            </div>
          )}
        </div>
        {!collapsed && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-1 w-full justify-start gap-2 text-muted-foreground"
            onClick={() => logout.mutate()}
          >
            <LogOut className="h-4 w-4" />
            退出
          </Button>
        )}
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center border-t py-2 text-muted-foreground hover:text-foreground"
      >
        <ChevronRight
          className={cn(
            "h-4 w-4 transition-transform",
            collapsed ? "" : "rotate-180",
          )}
        />
      </button>
    </aside>
  )
}
