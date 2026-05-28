import { redirect } from "next/navigation";
import { logoutUser } from "@/server/auth/service";

export default async function LogoutPage() {
  await logoutUser();
  redirect("/login");
}
