import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-dvh items-center justify-center px-4">
      <div className="max-w-md rounded-[28px] border border-white/75 bg-white/45 p-8 text-center shadow-[0_24px_70px_rgba(20,20,20,0.08)] backdrop-blur-2xl">
        <p className="text-sm font-medium text-neutral-500">404</p>
        <h1 className="mt-3 text-2xl font-semibold text-neutral-950">页面不存在</h1>
        <p className="mt-3 text-sm leading-7 text-neutral-600">
          可能是路由还没补齐，或者链接已变更。先回到工作台继续操作。
        </p>
        <Link
          href="/dashboard"
          className="mt-6 inline-flex h-11 items-center rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white shadow-[0_16px_30px_rgba(20,20,20,0.16)] transition hover:bg-neutral-800"
        >
          返回工作台
        </Link>
      </div>
    </main>
  );
}
