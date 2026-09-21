export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

interface Provenance {
  uploaded_by: string | null;
  created_at: string;
  last_uploaded_at: string;
}

/** "Uploaded by X on DATE" plus a re-upload note if the content was ever replaced —
 * the provenance line shown wherever a document is listed, so users can tell who put
 * it there and whether they're looking at the original or a refreshed version. */
export function provenanceText({ uploaded_by, created_at, last_uploaded_at }: Provenance): string {
  const uploader = uploaded_by ?? "an unknown user";
  const created = formatDate(created_at);
  const base = `Uploaded by ${uploader} on ${created}`;
  if (last_uploaded_at !== created_at) {
    return `${base} · last re-uploaded ${formatDate(last_uploaded_at)}`;
  }
  return base;
}
