import Link from "next/link";
import { redirect } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import type { Route } from "next";
import { loginUser } from "@/server/auth/service";
import { devLoginCredentials, devLoginEnabled } from "@/server/auth/dev-login";

export default async function LoginPage({
  searchParams,
}: Readonly<{
  searchParams?: Promise<{ error?: string }>;
}>) {
  const params = (await searchParams) ?? {};
  const error = params.error;

  async function loginAction(formData: FormData) {
    "use server";

    const email = String(formData.get("email") ?? "").trim();
    const password = String(formData.get("password") ?? "").trim();

    if (!email || !password) {
      redirect("/login?error=missing");
    }

    const user = await loginUser({ email, password });
    if (!user) {
      redirect("/login?error=invalid");
    }

    redirect("/dashboard" as Route);
  }

  return (
    <main className="relative flex min-h-dvh items-center justify-center overflow-hidden px-4 py-8 sm:px-6 lg:px-8">
      <section className="relative w-full max-w-md rounded-[32px] border border-white/80 bg-white/42 p-6 shadow-[0_28px_90px_rgba(20,20,20,0.12)] backdrop-blur-2xl sm:p-8">
        <div className="mb-8">
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs font-semibold uppercase tracking-[0.38em] text-neutral-500">Ohmyoffer</p>
            <div className="flex h-10 w-10 items-center justify-center rounded-full border border-white/75 bg-white/45 text-neutral-800 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]">
              <ShieldCheck className="h-5 w-5" />
            </div>
          </div>
          <h1 className="mt-8 text-3xl font-semibold tracking-tight text-neutral-950">登录</h1>
          <p className="mt-3 text-sm leading-6 text-neutral-600">
            仅内部用户可访问。
          </p>
        </div>

        {error ? (
          <div className="mb-5 rounded-2xl border border-neutral-950/10 bg-white/55 px-4 py-3 text-sm font-medium text-neutral-900">
            {error === "missing" ? "请输入邮箱和密码。" : "邮箱或密码错误。"}
          </div>
        ) : null}

        <form action={loginAction} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-neutral-800">
              邮箱
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="h-12 w-full rounded-2xl border border-white/80 bg-white/55 px-4 text-base text-neutral-950 outline-none transition placeholder:text-neutral-400 focus:border-neutral-950/20 focus:ring-2 focus:ring-neutral-950/10"
              placeholder="name@example.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-neutral-800">
              密码
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              className="h-12 w-full rounded-2xl border border-white/80 bg-white/55 px-4 text-base text-neutral-950 outline-none transition placeholder:text-neutral-400 focus:border-neutral-950/20 focus:ring-2 focus:ring-neutral-950/10"
              placeholder="输入密码"
            />
          </div>

          <button
            type="submit"
            className="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-neutral-950 text-sm font-semibold text-white shadow-[0_18px_35px_rgba(20,20,20,0.18)] transition hover:bg-neutral-800"
          >
            登录
          </button>
        </form>

        {devLoginEnabled ? (
          <div className="mt-5 rounded-2xl border border-white/75 bg-white/45 px-4 py-3 text-sm leading-6 text-neutral-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]">
            <p className="font-medium text-neutral-900">测试账号</p>
            <p className="mt-1">
              {devLoginCredentials.email} / {devLoginCredentials.password}
            </p>
          </div>
        ) : null}

        <p className="mt-6 text-center text-sm text-neutral-500">
          查看{" "}
          <Link href="/dashboard" className="font-medium text-neutral-950 underline underline-offset-4">
            工作台预览
          </Link>
        </p>
      </section>
    </main>
  );
}
