"use client";

import Link from "next/link";

import { Check, MapPin, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { UserAvatar } from "@/components/user-avatar";
import { useConnect } from "@/hooks/use-connections";
import type { ClassmateOut } from "@/types/api";

const STATE_LABEL: Record<string, string> = {
  connected: "Connected",
  pending_outgoing: "Request sent",
  pending_incoming: "Respond",
};

export function ClassmateCard({ person }: { person: ClassmateOut }) {
  const connect = useConnect();
  const settled = person.connection_state !== "none";

  return (
    <Card className="text-center">
      <CardContent className="flex flex-col items-center gap-1 p-5">
        <Link href={`/profile/${person.username}`}>
          <UserAvatar
            name={person.display_name}
            src={person.avatar_url}
            className="h-16 w-16"
          />
        </Link>
        <Link href={`/profile/${person.username}`} className="mt-2 font-bold hover:underline">
          {person.display_name}
        </Link>
        {person.graduation_year != null && (
          <p className="text-sm text-muted-foreground">Class of {person.graduation_year}</p>
        )}
        {person.city && (
          <p className="flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3" />
            {person.city}
          </p>
        )}
        <div className="mt-3">
          {settled ? (
            <Button variant="secondary" size="sm" disabled className="gap-1">
              <Check className="h-4 w-4" />
              {STATE_LABEL[person.connection_state]}
            </Button>
          ) : (
            <Button
              size="sm"
              className="gap-1.5 bg-brand-blue text-brand-blue-foreground hover:bg-brand-blue/90"
              disabled={connect.isPending}
              onClick={() => connect.mutate(person.id)}
            >
              <UserPlus className="h-4 w-4" /> Connect
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
