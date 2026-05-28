import { NextResponse } from "next/server";
import { getCurrentUser } from "@/server/auth/current-user";
import { createQuestionSchema, questionQuerySchema } from "@/server/schemas/question";
import {
  createQuestion,
  listQuestions,
} from "@/server/questions/service";
import { assertBankAccess } from "@/server/questions/authorization";

export async function GET(request: Request) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const query = questionQuerySchema.safeParse(Object.fromEntries(new URL(request.url).searchParams.entries()));
  if (!query.success) {
    return NextResponse.json({ ok: false, error: "查询参数无效" }, { status: 400 });
  }

  const questions = await listQuestions(query.data);
  return NextResponse.json({ ok: true, questions });
}

export async function POST(request: Request) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const parsed = createQuestionSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "表单校验失败" }, { status: 400 });
  }

  await assertBankAccess(parsed.data.bankId, user.id);
  const question = await createQuestion({ ...parsed.data, ownerId: user.id });
  return NextResponse.json({ ok: true, question });
}
