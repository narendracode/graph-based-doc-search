"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentOut, Project, Zone } from "@/lib/types";

export function RetagControl({
  doc,
  onUpdated,
}: {
  doc: DocumentOut;
  onUpdated: (updated: DocumentOut) => void;
}) {
  const [zones, setZones] = useState<Zone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [saving, setSaving] = useState<"zone" | "project" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Zone[]>("/zones").then(setZones).catch(() => {});
    api.get<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  async function handleZoneChange(zoneId: string) {
    setSaving("zone");
    setError(null);
    try {
      const updated = await api.patch<DocumentOut>(`/documents/${doc.id}`, { zone_id: zoneId });
      onUpdated(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update zone");
    } finally {
      setSaving(null);
    }
  }

  async function handleProjectChange(projectId: string) {
    setSaving("project");
    setError(null);
    try {
      const updated = await api.patch<DocumentOut>(`/documents/${doc.id}`, {
        project_id: projectId,
      });
      onUpdated(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update project");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
      <label className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
        Zone
        <select
          value={doc.zone_id}
          onChange={(e) => handleZoneChange(e.target.value)}
          disabled={saving !== null}
          className="rounded border border-slate-300 bg-white px-1.5 py-0.5 text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
        >
          {zones.map((z) => (
            <option key={z.id} value={z.id}>
              {z.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
        Project
        <select
          value={doc.project_id}
          onChange={(e) => handleProjectChange(e.target.value)}
          disabled={saving !== null}
          className="rounded border border-slate-300 bg-white px-1.5 py-0.5 text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
      {saving && <span className="text-slate-400 dark:text-slate-500">Saving…</span>}
      {error && <span className="text-red-600 dark:text-red-400">{error}</span>}
    </div>
  );
}
