"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ThemeToggle } from "@/lib/theme-toggle";

const NAV_LINKS = [
  { href: "/documents", label: "Search" },
  { href: "/upload", label: "Upload" },
];

const ADMIN_LINKS = [
  { href: "/admin/zones", label: "Zones" },
  { href: "/admin/projects", label: "Projects" },
  { href: "/admin/users", label: "Users" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      // Preserve where they were trying to go — e.g. a shared document link —
      // so login drops them back there instead of the generic search page.
      router.replace(`/login?redirect=${encodeURIComponent(pathname || "/documents")}`);
    }
  }, [loading, user, router, pathname]);

  if (loading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-slate-500 dark:text-slate-400">
        Loading…
      </div>
    );
  }

  const links = user.role === "super_admin" ? [...NAV_LINKS, ...ADMIN_LINKS] : NAV_LINKS;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              NBCC Archive
            </span>
            <nav className="flex gap-4">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm ${
                    pathname?.startsWith(link.href)
                      ? "font-semibold text-slate-900 dark:text-slate-100"
                      : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
            <ThemeToggle />
            <span>
              {user.username}
              {user.role === "super_admin" && (
                <span className="ml-2 rounded bg-slate-900 px-1.5 py-0.5 text-xs text-white dark:bg-slate-100 dark:text-slate-900">
                  admin
                </span>
              )}
            </span>
            <button
              onClick={() => logout().then(() => router.replace("/login"))}
              className="rounded-md border border-slate-300 px-3 py-1 text-sm hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>
    </div>
  );
}
