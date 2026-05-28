import { NextResponse } from "next/server";
import { acceptInvitationSchema } from "@/server/schemas/group";
import { acceptInvitation } from "@/server/groups/service";
import { getSessionUserId } from "@/server/auth/session";

type RouteContext = {
  params: Promise<{ token: string }>;
};

export async function POST(_request: Request, context: RouteContext) {
  const { token } = await context.params;
  const userId = await getSessionUserId();

  if (!userId) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const parsed = acceptInvitationSchema.safeParse({ token });

  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "邀请码无效" }, { status: 400 });
  }

  const member = await acceptInvitation({
    token: parsed.data.token,
    userId,
  });

  if (!member) {
    return NextResponse.json({ ok: false, error: "邀请不可用" }, { status: 400 });
  }

  return NextResponse.json({ ok: true, member });
}
