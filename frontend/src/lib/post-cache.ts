import type { QueryClient, QueryKey } from "@tanstack/react-query";

import type { CursorPage, PostOut, ReactionType } from "@/types/api";

type InfiniteFeed = { pages: CursorPage<PostOut>[]; pageParams: unknown[] };

// Every infinite list of posts a post can appear in: the global/profile feed
// (['feed', ...]) and a school's Memories tab (['school-posts', slug]).
const POST_LIST_KEYS = [["feed"], ["school-posts"]] as const;

// Apply a patch to a post wherever it appears: every post-list infinite query
// and the ['post', id] single-post cache.
export function patchPost(
  qc: QueryClient,
  postId: string,
  patch: (p: PostOut) => PostOut,
): void {
  for (const queryKey of POST_LIST_KEYS) {
    qc.setQueriesData<InfiniteFeed>({ queryKey }, (data) => {
      if (!data) return data;
      return {
        ...data,
        pages: data.pages.map((page) => ({
          ...page,
          items: page.items.map((item) => (item.id === postId ? patch(item) : item)),
        })),
      };
    });
  }
  qc.setQueryData<PostOut>(["post", postId], (p) => (p ? patch(p) : p));
}

export interface PostSnapshot {
  lists: [QueryKey, unknown][];
  post: unknown;
}

export function snapshotPostCaches(qc: QueryClient, postId: string): PostSnapshot {
  return {
    lists: POST_LIST_KEYS.flatMap((queryKey) => qc.getQueriesData({ queryKey })),
    post: qc.getQueryData(["post", postId]),
  };
}

export function restorePostCaches(
  qc: QueryClient,
  postId: string,
  snap: PostSnapshot,
): void {
  for (const [key, data] of snap.lists) qc.setQueryData(key, data);
  qc.setQueryData(["post", postId], snap.post);
}

// Optimistically compute the new reaction state for a post (mirrors the backend
// toggle semantics: same type removes, different switches, none adds).
export function applyReactionToggle(p: PostOut, type: ReactionType): PostOut {
  const counts: Record<string, number> = { ...p.reaction_counts };
  const current = p.my_reaction;
  let myReaction: ReactionType | null = type;

  if (current === type) {
    counts[type] = Math.max(0, (counts[type] ?? 1) - 1);
    if (counts[type] === 0) delete counts[type];
    myReaction = null;
  } else {
    if (current) {
      counts[current] = Math.max(0, (counts[current] ?? 1) - 1);
      if (counts[current] === 0) delete counts[current];
    }
    counts[type] = (counts[type] ?? 0) + 1;
  }
  return { ...p, my_reaction: myReaction, reaction_counts: counts };
}
