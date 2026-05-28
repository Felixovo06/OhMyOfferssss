import { NextResponse } from "next/server";
import { createGroupSchema } from "@/server/schemas/group";
import { createGroup } from "@/server/groups/service";
import { getSessionUserId } from "@/server/auth/session";

export async function POST(request: Request) {
  const ownerId = await getSessionUserId();
  if (!ownerId) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = createGroupSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "表单校验失败" }, { status: 400 });
  }

  const group = await createGroup({
    name: parsed.data.name,
    ownerId,
  });

  return NextResponse.json({ ok: true, group });
}
