"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import {
  ACCEPTED_FILE_TYPES,
  ACCEPTED_FILE_TYPES_LABEL,
  STATUS_LABELS,
  type ChecklistItem,
  type DocumentOut,
  type Project,
  type Zone,
} from "@/lib/types";
import { statusBadgeClass } from "@/lib/status-colors";
import { DocumentTypeSelect } from "@/lib/document-type-select";

interface TrackedUpload {
  key: string;
  filename: string;
  document?: DocumentOut;
  error?: string;
}

export default function UploadPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [docTypeId, setDocTypeId] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([]);
  const [checklistItemId, setChecklistItemId] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [uploads, setUploads] = useState<TrackedUpload[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get<Zone[]>("/zones").then(setZones).catch(() => {});
    api.get<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  // The checklist dropdown depends on whichever project the upload will actually
  // land in — the explicitly selected one, or the default project if none is
  // picked (leaving "project" blank doesn't mean "skip checklist enforcement",
  // it just means the default project's own checklist, if any, applies instead).
  // checklistItemId itself is reset in the project <select>'s onChange, below —
  // not here — so a stale item id from a previously selected project never gets
  // sent along with a different project.
  useEffect(() => {
    // Guards against a stale response overwriting a newer one — e.g. the default
    // project's (empty) checklist resolving after a just-selected project's
    // non-empty one, which would silently re-enable an upload that should be
    // blocked. Only the result from the most recent effect run is ever applied.
    let ignore = false;
    const defaultProject = projects.find((p) => p.is_default);
    const effectiveProjectId = projectId || defaultProject?.id;
    const items = effectiveProjectId
      ? api.get<ChecklistItem[]>(`/projects/${effectiveProjectId}/checklist-items`).catch(() => [])
      : Promise.resolve([]);
    items.then((result) => {
      if (!ignore) setChecklistItems(result);
    });
    return () => {
      ignore = true;
    };
  }, [projectId, projects]);

  // Poll status for any upload still in flight.
  useEffect(() => {
    const inFlight = uploads.filter(
      (u) => u.document && !["completed", "failed"].includes(u.document.status)
    );
    if (inFlight.length === 0) return;

    const timer = setInterval(async () => {
      for (const u of inFlight) {
        try {
          const fresh = await api.get<DocumentOut>(`/documents/${u.document!.id}/status`);
          setUploads((prev) => prev.map((p) => (p.key === u.key ? { ...p, document: fresh } : p)));
        } catch {
          // ignore transient polling errors
        }
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [uploads]);

  const UPLOAD_CONCURRENCY = 4;

  const uploadOne = useCallback(
    async (file: File) => {
      const key = `${file.name}-${Date.now()}-${Math.random()}`;
      setUploads((prev) => [{ key, filename: file.name }, ...prev]);

      if (checklistItems.length > 0 && !checklistItemId) {
        setUploads((prev) =>
          prev.map((p) =>
            p.key === key
              ? { ...p, error: "This project has a checklist — pick which item this satisfies" }
              : p
          )
        );
        return;
      }
      if (!checklistItemId && !docTypeId) {
        setUploads((prev) =>
          prev.map((p) => (p.key === key ? { ...p, error: "Pick a document type first" } : p))
        );
        return;
      }

      const form = new FormData();
      form.append("file", file);
      // When uploading against a checklist item, its required document type is
      // used automatically — no separate type field needed or sent.
      if (checklistItemId) {
        form.append("checklist_item_id", checklistItemId);
      } else {
        form.append("doc_type_id", docTypeId);
      }
      if (zoneId) form.append("zone_id", zoneId);
      if (projectId) form.append("project_id", projectId);

      try {
        const document = await api.post<DocumentOut>("/documents", form);
        setUploads((prev) => prev.map((p) => (p.key === key ? { ...p, document } : p)));
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Upload failed";
        setUploads((prev) => prev.map((p) => (p.key === key ? { ...p, error: message } : p)));
      }
    },
    [docTypeId, zoneId, projectId, checklistItemId, checklistItems]
  );

  const uploadFiles = useCallback(
    async (files: FileList | File[]) => {
      // Bulk drops (10-20+ files) fire concurrently, capped, rather than one at a
      // time — a large batch would otherwise trickle in over many round trips.
      const queue = Array.from(files);
      let index = 0;
      async function worker() {
        while (index < queue.length) {
          const file = queue[index++];
          await uploadOne(file);
        }
      }
      await Promise.all(Array.from({ length: UPLOAD_CONCURRENCY }, worker));
    },
    [uploadOne]
  );

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-xl font-semibold text-slate-900 dark:text-slate-100">Upload documents</h1>
      <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">
        Drop one or more documents ({ACCEPTED_FILE_TYPES_LABEL}). Zone and project are
        optional — documents without them go to the default zone and default project,
        visible to everyone.
      </p>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Document type
          </label>
          {checklistItems.length > 0 ? (
            <p className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400">
              {checklistItemId ? (
                <>
                  {checklistItems.find((i) => i.id === checklistItemId)?.document_type_name}{" "}
                  <span className="text-xs">(set by the checklist item)</span>
                </>
              ) : (
                <span className="text-slate-400 dark:text-slate-500">
                  Pick a checklist item below
                </span>
              )}
            </p>
          ) : (
            <DocumentTypeSelect value={docTypeId} onChange={(id) => setDocTypeId(id)} />
          )}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Zone (optional)
          </label>
          <select
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            value={zoneId}
            onChange={(e) => setZoneId(e.target.value)}
          >
            <option value="">Default zone</option>
            {zones
              .filter((z) => !z.is_default)
              .map((z) => (
                <option key={z.id} value={z.id}>
                  {z.name}
                </option>
              ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Project (optional)
          </label>
          <select
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            value={projectId}
            onChange={(e) => {
              setProjectId(e.target.value);
              setChecklistItemId("");
            }}
          >
            <option value="">Default project</option>
            {projects
              .filter((p) => !p.is_default)
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
          </select>
        </div>
      </div>

      {checklistItems.length > 0 && (
        <div className="mb-6">
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Checklist item (required)
          </label>
          <select
            required
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 sm:w-1/3 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            value={checklistItemId}
            onChange={(e) => setChecklistItemId(e.target.value)}
          >
            <option value="" disabled>
              Select a checklist item…
            </option>
            {checklistItems.map((item) => (
              <option key={item.id} value={item.id}>
                {item.document_type_name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            This project has a document checklist, so every upload here must be tagged
            to the item it satisfies — its document type is set automatically, and the
            upload is sent for admin approval before it counts toward the project&apos;s
            completion.
          </p>
        </div>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${
          dragActive
            ? "border-slate-500 bg-slate-100 dark:border-slate-400 dark:bg-slate-800"
            : "border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-900"
        }`}
      >
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Drag and drop documents here
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">or click to browse</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_FILE_TYPES}
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) uploadFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {uploads.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
            This session&apos;s uploads
          </h2>
          <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
            {uploads.map((u) => (
              <li key={u.key} className="flex items-center justify-between px-4 py-3 text-sm">
                <span className="truncate pr-4 text-slate-700 dark:text-slate-300">{u.filename}</span>
                {u.error ? (
                  <span className="text-red-600 dark:text-red-400">{u.error}</span>
                ) : (
                  <StatusBadge status={u.document?.status} detail={u.document?.status_detail} />
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status, detail }: { status?: string; detail?: string | null }) {
  if (!status) {
    return <span className="text-xs text-slate-400 dark:text-slate-500">Uploading…</span>;
  }
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(status)}`}
      title={detail ?? undefined}
    >
      {STATUS_LABELS[status as keyof typeof STATUS_LABELS] ?? status}
    </span>
  );
}
