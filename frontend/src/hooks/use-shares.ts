"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { patchPost, restorePostCaches, snapshotPostCaches } from "@/lib/post-cache";
import type { ShareState } from "@/types/api";

export function useShare(postId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (shared: boolean) =>
      api<ShareState>(`/posts/${postId}/shares`, { method: shared ? "DELETE" : "POST" }),
    onMutate: async (shared) => {
      await qc.cancelQueries({ queryKey: ["feed"] });
      await qc.cancelQueries({ queryKey: ["post", postId] });
      const snapshot = snapshotPostCaches(qc, postId);
      patchPost(qc, postId, (p) => ({
        ...p,
        shared_by_me: !shared,
        share_count: shared ? Math.max(0, p.share_count - 1) : p.share_count + 1,
      }));
      return { snapshot };
    },
    onError: (_err, _v, ctx) => {
      if (ctx?.snapshot) restorePostCaches(qc, postId, ctx.snapshot);
    },
    onSuccess: (state) => {
      patchPost(qc, postId, (p) => ({
        ...p,
        shared_by_me: state.shared_by_me,
        share_count: state.share_count,
      }));
    },
  });
}
