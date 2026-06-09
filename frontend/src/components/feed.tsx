"use client";

import { useEffect, useRef } from "react";

import { PostCard } from "@/components/post-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useFeed } from "@/hooks/use-feed";

export function Feed({ username }: { username?: string }) {
  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useFeed(username);
  const sentinel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = sentinel.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-40 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  const posts = data?.pages.flatMap((p) => p.items) ?? [];
  if (posts.length === 0) {
    return (
      <p className="py-10 text-center text-muted-foreground">
        No posts yet. Be the first to share your vibe!
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {posts.map((post, i) => (
        <PostCard key={`${post.id}-${post.shared_by?.username ?? "orig"}-${i}`} post={post} />
      ))}
      <div ref={sentinel} aria-hidden />
      {isFetchingNextPage && <Skeleton className="h-40 w-full rounded-xl" />}
    </div>
  );
}
