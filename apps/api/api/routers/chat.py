import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user
from api.models.chat import ChatMessage, ChatSession, MessageRole
from api.models.document import Document
from api.models.user import User
from api.schemas.chat import ChatMessageIn, ChatMessageOut, ChatSessionOut
from api.services.rag_chat import answer

router = APIRouter(prefix="/chat", tags=["chat"])

# Resending the whole session on every turn makes the prompt (and therefore
# latency, and truncation risk against CHAT_NUM_CTX) grow without bound over a
# long conversation — the last few turns give the model enough to handle a
# natural follow-up question without that.
MAX_HISTORY_MESSAGES = 6


def _message_out(db: Session, m: ChatMessage) -> dict:
    citations = []
    if m.cited_document_ids:
        docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(m.cited_document_ids))}
        for doc_id in m.cited_document_ids:
            doc = docs.get(doc_id)
            if doc:
                citations.append({"id": doc.id, "filename": doc.filename, "url": f"/documents/{doc.id}"})
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "citations": citations,
        "created_at": m.created_at,
    }


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "messages": []}


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat session not found")
    return {"id": session.id, "messages": [_message_out(db, m) for m in session.messages]}


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut)
def post_message(
    session_id: uuid.UUID,
    payload: ChatMessageIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat session not found")

    db.add(ChatMessage(session_id=session.id, role=MessageRole.user, content=payload.content))
    db.commit()

    history = [
        {"role": m.role.value, "content": m.content}
        for m in session.messages[:-1][-MAX_HISTORY_MESSAGES:]
    ]
    reply_text, cited_ids = answer(db, user, history, payload.content)

    reply = ChatMessage(
        session_id=session.id,
        role=MessageRole.assistant,
        content=reply_text,
        cited_document_ids=cited_ids,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return _message_out(db, reply)
