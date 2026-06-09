"use client";

import { useEffect, useState } from "react";

import { formatDistanceToNow } from "date-fns";

// Renders relative time on the client only, avoiding server/client hydration drift.
export function TimeAgo({ date, className }: { date: string; className?: string }) {
  const [text, setText] = useState("");
  useEffect(() => {
    setText(formatDistanceToNow(new Date(date), { addSuffix: true }));
  }, [date]);
  return (
    <time dateTime={date} className={className} suppressHydrationWarning>
      {text}
    </time>
  );
}
