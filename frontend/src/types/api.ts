// TypeScript mirrors of the backend Pydantic schemas.
// Field names are kept snake_case to match the API exactly (no client renaming).

export type ReactionType = "LIKE" | "LOVE" | "HAHA" | "WOW" | "SAD" | "ANGRY";

export const REACTION_TYPES: ReactionType[] = [
  "LIKE",
  "LOVE",
  "HAHA",
  "WOW",
  "SAD",
  "ANGRY",
];

export interface AuthorMini {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
  graduation_year: number | null;
}

export interface SharedBy {
  username: string;
  display_name: string;
  shared_at: string;
}

export interface PostOut {
  id: string;
  author: AuthorMini;
  content: string | null;
  image_url: string | null;
  tags: string[];
  note: string | null;
  created_at: string;
  updated_at: string;
  reaction_counts: Record<string, number>;
  my_reaction: ReactionType | null;
  comment_count: number;
  share_count: number;
  shared_by_me: boolean;
  shared_by: SharedBy | null;
}

export interface CommentOut {
  id: string;
  post_id: string;
  author: AuthorMini;
  content: string;
  created_at: string;
}

export interface SchoolMini {
  id: string;
  slug: string;
  name: string;
  short_name: string | null;
}

export interface UserOut {
  id: string;
  username: string;
  display_name: string;
  email: string;
  bio: string | null;
  avatar_url: string | null;
  cover_url: string | null;
  graduation_year: number | null;
  city: string | null;
  role: string | null;
  interests: string[];
  school: SchoolMini | null;
  created_at: string;
}

export interface UserProfile {
  id: string;
  username: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  cover_url: string | null;
  graduation_year: number | null;
  city: string | null;
  role: string | null;
  interests: string[];
  school: SchoolMini | null;
  created_at: string;
  post_count: number;
  connection_count: number;
}

export type RsvpStatus = "GOING" | "MAYBE" | "DECLINED";

export interface SchoolOut {
  id: string;
  slug: string;
  name: string;
  short_name: string | null;
  location: string | null;
  founded: number | null;
  cover_url: string | null;
  motto: string | null;
  member_count: number;
  is_member: boolean;
  created_at: string;
}

export interface ReunionOut {
  id: string;
  school_id: string;
  title: string;
  class_year: number | null;
  starts_at: string;
  ends_at: string | null;
  venue: string | null;
  address: string | null;
  city: string | null;
  cover_url: string | null;
  description: string | null;
  amenities: string[];
  host: AuthorMini;
  going_count: number;
  my_rsvp: RsvpStatus | null;
}

export interface AttendeeOut {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
  graduation_year: number | null;
  city: string | null;
  status: RsvpStatus;
}

export type ConnectionState =
  | "none"
  | "pending_outgoing"
  | "pending_incoming"
  | "connected";

export interface ClassmateOut {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
  graduation_year: number | null;
  city: string | null;
  role: string | null;
  connection_state: ConnectionState;
  mutual_count: number;
}

export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface ReactionState {
  my_reaction: ReactionType | null;
  reaction_counts: Record<string, number>;
}

export interface ShareState {
  share_count: number;
  shared_by_me: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserOut;
}
