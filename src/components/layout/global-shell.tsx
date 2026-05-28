"use client";

import Link from "next/link";
import type { Route } from "next";
import { ArrowRight, FileText, LayoutDashboard, LogOut, MessageSquareText, Shield, Users } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { mockGroup, mockUser } from "@/lib/mock-data";

const navItems = [
  { href: "/dashboard" as Route, label: "工作台", icon: LayoutDashboard },
  { href: "/banks" as Route, label: "题库", icon: FileText },
  { href: "/imports" as Route, label: "导入", icon: ArrowRight },
  { href: "/practice/normal" as Route, label: "面试", icon: MessageSquareText },
  { href: "/groups" as Route, label: "小组", icon: Users },
  { href: "/settings" as Route, label: "设置", icon: Shield },
];

export function GlobalShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const mobileNavItems = navItems.slice(0, 5);

  return (
    <div className="min-h-dvh bg-transparent text-neutral-950">
      <div className="mx-auto flex min-h-dvh max-w-[1600px] p-3 sm:p-4 lg:p-6">
        <div className="flex min-h-[calc(100dvh-1.5rem)] w-full overflow-hidden rounded-[28px] border border-white/80 bg-white/35 shadow-[0_28px_90px_rgba(20,20,20,0.12)] backdrop-blur-2xl sm:min-h-[calc(100dvh-2rem)] lg:min-h-[calc(100dvh-3rem)]">
          <aside className="hidden w-72 shrink-0 border-r border-white/70 bg-white/38 px-4 py-6 backdrop-blur-2xl lg:flex lg:flex-col">
            <div className="rounded-3xl border border-white/80 bg-white/45 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_18px_45px_rgba(20,20,20,0.06)]">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-neutral-500">Ohmyoffer</p>
              <h1 className="mt-3 text-lg font-semibold text-neutral-950">AI 面试抽题后台</h1>
              <p className="mt-2 text-sm leading-6 text-neutral-600">
                题库、导入、练习和小组协作都放在一处，尽量少噪音，多密度。
              </p>
            </div>

            <nav className="mt-8 space-y-1">
              {navItems.map(({ href, label, icon: Icon }) => {
                const active = pathname === href || pathname.startsWith(`${href}/`);
                return (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      "flex min-h-11 items-center gap-3 rounded-2xl px-3 text-sm font-medium transition-all duration-200",
                      active
                        ? "border border-neutral-950/10 bg-neutral-950 text-white shadow-[0_16px_35px_rgba(20,20,20,0.16)]"
                        : "text-neutral-600 hover:bg-white/55 hover:text-neutral-950",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </nav>

            <div className="mt-auto rounded-3xl border border-white/75 bg-white/42 p-4 text-neutral-800 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">当前空间</p>
              <p className="mt-2 text-sm font-semibold text-neutral-950">{mockGroup.name}</p>
              <p className="mt-1 text-sm leading-6 text-neutral-600">{mockGroup.scope}</p>
              <div className="mt-4 flex items-center gap-2 text-xs text-neutral-500">
                <span>{mockGroup.members} 位成员</span>
                <span>·</span>
                <span>{mockGroup.invitations} 个待处理邀请</span>
              </div>
            </div>
          </aside>

          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-20 border-b border-white/70 bg-white/40 backdrop-blur-2xl">
              <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-neutral-500">Ohmyoffer 后台</p>
                  <h2 className="truncate text-base font-semibold text-neutral-950 sm:text-lg">
                    {mockGroup.name}
                  </h2>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden items-center gap-3 rounded-full border border-white/80 bg-white/45 px-3 py-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] md:flex">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-neutral-950 text-xs font-semibold text-white">
                      {mockUser.name.slice(0, 1)}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-neutral-950">{mockUser.name}</p>
                      <p className="truncate text-xs text-neutral-500">{mockUser.email}</p>
                    </div>
                  </div>
                  <Link
                    href="/logout"
                    className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-neutral-950/10 bg-white/45 px-4 text-sm font-medium text-neutral-800 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)] transition-colors hover:bg-white/70"
                  >
                    <LogOut className="h-4 w-4" />
                    退出
                  </Link>
                </div>
              </div>
            </header>

            <main id="main-content" className="flex-1 px-4 pb-24 pt-6 sm:px-6 lg:px-8 lg:pb-8">
              {children}
            </main>
          </div>
        </div>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-white/70 bg-white/55 px-2 py-2 backdrop-blur-2xl lg:hidden">
        <div className="grid grid-cols-5 gap-1">
          {mobileNavItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex min-h-14 flex-col items-center justify-center rounded-2xl px-1 text-[11px] font-medium transition-colors",
                  active ? "bg-neutral-950 text-white" : "text-neutral-500 hover:bg-white/55 hover:text-neutral-950",
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="mt-1 truncate">{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
