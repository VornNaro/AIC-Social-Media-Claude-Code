"use client";

import { useEffect, useState } from "react";

import { formatDistanceToNow } from "date-fns";

// Renders relative time on the client only, avoiding server/client hydration drift.
// Setting state in the effect is intentional here: the server renders an empty
// string (stable HTML), and the relative time is filled in after mount.
export function TimeAgo({ date, className }: { date: string; className?: string }) {
  const [text, setText] = useState("");
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setText(formatDistanceToNow(new Date(date), { addSuffix: true }));
  }, [date]);
  return (
    <time dateTime={date} className={className} suppressHydrationWarning>
      {text}
    </time>
  );
}
