"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ChecklistItem } from "@/lib/types";
import { DocumentTypeSelect } from "@/lib/document-type-select";

export function ChecklistEditor({
  projectId,
  onChange,
}: {
  projectId: string;
  onChange: () => void;
}) {
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [documentTypeId, setDocumentTypeId] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDocumentTypeId, setEditDocumentTypeId] = useState("");
  const [editDescription, setEditDescription] = useState("");

  function load() {
    api
      .get<ChecklistItem[]>(`/projects/${projectId}/checklist-items`)
      .then(setItems)
      .catch(() => {});
  }

  useEffect(load, [projectId]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!documentTypeId) return;
    setError(null);
    setBusy(true);
    try {
      await api.post(`/projects/${projectId}/checklist-items`, {
        document_type_id: documentTypeId,
        description: description || null,
        order_index: items.length,
      });
      setDocumentTypeId("");
      setDescription("");
      load();
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add checklist item");
    } finally {
      setBusy(false);
    }
  }

  function startEdit(item: ChecklistItem) {
    setEditingId(item.id);
    setEditDocumentTypeId(item.document_type_id);
    setEditDescription(item.description ?? "");
  }

  async function handleSaveEdit(itemId: string) {
    setBusy(true);
    try {
      await api.patch(`/projects/${projectId}/checklist-items/${itemId}`, {
        document_type_id: editDocumentTypeId,
        description: editDescription || null,
      });
      setEditingId(null);
      load();
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update checklist item");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(itemId: string) {
    if (!confirm("Remove this checklist item? Documents already uploaded against it stay in the archive, just unlinked from the checklist.")) {
      return;
    }
    setBusy(true);
    try {
      await api.delete(`/projects/${projectId}/checklist-items/${itemId}`);
      load();
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to remove checklist item");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 rounded-md bg-slate-50 p-3 dark:bg-slate-800/50">
      <p className="mb-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
        Required documents for this project — pick from the document type list, or add
        a new type on the spot if what you need isn&apos;t listed yet. Users upload
        against these items, and the project shows as complete once every item is
        approved.
      </p>

      {items.length > 0 && (
        <ul className="mb-3 divide-y divide-slate-200 dark:divide-slate-700">
          {items.map((item) => (
            <li key={item.id} className="py-2">
              {editingId === item.id ? (
                <div className="flex flex-col gap-2">
                  <DocumentTypeSelect
                    value={editDocumentTypeId}
                    onChange={(id) => setEditDocumentTypeId(id)}
                  />
                  <input
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    placeholder="Description (optional)"
                    className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveEdit(item.id)}
                      disabled={busy}
                      className="rounded-md bg-brand px-3 py-1 text-xs font-medium text-white disabled:opacity-50 dark:bg-brand-light dark:text-ink"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="rounded-md border border-slate-300 px-3 py-1 text-xs dark:border-slate-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-800 dark:text-slate-200">
                      {item.document_type_name}
                    </p>
                    {item.description && (
                      <p className="text-xs text-slate-500 dark:text-slate-400">{item.description}</p>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => startEdit(item)}
                      className="text-xs text-slate-500 hover:underline dark:text-slate-400"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="text-xs text-red-600 hover:underline dark:text-red-400"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleCreate} className="flex flex-col gap-2 sm:flex-row">
        <div className="flex-1">
          <DocumentTypeSelect value={documentTypeId} onChange={(id) => setDocumentTypeId(id)} />
        </div>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          className="flex-1 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <button
          type="submit"
          disabled={busy || !documentTypeId}
          className="rounded-md bg-brand px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50 dark:bg-brand-light dark:text-ink"
        >
          Add item
        </button>
      </form>
      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
