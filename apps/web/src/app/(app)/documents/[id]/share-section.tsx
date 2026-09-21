"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatDate } from "@/lib/format";
import type { DocumentShares, Project, Zone } from "@/lib/types";

export function ShareSection({ documentId }: { documentId: string }) {
  const [shares, setShares] = useState<DocumentShares | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<DocumentShares>(`/documents/${documentId}/shares`).then(setShares).catch(() => {});
  }

  useEffect(() => {
    load();
    api.get<Zone[]>("/zones").then(setZones).catch(() => {});
    api.get<Project[]>("/projects").then(setProjects).catch(() => {});
  }, [documentId]);

  async function handleCopyLink() {
    const url = `${window.location.origin}/documents/${documentId}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Couldn't copy the link — your browser may be blocking clipboard access.");
    }
  }

  return (
    <div className="mt-6">
      <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
        Share this document
      </h2>
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4 dark:border-slate-800 dark:bg-slate-900">
        <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
          Users with access to this document&apos;s own zone/project can already see it.
          Exclusive shares below grant access to specific people, or to everyone with
          access to another zone/project, on top of that — without changing the
          document&apos;s own zone/project or giving anyone broader archive access.
        </p>

        <button
          onClick={handleCopyLink}
          className="mb-4 rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800"
        >
          {copied ? "Link copied" : "Copy link"}
        </button>
        {error && <p className="mb-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

        <UserShares documentId={documentId} shares={shares?.users ?? []} onChange={load} />
        <ZoneShares
          documentId={documentId}
          shares={shares?.zones ?? []}
          zones={zones}
          onChange={load}
        />
        <ProjectShares
          documentId={documentId}
          shares={shares?.projects ?? []}
          projects={projects}
          onChange={load}
        />
      </div>
    </div>
  );
}

function RevokeButton({ show, onClick }: { show: boolean; onClick: () => void }) {
  if (!show) return null;
  return (
    <button onClick={onClick} className="text-xs text-red-600 hover:underline dark:text-red-400">
      Revoke
    </button>
  );
}

function UserShares({
  documentId,
  shares,
  onChange,
}: {
  documentId: string;
  shares: DocumentShares["users"];
  onChange: () => void;
}) {
  const { user } = useAuth();
  const [username, setUsername] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleShare(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.post(`/documents/${documentId}/shares/users`, { username });
      setUsername("");
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to share");
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(userId: string) {
    try {
      await api.delete(`/documents/${documentId}/shares/users/${userId}`);
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to revoke");
    }
  }

  return (
    <div className="mb-4">
      <p className="mb-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400">
        Shared with specific people
      </p>
      <form onSubmit={handleShare} className="mb-2 flex gap-2">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username to share with"
          required
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-ink disabled:opacity-50 dark:bg-brand-light dark:text-ink dark:hover:bg-brand"
        >
          Share
        </button>
      </form>
      {error && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
      {shares.length > 0 && (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {shares.map((s) => (
            <li key={s.user_id} className="flex items-center justify-between py-2 text-sm">
              <span className="text-slate-700 dark:text-slate-300">
                {s.username}
                <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">
                  shared {formatDate(s.created_at)}
                  {s.granted_by ? ` by ${s.granted_by}` : ""}
                </span>
              </span>
              <RevokeButton
                show={user?.role === "super_admin" || user?.username === s.granted_by}
                onClick={() => handleRevoke(s.user_id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ZoneShares({
  documentId,
  shares,
  zones,
  onChange,
}: {
  documentId: string;
  shares: DocumentShares["zones"];
  zones: Zone[];
  onChange: () => void;
}) {
  const { user } = useAuth();
  const [zoneId, setZoneId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const sharedIds = new Set(shares.map((s) => s.zone_id));
  const options = zones.filter((z) => !sharedIds.has(z.id));

  async function handleShare(e: React.FormEvent) {
    e.preventDefault();
    if (!zoneId) return;
    setError(null);
    setBusy(true);
    try {
      await api.post(`/documents/${documentId}/shares/zones`, { zone_id: zoneId });
      setZoneId("");
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to share");
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(id: string) {
    try {
      await api.delete(`/documents/${documentId}/shares/zones/${id}`);
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to revoke");
    }
  }

  return (
    <div className="mb-4">
      <p className="mb-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400">
        Shared with everyone who has access to a zone
      </p>
      <form onSubmit={handleShare} className="mb-2 flex gap-2">
        <select
          value={zoneId}
          onChange={(e) => setZoneId(e.target.value)}
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          <option value="">Select a zone…</option>
          {options.map((z) => (
            <option key={z.id} value={z.id}>
              {z.name}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={busy || !zoneId}
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-ink disabled:opacity-50 dark:bg-brand-light dark:text-ink dark:hover:bg-brand"
        >
          Share
        </button>
      </form>
      {error && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
      {shares.length > 0 && (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {shares.map((s) => (
            <li key={s.zone_id} className="flex items-center justify-between py-2 text-sm">
              <span className="text-slate-700 dark:text-slate-300">
                {s.zone_name}
                <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">
                  shared {formatDate(s.created_at)}
                  {s.granted_by ? ` by ${s.granted_by}` : ""}
                </span>
              </span>
              <RevokeButton
                show={user?.role === "super_admin" || user?.username === s.granted_by}
                onClick={() => handleRevoke(s.zone_id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ProjectShares({
  documentId,
  shares,
  projects,
  onChange,
}: {
  documentId: string;
  shares: DocumentShares["projects"];
  projects: Project[];
  onChange: () => void;
}) {
  const { user } = useAuth();
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const sharedIds = new Set(shares.map((s) => s.project_id));
  const options = projects.filter((p) => !sharedIds.has(p.id));

  async function handleShare(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setError(null);
    setBusy(true);
    try {
      await api.post(`/documents/${documentId}/shares/projects`, { project_id: projectId });
      setProjectId("");
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to share");
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(id: string) {
    try {
      await api.delete(`/documents/${documentId}/shares/projects/${id}`);
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to revoke");
    }
  }

  return (
    <div>
      <p className="mb-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400">
        Shared with everyone who has access to a project
      </p>
      <form onSubmit={handleShare} className="mb-2 flex gap-2">
        <select
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          <option value="">Select a project…</option>
          {options.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={busy || !projectId}
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-ink disabled:opacity-50 dark:bg-brand-light dark:text-ink dark:hover:bg-brand"
        >
          Share
        </button>
      </form>
      {error && <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
      {shares.length > 0 && (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {shares.map((s) => (
            <li key={s.project_id} className="flex items-center justify-between py-2 text-sm">
              <span className="text-slate-700 dark:text-slate-300">
                {s.project_name}
                <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">
                  shared {formatDate(s.created_at)}
                  {s.granted_by ? ` by ${s.granted_by}` : ""}
                </span>
              </span>
              <RevokeButton
                show={user?.role === "super_admin" || user?.username === s.granted_by}
                onClick={() => handleRevoke(s.project_id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
