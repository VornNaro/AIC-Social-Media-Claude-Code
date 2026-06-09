"use client";

import { useParams } from "next/navigation";

import { Check, Clock, MapPin, PartyPopper, UserRound } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { UserAvatar } from "@/components/user-avatar";
import { useAttendees, useReunion, useRsvp } from "@/hooks/use-reunions";
import type { RsvpStatus } from "@/types/api";

export default function ReunionPage() {
  const id = useParams<{ id: string }>().id;
  const { data: r, isLoading } = useReunion(id);
  const attendees = useAttendees(id);
  const rsvp = useRsvp(id);

  if (isLoading || !r) return <Skeleton className="h-96 w-full rounded-2xl" />;

  const date = new Date(r.starts_at);
  const mon = date.toLocaleString("en-US", { month: "short", timeZone: "UTC" }).toUpperCase();
  const day = date.getUTCDate();

  function setRsvp(status: RsvpStatus | null) {
    rsvp.mutate(status, {
      onSuccess: () => {
        if (status === "GOING") toast.success("You're going! See you there 🎉");
        else if (status === "MAYBE") toast("Marked as maybe — we'll keep you posted.");
      },
      onError: () => toast.error("Could not update your RSVP."),
    });
  }

  const details = [
    {
      icon: <Clock className="h-4 w-4" />,
      label: "When",
      value: date.toLocaleString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
        timeZone: "UTC",
      }),
    },
    { icon: <MapPin className="h-4 w-4" />, label: "Where", value: r.address ?? r.venue ?? "TBA" },
    { icon: <UserRound className="h-4 w-4" />, label: "Host", value: r.host.display_name },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-6">
        <Card className="overflow-hidden p-0">
          <div className="relative h-64">
            {r.cover_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={r.cover_url} alt="" className="h-full w-full object-cover" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
            <div className="absolute bottom-5 left-5 flex items-end gap-4">
              <div className="overflow-hidden rounded-xl bg-card text-center shadow-md">
                <div className="bg-primary px-4 py-1 text-xs font-extrabold tracking-wider text-primary-foreground">
                  {mon}
                </div>
                <div className="px-4 py-1 text-2xl font-extrabold">{day}</div>
              </div>
              <div className="text-white">
                <h1 className="text-2xl font-extrabold text-white drop-shadow">{r.title}</h1>
                <p className="flex items-center gap-1.5 text-sm font-semibold">
                  <MapPin className="h-4 w-4" />
                  {r.venue}
                  {r.city ? `, ${r.city}` : ""}
                </p>
              </div>
            </div>
          </div>
          <CardContent className="grid gap-4 p-5 sm:grid-cols-3">
            {details.map((d) => (
              <div key={d.label} className="flex items-center gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-accent text-accent-foreground">
                  {d.icon}
                </span>
                <div className="min-w-0">
                  <div className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                    {d.label}
                  </div>
                  <div className="truncate text-sm font-semibold">{d.value}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {r.description && (
          <Card>
            <CardContent className="space-y-4 p-5">
              <h2 className="text-lg font-extrabold">About this reunion</h2>
              <p className="leading-relaxed text-muted-foreground">{r.description}</p>
              {r.amenities.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {r.amenities.map((a) => (
                    <span
                      key={a}
                      className="flex items-center gap-1 rounded-full bg-secondary px-3 py-1 text-sm font-semibold"
                    >
                      <Check className="h-3.5 w-3.5 text-primary" />
                      {a}
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* RSVP sidebar */}
      <div className="space-y-4">
        <Card>
          <CardContent className="space-y-3 p-5">
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-extrabold text-primary">{r.going_count}</span>
              <span className="text-sm text-muted-foreground">classmates going</span>
            </div>
            <Button
              size="lg"
              className="w-full gap-2"
              disabled={rsvp.isPending}
              onClick={() => setRsvp("GOING")}
            >
              {r.my_rsvp === "GOING" ? (
                <>
                  <Check className="h-5 w-5" /> You&apos;re going!
                </>
              ) : (
                <>
                  <PartyPopper className="h-5 w-5" /> Join Reunion
                </>
              )}
            </Button>
            <div className="flex gap-2">
              <Button
                variant={r.my_rsvp === "MAYBE" ? "secondary" : "outline"}
                className="flex-1"
                disabled={rsvp.isPending}
                onClick={() => setRsvp("MAYBE")}
              >
                Maybe
              </Button>
              <Button
                variant="ghost"
                className="flex-1 text-muted-foreground"
                disabled={rsvp.isPending}
                onClick={() => setRsvp(null)}
              >
                Can&apos;t go
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-3 p-5">
            <h2 className="font-extrabold">Who&apos;s coming</h2>
            {attendees.data?.length ? (
              attendees.data.slice(0, 8).map((a) => (
                <div key={a.id} className="flex items-center gap-3">
                  <UserAvatar name={a.display_name} src={a.avatar_url} className="h-9 w-9" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-bold">{a.display_name}</div>
                    {a.graduation_year != null && (
                      <div className="truncate text-xs text-muted-foreground">
                        Class of {a.graduation_year}
                        {a.city ? ` · ${a.city}` : ""}
                      </div>
                    )}
                  </div>
                  <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-semibold text-primary">
                    {a.status === "GOING" ? "Going" : "Maybe"}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">Be the first to RSVP.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
