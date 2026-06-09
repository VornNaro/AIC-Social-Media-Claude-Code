import { Feed } from "@/components/feed";
import { FeedRail } from "@/components/feed-rail";
import { PostComposer } from "@/components/post-composer";

export default function FeedPage() {
  return (
    <div className="flex justify-center gap-6">
      <div className="w-full max-w-xl space-y-4">
        <PostComposer />
        <Feed />
      </div>
      <FeedRail />
    </div>
  );
}
