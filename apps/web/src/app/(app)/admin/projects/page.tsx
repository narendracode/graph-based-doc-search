"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function ProjectsAdminPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<Project[]>("/projects").then(setProjects).catch(() => {});
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

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">Projects</h1>

      <form
        onSubmit={handleCreate}
        className="mb-6 flex gap-2 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
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
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
        >
          Add
        </button>
      </form>
      {error && <p className="mb-4 text-sm text-red-600 dark:text-red-400">{error}</p>}

      <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
        {projects.map((p) => (
          <li key={p.id} className="flex items-center justify-between px-4 py-3 text-sm text-slate-900 dark:text-slate-100">
            <span>
              {p.name} <span className="text-slate-400 dark:text-slate-500">({p.code})</span>
            </span>
            {p.is_default && (
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                default
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
