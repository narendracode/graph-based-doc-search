"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Project, ProjectChecklist } from "@/lib/types";
import { statusBadgeClass } from "@/lib/status-colors";

export default function ProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [checklists, setChecklists] = useState<Record<string, ProjectChecklist>>({});
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  function load() {
    api
      .get<Project[]>("/projects")
      .then((list) => {
        setProjects(list);
        list.forEach((p) => {
          api
            .get<ProjectChecklist>(`/projects/${p.id}/checklist`)
            .then((c) => setChecklists((prev) => ({ ...prev, [p.id]: c })))
            .catch(() => {});
        });
      })
      .catch(() => {});
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/projects", { name, code });
      setName("");
      setCode("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create project");
    }
  }

  async function handleDelete(project: Project) {
    if (!confirm(`Delete "${project.name}"? This can't be undone.`)) return;
    setError(null);
    try {
      await api.delete(`/projects/${project.id}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete project");
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-xl font-semibold text-slate-900 dark:text-slate-100">Projects</h1>
      <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">
        Each project&apos;s document checklist and completion status.
      </p>

      {user?.role === "super_admin" && (
        <form
          onSubmit={handleCreate}
          className="mb-6 flex gap-2 rounded-xl border border-slate-200 bg-white shadow-sm p-4 dark:border-slate-800 dark:bg-slate-900"
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Project name"
            required
            className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="Code"
            required
            className="w-28 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
          <button
            type="submit"
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-ink dark:bg-brand-light dark:text-ink dark:hover:bg-brand"
          >
            Add
          </button>
        </form>
      )}
      {error && <p className="mb-4 text-sm text-red-600 dark:text-red-400">{error}</p>}

      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
        {projects.map((p) => {
          const checklist = checklists[p.id];
          return (
            <li key={p.id} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
              <Link href={`/projects/${p.id}`} className="flex flex-1 items-center justify-between">
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  {p.name}
                  <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">
                    ({p.code})
                  </span>
                  {p.is_default && (
                    <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                      default
                    </span>
                  )}
                </span>
                {checklist && checklist.project_status !== "no_checklist" && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(
                      checklist.project_status
                    )}`}
                  >
                    {checklist.project_status_label}
                  </span>
                )}
              </Link>
              {user?.role === "super_admin" && !p.is_default && (
                <button
                  onClick={() => handleDelete(p)}
                  className="shrink-0 text-xs text-red-600 hover:underline dark:text-red-400"
                >
                  Delete
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
