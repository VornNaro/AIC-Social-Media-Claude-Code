import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Month abbreviation (e.g. "AUG") + day-of-month for a reunion date, in UTC. */
export function reunionDate(iso: string): { mon: string; day: number } {
  const d = new Date(iso)
  return {
    mon: d.toLocaleString("en-US", { month: "short", timeZone: "UTC" }).toUpperCase(),
    day: d.getUTCDate(),
  }
}
