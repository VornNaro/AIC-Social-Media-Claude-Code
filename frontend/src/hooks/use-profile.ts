"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { UserOut, UserProfile } from "@/types/api";

export function useProfile(username: string) {
  return useQuery({
    queryKey: ["profile", username],
    queryFn: () => api<UserProfile>(`/users/${username}`),
  });
}

export interface ProfileUpdate {
  display_name?: string;
  bio?: string;
  avatar_url?: string;
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ProfileUpdate) =>
      api<UserOut>("/users/me", { method: "PATCH", body: input }),
    onSuccess: (user) => {
      qc.setQueryData(["me"], user);
      qc.invalidateQueries({ queryKey: ["profile", user.username] });
    },
  });
}
