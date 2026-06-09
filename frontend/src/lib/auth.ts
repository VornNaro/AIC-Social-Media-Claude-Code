import type { UserOut } from "@/types/api";

// Client-side auth actions. These hit the same-origin Next route handlers,
// which manage the httpOnly cookies.

export interface RegisterInput {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}

export async function login(
  username_or_email: string,
  password: string,
): Promise<UserOut> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username_or_email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? "Login failed");
  return data.user as UserOut;
}

export async function register(input: RegisterInput): Promise<UserOut> {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? "Registration failed");
  return data.user as UserOut;
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" }).catch(() => {});
}

// Fetch the current user; on a 401, try one refresh then retry once.
export async function fetchMe(): Promise<UserOut | null> {
  let res = await fetch("/api/auth/me");
  if (res.status === 401) {
    const refreshed = await fetch("/api/auth/refresh", { method: "POST" });
    if (!refreshed.ok) return null;
    res = await fetch("/api/auth/me");
  }
  if (!res.ok) return null;
  return res.json() as Promise<UserOut>;
}
