"use client";

import { useRouter } from "next/navigation";

import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { logout } from "@/lib/auth";

export default function FeedPage() {
  const { data: user, isLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  async function onLogout() {
    await logout();
    queryClient.setQueryData(["me"], null);
    queryClient.clear();
    router.push("/login");
  }

  return (
    <main className="mx-auto max-w-xl px-4 py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Feed</h1>
        <Button variant="outline" onClick={onLogout}>
          Log out
        </Button>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>You&apos;re signed in</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-5 w-48" />
          ) : user ? (
            <p>
              Welcome, <strong>{user.display_name}</strong> (@{user.username}). The feed
              UI arrives in Phase 7.
            </p>
          ) : (
            <p className="text-muted-foreground">Not signed in.</p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
