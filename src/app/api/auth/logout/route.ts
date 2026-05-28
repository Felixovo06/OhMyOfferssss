import { NextResponse } from "next/server";
import { logoutUser } from "@/server/auth/service";

export async function POST() {
  await logoutUser();
  return NextResponse.json({ ok: true });
}
