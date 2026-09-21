"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Zone } from "@/lib/types";

export default function ZonesAdminPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<Zone[]>("/zones").then(setZones).catch(() => {});
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/zones", { name, code });
      setName("");
      setCode("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create zone");
    }
  }

  async function handleDelete(zone: Zone) {
    if (!confirm(`Delete "${zone.name}"? This can't be undone.`)) return;
    setError(null);
    try {
      await api.delete(`/zones/${zone.id}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete zone");
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">Zones</h1>

      <form
        onSubmit={handleCreate}
        className="mb-6 flex gap-2 rounded-xl border border-slate-200 bg-white shadow-sm p-4 dark:border-slate-800 dark:bg-slate-900"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Zone name"
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
      {error && <p className="mb-4 text-sm text-red-600 dark:text-red-400">{error}</p>}

      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
        {zones.map((z) => (
          <li key={z.id} className="flex items-center justify-between px-4 py-3 text-sm text-slate-900 dark:text-slate-100">
            <span>
              {z.name} <span className="text-slate-400 dark:text-slate-500">({z.code})</span>
            </span>
            <div className="flex items-center gap-3">
              {z.is_default ? (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                  default
                </span>
              ) : (
                <button
                  onClick={() => handleDelete(z)}
                  className="text-xs text-red-600 hover:underline dark:text-red-400"
                >
                  Delete
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
