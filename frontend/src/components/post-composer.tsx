"use client";

import { useState } from "react";

import { ImageIcon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { UserAvatar } from "@/components/user-avatar";
import { useAuth } from "@/hooks/use-auth";
import { useCreatePost } from "@/hooks/use-posts";

export function PostComposer() {
  const { data: user } = useAuth();
  const createPost = useCreatePost();
  const [content, setContent] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [showImage, setShowImage] = useState(false);

  async function submit() {
    const body = {
      content: content.trim() || undefined,
      image_url: imageUrl.trim() || undefined,
    };
    if (!body.content && !body.image_url) {
      toast.error("Write something or add an image.");
      return;
    }
    try {
      await createPost.mutateAsync(body);
      setContent("");
      setImageUrl("");
      setShowImage(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to post");
    }
  }

  return (
    <Card>
      <CardContent>
        <div className="flex gap-3">
          {user && (
            <UserAvatar name={user.display_name} src={user.avatar_url} className="h-10 w-10" />
          )}
          <div className="flex-1 space-y-2">
            <Textarea
              placeholder="What's happening?"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={3}
            />
            {showImage && (
              <Input
                placeholder="Image URL (https://…)"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
              />
            )}
            <div className="flex items-center justify-between">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowImage((s) => !s)}
              >
                <ImageIcon className="mr-2 h-4 w-4" />
                Image
              </Button>
              <Button onClick={submit} disabled={createPost.isPending}>
                {createPost.isPending ? "Posting…" : "Post"}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
