"use client";

import Link from "next/link";

import { CalendarDays, Check, MapPin, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { UserAvatar } from "@/components/user-avatar";
import { useConnect, useSuggestions } from "@/hooks/use-connections";
import { useUpcomingReunions } from "@/hooks/use-reunions";
import type { ClassmateOut } from "@/types/api";

function monthDay(iso: string): { mon: string; day: string } {
  const d = new Date(iso);
  return {
    mon: d.toLocaleString("en-US", { month: "short", timeZone: "UTC" }).toUpperCase(),
    day: String(d.getUTCDate()),
  };
}

function SuggestionRow({ s }: { s: ClassmateOut }) {
  const connect = useConnect();
  const pending = s.connection_state === "pending_outgoing";
  return (
    <div className="flex items-center gap-3">
      <Link href={`/profile/${s.username}`}>
        <UserAvatar name={s.display_name} src={s.avatar_url} className="h-10 w-10" />
      </Link>
      <div className="min-w-0 flex-1">
        <Link href={`/profile/${s.username}`} className="block truncate text-sm font-bold hover:underline">
          {s.display_name}
        </Link>
        <p className="truncate text-xs text-muted-foreground">
          {s.graduation_year ? `Class of ${s.graduation_year}` : "Classmate"}
          {s.mutual_count > 0 && ` · ${s.mutual_count} mutual`}
        </p>
      </div>
      {pending ? (
        <Button variant="secondary" size="sm" disabled className="gap-1">
          <Check className="h-4 w-4" /> Sent
        </Button>
      ) : (
        <Button
          size="icon"
          variant="outline"
          aria-label={`Connect with ${s.display_name}`}
          disabled={connect.isPending}
          onClick={() => connect.mutate(s.id)}
        >
          <UserPlus className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

export function FeedRail() {
  const suggestions = useSuggestions(5);
  const reunions = useUpcomingReunions(4);

  return (
    <aside className="hidden w-72 shrink-0 space-y-4 lg:block">
      <Card>
        <CardContent className="space-y-4 p-5">
          <h2 className="text-base font-extrabold">People you may know</h2>
          {suggestions.data?.length ? (
            suggestions.data.map((s) => <SuggestionRow key={s.id} s={s} />)
          ) : (
            <p className="text-sm text-muted-foreground">No suggestions right now.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-3 p-5">
          <h2 className="text-base font-extrabold">Upcoming reunions</h2>
          {reunions.data?.length ? (
            reunions.data.map((r) => {
              const { mon, day } = monthDay(r.starts_at);
              return (
                <Link
                  key={r.id}
                  href={`/reunion/${r.id}`}
                  className="flex items-center gap-3 rounded-xl border p-2.5 transition-colors hover:bg-accent"
                >
                  <div className="w-12 shrink-0 rounded-lg bg-primary/15 py-1.5 text-center">
                    <div className="text-[10px] font-extrabold tracking-wider text-primary">
                      {mon}
                    </div>
                    <div className="text-lg font-extrabold leading-none">{day}</div>
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-bold">{r.title}</div>
                    <div className="flex items-center gap-1 truncate text-xs text-muted-foreground">
                      <MapPin className="h-3 w-3" />
                      {r.venue ?? r.city} · {r.going_count} going
                    </div>
                  </div>
                </Link>
              );
            })
          ) : (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" /> No reunions yet.
            </p>
          )}
        </CardContent>
      </Card>
    </aside>
  );
}
