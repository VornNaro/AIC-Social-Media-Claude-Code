import { NextRequest, NextResponse } from "next/server";

import { API_BASE, clearAuthCookies } from "@/lib/auth-cookies";

export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get("refresh_token")?.value;
  if (refreshToken) {
    // Best-effort revoke on the backend; ignore failures.
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => {});
  }
  const response = NextResponse.json({ ok: true });
  clearAuthCookies(response);
  return response;
}
