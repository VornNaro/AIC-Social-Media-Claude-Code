"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { CalendarDays, Check, MapPin, Plus, Users } from "lucide-react";

import { ClassmateCard } from "@/components/classmate-card";
import { PostCard } from "@/components/post-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useJoinSchool,
  useSchool,
  useSchoolMembers,
  useSchoolPosts,
  useSchoolReunions,
} from "@/hooks/use-schools";

export default function SchoolPage() {
  const slug = useParams<{ slug: string }>().slug;
  const { data: school, isLoading } = useSchool(slug);
  const join = useJoinSchool(slug);

  if (isLoading || !school) {
    return <Skeleton className="h-72 w-full rounded-2xl" />;
  }

  return (
    <div className="space-y-6">
      {/* cover + header band */}
      <Card className="overflow-hidden p-0">
        <div className="relative h-44 sm:h-56">
          {school.cover_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={school.cover_url} alt="" className="h-full w-full object-cover" />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/55 to-transparent" />
        </div>
        <CardContent className="flex flex-wrap items-end justify-between gap-4 p-5">
          <div>
            <h1 className="text-2xl font-extrabold">{school.name}</h1>
            <div className="mt-1 flex flex-wrap gap-4 text-sm text-muted-foreground">
              {school.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4" />
                  {school.location}
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <Users className="h-4 w-4" />
                {school.member_count.toLocaleString()} members
              </span>
              {school.founded && (
                <span className="flex items-center gap-1.5">
                  <CalendarDays className="h-4 w-4" />
                  Est. {school.founded}
                </span>
              )}
            </div>
            {school.motto && (
              <p className="font-hand mt-1 text-lg text-brand-blue">{school.motto}</p>
            )}
          </div>
          <Button
            variant={school.is_member ? "secondary" : "default"}
            className="gap-1.5"
            disabled={join.isPending}
            onClick={() => join.mutate(!school.is_member)}
          >
            {school.is_member ? (
              <>
                <Check className="h-4 w-4" /> Joined
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" /> Join school
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="memories">
        <TabsList>
          <TabsTrigger value="memories">Memories</TabsTrigger>
          <TabsTrigger value="classmates">Classmates</TabsTrigger>
          <TabsTrigger value="reunions">Reunions</TabsTrigger>
        </TabsList>

        <TabsContent value="memories" className="mt-4">
          <MemoriesTab slug={slug} />
        </TabsContent>
        <TabsContent value="classmates" className="mt-4">
          <ClassmatesTab slug={slug} />
        </TabsContent>
        <TabsContent value="reunions" className="mt-4">
          <ReunionsTab slug={slug} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MemoriesTab({ slug }: { slug: string }) {
  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useSchoolPosts(slug);
  if (isLoading) return <Skeleton className="h-40 w-full rounded-2xl" />;
  const posts = data?.pages.flatMap((p) => p.items) ?? [];
  if (posts.length === 0)
    return <p className="py-10 text-center text-muted-foreground">No memories shared yet.</p>;
  return (
    <div className="mx-auto max-w-xl space-y-4">
      {posts.map((p) => (
        <PostCard key={p.id} post={p} />
      ))}
      {hasNextPage && (
        <Button
          variant="ghost"
          className="w-full"
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? "Loading…" : "Load more"}
        </Button>
      )}
    </div>
  );
}

const YEARS: (number | "all")[] = ["all", 2013, 2012, 2011, 2010, 2009];

function ClassmatesTab({ slug }: { slug: string }) {
  const [year, setYear] = useState<number | "all">("all");
  const [q, setQ] = useState("");
  const { data, isLoading } = useSchoolMembers(slug, year, q || undefined);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder="Search classmates by name or city…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-xs"
        />
        <div className="flex flex-wrap gap-2">
          {YEARS.map((y) => (
            <button
              key={y}
              onClick={() => setYear(y)}
              className={`rounded-full px-3 py-1 text-sm font-semibold transition-colors ${
                year === y
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-accent"
              }`}
            >
              {y === "all" ? "All years" : `Class of ${y}`}
            </button>
          ))}
        </div>
      </div>
      {isLoading ? (
        <Skeleton className="h-40 w-full rounded-2xl" />
      ) : data && data.length > 0 ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {data.map((p) => (
            <ClassmateCard key={p.id} person={p} />
          ))}
        </div>
      ) : (
        <p className="py-10 text-center text-muted-foreground">No classmates found.</p>
      )}
    </div>
  );
}

function ReunionsTab({ slug }: { slug: string }) {
  const { data, isLoading } = useSchoolReunions(slug);
  if (isLoading) return <Skeleton className="h-40 w-full rounded-2xl" />;
  if (!data || data.length === 0)
    return <p className="py-10 text-center text-muted-foreground">No reunions planned yet.</p>;
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {data.map((r) => (
        <Link key={r.id} href={`/reunion/${r.id}`}>
          <Card className="overflow-hidden p-0 transition-shadow hover:shadow-md">
            {r.cover_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={r.cover_url} alt="" className="h-32 w-full object-cover" />
            )}
            <CardContent className="p-4">
              <div className="font-extrabold">{r.title}</div>
              <div className="text-sm text-muted-foreground">
                {new Date(r.starts_at).toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                  timeZone: "UTC",
                })}
              </div>
              <div className="mt-2 text-xs text-muted-foreground">
                {r.going_count} going · {r.venue}
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
