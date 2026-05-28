import crypto from "node:crypto";
import { db } from "@/lib/db";

export async function createGroup(input: { name: string; ownerId: string }) {
  return db.$transaction(async (tx) => {
    const group = await tx.group.create({
      data: {
        name: input.name,
        ownerId: input.ownerId,
      },
    });

    await tx.groupMember.create({
      data: {
        groupId: group.id,
        userId: input.ownerId,
        role: "OWNER",
      },
    });

    return group;
  });
}

export async function createInvitation(input: {
  groupId: string;
  inviterId: string;
  recipientEmail?: string | null;
}) {
  await assertGroupOwner(input.groupId, input.inviterId);
  return db.groupInvitation.create({
    data: {
      token: crypto.randomUUID(),
      groupId: input.groupId,
      inviterId: input.inviterId,
      recipientEmail: input.recipientEmail || null,
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 7),
    },
  });
}

export async function acceptInvitation(input: { token: string; userId: string }) {
  return db.$transaction(async (tx) => {
    const invitation = await tx.groupInvitation.findUnique({
      where: { token: input.token },
    });

    if (!invitation || invitation.status !== "PENDING") return null;
    if (invitation.expiresAt < new Date()) return null;

    const member = await tx.groupMember.upsert({
      where: {
        groupId_userId: {
          groupId: invitation.groupId,
          userId: input.userId,
        },
      },
      create: {
        groupId: invitation.groupId,
        userId: input.userId,
        role: "MEMBER",
      },
      update: {},
    });

    await tx.groupInvitation.update({
      where: { token: input.token },
      data: {
        status: "ACCEPTED",
        acceptedAt: new Date(),
      },
    });

    return member;
  });
}

export async function getUserGroups(userId: string) {
  return db.group.findMany({
    where: {
      OR: [{ ownerId: userId }, { members: { some: { userId } } }],
    },
    orderBy: { createdAt: "desc" },
  });
}

export async function assertGroupAccess(groupId: string, userId: string) {
  const member = await db.groupMember.findUnique({
    where: {
      groupId_userId: {
        groupId,
        userId,
      },
    },
  });

  if (!member) throw new Error("无权访问该小组");
}

export async function assertGroupOwner(groupId: string, userId: string) {
  const group = await db.group.findUnique({
    where: { id: groupId },
  });

  if (!group || group.ownerId !== userId) {
    throw new Error("仅小组 owner 可执行该操作");
  }
}
