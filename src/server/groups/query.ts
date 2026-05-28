import { db } from "@/lib/db";

export async function listUserGroups(userId: string) {
  return db.group.findMany({
    where: {
      OR: [{ ownerId: userId }, { members: { some: { userId } } }],
    },
    orderBy: { createdAt: "desc" },
  });
}

export async function listGroupMembers(groupId: string) {
  return db.groupMember.findMany({
    where: { groupId },
    include: {
      user: {
        select: { id: true, email: true, name: true },
      },
    },
    orderBy: { createdAt: "asc" },
  });
}

export async function listPendingInvitations(groupId: string) {
  return db.groupInvitation.findMany({
    where: { groupId, status: "PENDING" },
    orderBy: { createdAt: "desc" },
  });
}
