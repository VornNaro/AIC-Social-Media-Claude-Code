"use client";

import { TimeAgo } from "@/components/time-ago";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { UserAvatar } from "@/components/user-avatar";
import { useComments } from "@/hooks/use-comments";

export function CommentList({ postId }: { postId: string }) {
  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useComments(postId);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  const comments = data?.pages.flatMap((p) => p.items) ?? [];
  if (comments.length === 0) {
    return <p className="text-sm text-muted-foreground">No comments yet. Be the first!</p>;
  }

  return (
    <div className="space-y-4">
      {comments.map((c) => (
        <div key={c.id} className="flex gap-3">
          <UserAvatar name={c.author.display_name} src={c.author.avatar_url} className="h-8 w-8" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-x-2 text-sm">
              <span className="font-semibold">{c.author.display_name}</span>
              <span className="text-muted-foreground">@{c.author.username}</span>
              <TimeAgo date={c.created_at} className="text-xs text-muted-foreground" />
            </div>
            <p className="whitespace-pre-wrap break-words text-sm">{c.content}</p>
          </div>
        </div>
      ))}
      {hasNextPage && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? "Loading…" : "Load more comments"}
        </Button>
      )}
    </div>
  );
}
