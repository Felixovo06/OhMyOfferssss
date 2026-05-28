import { NextResponse } from "next/server";
import { getCurrentUser } from "@/server/auth/current-user";
import { enableQuestion } from "@/server/questions/service";

type RouteContext = {
  params: Promise<{ questionId: string }>;
};

export async function POST(_request: Request, context: RouteContext) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ ok: false, error: "未登录" }, { status: 401 });
  }

  const { questionId } = await context.params;
  const question = await enableQuestion(questionId);
  return NextResponse.json({ ok: true, question });
}
