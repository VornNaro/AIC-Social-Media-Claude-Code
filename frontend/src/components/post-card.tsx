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
  const year = post.author.graduation_year;

  return (
    <Card className="overflow-hidden p-0">
      <CardContent className="p-5">
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
              className="h-11 w-11"
            />
          </Link>
          <div className="min-w-0 flex-1">
            <Link
              href={`/profile/${post.author.username}`}
              className="font-bold hover:underline"
            >
              {post.author.display_name}
            </Link>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              {year != null && (
                <span className="rounded-full bg-accent px-2 py-0.5 font-semibold text-accent-foreground">
                  Class of {year}
                </span>
              )}
              <TimeAgo date={post.created_at} />
            </div>
          </div>
        </div>

        {post.content && (
          <p className="mt-3 whitespace-pre-wrap break-words text-[15px] leading-relaxed">
            {post.content}
          </p>
        )}

        {post.tags?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {post.tags.map((t) => (
              <span key={t} className="text-sm font-semibold text-brand-blue">
                {t.startsWith("#") ? t : `#${t}`}
              </span>
            ))}
          </div>
        )}
      </CardContent>

      {post.image_url && (
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={post.image_url} alt="" className="max-h-[460px] w-full object-cover" />
          {post.note && (
            <div className="polaroid absolute bottom-4 right-4 w-36 -rotate-3 px-2 pt-2">
              <div className="polaroid__cap px-1 pb-2 pt-1.5 text-lg leading-tight">
                {post.note}
              </div>
            </div>
          )}
        </div>
      )}

      <CardContent className="flex items-center gap-2 p-3">
        <ReactionBar post={post} />
        <Button
          render={<Link href={`/post/${post.id}`} />}
          variant="ghost"
          size="sm"
          className="flex-1 gap-1.5"
        >
          <MessageCircle className="h-4 w-4" />
          {post.comment_count > 0 ? post.comment_count : "Comment"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={cn("flex-1 gap-1.5", post.shared_by_me && "text-brand-blue")}
          disabled={share.isPending}
          onClick={() => share.mutate(post.shared_by_me)}
        >
          <Repeat2 className="h-4 w-4" />
          {post.share_count > 0 ? post.share_count : "Share"}
        </Button>
      </CardContent>
    </Card>
  );
}
