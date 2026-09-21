"""Turns raw graph relatedness data (which entities/project two documents share) into
a plain-language explanation with a supporting excerpt pulled from the related
document's own text — so a business user can see *why* two documents are connected,
not just a machine-readable label like "shares 2 entities"."""

import re
import uuid

from sqlalchemy.orm import Session

from api.models.document import DocumentChunk

EXCERPT_CONTEXT_CHARS = 90
# Preference order for which shared entity is most worth explaining and quoting —
# who's involved matters more to a reader than a coincidentally-matching amount.
TYPE_PRIORITY = ["Organization", "Person", "ContractRef", "Date", "Amount"]


def _join(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def _describe(shared_entities: list[dict], shared_project: str | None) -> str:
    by_type: dict[str, list[str]] = {}
    for e in shared_entities:
        by_type.setdefault(e["type"], []).append(e["name"])

    sentences = []
    if by_type.get("Organization"):
        sentences.append(f"Both documents name {_join(by_type['Organization'][:3])}")
    if by_type.get("Person"):
        people = by_type["Person"][:3]
        verb = "is" if len(people) == 1 else "are"
        sentences.append(f"{_join(people)} {verb} named in both")
    if by_type.get("ContractRef"):
        refs = by_type["ContractRef"][:2]
        label = "reference" if len(refs) == 1 else "references"
        sentences.append(f"they cite the same contract {label} {_join(refs)}")
    if by_type.get("Date"):
        sentences.append(f"both mention {_join(by_type['Date'][:2])}")

    if not sentences:
        if shared_project:
            return f"Both documents are filed under the same project — {shared_project}."
        return "Related through the archive's knowledge graph."

    text = "; ".join(sentences)
    text = text[0].upper() + text[1:] + "."
    if shared_project:
        text += f" Both belong to the {shared_project} project."
    return text


def _find_excerpt(db: Session, document_id: str, needle: str) -> str | None:
    chunk = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == uuid.UUID(document_id),
            DocumentChunk.content.ilike(f"%{needle}%"),
        )
        .first()
    )
    if chunk is None:
        return None
    content = chunk.content
    idx = content.lower().find(needle.lower())
    if idx == -1:
        return None
    start = max(0, idx - EXCERPT_CONTEXT_CHARS)
    end = min(len(content), idx + len(needle) + EXCERPT_CONTEXT_CHARS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(content) else ""
    excerpt = re.sub(r"\s+", " ", content[start:end]).strip()
    return f"{prefix}{excerpt}{suffix}"


def explain(db: Session, related: list[dict]) -> list[dict]:
    """Adds `reason` (plain-language explanation) and `excerpt` (supporting text from
    the related document) to each raw relatedness record from graph.related_documents."""
    explained = []
    for r in related:
        reason = _describe(r["shared_entities"], r["shared_project"])

        excerpt = None
        ordered = sorted(
            r["shared_entities"],
            key=lambda e: TYPE_PRIORITY.index(e["type"]) if e["type"] in TYPE_PRIORITY else 99,
        )
        for entity in ordered:
            excerpt = _find_excerpt(db, r["id"], entity["name"])
            if excerpt:
                break

        explained.append({**r, "reason": reason, "excerpt": excerpt})
    return explained
