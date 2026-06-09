"use client";

import Link from "next/link";
import { useState } from "react";

import { GraduationCap, MapPin } from "lucide-react";
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
    return <Skeleton className="h-64 w-full rounded-2xl" />;
  }

  const isMe = me?.username === profile.username;

  async function onSave(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const yearRaw = String(form.get("graduation_year") ?? "").trim();
    const interestsRaw = String(form.get("interests") ?? "").trim();
    try {
      await update.mutateAsync({
        display_name: String(form.get("display_name") ?? "").trim() || undefined,
        bio: String(form.get("bio") ?? ""),
        avatar_url: String(form.get("avatar_url") ?? "").trim() || undefined,
        cover_url: String(form.get("cover_url") ?? "").trim() || undefined,
        city: String(form.get("city") ?? "").trim() || undefined,
        role: String(form.get("role") ?? "").trim() || undefined,
        graduation_year: yearRaw ? Number(yearRaw) : undefined,
        interests: interestsRaw
          ? interestsRaw.split(",").map((s) => s.trim()).filter(Boolean)
          : undefined,
      });
      setOpen(false);
      toast.success("Profile updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Update failed");
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border bg-card">
      {/* cover */}
      <div className="h-40 bg-gradient-to-r from-brand-blue/40 to-primary/30">
        {profile.cover_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={profile.cover_url} alt="" className="h-full w-full object-cover" />
        )}
      </div>

      <div className="px-6 pb-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="-mt-12 flex items-end gap-4">
            <UserAvatar
              name={profile.display_name}
              src={profile.avatar_url}
              className="h-24 w-24 ring-4 ring-card"
            />
          </div>
          {isMe && (
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger render={<Button variant="default" size="sm" />}>
                Edit profile
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Edit profile</DialogTitle>
                  <DialogDescription>Help your classmates recognize you.</DialogDescription>
                </DialogHeader>
                <form onSubmit={onSave} className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="display_name">Display name</Label>
                      <Input id="display_name" name="display_name" defaultValue={profile.display_name} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="graduation_year">Graduation year</Label>
                      <Input
                        id="graduation_year"
                        name="graduation_year"
                        type="number"
                        defaultValue={profile.graduation_year ?? ""}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="city">City</Label>
                      <Input id="city" name="city" defaultValue={profile.city ?? ""} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="role">What you do</Label>
                      <Input id="role" name="role" defaultValue={profile.role ?? ""} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bio">About you</Label>
                    <Textarea id="bio" name="bio" defaultValue={profile.bio ?? ""} rows={3} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="interests">Interests (comma-separated)</Label>
                    <Input
                      id="interests"
                      name="interests"
                      defaultValue={profile.interests.join(", ")}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="avatar_url">Avatar URL</Label>
                      <Input id="avatar_url" name="avatar_url" defaultValue={profile.avatar_url ?? ""} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cover_url">Cover URL</Label>
                      <Input id="cover_url" name="cover_url" defaultValue={profile.cover_url ?? ""} />
                    </div>
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

        <h1 className="mt-3 text-2xl font-extrabold">{profile.display_name}</h1>
        <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          {profile.graduation_year != null && (
            <span className="rounded-full bg-accent px-2.5 py-0.5 font-semibold text-accent-foreground">
              Class of {profile.graduation_year}
            </span>
          )}
          {profile.school && (
            <Link
              href={`/school/${profile.school.slug}`}
              className="flex items-center gap-1.5 font-semibold text-brand-blue hover:underline"
            >
              <GraduationCap className="h-4 w-4" />
              {profile.school.short_name ?? profile.school.name}
            </Link>
          )}
          {profile.city && (
            <span className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              {profile.city}
            </span>
          )}
        </div>

        <div className="mt-4 flex gap-8 border-t pt-4">
          <Stat n={profile.post_count} label="Memories" />
          <Stat n={profile.connection_count} label="Classmates" />
        </div>
      </div>
    </div>
  );
}

function Stat({ n, label }: { n: number; label: string }) {
  return (
    <div>
      <div className="text-xl font-extrabold">{n}</div>
      <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
    </div>
  );
}
