import { db } from "@/lib/db";
import { normalizeTagNames } from "./tags";
import type { Prisma } from "@/generated/prisma/client";
import type {
  CreateQuestionBankInput,
  CreateQuestionInput,
  QuestionQueryInput,
  UpdateQuestionBankInput,
  UpdateQuestionInput,
} from "@/server/schemas/question";

async function upsertTags(tx: Prisma.TransactionClient, tagNames: string[]) {
  const normalized = normalizeTagNames(tagNames);
  const tags = await Promise.all(
    normalized.map((name) =>
      tx.tag.upsert({
        where: { name },
        create: { name },
        update: {},
      }),
    ),
  );
  return tags;
}

export async function createQuestionBank(input: CreateQuestionBankInput & { ownerId: string }) {
  return db.questionBank.create({
    data: {
      name: input.name,
      scope: input.scope,
      groupId: input.scope === "GROUP" ? input.groupId ?? null : null,
      ownerId: input.ownerId,
    },
  });
}

export async function updateQuestionBank(input: UpdateQuestionBankInput & { ownerId: string }) {
  return db.questionBank.update({
    where: { id: input.id },
    data: {
      name: input.name,
      scope: input.scope,
      groupId: input.scope === "GROUP" ? input.groupId ?? null : null,
    },
  });
}

export async function listQuestionBanks(filter?: { ownerId?: string; groupId?: string }) {
  return db.questionBank.findMany({
    where: {
      ...(filter?.ownerId ? { ownerId: filter.ownerId } : {}),
      ...(filter?.groupId ? { OR: [{ groupId: filter.groupId }, { ownerId: filter.ownerId }] } : {}),
    },
    orderBy: { createdAt: "desc" },
  });
}

export async function createQuestion(input: CreateQuestionInput & { ownerId: string }) {
  return db.$transaction(async (tx) => {
    const tags = await upsertTags(tx, input.tagNames);
    const question = await tx.question.create({
      data: {
        bankId: input.bankId,
        question: input.question,
        answer: input.answer,
        difficultyScore: input.difficultyScore,
        enabled: input.enabled,
        ownerId: input.ownerId,
      },
    });

    await tx.questionTag.createMany({
      data: tags.map((tag) => ({
        questionId: question.id,
        tagId: tag.id,
      })),
      skipDuplicates: true,
    });

    return question;
  });
}

export async function updateQuestion(input: UpdateQuestionInput & { ownerId: string }) {
  return db.$transaction(async (tx) => {
    const question = await tx.question.update({
      where: { id: input.id },
      data: {
        ...(input.bankId ? { bankId: input.bankId } : {}),
        ...(input.question ? { question: input.question } : {}),
        ...(input.answer ? { answer: input.answer } : {}),
        ...(typeof input.difficultyScore === "number" ? { difficultyScore: input.difficultyScore } : {}),
        ...(typeof input.enabled === "boolean" ? { enabled: input.enabled } : {}),
      },
    });

    if (input.tagNames) {
      const tags = await upsertTags(tx, input.tagNames);
      await tx.questionTag.deleteMany({ where: { questionId: question.id } });
      await tx.questionTag.createMany({
        data: tags.map((tag) => ({
          questionId: question.id,
          tagId: tag.id,
        })),
      });
    }

    return question;
  });
}

export async function listQuestions(query: QuestionQueryInput = {}) {
  return db.question.findMany({
    where: {
      ...(query.bankId ? { bankId: query.bankId } : {}),
      ...(query.enabled === undefined ? {} : { enabled: query.enabled }),
      ...(query.minDifficulty !== undefined || query.maxDifficulty !== undefined
        ? {
            difficultyScore: {
              ...(query.minDifficulty !== undefined ? { gte: query.minDifficulty } : {}),
              ...(query.maxDifficulty !== undefined ? { lte: query.maxDifficulty } : {}),
            },
          }
        : {}),
      ...(query.keyword
        ? {
            OR: [
              { question: { contains: query.keyword, mode: "insensitive" } },
              { answer: { contains: query.keyword, mode: "insensitive" } },
            ],
          }
        : {}),
      ...(query.tag
        ? {
            tags: {
              some: {
                tag: {
                  name: {
                    equals: query.tag,
                    mode: "insensitive",
                  },
                },
              },
            },
          }
        : {}),
    },
    include: {
      tags: {
        include: {
          tag: true,
        },
      },
      bank: true,
    },
    orderBy: { createdAt: "desc" },
  });
}

export async function disableQuestion(questionId: string) {
  return db.question.update({
    where: { id: questionId },
    data: { enabled: false },
  });
}

export async function enableQuestion(questionId: string) {
  return db.question.update({
    where: { id: questionId },
    data: { enabled: true },
  });
}
