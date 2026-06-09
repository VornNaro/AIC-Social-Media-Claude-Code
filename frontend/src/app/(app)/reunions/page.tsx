"use client";

import Link from "next/link";

import { MapPin } from "lucide-react";

import { ReunionDateBadge } from "@/components/reunion-date-badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useUpcomingReunions } from "@/hooks/use-reunions";

export default function ReunionsPage() {
  const { data, isLoading } = useUpcomingReunions(20);

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-extrabold">Upcoming Reunions</h1>
      {isLoading ? (
        <Skeleton className="h-40 w-full rounded-2xl" />
      ) : data && data.length > 0 ? (
        data.map((r) => (
          <Link key={r.id} href={`/reunion/${r.id}`}>
            <Card className="overflow-hidden p-0 transition-shadow hover:shadow-md">
              <div className="flex">
                {r.cover_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={r.cover_url} alt="" className="h-28 w-28 shrink-0 object-cover" />
                )}
                <CardContent className="flex items-center gap-4 p-4">
                  <ReunionDateBadge startsAt={r.starts_at} />
                  <div className="min-w-0">
                    <div className="font-extrabold">{r.title}</div>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <MapPin className="h-3.5 w-3.5" />
                      {r.venue ?? r.city} · {r.going_count} going
                    </div>
                  </div>
                </CardContent>
              </div>
            </Card>
          </Link>
        ))
      ) : (
        <p className="py-10 text-center text-muted-foreground">No reunions planned yet.</p>
      )}
    </div>
  );
}
