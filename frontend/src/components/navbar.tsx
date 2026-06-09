"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useQueryClient } from "@tanstack/react-query";
import { CalendarDays, GraduationCap, Home, LogOut, User as UserIcon } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { UserAvatar } from "@/components/user-avatar";
import { useAuth } from "@/hooks/use-auth";
import { logout } from "@/lib/auth";

export function Navbar() {
  const { data: user } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();

  async function onLogout() {
    await logout();
    qc.setQueryData(["me"], null);
    qc.clear();
    router.push("/login");
  }

  const schoolHref = user?.school ? `/school/${user.school.slug}` : null;

  return (
    <header className="sticky top-0 z-40 border-b bg-card/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-4 px-4">
        <Link href="/feed" className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/schoolmate/logo/schoolmate-mark.png" alt="" className="h-9 w-9" />
          <span className="text-xl font-extrabold tracking-tight text-foreground">
            School<span className="text-primary">Mate</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          <NavLink href="/feed" icon={<Home className="h-5 w-5" />} label="Home" />
          {schoolHref && (
            <NavLink
              href={schoolHref}
              icon={<GraduationCap className="h-5 w-5" />}
              label="My School"
            />
          )}
          <NavLink
            href="/reunions"
            icon={<CalendarDays className="h-5 w-5" />}
            label="Reunions"
          />
          <ThemeToggle />
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger className="ml-1 rounded-full outline-none ring-offset-2 focus-visible:ring-2">
                <UserAvatar
                  name={user.display_name}
                  src={user.avatar_url}
                  className="h-9 w-9"
                />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>@{user.username}</DropdownMenuLabel>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem render={<Link href={`/profile/${user.username}`} />}>
                  <UserIcon className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </nav>
      </div>
    </header>
  );
}

function NavLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </Link>
  );
}
