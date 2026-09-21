export function statusBadgeClass(status: string): string {
  if (status === "completed" || status === "approved") {
    return "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300";
  }
  if (status === "failed" || status === "rejected") {
    return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300";
  }
  if (status === "not_uploaded" || status === "no_checklist") {
    return "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400";
  }
  return "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300";
}

/** The one place in the app that gets the "ink stamp" treatment (see .stamp in
 * globals.css) — an admin's approve/reject decision on a checklist document,
 * rendered like a physical approval stamp. Reserved for that single moment so
 * it stays a signature, not a generic badge style reused everywhere. */
export function reviewStampClass(decision: "approved" | "rejected"): string {
  return decision === "approved"
    ? "stamp border-approve text-approve dark:border-approve-light dark:text-approve-light"
    : "stamp border-reject text-reject dark:border-reject-light dark:text-reject-light";
}
