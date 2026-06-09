"use client";

import Link from "next/link";

import { Briefcase, GraduationCap, MapPin } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProfile } from "@/hooks/use-profile";

export function ProfileAbout({ username }: { username: string }) {
  const { data: p, isLoading } = useProfile(username);
  if (isLoading || !p) return <Skeleton className="h-48 w-full rounded-2xl" />;

  const hasDetails =
    p.bio || p.school || p.graduation_year != null || p.city || p.role || p.interests.length > 0;
  if (!hasDetails) return null;

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <h2 className="text-base font-extrabold">About me</h2>
        {p.bio && (
          <p className="whitespace-pre-wrap break-words leading-relaxed text-muted-foreground">
            {p.bio}
          </p>
        )}

        <div className="space-y-2.5 text-sm">
          {(p.school || p.graduation_year != null) && (
            <div className="flex items-center gap-2.5">
              <GraduationCap className="h-4 w-4 shrink-0 text-brand-blue" />
              <span>
                {p.school ? (
                  <Link href={`/school/${p.school.slug}`} className="font-semibold hover:underline">
                    {p.school.name}
                  </Link>
                ) : (
                  "School"
                )}
                {p.graduation_year != null && (
                  <span className="text-muted-foreground"> · Class of {p.graduation_year}</span>
                )}
              </span>
            </div>
          )}
          {p.city && (
            <div className="flex items-center gap-2.5">
              <MapPin className="h-4 w-4 shrink-0 text-brand-blue" />
              <span>Lives in {p.city}</span>
            </div>
          )}
          {p.role && (
            <div className="flex items-center gap-2.5">
              <Briefcase className="h-4 w-4 shrink-0 text-brand-blue" />
              <span>{p.role}</span>
            </div>
          )}
        </div>

        {p.interests.length > 0 && (
          <div className="flex flex-wrap gap-2 border-t pt-4">
            {p.interests.map((t) => (
              <span
                key={t}
                className="rounded-full bg-secondary px-3 py-1 text-sm font-semibold text-secondary-foreground"
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
