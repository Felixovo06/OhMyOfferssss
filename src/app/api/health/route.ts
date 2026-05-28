import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { redis } from "@/lib/redis";

export async function GET() {
  const [database, redisResult] = await Promise.allSettled([
    db.$queryRaw`SELECT 1`,
    redis.ping(),
  ]);

  return NextResponse.json({
    ok: database.status === "fulfilled" && redisResult.status === "fulfilled",
    database: database.status === "fulfilled",
    redis: redisResult.status === "fulfilled",
  });
}
