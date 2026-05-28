import { GlobalShell } from "./global-shell";

export function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <GlobalShell>{children}</GlobalShell>;
}
