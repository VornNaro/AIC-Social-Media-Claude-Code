"use client";

import { useState } from "react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useCreateComment } from "@/hooks/use-comments";

export function CommentForm({ postId }: { postId: string }) {
  const createComment = useCreateComment(postId);
  const [content, setContent] = useState("");

  async function submit() {
    const value = content.trim();
    if (!value) return;
    try {
      await createComment.mutateAsync(value);
      setContent("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to comment");
    }
  }

  return (
    <div className="space-y-2">
      <Textarea
        placeholder="Write a comment…"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={2}
      />
      <div className="flex justify-end">
        <Button size="sm" onClick={submit} disabled={createComment.isPending || !content.trim()}>
          {createComment.isPending ? "Posting…" : "Comment"}
        </Button>
      </div>
    </div>
  );
}
