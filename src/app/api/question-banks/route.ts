import { NextResponse } from "next/server";
import { getCurrentUser } from "@/server/auth/current-user";
import { createQuestionBankSchema } from "@/server/schemas/question";
import { createQuestionBank, listQuestionBanks } from "@/server/questions/service";
import { listUserGroups } from "@/server/groups/query";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const groups = await listUserGroups(user.id);
  const banks = await listQuestionBanks({
    ownerId: user.id,
    groupId: groups[0]?.id,
  });

  return NextResponse.json({ ok: true, banks });
}

export async function POST(request: Request) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const parsed = createQuestionBankSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "表单校验失败" }, { status: 400 });
  }

  const bank = await createQuestionBank({ ...parsed.data, ownerId: user.id });
  return NextResponse.json({ ok: true, bank });
}
