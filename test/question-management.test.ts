import { describe, expect, it } from "vitest";
import { createQuestionBankSchema, createQuestionSchema } from "@/server/schemas/question";
import { normalizeTagNames } from "@/server/questions/tags";

describe("stage 2 question management", () => {
  it("accepts personal and group question bank payloads", () => {
    expect(
      createQuestionBankSchema.safeParse({
        name: "前端题库",
        scope: "PERSONAL",
      }).success,
    ).toBe(true);

    expect(
      createQuestionBankSchema.safeParse({
        name: "小组题库",
        scope: "GROUP",
        groupId: "group_1",
      }).success,
    ).toBe(true);
  });

  it("requires difficulty score and tags for questions", () => {
    expect(
      createQuestionSchema.safeParse({
        bankId: "bank_1",
        question: "什么是闭包？",
        answer: "函数和其词法环境的组合",
        difficultyScore: 72,
        tagNames: ["JavaScript", "闭包"],
      }).success,
    ).toBe(true);
  });

  it("normalizes duplicate and blank tag names", () => {
    expect(normalizeTagNames([" React ", "React", "", "  浏览器  "])).toEqual(["React", "浏览器"]);
  });
});
