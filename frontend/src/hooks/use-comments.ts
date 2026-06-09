"use client";

import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { patchPost } from "@/lib/post-cache";
import type { CommentOut, CursorPage } from "@/types/api";

export function useComments(postId: string) {
  return useInfiniteQuery({
    queryKey: ["comments", postId],
    queryFn: ({ pageParam }) => {
      const params = new URLSearchParams({ limit: "20" });
      if (pageParam) params.set("cursor", pageParam);
      return api<CursorPage<CommentOut>>(`/posts/${postId}/comments?${params.toString()}`);
    },
    initialPageParam: "",
    getNextPageParam: (last) => (last.has_more ? (last.next_cursor ?? undefined) : undefined),
  });
}

export function useCreateComment(postId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (content: string) =>
      api<CommentOut>(`/posts/${postId}/comments`, { method: "POST", body: { content } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comments", postId] });
      patchPost(qc, postId, (p) => ({ ...p, comment_count: p.comment_count + 1 }));
    },
  });
}
