"""Derived status computation for project checklists.

Item and project status are always computed from the linked documents at read
time, never stored, so nothing can drift out of sync when a document is
uploaded, reuploaded, approved, rejected, or a checklist item is added/removed/
edited — there's no cached status field to forget to update.
"""

from api.models.checklist import ChecklistItem
from api.models.document import Document, ReviewStatus

ItemStatus = str  # "not_uploaded" | "pending_review" | "approved" | "rejected"


def latest_document(item: ChecklistItem) -> Document | None:
    if not item.documents:
        return None
    return max(item.documents, key=lambda d: d.created_at)


def item_status(item: ChecklistItem) -> ItemStatus:
    doc = latest_document(item)
    if doc is None:
        return "not_uploaded"
    if doc.review_status == ReviewStatus.approved:
        return "approved"
    if doc.review_status == ReviewStatus.rejected:
        return "rejected"
    # Covers both "still mid-ingestion" and "ingested but not yet reviewed".
    return "pending_review"


def project_status(items: list[ChecklistItem]) -> tuple[str, str, int, int]:
    """Returns (status, human_label, approved_count, total_items)."""
    total = len(items)
    if total == 0:
        return "no_checklist", "No checklist defined for this project", 0, 0

    approved = sum(1 for item in items if item_status(item) == "approved")
    if approved == total:
        return "completed", "Checklist complete", approved, total
    return (
        "pending",
        f"Pending checklist completion ({approved} of {total} approved)",
        approved,
        total,
    )
