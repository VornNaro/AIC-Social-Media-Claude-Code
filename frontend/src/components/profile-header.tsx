"use client";

import { useState } from "react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { UserAvatar } from "@/components/user-avatar";
import { useAuth } from "@/hooks/use-auth";
import { useProfile, useUpdateProfile } from "@/hooks/use-profile";

export function ProfileHeader({ username }: { username: string }) {
  const { data: profile, isLoading } = useProfile(username);
  const { data: me } = useAuth();
  const update = useUpdateProfile();
  const [open, setOpen] = useState(false);

  if (isLoading || !profile) {
    return <Skeleton className="h-36 w-full rounded-xl" />;
  }

  const isMe = me?.username === profile.username;

  async function onSave(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await update.mutateAsync({
        display_name: String(form.get("display_name") ?? "").trim() || undefined,
        bio: String(form.get("bio") ?? ""),
        avatar_url: String(form.get("avatar_url") ?? "").trim() || undefined,
      });
      setOpen(false);
      toast.success("Profile updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Update failed");
    }
  }

  return (
    <div className="rounded-xl border p-6">
      <div className="flex items-start gap-4">
        <UserAvatar name={profile.display_name} src={profile.avatar_url} className="h-16 w-16" />
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold">{profile.display_name}</h1>
          <p className="text-muted-foreground">@{profile.username}</p>
          {profile.bio && <p className="mt-2 whitespace-pre-wrap break-words">{profile.bio}</p>}
          <p className="mt-2 text-sm text-muted-foreground">{profile.post_count} posts</p>
        </div>
        {isMe && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger render={<Button variant="outline" size="sm" />}>
              Edit profile
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit profile</DialogTitle>
                <DialogDescription>Update your public profile.</DialogDescription>
              </DialogHeader>
              <form onSubmit={onSave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="display_name">Display name</Label>
                  <Input id="display_name" name="display_name" defaultValue={profile.display_name} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea id="bio" name="bio" defaultValue={profile.bio ?? ""} rows={3} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="avatar_url">Avatar URL</Label>
                  <Input id="avatar_url" name="avatar_url" defaultValue={profile.avatar_url ?? ""} />
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={update.isPending}>
                    {update.isPending ? "Saving…" : "Save changes"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  );
}
