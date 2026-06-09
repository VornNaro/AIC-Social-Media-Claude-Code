import { NextRequest, NextResponse } from "next/server";

import { API_BASE } from "@/lib/auth-cookies";

export async function GET(req: NextRequest) {
  const accessToken = req.cookies.get("access_token")?.value;
  if (!accessToken) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
