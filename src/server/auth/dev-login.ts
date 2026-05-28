export const devLoginEnabled = process.env.NODE_ENV !== "production";

export const devLoginCredentials = {
  email: "test@ohmyoffer.dev",
  password: "test123456",
  name: "测试用户",
};

export function isDevLogin(input: { email: string; password: string }) {
  return (
    devLoginEnabled &&
    input.email.toLowerCase() === devLoginCredentials.email &&
    input.password === devLoginCredentials.password
  );
}
