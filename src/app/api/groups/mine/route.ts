import { NextResponse } from "next/server";
import { getCurrentUser } from "@/server/auth/current-user";
import { listUserGroups } from "@/server/groups/query";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const groups = await listUserGroups(user.id);
  return NextResponse.json({ ok: true, groups });
}
