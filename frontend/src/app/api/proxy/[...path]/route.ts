import { NextRequest, NextResponse } from "next/server";

import { API_BASE } from "@/lib/auth-cookies";

// Forwards browser data requests to FastAPI, attaching the httpOnly access
// cookie as a Bearer header. Keeps tokens out of client JS entirely.
async function handler(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  const accessToken = req.cookies.get("access_token")?.value;

  const url = `${API_BASE}/${path.join("/")}${req.nextUrl.search}`;
  const headers: Record<string, string> = {};
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  let body: string | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    headers["Content-Type"] = "application/json";
    body = await req.text();
  }

  const res = await fetch(url, { method: req.method, headers, body });
  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
  });
}

export {
  handler as GET,
  handler as POST,
  handler as PATCH,
  handler as PUT,
  handler as DELETE,
};
