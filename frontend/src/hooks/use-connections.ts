"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ClassmateOut } from "@/types/api";

export function useSuggestions(limit = 5) {
  return useQuery({
    queryKey: ["connection-suggestions", { limit }],
    queryFn: () => api<ClassmateOut[]>(`/connections/suggestions?limit=${limit}`),
  });
}

export function useConnections() {
  return useQuery({
    queryKey: ["connections"],
    queryFn: () => api<ClassmateOut[]>("/connections"),
  });
}

/** Send a connection request to another user. Invalidates lists that show state. */
export function useConnect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      api("/connections", { method: "POST", body: { user_id: userId } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["connection-suggestions"] });
      qc.invalidateQueries({ queryKey: ["school-members"] });
      qc.invalidateQueries({ queryKey: ["connections"] });
    },
  });
}
