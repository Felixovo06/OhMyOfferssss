import type { Route } from "next";
import Link from "next/link";
import { AlertTriangle, ArrowRight, CheckCircle2, Inbox, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "default" | "warning" | "success";

const iconMap: Record<Variant, LucideIcon> = {
  default: Inbox,
  warning: AlertTriangle,
  success: CheckCircle2,
};

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  variant = "default",
}: Readonly<{
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: Route;
  variant?: Variant;
}>) {
  const Icon = iconMap[variant];
  return (
    <div className="rounded-[28px] border border-white/70 bg-white/45 p-8 text-center shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-white/80 bg-white/55 text-neutral-800 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]">
        <Icon className="h-5 w-5" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-neutral-950">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-neutral-600">{description}</p>
      {actionLabel && actionHref ? (
        <Link
          href={actionHref}
          className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-2xl border border-neutral-950/10 bg-neutral-950 px-4 text-sm font-medium text-white shadow-[0_16px_30px_rgba(20,20,20,0.16)] transition-colors hover:bg-neutral-800"
        >
          {actionLabel}
          <ArrowRight className="h-4 w-4" />
        </Link>
      ) : null}
    </div>
  );
}

export function StatusPill({
  children,
  tone = "default",
}: Readonly<{
  children: React.ReactNode;
  tone?: "default" | "warning" | "success";
}>) {
  const tones = {
    default: "border-neutral-950/10 bg-white/50 text-neutral-700",
    warning: "border-neutral-950/10 bg-neutral-950/6 text-neutral-800",
    success: "border-neutral-950/10 bg-neutral-950/8 text-neutral-900",
  };

  return <span className={cn("inline-flex rounded-full border px-2.5 py-1 text-xs font-medium backdrop-blur-xl", tones[tone])}>{children}</span>;
}

export function SectionCard({
  title,
  description,
  children,
  action,
}: Readonly<{
  title: string;
  description?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}>) {
  return (
    <section className="rounded-[28px] border border-white/70 bg-white/45 p-5 shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-neutral-950">{title}</h3>
          {description ? <p className="mt-1 text-sm leading-6 text-neutral-600">{description}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}
