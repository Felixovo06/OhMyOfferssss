import { NextResponse } from "next/server";
import { createInvitationSchema } from "@/server/schemas/group";
import { createInvitation } from "@/server/groups/service";
import { getSessionUserId } from "@/server/auth/session";

export async function POST(request: Request) {
  const inviterId = await getSessionUserId();
  if (!inviterId) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = createInvitationSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "表单校验失败" }, { status: 400 });
  }

  const invitation = await createInvitation({
    groupId: parsed.data.groupId,
    inviterId,
    recipientEmail: parsed.data.recipientEmail || null,
  });

  return NextResponse.json({ ok: true, invitation });
}
