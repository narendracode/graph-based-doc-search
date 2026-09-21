"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Project, UserDetail, UserOut, Zone } from "@/lib/types";

export default function UsersAdminPage() {
  const [users, setUsers] = useState<UserOut[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  function load() {
    api.get<UserOut[]>("/users").then(setUsers).catch(() => {});
  }

  useEffect(() => {
    load();
    api.get<Zone[]>("/zones").then(setZones).catch(() => {});
    api.get<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/users", { username, password });
      setUsername("");
      setPassword("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create user");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this user?")) return;
    await api.delete(`/users/${id}`);
    load();
  }

  return (
    <div className="max-w-3xl">
      <h1 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">Users</h1>

      <form
        onSubmit={handleCreate}
        className="mb-6 flex gap-2 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
      >
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          type="password"
          required
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
        {users.map((u) => (
          <li key={u.id} className="px-4 py-3 text-sm">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-slate-900 dark:text-slate-100">{u.username}</span>
                {u.role === "super_admin" && (
                  <span className="ml-2 rounded bg-slate-900 px-1.5 py-0.5 text-xs text-white dark:bg-slate-100 dark:text-slate-900">
                    super admin
                  </span>
                )}
                {!u.is_active && (
                  <span className="ml-2 rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                    inactive
                  </span>
                )}
              </div>
              {u.role !== "super_admin" && (
                <div className="flex gap-3">
                  <button
                    onClick={() => setExpanded(expanded === u.id ? null : u.id)}
                    className="text-slate-500 hover:underline dark:text-slate-400"
                  >
                    {expanded === u.id ? "Close" : "Manage access"}
                  </button>
                  <button
                    onClick={() => handleDelete(u.id)}
                    className="text-red-600 hover:underline dark:text-red-400"
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
            {expanded === u.id && (
              <AccessEditor userId={u.id} zones={zones} projects={projects} />
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function AccessEditor({
  userId,
  zones,
  projects,
}: {
  userId: string;
  zones: Zone[];
  projects: Project[];
}) {
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<UserDetail>(`/users/${userId}`).then(setDetail);
  }, [userId]);

  if (!detail) return <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">Loading…</p>;

  const zoneIds = new Set(detail.zones.map((z) => z.id));
  const projectIds = new Set(detail.projects.map((p) => p.id));

  async function toggleZone(id: string) {
    const next = new Set(zoneIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSaving(true);
    const updated = await api.put<UserDetail>(`/users/${userId}/zones`, { zone_ids: [...next] });
    setDetail(updated);
    setSaving(false);
  }

  async function toggleProject(id: string) {
    const next = new Set(projectIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSaving(true);
    const updated = await api.put<UserDetail>(`/users/${userId}/projects`, {
      project_ids: [...next],
    });
    setDetail(updated);
    setSaving(false);
  }

  return (
    <div className="mt-3 grid grid-cols-2 gap-4 rounded-md bg-slate-50 p-3 dark:bg-slate-800/50">
      <div>
        <p className="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-300">Zones</p>
        {zones
          .filter((z) => !z.is_default)
          .map((z) => (
            <label
              key={z.id}
              className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300"
            >
              <input
                type="checkbox"
                checked={zoneIds.has(z.id)}
                disabled={saving}
                onChange={() => toggleZone(z.id)}
                className="accent-slate-900 dark:accent-slate-300"
              />
              {z.name}
            </label>
          ))}
      </div>
      <div>
        <p className="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-300">Projects</p>
        {projects
          .filter((p) => !p.is_default)
          .map((p) => (
            <label
              key={p.id}
              className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300"
            >
              <input
                type="checkbox"
                checked={projectIds.has(p.id)}
                disabled={saving}
                onChange={() => toggleProject(p.id)}
                className="accent-slate-900 dark:accent-slate-300"
              />
              {p.name}
            </label>
          ))}
      </div>
    </div>
  );
}
