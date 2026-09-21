"use client";

import { use, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { API_URL, api, ApiError } from "@/lib/api";
import {
  STATUS_LABELS,
  type ChunkOut,
  type DocumentGraph as DocumentGraphType,
  type DocumentOut,
  type RelatedDocument,
} from "@/lib/types";
import { provenanceText } from "@/lib/format";
import { statusBadgeClass } from "@/lib/status-colors";
import { GraphView } from "./graph-view";
import { ShareSection } from "./share-section";
import { RetagControl } from "./retag-control";

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [related, setRelated] = useState<RelatedDocument[]>([]);
  const [chunks, setChunks] = useState<ChunkOut[] | null>(null);
  const [docGraph, setDocGraph] = useState<DocumentGraphType | null>(null);
  const [extractionTab, setExtractionTab] = useState<"chunks" | "graph">("graph");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const reuploadRef = useRef<HTMLInputElement>(null);

  async function load() {
    try {
      const d = await api.get<DocumentOut>(`/documents/${id}`);
      setDoc(d);
      if (d.status === "completed") {
        api.get<RelatedDocument[]>(`/documents/${id}/related`).then(setRelated).catch(() => {});
        api.get<ChunkOut[]>(`/documents/${id}/chunks`).then(setChunks).catch(() => {});
        api.get<DocumentGraphType>(`/documents/${id}/graph`).then(setDocGraph).catch(() => {});
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load document");
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 4000);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleDelete() {
    if (!confirm("Delete this document? This cannot be undone.")) return;
    setBusy(true);
    try {
      await api.delete(`/documents/${id}`);
      router.replace("/documents");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
      setBusy(false);
    }
  }

  async function handleReupload(file: File) {
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const updated = await api.post<DocumentOut>(`/documents/${id}/reupload`, form);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Reupload failed");
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="text-sm text-red-600 dark:text-red-400">{error}</p>;
  if (!doc) return <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href="/documents"
        className="mb-4 inline-block text-sm text-slate-500 hover:underline dark:text-slate-400"
      >
        ← Back to search
      </Link>
      <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{doc.filename}</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{doc.doc_type}</p>
            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{provenanceText(doc)}</p>
            <RetagControl doc={doc} onUpdated={setDoc} />
          </div>
          <StatusBadge status={doc.status} detail={doc.status_detail} />
        </div>

        <div className="flex flex-wrap gap-2">
          <a
            href={`${API_URL}/documents/${id}/download`}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800"
          >
            Download
          </a>
          <button
            onClick={() => reuploadRef.current?.click()}
            disabled={busy}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-800"
          >
            Re-upload
          </button>
          <input
            ref={reuploadRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) handleReupload(e.target.files[0]);
              e.target.value = "";
            }}
          />
          <button
            onClick={handleDelete}
            disabled={busy}
            className="rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950"
          >
            Delete
          </button>
        </div>
      </div>

      <ShareSection documentId={id} />

      {related.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
            Related documents
          </h2>
          <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
            {related.map((r) => (
              <li key={r.id} className="px-4 py-3 text-sm">
                <Link
                  href={r.url}
                  className="font-medium text-slate-900 hover:underline dark:text-slate-100"
                >
                  {r.filename}
                </Link>
                <p className="mt-0.5 text-slate-600 dark:text-slate-300">{r.reason}</p>
                {r.excerpt && (
                  <p className="mt-1.5 border-l-2 border-slate-200 pl-2 text-xs italic text-slate-400 dark:border-slate-700 dark:text-slate-500">
                    &ldquo;{r.excerpt}&rdquo;
                  </p>
                )}
                <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{provenanceText(r)}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {doc.status === "completed" && (chunks || docGraph) && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
            Extracted data — what NBCC Archive pulled out of this document
          </h2>
          <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <div className="flex gap-1 border-b border-slate-200 p-2 dark:border-slate-800">
              <button
                onClick={() => setExtractionTab("graph")}
                className={`rounded-md px-3 py-1 text-xs font-medium ${
                  extractionTab === "graph"
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
              >
                Knowledge graph
              </button>
              <button
                onClick={() => setExtractionTab("chunks")}
                className={`rounded-md px-3 py-1 text-xs font-medium ${
                  extractionTab === "chunks"
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
              >
                Parsed chunks {chunks ? `(${chunks.length})` : ""}
              </button>
            </div>

            <div className="p-4">
              {extractionTab === "graph" ? (
                docGraph && docGraph.nodes.length > 1 ? (
                  <GraphView graph={docGraph} />
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    No entities were extracted from this document — it's only linked to
                    its zone/project.
                  </p>
                )
              ) : (
                <ol className="space-y-3">
                  {(chunks ?? []).map((c) => (
                    <li
                      key={c.id}
                      className="rounded-md border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/50"
                    >
                      <div className="mb-1 flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
                        <span>Chunk {c.chunk_index + 1}</span>
                        <span
                          className={
                            c.has_embedding
                              ? "text-green-600 dark:text-green-400"
                              : "text-slate-400 dark:text-slate-500"
                          }
                        >
                          {c.has_embedding ? "embedded" : "not embedded"}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-300">
                        {c.content}
                      </p>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status, detail }: { status: string; detail?: string | null }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(status)}`}
      title={detail ?? undefined}
    >
      {STATUS_LABELS[status as keyof typeof STATUS_LABELS] ?? status}
    </span>
  );
}
