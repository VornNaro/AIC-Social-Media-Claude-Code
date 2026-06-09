"use client";

import { useParams } from "next/navigation";

import { CommentForm } from "@/components/comment-form";
import { CommentList } from "@/components/comment-list";
import { PostCard } from "@/components/post-card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { usePost } from "@/hooks/use-posts";

export default function PostPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { data: post, isLoading } = usePost(id);

  return (
    <div className="space-y-4">
      {isLoading || !post ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : (
        <PostCard post={post} />
      )}

      <div className="space-y-4 rounded-xl border p-4">
        <h2 className="font-semibold">Comments</h2>
        <CommentForm postId={id} />
        <Separator />
        <CommentList postId={id} />
      </div>
    </div>
  );
}
