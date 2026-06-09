import { NextRequest, NextResponse } from "next/server";

import { API_BASE, clearAuthCookies, setAuthCookies } from "@/lib/auth-cookies";

export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get("refresh_token")?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: "No refresh token" }, { status: 401 });
  }

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const response = NextResponse.json({ detail: "Session expired" }, { status: 401 });
    clearAuthCookies(response);
    return response;
  }

  const response = NextResponse.json({ ok: true });
  setAuthCookies(response, data.access_token, data.refresh_token);
  return response;
}
