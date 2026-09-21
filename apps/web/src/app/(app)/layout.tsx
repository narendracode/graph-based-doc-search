"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ThemeToggle } from "@/lib/theme-toggle";

const NAV_LINKS = [
  { href: "/documents", label: "Search" },
  { href: "/upload", label: "Upload" },
  { href: "/projects", label: "Projects" },
  { href: "/about", label: "About" },
];

const ADMIN_LINKS = [
  { href: "/admin/zones", label: "Zones" },
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
          <div className="flex items-center gap-8">
            <Link href="/documents" className="flex items-center gap-2">
              <SealMark />
              <span className="font-sans text-sm font-semibold tracking-tight text-ink dark:text-slate-100">
                NBCC Archive
              </span>
            </Link>
            <nav className="flex gap-5">
              {links.map((link) => {
                const active = pathname?.startsWith(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`border-b-2 pb-1 text-sm transition-colors ${
                      active
                        ? "border-brand font-semibold text-ink dark:border-brand-light dark:text-slate-100"
                        : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
            <ThemeToggle />
            <span>
              {user.username}
              {user.role === "super_admin" && (
                <span className="ml-2 rounded bg-brand px-1.5 py-0.5 text-xs font-medium text-white dark:bg-brand-light dark:text-ink">
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

/* A small round seal mark — the brand's one graphic element, echoing the
 * official-approval-stamp motif used for checklist review decisions. */
function SealMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <circle cx="11" cy="11" r="9.5" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-brand dark:text-brand-light" />
      <path
        d="M6.5 11.5l3 3 6-6.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-brand dark:text-brand-light"
      />
    </svg>
  );
}
