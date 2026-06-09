import { Feed } from "@/components/feed";
import { PostComposer } from "@/components/post-composer";

export default function FeedPage() {
  return (
    <div className="space-y-4">
      <PostComposer />
      <Feed />
    </div>
  );
}
