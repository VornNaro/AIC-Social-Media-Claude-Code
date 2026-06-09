// Central browser-side API wrapper. All component/hook data access goes through
// here. Requests hit the same-origin Next proxy (`/api/proxy/...`), which attaches
// the httpOnly access-token cookie as a Bearer header. On 401 we try a single
// refresh, then retry once; if that fails the user is sent to /login.
//
// The `/api/proxy` and `/api/auth/refresh` route handlers are added in Phase 6.

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

interface ApiOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

async function rawRequest<T>(path: string, opts: ApiOptions): Promise<Response> {
  return fetch(`/api/proxy${path}`, {
    method: opts.method ?? "GET",
    headers: { "Content-Type": "application/json" },
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    credentials: "include",
    signal: opts.signal,
  });
}

async function refresh(): Promise<boolean> {
  const res = await fetch("/api/auth/refresh", {
    method: "POST",
    credentials: "include",
  });
  return res.ok;
}

export async function api<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  let res = await rawRequest<T>(path, opts);

  if (res.status === 401) {
    if (await refresh()) {
      res = await rawRequest<T>(path, opts);
    }
    if (res.status === 401) {
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new ApiError(401, "Not authenticated");
    }
  }

  if (res.status === 204) {
    return undefined as T;
  }

  if (!res.ok) {
    const detail = await res
      .json()
      .then((b) => b?.detail ?? res.statusText)
      .catch(() => res.statusText);
    throw new ApiError(res.status, typeof detail === "string" ? detail : "Request failed");
  }

  return res.json() as Promise<T>;
}
