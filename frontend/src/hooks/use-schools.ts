"use client";

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  ClassmateOut,
  CursorPage,
  PostOut,
  ReunionOut,
  SchoolOut,
} from "@/types/api";

export function useSchool(slug: string) {
  return useQuery({
    queryKey: ["school", slug],
    queryFn: () => api<SchoolOut>(`/schools/${slug}`),
    enabled: !!slug,
  });
}

export function useSchoolMembers(slug: string, year?: number | "all", q?: string) {
  return useQuery({
    queryKey: ["school-members", slug, year ?? "all", q ?? ""],
    queryFn: () => {
      const params = new URLSearchParams();
      if (year && year !== "all") params.set("year", String(year));
      if (q) params.set("q", q);
      const qs = params.toString();
      return api<ClassmateOut[]>(`/schools/${slug}/members${qs ? `?${qs}` : ""}`);
    },
    enabled: !!slug,
  });
}

export function useSchoolReunions(slug: string) {
  return useQuery({
    queryKey: ["school-reunions", slug],
    queryFn: () => api<ReunionOut[]>(`/schools/${slug}/reunions`),
    enabled: !!slug,
  });
}

export function useSchoolPosts(slug: string) {
  return useInfiniteQuery({
    queryKey: ["school-posts", slug],
    queryFn: ({ pageParam }) => {
      const params = new URLSearchParams();
      if (pageParam) params.set("cursor", pageParam as string);
      const qs = params.toString();
      return api<CursorPage<PostOut>>(`/schools/${slug}/posts${qs ? `?${qs}` : ""}`);
    },
    initialPageParam: "",
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    enabled: !!slug,
  });
}

export function useJoinSchool(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (join: boolean) =>
      api<SchoolOut>(`/schools/${slug}/join`, { method: join ? "POST" : "DELETE" }),
    onSuccess: (data) => {
      qc.setQueryData(["school", slug], data);
    },
  });
}
