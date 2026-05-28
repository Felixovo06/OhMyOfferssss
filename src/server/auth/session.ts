import crypto from "node:crypto";
import { cookies } from "next/headers";
import { redis } from "@/lib/redis";

const SESSION_COOKIE = "ohmyoffer_session";
const sessionKey = (token: string) => `session:${token}`;

export async function createSession(userId: string) {
  const token = crypto.randomUUID();
  await redis.set(sessionKey(token), userId, "EX", 60 * 60 * 24 * 7);
  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });
}

export async function clearSession() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (token) {
    await redis.del(sessionKey(token));
  }
  cookieStore.delete(SESSION_COOKIE);
}

export async function getSessionUserId() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  return (await redis.get(sessionKey(token))) ?? null;
}

export function hasSession(token: string) {
  return redis.exists(sessionKey(token)).then((value) => value === 1);
}
