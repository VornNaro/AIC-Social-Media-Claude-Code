"use client";

import Link from "next/link";

import { Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { UserAvatar } from "@/components/user-avatar";
import { useAuth } from "@/hooks/use-auth";
import { useConnections } from "@/hooks/use-connections";
import { useProfile } from "@/hooks/use-profile";

export function ProfileClassmates({ username }: { username: string }) {
  const { data: profile } = useProfile(username);
  const { data: me } = useAuth();
  const isMe = me?.username === username;
  // Only the signed-in user's own connections are listable via the API.
  const { data: connections } = useConnections();

  if (isMe) {
    const list = connections ?? [];
    return (
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-extrabold">Classmates</h2>
            {profile?.school && (
              <Link
                href={`/school/${profile.school.slug}`}
                className="text-sm font-semibold text-brand-blue hover:underline"
              >
                See all
              </Link>
            )}
          </div>
          {list.length > 0 ? (
            <div className="grid grid-cols-4 gap-3">
              {list.slice(0, 8).map((c) => (
                <Link key={c.id} href={`/profile/${c.username}`} className="text-center">
                  <UserAvatar
                    name={c.display_name}
                    src={c.avatar_url}
                    className="mx-auto h-12 w-12"
                  />
                  <div className="mt-1 truncate text-xs font-semibold">
                    {c.display_name.split(" ")[0]}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No classmates yet — find your old crowd in your school group.
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  // Viewing someone else's profile: point to their school community.
  if (!profile?.school) return null;
  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <h2 className="text-base font-extrabold">School community</h2>
        <p className="text-sm text-muted-foreground">
          {profile.display_name.split(" ")[0]} is part of{" "}
          <span className="font-semibold text-foreground">{profile.school.name}</span>.
        </p>
        <Button
          variant="outline"
          className="w-full gap-1.5"
          render={<Link href={`/school/${profile.school.slug}`} />}
          nativeButton={false}
        >
          <Users className="h-4 w-4" /> See classmates
        </Button>
      </CardContent>
    </Card>
  );
}
