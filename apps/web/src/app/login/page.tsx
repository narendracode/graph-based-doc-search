"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";

// Only ever redirect somewhere inside this app — a `redirect` query param is
// attacker-controlled input (anyone can craft a link), so a bare "starts with /"
// check without also rejecting "//host/..." would let someone build a login link
// that quietly sends the user off-site after they authenticate.
function safeRedirect(target: string | null): string {
  if (target && target.startsWith("/") && !target.startsWith("//")) {
    return target;
  }
  return "/documents";
}

function LoginForm() {
  const { user, loading, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const destination = safeRedirect(searchParams.get("redirect"));
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace(destination);
    }
  }, [loading, user, router, destination]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      router.replace(destination);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">NBCC Document Archive</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Sign in to search, upload, and manage documents.
          </p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Username
            </label>
            <input
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />
          </div>
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Password
            </label>
            <input
              type="password"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="mb-4 text-sm text-red-600 dark:text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-300"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
