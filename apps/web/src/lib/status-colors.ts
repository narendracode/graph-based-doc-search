export function statusBadgeClass(status: string): string {
  if (status === "completed") {
    return "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300";
  }
  if (status === "failed") {
    return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300";
  }
  return "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300";
}
