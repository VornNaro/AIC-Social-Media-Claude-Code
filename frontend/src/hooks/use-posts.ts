"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { PostOut } from "@/types/api";

export function usePost(id: string) {
  return useQuery({
    queryKey: ["post", id],
    queryFn: () => api<PostOut>(`/posts/${id}`),
  });
}

export interface CreatePostInput {
  content?: string;
  image_url?: string;
}

export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CreatePostInput) =>
      api<PostOut>("/posts", { method: "POST", body: input }),
    onSuccess: () => {
      // Simple + correct for v1: refetch the feed so the new post appears on top.
      qc.invalidateQueries({ queryKey: ["feed"] });
    },
  });
}
