import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PREFIXES = ["/feed", "/profile", "/post"];
const AUTH_PAGES = ["/login", "/register"];

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  // Presence check only — real validation happens at the API. The refresh cookie
  // is path-scoped to /api/auth, so here we look at the access cookie.
  const hasSession = req.cookies.has("access_token");

  const isProtected = PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );

  if (isProtected && !hasSession) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  if (AUTH_PAGES.includes(pathname) && hasSession) {
    const url = req.nextUrl.clone();
    url.pathname = "/feed";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/feed/:path*", "/profile/:path*", "/post/:path*", "/login", "/register"],
};
