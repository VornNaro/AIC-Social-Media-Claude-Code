import type { NextResponse } from "next/server";

// Server-only helpers for the httpOnly auth cookies.
// FastAPI is a pure Bearer API; these cookies live only between the browser and
// the Next.js route handlers.

const isProd = process.env.NODE_ENV === "production";

// The access cookie is a *presence marker* for middleware (its JWT is only valid
// ~15 min; the client refresh flow renews it). The refresh cookie is scoped to
// /api/auth so it is never sent on normal/proxy requests.
const ACCESS_MAX_AGE = 7 * 24 * 60 * 60;
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60;

export const API_BASE = process.env.API_INTERNAL_URL ?? "http://localhost:8000/api/v1";

export function setAuthCookies(res: NextResponse, access: string, refresh: string): void {
  res.cookies.set("access_token", access, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: ACCESS_MAX_AGE,
    secure: isProd,
  });
  res.cookies.set("refresh_token", refresh, {
    httpOnly: true,
    sameSite: "lax",
    path: "/api/auth",
    maxAge: REFRESH_MAX_AGE,
    secure: isProd,
  });
}

export function clearAuthCookies(res: NextResponse): void {
  res.cookies.set("access_token", "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
    secure: isProd,
  });
  res.cookies.set("refresh_token", "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/api/auth",
    maxAge: 0,
    secure: isProd,
  });
}
