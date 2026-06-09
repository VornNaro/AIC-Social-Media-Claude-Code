"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { register } from "@/lib/auth";

const schema = z.object({
  username: z
    .string()
    .min(3, "Username must be 3-30 characters")
    .max(30)
    .regex(/^[a-zA-Z0-9_]+$/, "Letters, numbers, and underscores only"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  display_name: z.string().max(80).optional(),
  school_name: z.string().max(160).optional(),
  graduation_year: z.number().int().min(1900).max(2100).optional(),
});

export default function RegisterPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const yearRaw = String(form.get("graduation_year") ?? "").trim();
    const values = {
      username: String(form.get("username") ?? "").trim(),
      email: String(form.get("email") ?? "").trim(),
      password: String(form.get("password") ?? ""),
      display_name: String(form.get("display_name") ?? "").trim() || undefined,
      school_name: String(form.get("school_name") ?? "").trim() || undefined,
      graduation_year: yearRaw ? Number(yearRaw) : undefined,
    };
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }
    setLoading(true);
    try {
      const user = await register(parsed.data);
      queryClient.setQueryData(["me"], user);
      router.push("/feed");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Create your SchoolMate account</CardTitle>
        <CardDescription>
          Add your school and graduation year, and we&apos;ll start finding your old
          classmates right away.
        </CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="display_name">Full name</Label>
            <Input id="display_name" name="display_name" placeholder="e.g. Aisha Sharma" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input id="username" name="username" autoComplete="username" />
          </div>
          <div className="grid grid-cols-[1fr_auto] gap-3">
            <div className="space-y-2">
              <Label htmlFor="school_name">School name</Label>
              <Input
                id="school_name"
                name="school_name"
                placeholder="e.g. Chungbuk National University"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="graduation_year">Class of</Label>
              <Input
                id="graduation_year"
                name="graduation_year"
                type="number"
                placeholder="2012"
                className="w-24"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" name="email" type="email" autoComplete="email" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" name="password" type="password" autoComplete="new-password" />
          </div>
        </CardContent>
        <CardFooter className="mt-4 flex-col gap-3">
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating your account…" : "Create Account"}
          </Button>
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium underline underline-offset-4">
              Log in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
