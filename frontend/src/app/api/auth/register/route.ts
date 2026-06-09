import { NextRequest, NextResponse } from "next/server";

import { API_BASE, setAuthCookies } from "@/lib/auth-cookies";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    return NextResponse.json(
      { detail: data.detail ?? "Registration failed" },
      { status: res.status },
    );
  }

  const response = NextResponse.json({ user: data.user });
  setAuthCookies(response, data.access_token, data.refresh_token);
  return response;
}
