"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

const STEPS = [
  {
    n: "01",
    title: "Upload",
    body:
      "Drop in PDFs, Word, Excel, PowerPoint, CSV, or text files. Tag each one with a zone and project — or leave it for the default zone and project, visible to everyone.",
  },
  {
    n: "02",
    title: "Indexed automatically",
    body:
      "Every document is parsed, embedded, and lightly linked into a knowledge graph in the background — no manual filing, no folder structure to maintain.",
  },
  {
    n: "03",
    title: "Search or ask",
    body:
      "Find documents by keyword, or switch to AI Mode and ask a plain-language question — it answers from the archive's actual contents and cites exactly which documents it used.",
  },
  {
    n: "04",
    title: "Track project checklists",
    body:
      "Admins define the documents a project requires. Users upload against each item, and every upload is approved or rejected — with feedback — before it counts toward the project being complete.",
  },
  {
    n: "05",
    title: "Share deliberately",
    body:
      "Grant one person, or an entire zone or project, access to a specific document — without changing that document's own zone or project, or opening up the rest of the archive.",
  },
];

export default function AboutPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-3xl">
      {/* Hero */}
      <div className="mb-10 border-b border-slate-200 pb-10 dark:border-slate-800">
        <p className="mb-3 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-brand dark:text-brand-light">
          NBCC Document Archive
        </p>
        <h1 className="mb-4 max-w-xl font-sans text-3xl font-semibold leading-tight tracking-tight text-ink dark:text-slate-100">
          Know what&apos;s missing, what&apos;s approved, and what&apos;s safe to act on.
        </h1>
        <p className="max-w-xl text-sm leading-relaxed text-slate-600 dark:text-slate-400">
          NBCC&apos;s project paperwork — clearances, land titles, contracts, approvals —
          used to live scattered across desks and inboxes, hard to search and easy to
          lose track of. This archive gives every document one home, makes it
          searchable in plain language, and tracks whether each project&apos;s required
          paperwork is actually complete and approved — so the wrong document never
          quietly stands in for the right one.
        </p>
      </div>

      {/* The problem, stated plainly */}
      <div className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            Before
          </h2>
          <ul className="space-y-1.5 text-sm text-slate-600 dark:text-slate-400">
            <li>Documents scattered across desks, drives, and inboxes</li>
            <li>No way to tell if a project&apos;s paperwork is actually complete</li>
            <li>No safe way to share one file without opening up everything else</li>
          </ul>
        </div>
        <div className="rounded-xl border border-brand/30 bg-white p-5 shadow-sm dark:border-brand-light/30 dark:bg-slate-900">
          <h2 className="mb-2 text-sm font-semibold text-ink dark:text-brand-light">
            With the archive
          </h2>
          <ul className="space-y-1.5 text-sm text-slate-600 dark:text-slate-400">
            <li>One searchable home for every document, in whatever format it arrives</li>
            <li>A checklist per project that shows exactly what&apos;s approved, pending, or rejected</li>
            <li>Exclusive sharing — grant access to one document without touching the rest</li>
          </ul>
        </div>
      </div>

      {/* Walkthrough */}
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        How it works
      </h2>
      <ol className="mb-10 space-y-4">
        {STEPS.map((step) => (
          <li
            key={step.n}
            className="flex gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <span className="shrink-0 font-mono text-sm font-semibold text-brand dark:text-brand-light">
              {step.n}
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {step.title}
              </p>
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>

      {/* The signature moment, explained */}
      <div className="mb-10 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Every decision is on the record
        </h2>
        <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
          When a document is uploaded against a checklist item, an admin approves or
          rejects it — the same way a physical document would be stamped. A rejection
          always comes with feedback, so the next upload gets it right.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <span className="stamp border-approve text-approve dark:border-approve-light dark:text-approve-light">
            approved
          </span>
          <span className="stamp border-reject text-reject dark:border-reject-light dark:text-reject-light">
            rejected
          </span>
        </div>
      </div>

      {/* Role note + CTA */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-800/50">
        <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">
          {user?.role === "super_admin"
            ? "As a super admin, you manage zones and users from the admin pages in the nav, and projects — including creating them and building each one's document checklist — right from the Projects page."
            : "You can see the zones and projects you've been given access to, plus anything shared with you directly. Ask your admin if you need access to more."}
        </p>
        <div className="flex gap-3">
          <Link
            href="/documents"
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-ink dark:bg-brand-light dark:text-ink dark:hover:bg-brand"
          >
            Go to search
          </Link>
          <Link
            href="/upload"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm hover:bg-white dark:border-slate-600 dark:hover:bg-slate-800"
          >
            Upload a document
          </Link>
        </div>
      </div>
    </div>
  );
}
