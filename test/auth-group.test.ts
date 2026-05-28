import { describe, expect, it } from "vitest";
import { loginSchema } from "@/server/schemas/auth";
import { createGroupSchema, createInvitationSchema } from "@/server/schemas/group";

describe("phase 1 auth and groups", () => {
  it("validates login payloads", () => {
    expect(loginSchema.safeParse({ email: "a@b.com", password: "secret1" }).success).toBe(true);
    expect(loginSchema.safeParse({ email: "bad", password: "x" }).success).toBe(false);
  });

  it("validates group creation and invitation payloads", () => {
    expect(createGroupSchema.safeParse({ name: "Alpha" }).success).toBe(true);
    expect(createInvitationSchema.safeParse({ groupId: "g1", recipientEmail: "a@b.com" }).success).toBe(true);
  });
});
