import { db } from "@/lib/db";
import { hashPassword, verifyPassword } from "./password";
import { createSession, clearSession } from "./session";
import { devLoginCredentials, isDevLogin } from "./dev-login";

export async function registerUser(input: {
  email: string;
  password: string;
  name?: string;
}) {
  const passwordHash = hashPassword(input.password);
  return db.user.create({
    data: {
      email: input.email.toLowerCase(),
      passwordHash,
      name: input.name,
    },
  });
}

export async function loginUser(input: { email: string; password: string }) {
  const email = input.email.toLowerCase();
  const user = isDevLogin(input)
    ? await db.user.upsert({
        where: { email: devLoginCredentials.email },
        create: {
          email: devLoginCredentials.email,
          passwordHash: hashPassword(devLoginCredentials.password),
          name: devLoginCredentials.name,
        },
        update: {
          passwordHash: hashPassword(devLoginCredentials.password),
          name: devLoginCredentials.name,
        },
      })
    : await db.user.findUnique({
        where: { email },
      });

  if (!user) return null;
  if (!verifyPassword(input.password, user.passwordHash)) return null;

  await createSession(user.id);
  return user;
}

export async function logoutUser() {
  await clearSession();
}
