"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function ProtectedError({
  error,
  reset,
}: Readonly<{
  error: Error & { digest?: string };
  reset: () => void;
}>) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[50vh] max-w-2xl flex-col items-center justify-center px-4 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full border border-white/75 bg-white/45 text-neutral-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <h2 className="mt-4 text-2xl font-semibold text-neutral-950">页面出错了</h2>
      <p className="mt-3 text-sm leading-7 text-neutral-600">
        这通常是某个页面数据或组件发生了异常。你可以先重试一次，若仍失败再回到工作台。
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 inline-flex h-11 items-center gap-2 rounded-xl bg-neutral-950 px-4 text-sm font-medium text-white shadow-[0_16px_30px_rgba(20,20,20,0.16)] transition hover:bg-neutral-800"
      >
        <RefreshCw className="h-4 w-4" />
        重试
      </button>
    </div>
  );
}
