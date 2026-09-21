"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";

/** Approve/reject a checklist document, with optional feedback. Used both on the
 * project checklist page and the document detail page — wherever "awaiting admin
 * review" appears, this is the one place the actual decision gets made. */
export function ReviewControls({
  documentId,
  onReviewed,
}: {
  documentId: string;
  onReviewed: () => void;
}) {
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: "approved" | "rejected") {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/documents/${documentId}/review`, { decision, feedback: feedback || null });
      onReviewed();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to submit review");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 border-t border-slate-200 pt-3 dark:border-slate-700">
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Feedback (optional for approval, recommended if rejecting)"
        rows={2}
        className="mb-2 w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-xs text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
      />
      <div className="flex gap-2">
        <button
          onClick={() => decide("approved")}
          disabled={busy}
          className="rounded-md bg-approve px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={() => decide("rejected")}
          disabled={busy}
          className="rounded-md bg-reject px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
