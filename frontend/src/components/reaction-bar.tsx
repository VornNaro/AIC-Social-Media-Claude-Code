"use client";

import { useState } from "react";

import { ThumbsUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useReact } from "@/hooks/use-reactions";
import { REACTION_EMOJI } from "@/lib/reactions";
import { cn } from "@/lib/utils";
import { REACTION_TYPES, type PostOut, type ReactionType } from "@/types/api";

export function ReactionBar({ post }: { post: PostOut }) {
  const react = useReact(post.id);
  const [open, setOpen] = useState(false);

  const total = Object.values(post.reaction_counts).reduce((a, b) => a + b, 0);
  const emojis = REACTION_TYPES.filter((t) => post.reaction_counts[t]).map(
    (t) => REACTION_EMOJI[t],
  );

  function choose(type: ReactionType) {
    react.mutate(type);
    setOpen(false);
  }

  return (
    <div className="flex items-center gap-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          render={
            <Button
              variant={post.my_reaction ? "secondary" : "ghost"}
              size="sm"
              className="gap-1.5"
            />
          }
        >
          {post.my_reaction ? (
            <span>{REACTION_EMOJI[post.my_reaction]}</span>
          ) : (
            <ThumbsUp className="h-4 w-4" />
          )}
          <span>{post.my_reaction ?? "React"}</span>
        </PopoverTrigger>
        <PopoverContent className="flex w-auto gap-1 p-1" align="start">
          {REACTION_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => choose(t)}
              title={t}
              className={cn(
                "rounded-md p-1.5 text-xl transition hover:scale-125",
                post.my_reaction === t && "bg-accent",
              )}
            >
              {REACTION_EMOJI[t]}
            </button>
          ))}
        </PopoverContent>
      </Popover>
      {total > 0 && (
        <span className="text-sm text-muted-foreground">
          {emojis.join("")} {total}
        </span>
      )}
    </div>
  );
}
