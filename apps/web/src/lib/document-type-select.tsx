"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentType } from "@/lib/types";

const NEW_TYPE_OPTION = "__new__";

/** A document-type picker that doubles as the one place new types get created —
 * if what's needed isn't in the list yet, anyone can add it right here and it's
 * immediately available everywhere else a document type is picked (uploads, other
 * projects' checklists). Self-fetches its own options so callers don't each need
 * their own /document-types state. */
export function DocumentTypeSelect({
  value,
  onChange,
  disabled,
  className,
}: {
  value: string;
  onChange: (id: string, type: DocumentType) => void;
  disabled?: boolean;
  className?: string;
}) {
  const [types, setTypes] = useState<DocumentType[]>([]);
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<DocumentType[]>("/document-types").then(setTypes).catch(() => {});
  }, []);

  async function handleCreate() {
    if (!newName.trim()) return;
    setError(null);
    setBusy(true);
    try {
      const created = await api.post<DocumentType>("/document-types", { name: newName });
      setTypes((prev) => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)));
      setNewName("");
      setAdding(false);
      onChange(created.id, created);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add document type");
    } finally {
      setBusy(false);
    }
  }

  if (adding) {
    // A plain div, not a <form> — this can render inside a parent <form> (e.g. the
    // checklist item create form), and nested <form> elements are invalid HTML that
    // browsers silently break in confusing ways (submits bubble to the wrong form).
    return (
      <div className={`flex gap-2 ${className ?? ""}`}>
        <input
          autoFocus
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleCreate();
            }
          }}
          placeholder="New document type name"
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <button
          type="button"
          onClick={handleCreate}
          disabled={busy}
          className="rounded-md bg-brand px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-brand-light dark:text-ink"
        >
          Add
        </button>
        <button
          type="button"
          onClick={() => {
            setAdding(false);
            setError(null);
          }}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600"
        >
          Cancel
        </button>
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      </div>
    );
  }

  return (
    <select
      disabled={disabled}
      className={`w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 ${className ?? ""}`}
      value={value}
      onChange={(e) => {
        if (e.target.value === NEW_TYPE_OPTION) {
          setAdding(true);
          return;
        }
        const type = types.find((t) => t.id === e.target.value);
        if (type) onChange(type.id, type);
      }}
    >
      <option value="" disabled>
        Select a document type…
      </option>
      {types.map((t) => (
        <option key={t.id} value={t.id}>
          {t.name}
        </option>
      ))}
      <option value={NEW_TYPE_OPTION}>+ Add new document type…</option>
    </select>
  );
}
