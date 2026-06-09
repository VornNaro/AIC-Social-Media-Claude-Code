"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useQueryClient } from "@tanstack/react-query";
import { ImageIcon, PartyPopper, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/lib/auth";

const BENEFITS = [
  { icon: Users, title: "Find your whole class", sub: "Search by school and graduation year." },
  { icon: ImageIcon, title: "Share old photos", sub: "Build a yearbook that never closes." },
  { icon: PartyPopper, title: "Plan reunions", sub: "RSVP and organize in a few taps." },
];

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const identifier = String(form.get("username_or_email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    if (!identifier || !password) {
      toast.error("Please fill in all fields.");
      return;
    }
    setLoading(true);
    try {
      const user = await login(identifier, password);
      queryClient.setQueryData(["me"], user);
      router.push("/feed");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-4xl overflow-hidden p-0 shadow-lg">
      <div className="grid md:grid-cols-2">
        {/* Welcome / benefits panel */}
        <div className="relative hidden flex-col justify-between gap-8 bg-gradient-to-br from-brand-blue/20 via-cream/50 to-primary/15 p-8 md:flex">
          <div>
            <span className="font-hand text-2xl text-brand-blue">
              Welcome back to the class ♥
            </span>
            <h2 className="mt-2 text-2xl font-extrabold leading-tight">
              Pick up right where you left off
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Your classmates, memories, and reunions are waiting.
            </p>
            <div className="mt-7 space-y-4">
              {BENEFITS.map((b) => (
                <div key={b.title} className="flex items-start gap-3">
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-brand-blue/15 text-brand-blue">
                    <b.icon className="h-5 w-5" />
                  </span>
                  <div>
                    <div className="font-bold text-foreground">{b.title}</div>
                    <div className="text-sm text-muted-foreground">{b.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/schoolmate/illustrations/connected-people.png"
            alt=""
            className="mx-auto max-h-40 w-auto object-contain drop-shadow-sm"
          />
        </div>

        {/* Login form */}
        <div className="p-8 sm:p-10">
          <h1 className="text-2xl font-extrabold">Welcome back</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Log in to reconnect with your old schoolmates.
          </p>
          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username_or_email">Username or email</Label>
              <Input id="username_or_email" name="username_or_email" autoComplete="username" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
              />
            </div>
            <Button type="submit" size="lg" className="w-full" disabled={loading}>
              {loading ? "Logging in…" : "Log In"}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            New here?{" "}
            <Link href="/register" className="font-bold text-primary hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </Card>
  );
}
