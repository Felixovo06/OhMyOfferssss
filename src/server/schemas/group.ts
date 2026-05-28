import { z } from "zod";

export const createGroupSchema = z.object({
  name: z.string().trim().min(2).max(100),
});

export const createInvitationSchema = z.object({
  groupId: z.string().min(1),
  recipientEmail: z.string().email().optional().or(z.literal("")),
});

export const acceptInvitationSchema = z.object({
  token: z.string().min(1),
});

export type CreateGroupInput = z.infer<typeof createGroupSchema>;
export type CreateInvitationInput = z.infer<typeof createInvitationSchema>;
export type AcceptInvitationInput = z.infer<typeof acceptInvitationSchema>;
