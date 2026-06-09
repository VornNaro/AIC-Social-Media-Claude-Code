"use client";

import { useParams } from "next/navigation";

import { Feed } from "@/components/feed";
import { ProfileAbout } from "@/components/profile-about";
import { ProfileClassmates } from "@/components/profile-classmates";
import { ProfileHeader } from "@/components/profile-header";

export default function ProfilePage() {
  const username = useParams<{ username: string }>().username;

  return (
    <div className="space-y-6">
      <ProfileHeader username={username} />

      <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <div className="space-y-6 lg:sticky lg:top-20 lg:self-start">
          <ProfileAbout username={username} />
          <ProfileClassmates username={username} />
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-extrabold">Memories</h2>
          <Feed username={username} />
        </div>
      </div>
    </div>
  );
}
