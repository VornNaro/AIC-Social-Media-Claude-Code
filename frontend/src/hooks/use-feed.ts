"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CursorPage, PostOut } from "@/types/api";

function buildPath(base: string, cursor: string): string {
  const params = new URLSearchParams({ limit: "20" });
  if (cursor) params.set("cursor", cursor);
  return `${base}?${params.toString()}`;
}

// Global feed when no username; a user's authored posts otherwise.
export function useFeed(username?: string) {
  const queryKey = username ? ["feed", { username }] : ["feed"];
  const base = username ? `/users/${username}/posts` : "/posts";

  return useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => api<CursorPage<PostOut>>(buildPath(base, pageParam)),
    initialPageParam: "",
    getNextPageParam: (last) => (last.has_more ? (last.next_cursor ?? undefined) : undefined),
  });
}
