import { NextResponse } from "next/server";
import { getCurrentUser } from "@/server/auth/current-user";
import { assertGroupAccess } from "@/server/groups/service";
import { listGroupMembers } from "@/server/groups/query";

type RouteContext = {
  params: Promise<{ groupId: string }>;
};

export async function GET(_request: Request, context: RouteContext) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const { groupId } = await context.params;
  await assertGroupAccess(groupId, user.id);
  const members = await listGroupMembers(groupId);
  return NextResponse.json({ ok: true, members });
}
