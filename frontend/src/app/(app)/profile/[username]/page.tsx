"use client";

import { useParams } from "next/navigation";

import { Feed } from "@/components/feed";
import { ProfileHeader } from "@/components/profile-header";

export default function ProfilePage() {
  const params = useParams<{ username: string }>();
  const username = params.username;

  return (
    <div className="space-y-4">
      <ProfileHeader username={username} />
      <Feed username={username} />
    </div>
  );
}
