import { db } from "@/lib/db";

export async function assertBankAccess(bankId: string, userId: string) {
  const bank = await db.questionBank.findUnique({
    where: { id: bankId },
    select: {
      id: true,
      ownerId: true,
      groupId: true,
      scope: true,
    },
  });

  if (!bank) {
    throw new Error("题库不存在");
  }

  if (bank.ownerId === userId) return bank;
  if (!bank.groupId) throw new Error("无权访问该题库");

  const member = await db.groupMember.findUnique({
    where: {
      groupId_userId: {
        groupId: bank.groupId,
        userId,
      },
    },
  });

  if (!member) throw new Error("无权访问该题库");

  return bank;
}

export async function assertBankOwner(bankId: string, userId: string) {
  const bank = await db.questionBank.findUnique({
    where: { id: bankId },
    select: { ownerId: true, groupId: true, scope: true },
  });

  if (!bank) throw new Error("题库不存在");
  if (bank.scope === "GROUP") {
    const group = await db.group.findUnique({
      where: { id: bank.groupId ?? "" },
      select: { ownerId: true },
    });
    if (!group || group.ownerId !== userId) throw new Error("仅小组 owner 可管理该题库");
    return bank;
  }

  if (bank.ownerId !== userId) throw new Error("无权管理该题库");
  return bank;
}
