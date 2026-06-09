"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchMe } from "@/lib/auth";

export function useAuth() {
  return useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
    staleTime: 60_000,
    retry: false,
  });
}
