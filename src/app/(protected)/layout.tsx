import { redirect } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { getSessionUserId } from "@/server/auth/session";

export default async function ProtectedLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const userId = await getSessionUserId();
  if (!userId) {
    redirect("/login");
  }

  return <AppShell>{children}</AppShell>;
}
