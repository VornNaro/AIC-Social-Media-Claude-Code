"use client";

import Link from "next/link";

import { MessageCircle, Repeat2 } from "lucide-react";

import { ReactionBar } from "@/components/reaction-bar";
import { TimeAgo } from "@/components/time-ago";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { UserAvatar } from "@/components/user-avatar";
import { useShare } from "@/hooks/use-shares";
import { cn } from "@/lib/utils";
import type { PostOut } from "@/types/api";

export function PostCard({ post }: { post: PostOut }) {
  const share = useShare(post.id);

  return (
    <Card>
      <CardContent>
        {post.shared_by && (
          <p className="mb-2 flex items-center gap-1 text-xs text-muted-foreground">
            <Repeat2 className="h-3.5 w-3.5" /> {post.shared_by.display_name} shared
          </p>
        )}
        <div className="flex gap-3">
          <Link href={`/profile/${post.author.username}`}>
            <UserAvatar
              name={post.author.display_name}
              src={post.author.avatar_url}
              className="h-10 w-10"
            />
          </Link>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-x-2 text-sm">
              <Link
                href={`/profile/${post.author.username}`}
                className="font-semibold hover:underline"
              >
                {post.author.display_name}
              </Link>
              <span className="text-muted-foreground">@{post.author.username}</span>
              <span className="text-muted-foreground">·</span>
              <TimeAgo date={post.created_at} className="text-muted-foreground" />
            </div>

            {post.content && <p className="mt-1 whitespace-pre-wrap break-words">{post.content}</p>}
            {post.image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={post.image_url}
                alt=""
                className="mt-2 max-h-96 w-full rounded-lg border object-cover"
              />
            )}

            <div className="mt-3 flex items-center gap-3">
              <ReactionBar post={post} />
              <Button
                render={<Link href={`/post/${post.id}`} />}
                variant="ghost"
                size="sm"
                className="gap-1.5"
              >
                <MessageCircle className="h-4 w-4" />
                {post.comment_count > 0 && post.comment_count}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className={cn("gap-1.5", post.shared_by_me && "text-green-600")}
                disabled={share.isPending}
                onClick={() => share.mutate(post.shared_by_me)}
              >
                <Repeat2 className="h-4 w-4" />
                {post.share_count > 0 && post.share_count}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
