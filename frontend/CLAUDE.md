# Frontend (Next.js) — Agent Guide

Next.js App Router + TypeScript + Tailwind + shadcn/ui + TanStack React Query. Spec docs: `../docs/06-frontend.md`, `../docs/05-auth-flow.md` (Next.js sections).

## Route groups

- `(auth)` — `/login`, `/register`: public, centered minimal layout, no navbar.
- `(app)` — `/feed`, `/profile/[username]`, `/post/[id]`: protected by `src/middleware.ts` (cookie-presence check → redirect `/login`).
- `src/app/api/auth/*` — route handlers that exchange credentials with FastAPI and set/clear **httpOnly cookies**. `src/app/api/proxy/[...path]` — forwards data requests with the access cookie as a Bearer header.

## Data access rules

- Components/hooks NEVER call `fetch` directly. All data goes through `api<T>()` in `src/lib/api.ts` (proxy path, 401 → refresh → retry once). Auth actions go through `src/lib/auth.ts` → `/api/auth/*`.
- Types in `src/types/api.ts` mirror backend schemas exactly — **snake_case preserved**, no renaming.
- Backend base URL for route handlers/server components is `process.env.API_INTERNAL_URL` (differs between host dev and Docker — never hardcode).

## React Query

Query keys (keep canonical):

| Key | Hook |
|---|---|
| `['me']` | `use-auth.ts` |
| `['feed']` / `['feed', {username}]` | `use-feed.ts` (`useInfiniteQuery`, cursor from `next_cursor`) |
| `['post', id]` | post detail |
| `['comments', postId]` | comments (ascending, infinite) |
| `['profile', username]` | profile header |

**Optimistic updates** — `src/hooks/use-reactions.ts` is the canonical pattern; copy it for shares/comments:
`onMutate`: `cancelQueries` → snapshot → patch cached pages · `onError`: restore snapshot · `onSettled`: invalidate.
When patching the feed cache, remember it's an infinite query: map over `data.pages[].items[]`.

## UI conventions

- shadcn components live in `src/components/ui/` — NEVER hand-edit; regenerate with `npx shadcn@latest add <name>`.
- Feature components are flat in `src/components/` (kebab-case files, PascalCase exports).
- Layout: centered `max-w-xl mx-auto px-4` feed; sticky blurred navbar; `rounded-xl border shadow-sm` cards; `Skeleton` while loading; `sonner` toasts for errors; timestamps via `date-fns/formatDistanceToNow`.
- Dark mode via `next-themes` — use Tailwind `dark:` variants, no custom theme state.
- Post images are arbitrary remote URLs → plain `<img>` (not `next/image`) in v1.

## Gotchas

- httpOnly cookies are invisible to client JS — don't try to read tokens or set Authorization headers in client components; that's the proxy's job.
- `middleware.ts` only checks cookie presence (no JWT decode at the edge); real auth enforcement is the API's 401.
- The refresh cookie is scoped to `Path=/api/auth` — it will never appear on proxy requests; that's intentional.
- After login/register mutations, set `queryClient.setQueryData(['me'], user)` then `router.push('/feed')`.
