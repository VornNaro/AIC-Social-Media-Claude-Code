"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AttendeeOut, ReunionOut, RsvpStatus } from "@/types/api";

export function useUpcomingReunions(limit = 5) {
  return useQuery({
    queryKey: ["reunions", { limit }],
    queryFn: () => api<ReunionOut[]>(`/reunions?limit=${limit}`),
  });
}

export function useReunion(id: string) {
  return useQuery({
    queryKey: ["reunion", id],
    queryFn: () => api<ReunionOut>(`/reunions/${id}`),
    enabled: !!id,
  });
}

export function useAttendees(id: string) {
  return useQuery({
    queryKey: ["reunion-attendees", id],
    queryFn: () => api<AttendeeOut[]>(`/reunions/${id}/attendees`),
    enabled: !!id,
  });
}

export function useRsvp(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (status: RsvpStatus | null) =>
      status === null
        ? api<ReunionOut>(`/reunions/${id}/rsvp`, { method: "DELETE" })
        : api<ReunionOut>(`/reunions/${id}/rsvp`, { method: "PUT", body: { status } }),
    onSuccess: (data) => {
      qc.setQueryData(["reunion", id], data);
      qc.invalidateQueries({ queryKey: ["reunion-attendees", id] });
      qc.invalidateQueries({ queryKey: ["reunions"] });
    },
  });
}
