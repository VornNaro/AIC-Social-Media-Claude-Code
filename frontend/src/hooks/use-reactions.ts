"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import {
  applyReactionToggle,
  patchPost,
  restorePostCaches,
  snapshotPostCaches,
} from "@/lib/post-cache";
import type { ReactionState, ReactionType } from "@/types/api";

// Canonical optimistic-update hook. Copy this pattern for other mutations:
// onMutate: cancel + snapshot + patch · onError: restore · onSuccess: authoritative.
export function useReact(postId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (type: ReactionType) =>
      api<ReactionState>(`/posts/${postId}/reactions`, { method: "PUT", body: { type } }),
    onMutate: async (type) => {
      await qc.cancelQueries({ queryKey: ["feed"] });
      await qc.cancelQueries({ queryKey: ["post", postId] });
      const snapshot = snapshotPostCaches(qc, postId);
      patchPost(qc, postId, (p) => applyReactionToggle(p, type));
      return { snapshot };
    },
    onError: (_err, _type, ctx) => {
      if (ctx?.snapshot) restorePostCaches(qc, postId, ctx.snapshot);
    },
    onSuccess: (state) => {
      patchPost(qc, postId, (p) => ({
        ...p,
        my_reaction: state.my_reaction,
        reaction_counts: state.reaction_counts,
      }));
    },
  });
}
