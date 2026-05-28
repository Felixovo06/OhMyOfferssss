import { NextResponse } from "next/server";
import { loginSchema } from "@/server/schemas/auth";
import { loginUser } from "@/server/auth/service";

export async function POST(request: Request) {
  const body = await request.json();
  const parsed = loginSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "表单校验失败" }, { status: 400 });
  }

  const user = await loginUser(parsed.data);

  if (!user) {
    return NextResponse.json({ ok: false, error: "邮箱或密码错误" }, { status: 401 });
  }

  return NextResponse.json({ ok: true, user: { id: user.id, email: user.email } });
}
