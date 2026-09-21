import re
import uuid

from sqlalchemy.orm import Session

from api.models.user import User
from api.services import search as search_service
from api.services.ollama_client import chat

SYSTEM_PROMPT = (
    "You are the NBCC document archive assistant. Answer only using the provided "
    "document excerpts. If the excerpts don't contain the answer, say you couldn't "
    "find it in the archive rather than guessing. Keep answers concise.\n\n"
    "Some excerpts may be irrelevant even though they were retrieved — ignore any "
    "that don't actually help answer the question.\n\n"
    "End your reply with exactly one line, listing only the filenames of the "
    "documents you actually used to answer (not every excerpt you were given):\n"
    "SOURCES: filename1.pdf, filename2.pdf\n"
    "or, if none of the excerpts were relevant:\n"
    "SOURCES: none"
)

SOURCES_LINE_RE = re.compile(r"\n?SOURCES:\s*(.*?)\s*$", re.IGNORECASE | re.DOTALL)


def _build_context(matches: list[dict]) -> str:
    blocks = [
        f"[Document: {m['filename']}]\n{m['content']}" for m in matches
    ]
    return "\n\n---\n\n".join(blocks)


def _split_sources(raw_content: str, matches: list[dict]) -> tuple[str, list[uuid.UUID]]:
    """Pulls the trailing `SOURCES: ...` line the model was asked to emit out of the
    visible answer, and resolves it against the retrieved candidates — trusting the
    model's own judgement of what it actually used, rather than guessing from prose."""
    match = SOURCES_LINE_RE.search(raw_content)
    if match is None:
        return raw_content, []

    display_content = raw_content[: match.start()].rstrip()
    named = [name.strip().lower() for name in match.group(1).split(",") if name.strip()]

    seen: set[str] = set()
    cited_ids: list[uuid.UUID] = []
    for m in matches:
        if m["filename"].lower() in named and m["filename"] not in seen:
            seen.add(m["filename"])
            cited_ids.append(m["id"])
    return display_content, cited_ids


def answer(
    db: Session, user: User, history: list[dict], question: str
) -> tuple[str, list[uuid.UUID]]:
    matches = search_service.retrieve_context(db, user, question, limit=5)
    context = _build_context(matches) if matches else "No matching documents were found."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": f"Document excerpts:\n{context}\n\nQuestion: {question}",
        }
    )

    response = chat(messages, stream=False)
    raw_content = response["message"]["content"]
    content, cited_ids = _split_sources(raw_content, matches)
    return content, cited_ids
