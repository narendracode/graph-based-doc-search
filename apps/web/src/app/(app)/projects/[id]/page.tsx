"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatDate } from "@/lib/format";
import { reviewStampClass, statusBadgeClass } from "@/lib/status-colors";
import {
  CHECKLIST_ITEM_STATUS_LABELS,
  type ChecklistDocument,
  type ChecklistItemWithStatus,
  type ProjectChecklist,
} from "@/lib/types";
import { ChecklistEditor } from "./checklist-editor";
import { ReviewControls } from "@/lib/review-controls";

export default function ProjectChecklistPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const router = useRouter();
  const [checklist, setChecklist] = useState<ProjectChecklist | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [managing, setManaging] = useState(false);

  function load() {
    api
      .get<ProjectChecklist>(`/projects/${id}/checklist`)
      .then(setChecklist)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load checklist"));
  }

  useEffect(load, [id]);

  async function handleDeleteProject() {
    if (!confirm(`Delete "${checklist?.project_name}"? This can't be undone.`)) return;
    setDeleteError(null);
    try {
      await api.delete(`/projects/${id}`);
      router.replace("/projects");
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : "Failed to delete project");
    }
  }

  if (error) return <p className="text-sm text-red-600 dark:text-red-400">{error}</p>;
  if (!checklist) return <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href="/projects"
        className="mb-4 inline-block text-sm text-slate-500 hover:underline dark:text-slate-400"
      >
        ← Back to projects
      </Link>

      <div className="mb-6 rounded-xl border border-slate-200 bg-white shadow-sm p-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {checklist.project_name}
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {checklist.total_items === 0
                ? "No checklist defined for this project yet."
                : `${checklist.approved_count} of ${checklist.total_items} required documents approved`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {checklist.project_status !== "no_checklist" && (
              <span
                className={`rounded-full px-3 py-1 text-sm font-medium ${statusBadgeClass(
                  checklist.project_status
                )}`}
              >
                {checklist.project_status_label}
              </span>
            )}
            {user?.role === "super_admin" && (
              <>
                <button
                  onClick={() => setManaging((v) => !v)}
                  className="text-sm text-slate-500 hover:underline dark:text-slate-400"
                >
                  {managing ? "Done" : "Manage checklist"}
                </button>
                <button
                  onClick={handleDeleteProject}
                  className="text-sm text-red-600 hover:underline dark:text-red-400"
                >
                  Delete project
                </button>
              </>
            )}
          </div>
        </div>
        {deleteError && (
          <p className="mt-3 text-sm text-red-600 dark:text-red-400">{deleteError}</p>
        )}
        {managing && <ChecklistEditor projectId={id} onChange={load} />}
      </div>

      {checklist.items.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {user?.role === "super_admin"
            ? 'This project doesn’t have a checklist yet — use "Manage checklist" above to add the first item.'
            : "This project doesn't have a document checklist yet."}
        </p>
      ) : (
        <ul className="space-y-4">
          {checklist.items.map((item) => (
            <ChecklistItemCard
              key={item.id}
              item={item}
              isSuperAdmin={user?.role === "super_admin"}
              onReviewed={load}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function ChecklistItemCard({
  item,
  isSuperAdmin,
  onReviewed,
}: {
  item: ChecklistItemWithStatus;
  isSuperAdmin: boolean;
  onReviewed: () => void;
}) {
  const [showHistory, setShowHistory] = useState(false);
  const doc = item.latest_document;
  // Reviewable once ingestion has settled either way — including "failed", so a
  // reviewer isn't permanently blocked from rejecting a bad/corrupt upload just
  // because the pipeline couldn't parse it.
  const isSettled = doc && (doc.status === "completed" || doc.status === "failed");
  const needsDecision = isSuperAdmin && isSettled && doc.review_status === null;

  return (
    <li className="rounded-xl border border-slate-200 bg-white shadow-sm p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
            {item.document_type_name}
          </p>
          {item.description && (
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{item.description}</p>
          )}
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(
            item.item_status
          )}`}
        >
          {CHECKLIST_ITEM_STATUS_LABELS[item.item_status]}
        </span>
      </div>

      {doc ? (
        <div className="mt-3 rounded-md bg-slate-50 p-3 dark:bg-slate-800/50">
          <div className="flex items-start justify-between gap-3">
            <Link
              href={doc.url}
              className="text-sm font-medium text-slate-900 hover:underline dark:text-slate-100"
            >
              {doc.filename}
            </Link>
            {doc.review_status && (
              <span className={reviewStampClass(doc.review_status)}>{doc.review_status}</span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Uploaded by {doc.uploaded_by ?? "an unknown user"} on {formatDate(doc.created_at)}
            {doc.status === "failed" && " · processing failed, but it can still be reviewed"}
            {doc.status !== "completed" && doc.status !== "failed" && ` · still ${doc.status}`}
          </p>
          {doc.review_status && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {doc.review_status === "approved" ? "Approved" : "Rejected"}
              {doc.reviewed_by ? ` by ${doc.reviewed_by}` : ""}
              {doc.reviewed_at ? ` on ${formatDate(doc.reviewed_at)}` : ""}
            </p>
          )}
          {doc.review_status === "rejected" && doc.review_feedback && (
            <p className="mt-2 rounded-md border border-reject/30 bg-reject/5 p-2 text-xs text-reject dark:border-reject-light/30 dark:text-reject-light">
              {doc.review_feedback}
            </p>
          )}

          {needsDecision && <ReviewControls documentId={doc.id} onReviewed={onReviewed} />}
        </div>
      ) : (
        <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">
          No document uploaded yet — upload one from the Upload page and select this
          checklist item.
        </p>
      )}

      {item.documents.length > 1 && (
        <div className="mt-2">
          <button
            onClick={() => setShowHistory((v) => !v)}
            className="text-xs text-slate-500 hover:underline dark:text-slate-400"
          >
            {showHistory ? "Hide" : "Show"} earlier submissions ({item.documents.length - 1})
          </button>
          {showHistory && (
            <ul className="mt-2 space-y-2 border-l-2 border-slate-200 pl-3 dark:border-slate-700">
              {item.documents.slice(1).map((d) => (
                <HistoryEntry key={d.id} doc={d} />
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}

function HistoryEntry({ doc }: { doc: ChecklistDocument }) {
  return (
    <li className="text-xs text-slate-500 dark:text-slate-400">
      <Link href={doc.url} className="hover:underline">
        {doc.filename}
      </Link>{" "}
      · {formatDate(doc.created_at)} ·{" "}
      <span className={doc.review_status === "rejected" ? "text-red-600 dark:text-red-400" : ""}>
        {doc.review_status ?? "pending review"}
      </span>
      {doc.review_status === "rejected" && doc.review_feedback && `: ${doc.review_feedback}`}
    </li>
  );
}

