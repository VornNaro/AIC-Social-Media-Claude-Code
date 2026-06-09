import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

async function checkApi(): Promise<boolean> {
  const base = process.env.API_INTERNAL_URL ?? "http://localhost:8000/api/v1";
  try {
    const res = await fetch(`${base}/posts?limit=1`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export default async function Home() {
  const apiOk = await checkApi();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">Social Hub</h1>
        <p className="mt-2 text-muted-foreground">
          Frontend scaffold is live (Phase 5).
        </p>
      </div>

      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Setup status</CardTitle>
          <CardDescription>Next.js · Tailwind · shadcn/ui · React Query</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span>Frontend</span>
            <span className="rounded-full bg-green-500/15 px-2 py-0.5 text-green-600 dark:text-green-400">
              running
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Backend API</span>
            {apiOk ? (
              <span className="rounded-full bg-green-500/15 px-2 py-0.5 text-green-600 dark:text-green-400">
                connected
              </span>
            ) : (
              <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-red-600 dark:text-red-400">
                unreachable
              </span>
            )}
          </div>
          <p className="pt-2 text-muted-foreground">
            Auth pages and the feed UI arrive in Phases 6–7.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
