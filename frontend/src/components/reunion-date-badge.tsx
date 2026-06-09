import { cn, reunionDate } from "@/lib/utils";

/** The small coral month/day chip used in reunion lists and the feed rail. */
export function ReunionDateBadge({
  startsAt,
  className,
}: {
  startsAt: string;
  className?: string;
}) {
  const { mon, day } = reunionDate(startsAt);
  return (
    <div
      className={cn(
        "w-12 shrink-0 rounded-lg bg-primary/15 py-1.5 text-center",
        className,
      )}
    >
      <div className="text-[10px] font-extrabold tracking-wider text-primary">{mon}</div>
      <div className="text-lg font-extrabold leading-none">{day}</div>
    </div>
  );
}
