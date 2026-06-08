# 06 — Frontend Architecture (Next.js)

## Scaffold commands (Phase 5)

```bash
npx create-next-app@latest frontend --ts --tailwind --app --src-dir --eslint
cd frontend
npx shadcn@latest init
npx shadcn@latest add button card input textarea avatar dropdown-menu dialog tabs skeleton sonner form label separator
npm install @tanstack/react-query zod date-fns lucide-react clsx tailwind-merge next-themes
```

`next.config.ts`: set `output: 'standalone'` (needed by the Docker image).

## Routes

| Route | Group | Auth | Page |
|---|---|---|---|
| `/` | — | — | redirect → `/feed` (or `/login` via middleware) |
| `/login`, `/register` | `(auth)` | public | centered Card forms, no navbar |
| `/feed` | `(app)` | protected | composer + infinite feed |
| `/profile/[username]` | `(app)` | protected | profile header + user feed |
| `/post/[id]` | `(app)` | protected | expanded post + comments |

`(app)/layout.tsx` renders the Navbar and wraps children; `(auth)` has its own minimal centered layout.

## Component trees

```
(app)/layout.tsx ─ Navbar [logo · feed link · theme toggle · avatar DropdownMenu(profile, logout)]
└─ feed/page.tsx ─ Feed
                    ├─ PostComposer [Avatar · Textarea · image-url Input · Post Button]
                    └─ PostCard*  (infinite list, IntersectionObserver sentinel at bottom)
                        ├─ (shared-by banner, when repost)
                        ├─ header: Avatar · display_name · @username · time-ago
                        ├─ content text · optional <img>
                        ├─ ReactionBar [picker popover · per-type counts · my-reaction highlight]
                        └─ footer: 💬 comment_count (→ /post/[id]) · 🔁 ShareButton (count, toggled state)

post/[id]/page.tsx ─ PostCard (expanded) · CommentForm · CommentList [CommentItem*]
profile/[username]/page.tsx ─ ProfileHeader [Avatar · name · @username · bio · post_count · Edit Dialog if me]
                              └─ Feed (user-scoped)
(auth)/login · register ─ Card · zod-validated Form · submit Button · link to the other page
```

## Data layer

### `lib/api.ts` — the single fetch wrapper

```ts
export async function api<T>(path: string, opts?: {method?: string; body?: unknown}): Promise<T>
// fetch(`/api/proxy${path}`, { method, headers: {'Content-Type':'application/json'},
//                              body: JSON.stringify(body), credentials: 'include' })
// on 401: POST /api/auth/refresh → ok ? retry original ONCE : window.location.href = '/login'
// on !ok: throw new ApiError(status, detail)   // components surface via sonner toast
```

Rules: components/hooks never call `fetch` directly — always through `api()`. Auth-specific calls (`login`, `register`, `logout`, `me`) go to `/api/auth/*` via `lib/auth.ts`.

### `types/api.ts`

TypeScript mirrors of the backend schemas: `UserOut`, `AuthorMini`, `PostOut`, `CommentOut`, `ReactionType`, `CursorPage<T>`. Keep field names snake_case to match the API exactly (no client-side renaming in v1). zod schemas only for the login/register forms.

### React Query keys & hooks

| Key | Hook | Type |
|---|---|---|
| `['me']` | `useAuth()` | query — current user or null (401 → null, not error) |
| `['feed']` | `useFeed()` | `useInfiniteQuery`, `getNextPageParam: (last) => last.has_more ? last.next_cursor : undefined` |
| `['feed', {username}]` | `useFeed(username)` | profile posts |
| `['post', id]` | `usePost(id)` | single post |
| `['comments', postId]` | `useComments(postId)` | infinite, ascending |
| `['profile', username]` | `useProfile(username)` | header data |

`lib/query-client.ts`: one `QueryClient` (staleTime ~30 s) provided by a `'use client'` Providers component in the root layout (with `next-themes` ThemeProvider).

### Mutations + optimistic updates

- **`useReact(postId)`** (canonical optimistic pattern — `hooks/use-reactions.ts`):
  - `onMutate`: `cancelQueries` → snapshot previous data → patch `my_reaction` + `reaction_counts` in every cached `['feed'...]` page and `['post', id]`
  - `onError`: restore snapshot
  - `onSettled`: `invalidateQueries`
- **`useShare(postId)`**: same pattern toggling `shared_by_me` / `share_count`.
- **`useCreatePost`**: v1 keeps it simple — `invalidateQueries(['feed'])` on success.
- **`useComment(postId)`**: optimistic append with a temp id, replaced by the server row on success; also bump `comment_count` on the post.

## UI design notes (Social Hub look)

- Centered single-column feed: `max-w-xl mx-auto px-4`, sticky top navbar (`sticky top-0 backdrop-blur border-b`).
- Cards: `rounded-xl border shadow-sm`, avatar circles (`Avatar` shadcn), muted small timestamps via `date-fns/formatDistanceToNow`.
- Reaction picker: popover on click of the react button showing the 6 emoji types; selected reaction highlights the button.
- Loading: `Skeleton` cards while feed fetches; sonner toasts for errors; empty states ("No posts yet — be the first!").
- Dark mode: `next-themes` + Tailwind `dark:` variants; toggle in navbar.
- Images: plain `<img>` with `rounded-lg max-h-96 object-cover` (remote URLs are arbitrary — skip `next/image` domain config in v1).

## Auth pages

- React Hook Form is NOT required — simple controlled forms + zod `safeParse` on submit are fine at this scope (or use shadcn `Form` with RHF if generated — either is acceptable, pick one and stay consistent).
- On success: route handler set cookies → `router.push('/feed')` + `queryClient.setQueryData(['me'], user)`.
- Show field errors inline; API errors (409/401) as a form-level message.

## Files that must exist when the frontend is done

```
src/lib/api.ts  src/lib/auth.ts  src/lib/query-client.ts  src/lib/utils.ts
src/types/api.ts
src/hooks/use-auth.ts  use-feed.ts  use-reactions.ts
src/middleware.ts
src/app/api/auth/{login,register,refresh,logout,me}/route.ts
src/app/api/proxy/[...path]/route.ts
src/components/{navbar,feed,post-card,post-composer,comment-list,comment-form,reaction-bar,profile-header}.tsx
```
